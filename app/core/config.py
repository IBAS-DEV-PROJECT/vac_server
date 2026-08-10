import os
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.secrets import get_secret


class Settings(BaseSettings):
    """애플리케이션 환경 설정."""

    database_url: str = "sqlite+aiosqlite:///./vac.db"
    secret_key: str = "local-development-secret-key-change-me!!"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14
    debug: bool = False

    api_v1_prefix: str = "/api/v1"

    # 앱 기동 시 테이블을 자동 생성할지 여부. 운영에서는 Alembic 마이그레이션을
    # 사용하므로 false 로 둔다.
    auto_create_tables: bool = True

    # ---- AWS (Lambda + Aurora Serverless v2) ----
    # 설정되면 Secrets Manager에서 DB 접속 정보를 읽어 database_url 을 대체한다.
    db_secret_arn: str | None = None
    # 시크릿에 담긴 host 대신 사용할 접속 대상. 비워두면 시크릿 값을 그대로 쓴다.
    db_host: str | None = None
    db_port: int | None = None
    db_name: str | None = None
    # Aurora PostgreSQL은 TLS 접속을 요구하므로 asyncpg 접속 시 TLS를 켠다.
    db_ssl_mode: str = "require"
    # 설정되면 Secrets Manager에서 JWT 서명 키를 읽어 secret_key 를 대체한다.
    jwt_secret_arn: str | None = None
    aws_region: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def is_lambda(self) -> bool:
        return bool(os.getenv("AWS_LAMBDA_FUNCTION_NAME"))

    def resolved_database_url(self) -> str:
        """실제 접속에 사용할 DB URL을 반환한다.

        `db_secret_arn` 이 없으면 `database_url` 을 그대로 사용한다(로컬/테스트).
        """
        if not self.db_secret_arn:
            return self.database_url

        secret = get_secret(self.db_secret_arn, self.aws_region)
        username = quote_plus(secret["username"])
        password = quote_plus(secret["password"])
        host = self.db_host or secret["host"]
        port = self.db_port or secret.get("port", 5432)
        database = self.db_name or secret.get("dbname", "vac")

        return f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{database}"

    def resolved_secret_key(self) -> str:
        """JWT 서명에 사용할 키를 반환한다."""
        if not self.jwt_secret_arn:
            return self.secret_key
        return get_secret(self.jwt_secret_arn, self.aws_region)["secret_key"]


settings = Settings()
