## 프로젝트 구조

도메인(기능) 단위로 디렉토리를 나누는 방식을 기본으로 합니다.

```
app/
├── main.py                 # FastAPI 앱 진입점
├── core/
│   ├── config.py            # 환경설정 (Settings)
│   ├── security.py          # 인증/보안 관련 (JWT, 해싱 등)
│   ├── exceptions.py        # 커스텀 예외 정의
│   └── logging.py           # 로깅 설정
├── db/
│   ├── base.py               # Base 모델, 세션 관리
│   └── session.py            # DB 세션 dependency
├── domains/                  # 도메인(기능) 단위 모듈
│   ├── user/
│   │   ├── router.py         # 엔드포인트
│   │   ├── schemas.py        # Pydantic 스키마
│   │   ├── models.py         # ORM 모델
│   │   ├── service.py        # 비즈니스 로직
│   │   └── repository.py     # DB 접근 로직
│   └── auth/
│       ├── router.py
│       ├── schemas.py
│       └── service.py
├── common/
│   ├── dependencies.py       # 공통 의존성 (get_current_user 등)
│   ├── response.py           # 공통 응답 포맷
│   └── utils.py
└── tests/
    ├── conftest.py
    └── domains/
        └── user/
            └── test_user_router.py
```

- 도메인이 커지면 `domains/<도메인명>` 내부만 확장, 다른 도메인에 영향 최소화
- 순환 참조 방지를 위해 상위 계층(router) → 하위 계층(service) → 최하위(repository) 방향으로만 의존

---

## 네이밍 컨벤션

| 대상 | 규칙 | 예시 |
| --- | --- | --- |
| 파일/디렉토리 | snake_case | `user_service.py` |
| 클래스 | PascalCase | `UserService`, `UserCreateRequest` |
| 함수/변수 | snake_case | `get_user_by_id` |
| 상수 | UPPER_SNAKE_CASE | `MAX_LOGIN_ATTEMPT` |
| Pydantic 스키마 | 목적 접미사 명시 | `UserCreateRequest`, `UserResponse`, `UserUpdateRequest` |
| DB 모델(ORM) | 단수형 PascalCase, 테이블명은 복수형 snake_case | `class User` → `__tablename__ = "users"` |
| 라우터 prefix | kebab-case, 복수형 리소스명 | `/api/v1/user-profiles` |