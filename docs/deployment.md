# 배포 가이드

AWS Lambda + API Gateway(HTTP API) + Aurora Serverless v2(PostgreSQL) 서버리스 구성.

```
Client → API Gateway (HTTP API v2) → Lambda (FastAPI + Mangum) → RDS Proxy → Aurora Serverless v2
                                          ↓                          ↑
                                    CloudWatch Logs        Secrets Manager (VPC 엔드포인트)
```

배포는 **AWS 콘솔의 CloudFormation**으로 한다. 컨테이너 이미지 빌드/푸시만 로컬에서
하고, 나머지 리소스는 `template.yaml` 한 장으로 스택이 만들어준다.

## 사전 준비

- Docker (실행 중이어야 한다)
- AWS CLI (ECR 로그인에만 사용)
- 서로 다른 AZ에 있는 **프라이빗 서브넷 2개 이상**과 해당 VPC ID
  - 인터페이스 엔드포인트 제약으로 **한 AZ당 서브넷은 1개만** 선택한다
  - VPC의 `enableDnsSupport` / `enableDnsHostnames` 가 모두 켜져 있어야 한다
- IAM 권한: CloudFormation, Lambda, RDS, EC2(VPC), Secrets Manager, ECR,
  그리고 **`iam:CreateRole` / `iam:AttachRolePolicy`** (스택이 IAM 역할을 만든다)

## 1. 이미지 빌드 & ECR 푸시

ECR 콘솔에서 **리포지토리 생성** → 이름 `vac`.

ECR 상세 화면의 "푸시 명령 보기"에 나오는 `docker build` + `docker push` 2단계 방식은
**쓰지 않는다.** 아래 `buildx` 한 줄을 쓴다.

```bash
REGION=ap-northeast-2
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
REPO=$ACCOUNT.dkr.ecr.$REGION.amazonaws.com/vac

aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT.dkr.ecr.$REGION.amazonaws.com

docker buildx build --platform linux/arm64 --provenance=false --sbom=false \
  -t $REPO:v1 --push .
```

세 가지 플래그가 모두 필요하다.

| 플래그 | 이유 |
| --- | --- |
| `--platform linux/arm64` | Lambda를 arm64로 띄운다. 다르면 배포는 성공하고 호출 시점에 실패한다 |
| `--provenance=false --sbom=false` | 첨부물이 붙으면 결과가 **OCI 이미지 인덱스**가 되는데, Lambda는 인덱스를 지원하지 않는다 (`The image manifest, config or layer media type ... is not supported`) |
| `--push` | 로컬 이미지 스토어를 거치는 2단계 푸시는 다시 인덱스가 될 수 있다 |

푸시 후 매니페스트 형식을 확인한다. `index` 가 아니라 `manifest` 여야 한다.

```bash
aws ecr describe-images --repository-name vac --region $REGION \
  --query 'imageDetails[?contains(imageTags, `v1`)].{Media:imageManifestMediaType,Arch:imageArchitecture}'
```

푸시된 URI(`...amazonaws.com/vac:v1`)를 다음 단계에서 파라미터로 넣는다.

## 2. CloudFormation 스택 생성 (콘솔)

**CloudFormation → 스택 생성 → 새 리소스 사용(표준)**

| 단계 | 입력 |
| --- | --- |
| 템플릿 지정 | "템플릿 파일 업로드" 로 `template.yaml` 선택 |
| 스택 이름 | 짧은 소문자 (예: `vac`) — API Gateway 스테이지 이름이 되어 URL 경로에 들어간다 |
| `ImageUri` | 1단계에서 푸시한 이미지 URI |
| `VpcId` | 드롭다운에서 선택 |
| `PrivateSubnetIds` | 프라이빗 서브넷 2개 이상 (AZ당 1개) |
| `DBMinCapacity` | 개발 단계면 `0` (유휴 시 자동 일시정지) |

마지막 검토 화면에서 아래 두 가지를 체크해야 한다.

- **`CAPABILITY_IAM`** — 스택이 IAM 역할을 생성하는 것에 대한 승인
- **`CAPABILITY_AUTO_EXPAND`** — SAM `Transform` 처리에 필요. 빼면 즉시 실패한다.

생성에는 **15~25분** 정도 걸린다 (Aurora와 RDS Proxy가 오래 걸린다). 진행 상황과
실패 원인은 **이벤트** 탭에서 확인한다. 완료되면 **출력** 탭에 `ApiUrl`,
`MigrationFunctionName`, `ProxyEndpoint` 가 나온다.

> 생성에 실패하면 스택은 자동 롤백되어 `ROLLBACK_COMPLETE` 가 되는데, 이 상태에서는
> **업데이트가 불가능하다.** 스택을 삭제하고 처음부터 다시 생성해야 한다.
> 템플릿만 고친 경우라면 이미지를 다시 빌드/푸시할 필요는 없다.

## 3. 마이그레이션

스키마는 **Alembic**이 관리한다. 앱은 `AUTO_CREATE_TABLES=false` 로 뜨기 때문에 배포
직후 마이그레이션 함수를 1회 실행해야 한다. 하지 않으면 테이블이 없어 모든 API가
실패한다.

**Lambda 콘솔 → 출력 탭의 `MigrationFunctionName` 함수 → 테스트 탭 → 이벤트 JSON은
`{}` 그대로 → 테스트** 버튼.

이미지를 새로 푸시해 스키마가 바뀐 경우에도 같은 방법으로 다시 실행한다.

