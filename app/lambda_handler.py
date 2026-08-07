"""AWS Lambda 진입점.

- `handler`: API Gateway(HTTP API v2) 요청을 FastAPI 앱으로 전달한다.
- `migrate_handler`: 배포 파이프라인에서 Alembic 마이그레이션을 실행한다.
"""

import logging
import os
from typing import Any

from mangum import Mangum

from app.core.logging import setup_logging
from app.main import app

setup_logging()

logger = logging.getLogger(__name__)

# API Gateway 기본 엔드포인트는 경로 앞에 스테이지명이 붙으므로 이를 제거한다.
BASE_PATH = os.getenv("API_GATEWAY_BASE_PATH", "/")

# Lambda에서는 lifespan을 사용하지 않는다. 스키마 생성은 마이그레이션이 담당하고,
# 콜드 스타트마다 DDL이 실행되는 것을 막기 위함이다.
handler = Mangum(app, lifespan="off", api_gateway_base_path=BASE_PATH)


def migrate_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """`alembic upgrade head` 를 실행한다."""
    from alembic import command
    from alembic.config import Config

    config = Config("/var/task/alembic.ini")
    config.set_main_option("script_location", "/var/task/migrations")

    revision = event.get("revision", "head") if isinstance(event, dict) else "head"
    logger.info("Running alembic upgrade to %s", revision)
    command.upgrade(config, revision)

    return {"status": "ok", "revision": revision}
