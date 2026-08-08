# vac_server

고민 기록 서비스 API 서버. FastAPI + SQLAlchemy(async) 기반 도메인 주도 구조.

## 실행

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env

uvicorn app.main:app --reload
```

- API 문서: http://127.0.0.1:8000/docs
- Base URL: `/api/v1`

로컬에서는 `AUTO_CREATE_TABLES=true`(기본값)라 앱 기동 시 테이블이 자동 생성된다.
운영과 동일하게 마이그레이션으로 스키마를 만들려면 `.env` 에 `AUTO_CREATE_TABLES=false`
를 설정한 뒤 `alembic upgrade head` 를 사용한다. `true` 인 채로 두면 기동 시 테이블이
그대로 자동 생성되어 마이그레이션 검증이 되지 않는다.

## 테스트

```bash
pytest
```

## 배포

AWS Lambda + API Gateway(HTTP API) + RDS Proxy + Aurora Serverless v2 서버리스 구성.

컨테이너 이미지 빌드/푸시만 로컬에서 하고, 나머지 리소스는 `template.yaml` 한 장으로
**AWS 콘솔의 CloudFormation** 이 만든다.

**1. 이미지를 ECR 에 푸시한다.** Lambda 는 arm64 단일 매니페스트만 지원하므로 플래그 3개가
모두 필요하다(이유는 배포 가이드 참고).

```bash
REGION=ap-northeast-2
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
REPO=$ACCOUNT.dkr.ecr.$REGION.amazonaws.com/vac

aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT.dkr.ecr.$REGION.amazonaws.com
docker buildx build --platform linux/arm64 --provenance=false --sbom=false \
  -t $REPO:v1 --push .
```

**2. 스택을 생성한다.** CloudFormation → 스택 생성에서 `template.yaml` 을 업로드하고
`ImageUri`(1단계에서 푸시한 URI), `VpcId`, `PrivateSubnetIds` 를 입력한다. 검토 화면에서
`CAPABILITY_IAM` 과 `CAPABILITY_AUTO_EXPAND` 를 모두 체크해야 한다. 생성에 15~25분 걸린다.

**3. 스키마 마이그레이션을 1회 실행한다.** 하지 않으면 테이블이 없어 모든 API 가 실패한다.
스택 출력 탭의 `MigrationFunctionName` 함수를 Lambda 콘솔에서 빈 이벤트(`{}`)로 테스트하거나,
CLI 로 실행한다.

```bash
aws lambda invoke --function-name <MigrationFunctionName> /dev/stdout
```

사전 준비 조건, 재배포 방법, 구성별 상세 근거는 [docs/deployment.md](docs/deployment.md) 참고.

## 코드 스타일

```bash
black app tests && isort app tests && ruff check app tests
```

## 문서

- API 명세서: [docs/api-spec.md](docs/api-spec.md)
- 기능 명세서: [docs/feature-spec.md](docs/feature-spec.md)
- 배포 가이드: [docs/deployment.md](docs/deployment.md)
- 개발 컨벤션: [.claude/rules/](.claude/rules/)
