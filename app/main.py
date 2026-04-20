from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.routes import auth, health
from app.api.deps import db_session
from app.api.routes.analysis import limiter

from app.api.routes.analysis import router as analysis_router
from app.api.routes.tasks import router as tasks_router
from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import AppException
from app.core.logging import get_logger, setup_logging
from app.core.redis import redis_client
from app.core.responses import error_response

from app.models import Base


setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Application started and database schema ensured.")
    yield
    await redis_client.close()
    await engine.dispose()
    logger.info("Application stopped cleanly.")


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(AppException)
async def app_exception_handler(_: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(exc.message),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=error_response("Request validation failed", details=exc.errors()),
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exception_handler(_: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content=error_response("Rate limit exceeded", details=str(exc)),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content=error_response("Internal server error"),
    )


api_prefix = settings.API_PREFIX
app.include_router(auth.router, prefix=api_prefix)
app.include_router(health.router, prefix=api_prefix)
app.include_router(analysis_router, prefix=api_prefix)
app.include_router(tasks_router, prefix=api_prefix)

Instrumentator().instrument(app).expose(app, include_in_schema=False)
app.mount("/static", StaticFiles(directory="static"), name="static")











