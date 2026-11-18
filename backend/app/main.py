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
logger = logging.getLogger("faultline.main")

_worker_task = None

async def seed_default_project():
    """Ensure a default project exists for immediate zero-config testing."""
    session_maker = get_session_maker()
    async with session_maker() as session:
        demo_key = "fl_live_production_demo_key_99"
        stmt = select(Project).where(Project.api_key == demo_key)
        res = await session.execute(stmt)
        project = res.scalar_one_or_none()
        
        if not project:
            project = Project(
                name="E-Commerce Core & Checkout API",
                slug="ecommerce-checkout-api",
                api_key=demo_key,
                api_secret="fl_sec_prod_secret_8492049182390124",
                platform="python",
                environment="production",
                settings={"alert_threshold": 5, "slack_webhook": "https://hooks.slack.com/services/mock"}
            )
            session.add(project)
            await session.commit()
            await session.refresh(project)
            logger.info(f"Default demo project created. API Key: {demo_key}")

        await set_cached_project(demo_key, {
            "id": project.id,
            "name": project.name,
            "slug": project.slug,
            "api_key": project.api_key,
            "settings": project.settings
        })

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _worker_task
    logger.info("Initializing Faultline Server...")
    
    # 1. Initialize DB & Tables
    await init_engine()
    await create_tables()
    
    # 2. Seed default project
    await seed_default_project()
    
    # 3. Start embedded async ingestion worker
    _worker_task = asyncio.create_task(run_worker())
    logger.info("Faultline Ingestion Worker started in background.")
    
    yield
    
    # Graceful shutdown
    logger.info("Shutting down Faultline Server...")
    stop_worker()
    if _worker_task:
        _worker_task.cancel()
        try:
            await _worker_task
        except asyncio.CancelledError:
            pass

app = FastAPI(
    title="Faultline - AI Error Monitoring Platform",
    description="Sub-15ms asynchronous error capture pipeline with intelligent clustering and Claude 3.5 Sonnet incident remediation.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    q_size = await get_queue_size()
    return {
        "status": "healthy",
        "service": "faultline-api",
        "queue_size": q_size,
        "claude_model": settings.CLAUDE_MODEL,
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    return {
        "message": "Welcome to Faultline - AI Error Monitoring Platform",
        "docs": "/docs",
        "health": "/health",
        "capture_endpoint": f"{settings.API_V1_STR}/capture"
    }
