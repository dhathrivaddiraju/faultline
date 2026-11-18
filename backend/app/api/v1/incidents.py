from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database import get_db
from backend.app.models.incident import Incident
from backend.app.models.event import Event
from backend.app.schemas.incident import IncidentOut, IncidentStatusUpdate
from backend.app.services.ai_analyzer import analyze_incident_with_claude

router = APIRouter()

@router.get("", response_model=list[IncidentOut])
async def list_incidents(
    project_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """List grouped error incidents with filters and search."""
    stmt = select(Incident).order_by(desc(Incident.last_seen))
    
    if project_id:
        stmt = stmt.where(Incident.project_id == project_id)
    if status and status != "all":
        stmt = stmt.where(Incident.status == status)
    if severity and severity != "all":
        stmt = stmt.where(Incident.severity == severity)
    if search:
        search_filter = f"%{search}%"
        stmt = stmt.where(
            (Incident.title.ilike(search_filter)) | 
            (Incident.culprit.ilike(search_filter)) |
            (Incident.exception_type.ilike(search_filter))
        )

    stmt = stmt.limit(limit).offset(offset)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{incident_id}", response_model=dict[str, Any])
async def get_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve full incident details including AI analysis, culprit, and latest event."""
    stmt = select(Incident).where(Incident.id == incident_id)
    result = await db.execute(stmt)
    incident = result.scalar_one_or_none()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Fetch latest raw event for full stack trace inspection
    ev_stmt = select(Event).where(Event.incident_id == incident_id).order_by(desc(Event.created_at)).limit(1)
    ev_res = await db.execute(ev_stmt)
    latest_event = ev_res.scalar_one_or_none()

    latest_event_data = None
    if latest_event:
        latest_event_data = {
            "id": latest_event.id,
            "created_at": latest_event.created_at.isoformat(),
            "message": latest_event.message,
            "stack_trace": latest_event.stack_trace,
            "breadcrumbs": latest_event.breadcrumbs,
            "tags": latest_event.tags,
            "user_context": latest_event.user_context,
            "request_context": latest_event.request_context,
            "environment": latest_event.environment,
            "handled": latest_event.handled,
            "release": latest_event.release
        }

    return {
        "id": incident.id,
        "project_id": incident.project_id,
        "fingerprint": incident.fingerprint,
        "title": incident.title,
        "culprit": incident.culprit,
        "exception_type": incident.exception_type,
        "status": incident.status,
        "severity": incident.severity,
        "first_seen": incident.first_seen.isoformat(),
        "last_seen": incident.last_seen.isoformat(),
        "events_count": incident.events_count,
        "users_impacted": incident.users_impacted,
        "ai_analysis": incident.ai_analysis,
        "assigned_to": incident.assigned_to,
        "created_at": incident.created_at.isoformat(),
        "updated_at": incident.updated_at.isoformat(),
        "latest_event": latest_event_data
    }

@router.patch("/{incident_id}", response_model=IncidentOut)
async def update_incident(
    incident_id: str,
    update_data: IncidentStatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update incident status (e.g. resolve, ignore), severity, or assignee."""
    stmt = select(Incident).where(Incident.id == incident_id)
    result = await db.execute(stmt)
    incident = result.scalar_one_or_none()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    if update_data.status is not None:
        incident.status = update_data.status
    if update_data.severity is not None:
        incident.severity = update_data.severity
    if update_data.assigned_to is not None:
        incident.assigned_to = update_data.assigned_to

    await db.commit()
    await db.refresh(incident)
    return incident

@router.post("/{incident_id}/ai-analyze")
async def trigger_ai_analysis(
    incident_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger Claude 3.5 Sonnet root-cause analysis and remediation generation."""
    stmt = select(Incident).where(Incident.id == incident_id)
    result = await db.execute(stmt)
    incident = result.scalar_one_or_none()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Fetch latest event
    ev_stmt = select(Event).where(Event.incident_id == incident_id).order_by(desc(Event.created_at)).limit(1)
    ev_res = await db.execute(ev_stmt)
    latest_event = ev_res.scalar_one_or_none()

    stack_trace = latest_event.stack_trace if latest_event else []
    breadcrumbs = latest_event.breadcrumbs if latest_event else []
    request_ctx = latest_event.request_context if latest_event else {}
    user_ctx = latest_event.user_context if latest_event else {}
    message = latest_event.message if latest_event else incident.title

    analysis = await analyze_incident_with_claude(
        title=incident.title,
        exception_type=incident.exception_type,
        message=message,
        culprit=incident.culprit or "",
        stack_trace=stack_trace,
        breadcrumbs=breadcrumbs,
        request_context=request_ctx,
        user_context=user_ctx
    )

    incident.ai_analysis = analysis
    await db.commit()
    await db.refresh(incident)
    
    return {
        "status": "success",
        "incident_id": incident.id,
        "ai_analysis": analysis
    }

@router.get("/{incident_id}/events")
async def get_incident_events(
    incident_id: str,
    limit: int = Query(25, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve raw historical events belonging to this incident cluster."""
    stmt = select(Event).where(Event.incident_id == incident_id).order_by(desc(Event.created_at)).limit(limit)
    res = await db.execute(stmt)
    events = res.scalars().all()
    return events
