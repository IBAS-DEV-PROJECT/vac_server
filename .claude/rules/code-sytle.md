## 코드 스타일

- **포매터**: Black
- **import 정렬**: isort
- **린터**: ruff 또는 flake8
- **타입 힌트**: 모든 함수 시그니처에 타입 명시 (mypy로 정적 검사 권장)
- **비동기 처리**: DB, 외부 API 호출은 가능한 `async def` + 비동기 드라이버(`asyncpg`, `httpx.AsyncClient`) 사용
- 라인 길이: 88자 (Black 기본값) 기준

`pyproject.toml` 예시:

```toml
[tool.black]
line-length = 88

[tool.isort]
profile = "black"

[tool.ruff]
line-length = 88
```

---

## 예외 처리

- 도메인별 커스텀 예외를 `core/exceptions.py`에 정의
- 전역 예외 핸들러(`@app.exception_handler`)로 일관된 에러 응답 형식 유지

```python
class UserNotFoundException(Exception):
    def __init__(self, user_id: int):
        self.user_id = user_id

@app.exception_handler(UserNotFoundException)
async def user_not_found_handler(request: Request, exc: UserNotFoundException):
    return JSONResponse(
        status_code=404,
        content={"success": False, "message": f"User {exc.user_id} not found"},
    )
```

---

## 환경 변수 관리

- `pydantic-settings`의 `BaseSettings` 사용
- `.env` 파일은 `.gitignore`에 반드시 포함, `.env.example`만 커밋

```python
class Settings(BaseSettings):
    database_url: str
    secret_key: str
    debug: bool = False

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
```

---

## 로깅

- 표준 `logging` 모듈 사용, uvicorn 로그와 통합
- 요청/응답 미들웨어로 요청 ID, 처리 시간 로깅 권장
- 운영 환경에서는 로그 레벨 INFO 이상, 개발 환경은 DEBUG