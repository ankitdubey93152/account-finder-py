from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.routes.health import router as health_router
from api.routes.username import router as username_router
from core.config import settings
from core.exceptions import OSINTError, PlatformUnavailableError, RateLimitedError, ScanTimeoutError
from core.logging import logger, setup_logging
from database.session import init_db

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting OSINT Account & Digital Footprint Analyzer API", env=settings.ENV)
    await init_db()
    yield
    logger.info("Shutting down OSINT Analyzer API")


app = FastAPI(
    title=settings.APP_NAME,
    description="OSINT Account & Digital Footprint Analyzer operating exclusively on publicly available data.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.exception_handler(OSINTError)
async def osint_exception_handler(request: Request, exc: OSINTError) -> JSONResponse:
    logger.warning("OSINT exception occurred", error=exc.message, detail=exc.detail)
    status_code = 400
    if isinstance(exc, ScanTimeoutError):
        status_code = 504
    elif isinstance(exc, RateLimitedError):
        status_code = 429
    elif isinstance(exc, PlatformUnavailableError):
        status_code = 503

    return JSONResponse(
        status_code=status_code,
        content={"error": exc.message, "detail": exc.detail},
    )


app.include_router(health_router)
app.include_router(username_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
