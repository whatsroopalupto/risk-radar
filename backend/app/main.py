"""FastAPI startup entrypoint."""
import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .db import init_db
from .logging_conf import configure_logging
from .api.routes import router
from .config import settings
from .pipeline.locking import JobBusy, exclusive_job


logger = logging.getLogger(__name__)


async def run_ais_collector():
    from .connectors.ais import collect_forever

    try:
        with exclusive_job("ais"):
            await collect_forever()
    except JobBusy:
        logger.warning("AIS collector is already running")
    except Exception:
        logger.exception("AIS collector stopped unexpectedly")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    ais_task = None

    if settings.aisstream_api_key:
        ais_task = asyncio.create_task(
            run_ais_collector(),
            name="ais-collector",
        )
        logger.info("AIS collector background task started")
    else:
        logger.warning("AIS collector not started: AISSTREAM_API_KEY is missing")

    logger.info("Risk Radar API ready")

    try:
        yield
    finally:
        if ais_task:
            ais_task.cancel()
            with suppress(asyncio.CancelledError):
                await ais_task


configure_logging()

app = FastAPI(
    title="Geopolitical Risk Radar",
    version="0.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def errors(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": "Internal server error",
                "type": type(exc).__name__,
            }
        },
    )


app.include_router(router)


@app.exception_handler(JobBusy)
async def job_busy(_: Request, exc: JobBusy) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})
