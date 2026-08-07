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

## 테스트

```bash
pytest
```

## 코드 스타일

```bash
black app tests && isort app tests && ruff check app tests
```

## 문서

- API 명세서: [docs/api-spec.md](docs/api-spec.md)
- 기능 명세서: [docs/feature-spec.md](docs/feature-spec.md)
- 개발 컨벤션: [.claude/rules/](.claude/rules/)
