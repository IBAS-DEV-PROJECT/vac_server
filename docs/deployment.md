# 배포 가이드

AWS Lambda + API Gateway(HTTP API) + Aurora Serverless v2(PostgreSQL) 서버리스 구성.

```
Client → API Gateway (HTTP API v2) → Lambda (FastAPI + Mangum) → RDS Proxy → Aurora Serverless v2
                                          ↓                          ↑
                                    CloudWatch Logs           Secrets Manager
```

## 사전 준비

- AWS SAM CLI, Docker
- 서로 다른 AZ에 있는 **프라이빗 서브넷 2개 이상**과 해당 VPC ID
- Lambda가 Secrets Manager를 호출하므로, 프라이빗 서브넷에 **NAT Gateway** 또는
  **Secrets Manager VPC 엔드포인트**가 필요하다 (엔드포인트 쪽이 저렴하다)

## 배포

```bash
sam build
sam deploy --guided \
  --parameter-overrides VpcId=vpc-xxxx PrivateSubnetIds=subnet-aaa,subnet-bbb
```

배포가 끝나면 Outputs에 `ApiUrl`, `MigrationFunctionName`, `ProxyEndpoint` 가 출력된다.

## 마이그레이션

스키마는 **Alembic**이 관리한다. 앱은 `AUTO_CREATE_TABLES=false` 로 뜨기 때문에 배포
직후 마이그레이션 함수를 1회 호출해야 한다.

```bash
aws lambda invoke --function-name <MigrationFunctionName> /dev/stdout
```

로컬에서 마이그레이션을 다루는 명령:

```bash
alembic upgrade head              # 최신 스키마 적용
alembic downgrade -1              # 한 단계 되돌리기
alembic revision --autogenerate -m "설명"   # 모델 변경 후 새 리비전 생성
```

`migrations/env.py` 가 `app.core.config.settings` 에서 DB URL을 읽으므로 별도 설정이
필요 없다. 로컬은 `.env` 의 `DATABASE_URL`, Lambda는 Secrets Manager 값을 사용한다.

## 동작 확인

```bash
curl "$API_URL/auth/id/check?id=layer2026"
```

## 구성 상세

### Lambda

| 항목 | 값 | 이유 |
| --- | --- | --- |
| 패키징 | 컨테이너 이미지 | `bcrypt`/`greenlet`/`asyncpg` 네이티브 휠을 Amazon Linux용으로 확보 |
| 아키텍처 | arm64 (Graviton) | x86_64 대비 약 20% 저렴 |
| 핸들러 | `app.lambda_handler.handler` | Mangum ASGI 어댑터 |
| lifespan | `off` | 콜드 스타트마다 DDL이 실행되는 것을 방지 |

`API_GATEWAY_BASE_PATH` 로 스테이지 경로(`/{스택명}`)를 제거하므로, 클라이언트는
`{ApiUrl}/auth/login` 처럼 명세서 그대로의 경로를 사용한다.

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

- **Aurora 최소 ACU**: 기본 `0.5`. `0` 으로 두면 유휴 시 자동 일시정지되지만 첫 요청에
  수 초가 추가된다.
- **NAT Gateway**: 시간당 고정비가 발생한다. Secrets Manager VPC 엔드포인트로 대체 가능.
- **RDS Proxy**: vCPU 기준 시간당 과금.

### 콜드 스타트

FastAPI + SQLAlchemy + asyncpg 조합은 초기화가 무거워 콜드 스타트가 1~3초 나올 수
있다. VPC 연결과 Secrets Manager 조회가 여기에 더해진다. 체감이 문제되면
Provisioned Concurrency를 검토하거나, 트래픽이 꾸준하다면 App Runner / ECS Fargate
같은 상시 구동 방식이 더 단순하고 저렴할 수 있다.

## 로컬에서 검증하기

```bash
cfn-lint template.yaml                              # 템플릿 검증
docker build --platform linux/arm64 -t vac-api .    # 이미지 빌드
sam local start-api                                 # 로컬에서 API Gateway 흉내
```
