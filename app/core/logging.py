import logging

from app.core.config import settings

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def setup_logging() -> None:
    """uvicorn 로거와 동일한 포맷/레벨을 사용하도록 루트 로거를 설정한다."""
    level = logging.DEBUG if settings.debug else logging.INFO
    logging.basicConfig(level=level, format=LOG_FORMAT)

    for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        logging.getLogger(name).setLevel(level)
