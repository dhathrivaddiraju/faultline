from datetime import datetime, timezone, timedelta
from typing import Optional, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.models.incident import Incident
from backend.app.models.event import Event
from backend.app.models.metrics import HourlyMetric
from backend.app.services.notifier import latency_tracker

router = APIRouter()


def current_utc_time() -> datetime:
    return datetime.now(timezone.utc)


@router.get("/stats", response_model=dict[str, Any])
async def get_analytics_stats(
    project_id: Optional[str] = Query(None),
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db)
):
    now = current_utc_time()
    window_start = now - timedelta(hours=hours)

    events_query = select(func.count(Event.id)).where(Event.created_at >= window_start)
    if project_id:
        events_query = events_query.where(Event.project_id == project_id)
    total_events = (await db.execute(events_query)).scalar() or 0

    active_incidents_query = select(func.count(Incident.id)).where(
        Incident.status.in_(["unresolved", "investigating"])
    )
    if project_id:
        active_incidents_query = active_incidents_query.where(Incident.project_id == project_id)
    active_incidents = (await db.execute(active_incidents_query)).scalar() or 0

    resolved_incidents_query = select(func.count(Incident.id)).where(Incident.status == "resolved")
    if project_id:
        resolved_incidents_query = resolved_incidents_query.where(Incident.project_id == project_id)
    resolved_incidents = (await db.execute(resolved_incidents_query)).scalar() or 0

    recent_window_start = now - timedelta(minutes=15)
    recent_events_query = select(func.count(Event.id)).where(Event.created_at >= recent_window_start)
    if project_id:
        recent_events_query = recent_events_query.where(Event.project_id == project_id)
    recent_events_count = (await db.execute(recent_events_query)).scalar() or 0
    error_rate_per_minute = round(recent_events_count / 15.0, 2)

    resolved_records_query = select(Incident.created_at, Incident.updated_at).where(
        Incident.status == "resolved"
    )
    if project_id:
        resolved_records_query = resolved_records_query.where(Incident.project_id == project_id)
    resolved_records = (await db.execute(resolved_records_query)).all()

    if resolved_records:
        durations = [
            max(0.0, (rec[1] - rec[0]).total_seconds() / 60.0)
            for rec in resolved_records
            if rec[0] and rec[1]
        ]
        mttr_minutes = round(sum(durations) / len(durations), 1) if durations else 0.0
    else:
        mttr_minutes = 0.0

    bucket_map = {}
    for hour_offset in range(hours):
        bucket_time = (now - timedelta(hours=hours - 1 - hour_offset)).replace(
            minute=0, second=0, microsecond=0
        )
        bucket_key = bucket_time.isoformat()
        bucket_map[bucket_key] = {
            "timestamp": bucket_key,
            "display_time": bucket_time.strftime("%H:%M"),
            "total": 0,
            "critical": 0,
            "error": 0,
            "warning": 0
        }

    metrics_query = select(
        HourlyMetric.bucket_time,
        HourlyMetric.severity,
        func.sum(HourlyMetric.count)
    ).where(HourlyMetric.bucket_time >= window_start)

    if project_id:
        metrics_query = metrics_query.where(HourlyMetric.project_id == project_id)
    metrics_query = metrics_query.group_by(HourlyMetric.bucket_time, HourlyMetric.severity)

    metrics_rows = await db.execute(metrics_query)
    for bucket_timestamp, severity_tier, aggregate_count in metrics_rows.all():
        formatted_key = bucket_timestamp.replace(minute=0, second=0, microsecond=0).isoformat()
        if formatted_key in bucket_map:
            count_val = aggregate_count or 0
            bucket_map[formatted_key]["total"] += count_val
            normalized_tier = (severity_tier or "error").lower()
            if normalized_tier in ("fatal", "critical"):
                bucket_map[formatted_key]["critical"] += count_val
            elif normalized_tier == "warning":
                bucket_map[formatted_key]["warning"] += count_val
            else:
                bucket_map[formatted_key]["error"] += count_val

    timeseries_data = list(bucket_map.values())

    environment_query = select(Event.environment, func.count(Event.id)).where(
        Event.created_at >= window_start
    )
    if project_id:
        environment_query = environment_query.where(Event.project_id == project_id)
    environment_query = environment_query.group_by(Event.environment)
    environment_rows = (await db.execute(environment_query)).all()
    environment_breakdown = {
        (env or "production"): count for env, count in environment_rows
    }

    culprits_query = select(
        Incident.culprit,
        Incident.title,
        Incident.severity,
        Incident.events_count
    ).order_by(Incident.events_count.desc()).limit(5)
    if project_id:
        culprits_query = culprits_query.where(Incident.project_id == project_id)

    top_culprits = [
        {"culprit": c, "title": t, "severity": s, "count": count}
        for c, t, s, count in (await db.execute(culprits_query)).all()
    ]

    p99_latency = latency_tracker.get_p99()

    return {
        "total_events_today": total_events,
        "active_incidents": active_incidents,
        "resolved_incidents": resolved_incidents,
        "error_rate_per_min": error_rate_per_minute,
        "mttr_minutes": mttr_minutes,
        "p99_ingest_latency_ms": p99_latency,
        "timeseries": timeseries_data,
        "environment_breakdown": environment_breakdown,
        "top_culprits": top_culprits
    }
