"""API 명세서(docs/api-spec.md)에 정의된 에러 코드만 다룬다."""


class AppException(Exception):
    """공통 에러 응답 포맷으로 변환되는 예외의 기반 클래스."""

    code: str = "UNKNOWN"
    message: str = ""
    status_code: int = 400

    def __init__(self, message: str | None = None) -> None:
        if message is not None:
            self.message = message
        super().__init__(self.message)


class InvalidCredentialsException(AppException):
    code = "INVALID_CREDENTIALS"
    message = "아이디 또는 비밀번호를 다시 확인해주세요."
    status_code = 401


class DuplicateIdException(AppException):
    code = "DUPLICATE_ID"
    message = "이미 사용 중인 아이디예요. 다시 입력해주세요."
    status_code = 409


class TokenExpiredException(AppException):
    code = "TOKEN_EXPIRED"
    message = "로그인이 만료되었습니다. 다시 로그인해주세요."
    status_code = 401


class RefreshTokenReusedException(AppException):
    code = "REFRESH_TOKEN_REUSED"
    message = "비정상적인 접근이 감지되어 로그아웃되었습니다."
    status_code = 401
