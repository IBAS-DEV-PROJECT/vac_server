from app.common.response import CamelModel


class IdCheckResponse(CamelModel):
    available: bool


class SignupRequest(CamelModel):
    id: str
    nickname: str
    password: str
    password_confirm: str


class SignupResponse(CamelModel):
    user_id: str


class LoginRequest(CamelModel):
    id: str
    password: str


class LoginUserResponse(CamelModel):
    id: str
    login_id: str
    nickname: str


class LoginResponse(CamelModel):
    access_token: str
    refresh_token: str
    user: LoginUserResponse
    activate_onboarding: bool


class RefreshTokenRequest(CamelModel):
    refresh_token: str


class TokenResponse(CamelModel):
    access_token: str
    refresh_token: str
