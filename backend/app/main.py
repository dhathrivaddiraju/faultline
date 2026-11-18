import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from backend.app.config import settings
from backend.app.database import init_engine, create_tables, get_session_maker
from backend.app.models.project import Project
from backend.app.services.cache import set_cached_project
from backend.app.services.queue import get_queue_size
from backend.app.worker import run_worker, stop_worker
from backend.app.api.v1 import api_v1_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("faultline.server")

_worker_task = None


async def initialize_default_project():
    session_maker = get_session_maker()
    async with session_maker() as session:
        default_key = "fl_live_production_demo_key_99"
        query = select(Project).where(Project.api_key == default_key)
        result = await session.execute(query)
        project = result.scalar_one_or_none()

        if not project:
            project = Project(
                name="E-Commerce Core & Checkout API",
                slug="ecommerce-checkout-api",
                api_key=default_key,
                api_secret="fl_sec_prod_secret_8492049182390124",
                platform="python",
                environment="production",
                settings={"alert_threshold": 5}
            )
            session.add(project)
            await session.commit()
            await session.refresh(project)

        await set_cached_project(default_key, {
            "id": project.id,
            "name": project.name,
            "slug": project.slug,
            "api_key": project.api_key,
            "settings": project.settings
        })


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _worker_task
    await init_engine()
    await create_tables()
    await initialize_default_project()

    _worker_task = asyncio.create_task(run_worker())

    yield

    stop_worker()
    if _worker_task:
        _worker_task.cancel()
        try:
            await _worker_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="Faultline Error Monitoring API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health_check():
    queue_depth = await get_queue_size()
    return {
        "status": "healthy",
        "service": "faultline-api",
        "queue_depth": queue_depth,
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    return {
        "service": "faultline-api",
        "docs": "/docs",
        "health": "/health",
        "ingest_endpoint": f"{settings.API_V1_STR}/capture"
    }
