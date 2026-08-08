## 테스트

- `pytest` + `pytest-asyncio` + `httpx.AsyncClient` 조합 사용
- 테스트 파일명: `test_<대상>.py`, 함수명: `test_<동작>_<조건>_<기대결과>`
- 도메인 구조와 동일하게 `tests/domains/<도메인명>/` 하위에 배치

```python
async def test_create_user_with_valid_data_returns_201(client: AsyncClient):
    response = await client.post("/api/v1/users", json={"email": "a@a.com", "name": "홍길동", "password": "1234"})
    assert response.status_code == 201
```

## 인프라

AWS Lambda + API Gateway(HTTP API) + RDS Proxy + Aurora Serverless v2(PostgreSQL)
서버리스 아키텍처. DB 접근은 SQLAlchemy(asyncpg) + Alembic 마이그레이션.

- 인프라 정의: `template.yaml` (CloudFormation/SAM)
- 배포 절차: `docs/deployment.md`