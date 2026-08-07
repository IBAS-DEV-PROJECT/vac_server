from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import setup_logging
from app.db.session import init_db
from app.domains.auth.router import router as auth_router
from app.domains.concern.router import router as concern_router
from app.domains.home.router import router as home_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    await init_db()
    yield


app = FastAPI(title="vac API", version="1.0.0", lifespan=lifespan)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {"code": exc.code, "message": exc.message},
        },
    )


api_router = APIRouter(prefix=settings.api_v1_prefix)
api_router.include_router(auth_router)
api_router.include_router(home_router)
api_router.include_router(concern_router)

app.include_router(api_router)


@app.get("/")
def health_check_handler() -> dict:
    return {"ping": "pong"}
