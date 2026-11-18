import time
import uuid
from typing import Optional
from fastapi import APIRouter, Header, Query, Request, HTTPException, status
from sqlalchemy import select
from backend.app.schemas.event_ingest import EventIngestPayload, EventIngestResponse
from backend.app.services.cache import get_cached_project, set_cached_project
from backend.app.services.queue import enqueue_event
from backend.app.database import get_session_maker
from backend.app.models.project import Project

router = APIRouter()

async def authenticate_project(
    api_key_header: Optional[str] = None,
    bearer_auth: Optional[str] = None,
    api_key_query: Optional[str] = None
) -> dict:
    """
    Sub-millisecond project authentication using Redis/in-memory cache.
    Falls back to PostgreSQL lookup and populates cache on first request.
    """
    # Extract API key from header, bearer token, or query parameter
    api_key = api_key_header
    if not api_key and bearer_auth:
        if bearer_auth.startswith("Bearer "):
            api_key = bearer_auth[7:]
        else:
            api_key = bearer_auth
    if not api_key:
        api_key = api_key_query

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key. Pass 'X-Project-Key', 'Authorization: Bearer <key>', or ?api_key=<key>."
        )

    # 1. Fast Cache Lookup (sub-1ms)
    cached = await get_cached_project(api_key)
    if cached:
        return cached

    # 2. Database Lookup on cache miss
    session_maker = get_session_maker()
    async with session_maker() as session:
        stmt = select(Project).where(Project.api_key == api_key)
        res = await session.execute(stmt)
        project = res.scalar_one_or_none()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Project API Key."
            )
            
        proj_data = {
            "id": project.id,
            "name": project.name,
            "slug": project.slug,
            "api_key": project.api_key,
            "settings": project.settings or {}
        }
        await set_cached_project(api_key, proj_data)
        return proj_data

@router.post(
    "/capture",
    response_model=EventIngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest error event (Sub-15ms asynchronous capture)",
    description="Authenticates incoming requests via cached project API key, validates payload, and pushes to high-speed stream for batch ingestion."
)
async def capture_event(
    payload: EventIngestPayload,
    request: Request,
    x_project_key: Optional[str] = Header(None, alias="X-Project-Key"),
    authorization: Optional[str] = Header(None),
    api_key: Optional[str] = Query(None)
):
    start_time = time.perf_counter()
    
    # 1. High-speed cached authentication (<1ms)
    project = await authenticate_project(
        api_key_header=x_project_key,
        bearer_auth=authorization,
        api_key_query=api_key
    )
    
    # 2. Prepare payload for worker
    event_id = str(uuid.uuid4())
    raw_dict = payload.model_dump()
    raw_dict["event_id"] = event_id
    raw_dict["project_id"] = project["id"]
    
    # If client didn't supply IP, extract from request
    if not raw_dict.get("user"):
        raw_dict["user"] = {}
    if not raw_dict["user"].get("ip_address") and request.client:
        raw_dict["user"]["ip_address"] = request.client.host

    # 3. Asynchronously push to Redis stream/queue
    enqueued = await enqueue_event(raw_dict)
    if not enqueued:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ingestion queue full, event dropped"
        )

    latency_ms = (time.perf_counter() - start_time) * 1000.0

    return EventIngestResponse(
        status="accepted",
        event_id=event_id,
        message=f"Event queued successfully in {latency_ms:.2f}ms"
    )

@router.post(
    "/projects/{project_key}/events/",
    response_model=EventIngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    include_in_schema=False
)
async def capture_event_path_compat(
    project_key: str,
    payload: EventIngestPayload,
    request: Request
):
    """SDK compatibility endpoint accepting project_key in URL path."""
    return await capture_event(
        payload=payload,
        request=request,
        x_project_key=project_key
    )
