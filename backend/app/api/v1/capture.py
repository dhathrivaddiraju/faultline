import time
import uuid
from typing import Optional
from fastapi import APIRouter, Header, Query, Request, HTTPException, status
from sqlalchemy import select

from backend.app.schemas.event_ingest import EventIngestPayload, EventIngestResponse
from backend.app.services.cache import get_cached_project, set_cached_project
from backend.app.services.queue import enqueue_event
from backend.app.services.notifier import latency_tracker
from backend.app.database import get_session_maker
from backend.app.models.project import Project

router = APIRouter()


async def resolve_project_credentials(
    api_key_header: Optional[str] = None,
    bearer_auth: Optional[str] = None,
    api_key_query: Optional[str] = None
) -> dict:
    target_key = api_key_header
    if not target_key and bearer_auth:
        target_key = bearer_auth[7:] if bearer_auth.startswith("Bearer ") else bearer_auth
    if not target_key:
        target_key = api_key_query

    if not target_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing project API key."
        )

    cached_project = await get_cached_project(target_key)
    if cached_project:
        return cached_project

    session_maker = get_session_maker()
    async with session_maker() as session:
        query = select(Project).where(Project.api_key == target_key)
        result = await session.execute(query)
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid project API key."
            )

        project_record = {
            "id": project.id,
            "name": project.name,
            "slug": project.slug,
            "api_key": project.api_key,
            "settings": project.settings or {}
        }
        await set_cached_project(target_key, project_record)
        return project_record


@router.post(
    "/capture",
    response_model=EventIngestResponse,
    status_code=status.HTTP_202_ACCEPTED
)
async def capture_event(
    payload: EventIngestPayload,
    request: Request,
    x_project_key: Optional[str] = Header(None, alias="X-Project-Key"),
    authorization: Optional[str] = Header(None),
    api_key: Optional[str] = Query(None)
):
    start_time = time.perf_counter()

    project = await resolve_project_credentials(
        api_key_header=x_project_key,
        bearer_auth=authorization,
        api_key_query=api_key
    )

    event_id = str(uuid.uuid4())
    event_dict = payload.model_dump()
    event_dict["event_id"] = event_id
    event_dict["project_id"] = project["id"]

    if not event_dict.get("user"):
        event_dict["user"] = {}
    if not event_dict["user"].get("ip_address") and request.client:
        event_dict["user"]["ip_address"] = request.client.host

    enqueued = await enqueue_event(event_dict)
    if not enqueued:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ingestion queue buffer exceeded."
        )

    duration_ms = (time.perf_counter() - start_time) * 1000.0
    latency_tracker.record(duration_ms)

    return EventIngestResponse(
        status="accepted",
        event_id=event_id,
        message=f"Event queued in {duration_ms:.2f}ms"
    )


@router.post(
    "/projects/{project_key}/events/",
    response_model=EventIngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    include_in_schema=False
)
async def capture_event_compatibility(
    project_key: str,
    payload: EventIngestPayload,
    request: Request
):
    return await capture_event(
        payload=payload,
        request=request,
        x_project_key=project_key
    )
