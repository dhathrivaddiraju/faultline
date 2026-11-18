import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from backend.app.config import settings

logger = logging.getLogger("faultline.database")

Base = declarative_base()

_engine = None
_async_session_maker = None

async def init_engine():
    global _engine, _async_session_maker
    
    # Attempt connecting to primary database (PostgreSQL)
    primary_url = settings.DATABASE_URL
    try:
        engine = create_async_engine(
            primary_url,
            echo=False,
            future=True,
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True
        )
        # Test connection
        async with engine.connect() as conn:
            await conn.execute(Base.metadata.tables.get('projects', None) or "SELECT 1")
        _engine = engine
        logger.info(f"Connected to primary database: {primary_url.split('@')[-1] if '@' in primary_url else primary_url}")
    except Exception as e:
        if settings.USE_SQLITE_IF_NO_POSTGRES:
            fallback_url = settings.SQLITE_FALLBACK_URL
            logger.warning(f"Could not connect to PostgreSQL ({e}). Falling back to SQLite: {fallback_url}")
            _engine = create_async_engine(
                fallback_url,
                echo=False,
                future=True,
                connect_args={"check_same_thread": False}
            )
        else:
            raise e

    _async_session_maker = async_sessionmaker(
        _engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    return _engine

def get_engine():
    global _engine
    if _engine is None:
        # Fallback synchronous creation for quick startup
        try:
            _engine = create_async_engine(
                settings.DATABASE_URL,
                pool_pre_ping=True
            )
        except Exception:
            _engine = create_async_engine(
                settings.SQLITE_FALLBACK_URL,
                connect_args={"check_same_thread": False}
            )
    return _engine

def get_session_maker():
    global _async_session_maker
    if _async_session_maker is None:
        engine = get_engine()
        _async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    return _async_session_maker

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

async def create_tables():
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified and initialized.")
