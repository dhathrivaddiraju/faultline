import uuid
import logging
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.incident import Incident
from backend.app.models.event import Event
from backend.app.models.metrics import HourlyMetric
from backend.app.services.clustering import generate_fingerprint
from backend.app.services.ai_analyzer import analyze_incident_with_claude
from backend.app.services.notifier import ws_manager
from backend.app.config import settings

logger = logging.getLogger("faultline.storage")

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def truncate_to_hour(dt: datetime) -> datetime:
    return dt.replace(minute=0, second=0, microsecond=0)

async def process_events_batch(
    raw_events: list[dict[str, Any]], 
    db: AsyncSession
) -> int:
    """
    Process and persist a batch of raw ingested events:
    1. Fingerprint and group similar traces.
    2. Upsert Incidents (clusters).
    3. Bulk-insert raw Events.
    4. Update Hourly Timeseries Metrics.
    5. Trigger Claude AI Analysis on new/threshold-crossing incidents.
    6. Broadcast to real-time WebSockets.
    """
    if not raw_events:
        return 0

    processed_events = []
    # Key: (project_id, fingerprint) -> { incident_data, events_in_batch }
    grouped_by_fingerprint: dict[tuple[str, str], dict[str, Any]] = {}

    for raw in raw_events:
        project_id = raw.get("project_id")
        if not project_id:
            continue

        exception_type = raw.get("exception_type", "UnknownError")
        message = raw.get("message", "")
        stack_trace = raw.get("stack_trace", [])
        
        fingerprint, culprit, title = generate_fingerprint(
            exception_type=exception_type,
            stack_trace=stack_trace,
            message=message
        )
        
        event_id = raw.get("event_id") or str(uuid.uuid4())
        created_at_str = raw.get("timestamp")
        try:
            created_at = datetime.fromisoformat(created_at_str) if created_at_str else utc_now()
        except Exception:
            created_at = utc_now()

        # Severity determination
        level = raw.get("level", "error").lower()
        severity = "critical" if level in ("fatal", "critical") else ("warning" if level == "warning" else "error")

        event_obj = {
            "id": event_id,
            "project_id": project_id,
            "fingerprint": fingerprint,
            "exception_type": exception_type,
            "message": message,
            "stack_trace": stack_trace,
            "environment": raw.get("environment", "production"),
            "handled": raw.get("handled", False),
            "level": level,
            "release": raw.get("release"),
            "server_name": raw.get("server_name"),
            "tags": raw.get("tags", {}),
            "breadcrumbs": raw.get("breadcrumbs", []),
            "user_context": raw.get("user") or {},
            "request_context": raw.get("request") or {},
            "created_at": created_at,
            "severity": severity,
            "title": title,
            "culprit": culprit
        }
        processed_events.append(event_obj)

        key = (project_id, fingerprint)
        if key not in grouped_by_fingerprint:
            grouped_by_fingerprint[key] = {
                "project_id": project_id,
                "fingerprint": fingerprint,
                "title": title,
                "culprit": culprit,
                "exception_type": exception_type,
                "severity": severity,
                "events": [],
                "users": set()
            }
        grouped_by_fingerprint[key]["events"].append(event_obj)
        user_id = (raw.get("user") or {}).get("id") or (raw.get("user") or {}).get("email")
        if user_id:
            grouped_by_fingerprint[key]["users"].add(user_id)

    # Database Upserts for Incidents
    for (project_id, fingerprint), cluster in grouped_by_fingerprint.items():
        stmt = select(Incident).where(
            Incident.project_id == project_id,
            Incident.fingerprint == fingerprint
        )
        result = await db.execute(stmt)
        incident = result.scalar_one_or_none()

        count_in_batch = len(cluster["events"])
        users_in_batch = len(cluster["users"]) or 1
        now = utc_now()
        sample_event = cluster["events"][0]

        if incident:
            # Existing incident cluster: update aggregate counters
            incident.events_count += count_in_batch
            incident.last_seen = now
            if cluster["users"]:
                incident.users_impacted += users_in_batch
            # Reopen if was resolved
            if incident.status == "resolved":
                incident.status = "unresolved"
            incident_id = incident.id

            # Trigger AI analysis if not yet analyzed and threshold reached
            if incident.ai_analysis is None and settings.AI_ANALYSIS_AUTO_TRIGGER:
                try:
                    analysis = await analyze_incident_with_claude(
                        title=incident.title,
                        exception_type=incident.exception_type,
                        message=sample_event["message"],
                        culprit=incident.culprit or "",
                        stack_trace=sample_event["stack_trace"],
                        breadcrumbs=sample_event["breadcrumbs"],
                        request_context=sample_event["request_context"],
                        user_context=sample_event["user_context"]
                    )
                    incident.ai_analysis = analysis
                except Exception as e:
                    logger.error(f"Auto AI analysis failed: {e}")
        else:
            # New Incident cluster
            incident_id = str(uuid.uuid4())
            new_incident = Incident(
                id=incident_id,
                project_id=project_id,
                fingerprint=fingerprint,
                title=cluster["title"],
                culprit=cluster["culprit"],
                exception_type=cluster["exception_type"],
                status="unresolved",
                severity=cluster["severity"],
                first_seen=now,
                last_seen=now,
                events_count=count_in_batch,
                users_impacted=users_in_batch,
                ai_analysis=None
            )
            
            # Immediately trigger AI Analysis for new cluster
            if settings.AI_ANALYSIS_AUTO_TRIGGER:
                try:
                    analysis = await analyze_incident_with_claude(
                        title=cluster["title"],
                        exception_type=cluster["exception_type"],
                        message=sample_event["message"],
                        culprit=cluster["culprit"],
                        stack_trace=sample_event["stack_trace"],
                        breadcrumbs=sample_event["breadcrumbs"],
                        request_context=sample_event["request_context"],
                        user_context=sample_event["user_context"]
                    )
                    new_incident.ai_analysis = analysis
                except Exception as e:
                    logger.error(f"Initial AI analysis failed: {e}")

            db.add(new_incident)

        # Associate incident_id with each event in this cluster
        for ev in cluster["events"]:
            ev["incident_id"] = incident_id

    # Bulk-insert Events
    for ev in processed_events:
        db_event = Event(
            id=ev["id"],
            project_id=ev["project_id"],
            incident_id=ev["incident_id"],
            fingerprint=ev["fingerprint"],
            exception_type=ev["exception_type"],
            message=ev["message"],
            stack_trace=ev["stack_trace"],
            environment=ev["environment"],
            handled=ev["handled"],
            level=ev["level"],
            release=ev["release"],
            server_name=ev["server_name"],
            tags=ev["tags"],
            breadcrumbs=ev["breadcrumbs"],
            user_context=ev["user_context"],
            request_context=ev["request_context"],
            created_at=ev["created_at"]
        )
        db.add(db_event)

        # Update hourly metric
        bucket_time = truncate_to_hour(ev["created_at"])
        metric_stmt = select(HourlyMetric).where(
            HourlyMetric.project_id == ev["project_id"],
            HourlyMetric.incident_id == ev["incident_id"],
            HourlyMetric.bucket_time == bucket_time
        )
        m_result = await db.execute(metric_stmt)
        metric = m_result.scalar_one_or_none()
        if metric:
            metric.count += 1
        else:
            new_metric = HourlyMetric(
                project_id=ev["project_id"],
                incident_id=ev["incident_id"],
                environment=ev["environment"],
                severity=ev["severity"],
                bucket_time=bucket_time,
                count=1
            )
            db.add(new_metric)

    await db.commit()

    # Broadcast to live WebSockets for real-time frontend updates
    for ev in processed_events:
        await ws_manager.broadcast({
            "type": "new_event",
            "event": {
                "id": ev["id"],
                "incident_id": ev["incident_id"],
                "project_id": ev["project_id"],
                "title": ev["title"],
                "exception_type": ev["exception_type"],
                "message": ev["message"],
                "environment": ev["environment"],
                "severity": ev["severity"],
                "culprit": ev["culprit"],
                "created_at": ev["created_at"].isoformat()
            }
        })

    logger.info(f"Successfully processed batch of {len(processed_events)} events into database.")
    return len(processed_events)
