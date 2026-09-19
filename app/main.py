"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import config
from app.clinic import clinic
from app.web.routes import router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    clinic.start()
    try:
        yield
    finally:
        clinic.stop()


app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    description="Continuous physiological change monitoring for waiting-room reassessment.",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=str(config.STATIC_DIR)), name="static")
app.include_router(router)


def create_app() -> FastAPI:
    return app
