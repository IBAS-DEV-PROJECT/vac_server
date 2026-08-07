## API 설계 컨벤션

- 버전 관리: `/api/v1/...` 형태로 prefix에 버전 명시
- RESTful 원칙 준수 (리소스 중심 URL, HTTP 메서드로 행위 구분)

| 메서드 | 용도 |
| --- | --- |
| GET | 조회 |
| POST | 생성 |
| PUT/PATCH | 전체/부분 수정 |
| DELETE | 삭제 |

---

## Pydantic 스키마 컨벤션

- 요청/응답 스키마 분리 (`Request`, `Response` 접미사)
- `orm_mode`(v1) / `model_config = ConfigDict(from_attributes=True)`(v2) 사용해 ORM 객체 직렬화
- 공통 필드는 `Base` 스키마로 분리 후 상속

```python
class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreateRequest(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
```