로컬에서 마이그레이션을 다루는 명령:

```bash
alembic upgrade head              # 최신 스키마 적용
alembic downgrade -1              # 한 단계 되돌리기
alembic revision --autogenerate -m "설명"   # 모델 변경 후 새 리비전 생성
```

`migrations/env.py` 가 `app.core.config.settings` 에서 DB URL을 읽으므로 별도 설정이
필요 없다. 로컬은 `.env` 의 `DATABASE_URL`, Lambda는 Secrets Manager 값을 사용한다.

## 4. 동작 확인

```bash
curl "$API_URL/auth/id/check?id=layer2026"
```

## 코드 변경 후 재배포

이미지 태그를 고정(`:latest`)해두면 CloudFormation이 변경을 감지하지 못해 스택
업데이트가 "변경 없음"으로 끝난다. 두 가지 중 하나를 쓴다.

- **태그를 바꾼다** (권장): `:v2`, `:20260808` 등으로 푸시한 뒤 스택 업데이트에서
  `ImageUri` 파라미터만 새 태그로 교체한다. 롤백도 이전 태그로 되돌리면 된다.
- 태그를 유지한다면 Lambda 콘솔에서 각 함수의 이미지를 수동으로 재배포해야 한다.

## 구성 상세

### Lambda

| 항목 | 값 | 이유 |
| --- | --- | --- |
| 패키징 | 컨테이너 이미지 | `bcrypt`/`greenlet`/`asyncpg` 네이티브 휠을 Amazon Linux용으로 확보 |
| 아키텍처 | arm64 (Graviton) | x86_64 대비 약 20% 저렴 |
| 핸들러 | `app.lambda_handler.handler` | Mangum ASGI 어댑터 |
| lifespan | `off` | 콜드 스타트마다 DDL이 실행되는 것을 방지 |

API 함수와 마이그레이션 함수는 **같은 이미지**를 쓰고 `ImageConfig.Command` 로 핸들러만
구분한다. 그래서 푸시는 한 번이면 된다.

`API_GATEWAY_BASE_PATH` 로 스테이지 경로(`/{스택명}`)를 제거하므로, 클라이언트는
`{ApiUrl}/auth/login` 처럼 명세서 그대로의 경로를 사용한다.

### 네트워크

프라이빗 서브넷에는 인터넷으로 나가는 경로가 없다. Lambda가 Secrets Manager를
호출해야 하므로 스택이 **Secrets Manager 인터페이스 VPC 엔드포인트**를 함께 만든다
(`PrivateDnsEnabled: true` 라서 애플리케이션 코드는 수정할 필요가 없다).
NAT Gateway로도 해결되지만 시간당 고정비가 엔드포인트보다 훨씬 비싸다.

CloudWatch Logs 전송은 Lambda 서비스가 처리하므로 별도 엔드포인트가 필요 없다.

### DB 커넥션

Lambda는 실행 환경이 freeze/thaw 되면서 풀에 남은 커넥션이 끊기고, 동시 실행 수만큼
커넥션이 늘어난다. 따라서:

- 애플리케이션은 **`NullPool`** (풀링하지 않음) — `app/db/session.py`
- 실제 풀링은 **RDS Proxy**가 담당
- RDS Proxy가 커넥션을 다중화하므로 **prepared statement 캐시를 비활성화**
  (`prepared_statement_cache_size=0`, `statement_cache_size=0`)
- RDS Proxy는 `RequireTLS: true` 이므로 asyncpg 접속 시 `ssl=require`

> `ssl=require` 는 암호화는 하되 CA 검증은 하지 않는다(libpq의 `require` 와 동일).
> `verify-full` 로 올리려면 RDS CA 번들을 이미지에 포함하고 `DB_SSL_MODE` 를 바꾼다.

### 시크릿

DB 접속 정보와 JWT 서명 키는 Secrets Manager에 저장하고, Lambda에는 **ARN만** 환경
변수로 전달한다. 환경 변수에 평문을 넣으면 Lambda 콘솔에 그대로 노출되기 때문이다.
`app/core/secrets.py` 가 콜드 스타트 시 1회 조회 후 캐시한다.

### 비용에 영향이 큰 항목

트래픽이 0이어도 고정비가 발생한다. 대략적인 월 비용:

| 항목 | 비용 | 비고 |
| --- | --- | --- |
| Aurora Serverless v2 | ~$45 (0.5 ACU 기준) | `DBMinCapacity=0` 이면 유휴 시 거의 0 |
| RDS Proxy | ~$22 | vCPU 기준 시간당 과금 |
| Secrets Manager 엔드포인트 | ~$8 | NAT Gateway(~$45) 대신 사용 |

`DBMinCapacity=0` 은 유휴 시 자동 일시정지되지만 첫 요청에 수 초가 추가된다.

### 콜드 스타트

FastAPI + SQLAlchemy + asyncpg 조합은 초기화가 무거워 콜드 스타트가 1~3초 나올 수
있다. VPC 연결과 Secrets Manager 조회가 여기에 더해진다. 체감이 문제되면
Provisioned Concurrency를 검토하거나, 트래픽이 꾸준하다면 App Runner / ECS Fargate
같은 상시 구동 방식이 더 단순하고 저렴할 수 있다.

## 로컬에서 검증하기

```bash
cfn-lint template.yaml                              # 템플릿 검증
docker build --platform linux/arm64 -t vac-api .    # 이미지 빌드
```
