import uuid
import logging
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.incident import Incident
from backend.app.models.event import Event
from backend.app.models.metrics import HourlyMetric
from backend.app.models.project import Project
from backend.app.services.clustering import generate_fingerprint
from backend.app.services.ai_analyzer import analyze_incident_with_claude
from backend.app.services.notifier import ws_manager, dispatch_incident_webhook
from backend.app.config import settings

logger = logging.getLogger("faultline.storage")


def current_utc_time() -> datetime:
    return datetime.now(timezone.utc)


def truncate_to_hour(timestamp: datetime) -> datetime:
    return timestamp.replace(minute=0, second=0, microsecond=0)


async def process_events_batch(
    raw_events: list[dict[str, Any]], 
    db: AsyncSession
) -> int:
    if not raw_events:
        return 0

    processed_events: list[dict[str, Any]] = []
    clusters: dict[tuple[str, str], dict[str, Any]] = {}

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
        created_at_raw = raw.get("timestamp")
        try:
            created_at = datetime.fromisoformat(created_at_raw) if created_at_raw else current_utc_time()
        except (ValueError, TypeError):
            created_at = current_utc_time()

        level = (raw.get("level") or "error").lower()
        severity = "critical" if level in ("fatal", "critical") else ("warning" if level == "warning" else "error")

        event_item = {
            "id": event_id,
            "project_id": project_id,
            "fingerprint": fingerprint,
            "exception_type": exception_type,
            "message": message,
            "stack_trace": stack_trace,
            "environment": raw.get("environment", "production"),
            "handled": bool(raw.get("handled", False)),
            "level": level,
            "release": raw.get("release"),
            "server_name": raw.get("server_name"),
            "tags": raw.get("tags") or {},
            "breadcrumbs": raw.get("breadcrumbs") or [],
            "user_context": raw.get("user") or {},
            "request_context": raw.get("request") or {},
            "created_at": created_at,
            "severity": severity,
            "title": title,
            "culprit": culprit
        }
        processed_events.append(event_item)

        cluster_key = (project_id, fingerprint)
        if cluster_key not in clusters:
            clusters[cluster_key] = {
                "project_id": project_id,
                "fingerprint": fingerprint,
                "title": title,
                "culprit": culprit,
                "exception_type": exception_type,
                "severity": severity,
                "events": [],
                "user_identifiers": set()
            }
        clusters[cluster_key]["events"].append(event_item)

        user_info = raw.get("user") or {}
        user_identifier = user_info.get("id") or user_info.get("email")
        if user_identifier:
            clusters[cluster_key]["user_identifiers"].add(user_identifier)

    new_incidents_for_alerting = []

    for (project_id, fingerprint), cluster in clusters.items():
        lookup_query = select(Incident).where(
            Incident.project_id == project_id,
            Incident.fingerprint == fingerprint
        )
        existing_result = await db.execute(lookup_query)
        incident = existing_result.scalar_one_or_none()

        batch_event_count = len(cluster["events"])
        batch_user_count = len(cluster["user_identifiers"]) or 1
        now = current_utc_time()
        representative_event = cluster["events"][0]

        if incident:
            incident.events_count += batch_event_count
            incident.last_seen = now
            if cluster["user_identifiers"]:
                incident.users_impacted += batch_user_count
            if incident.status == "resolved":
                incident.status = "unresolved"
            incident_id = incident.id

            if incident.ai_analysis is None and settings.AI_ANALYSIS_AUTO_TRIGGER:
                try:
                    analysis = await analyze_incident_with_claude(
                        title=incident.title,
                        exception_type=incident.exception_type,
                        message=representative_event["message"],
                        culprit=incident.culprit or "",
                        stack_trace=representative_event["stack_trace"],
                        breadcrumbs=representative_event["breadcrumbs"],
                        request_context=representative_event["request_context"],
                        user_context=representative_event["user_context"]
                    )
                    incident.ai_analysis = analysis
                except Exception as exc:
                    logger.error(f"Claude analysis failed for existing incident: {exc}")
        else:
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
                events_count=batch_event_count,
                users_impacted=batch_user_count,
                ai_analysis=None
            )

            if settings.AI_ANALYSIS_AUTO_TRIGGER:
                try:
                    analysis = await analyze_incident_with_claude(
                        title=cluster["title"],
                        exception_type=cluster["exception_type"],
                        message=representative_event["message"],
                        culprit=cluster["culprit"],
                        stack_trace=representative_event["stack_trace"],
                        breadcrumbs=representative_event["breadcrumbs"],
                        request_context=representative_event["request_context"],
                        user_context=representative_event["user_context"]
                    )
                    new_incident.ai_analysis = analysis
                except Exception as exc:
                    logger.error(f"Claude analysis failed for new incident: {exc}")

            db.add(new_incident)
            new_incidents_for_alerting.append(new_incident)

        for event_item in cluster["events"]:
            event_item["incident_id"] = incident_id

    for event_item in processed_events:
        event_record = Event(
            id=event_item["id"],
            project_id=event_item["project_id"],
            incident_id=event_item["incident_id"],
            fingerprint=event_item["fingerprint"],
            exception_type=event_item["exception_type"],
            message=event_item["message"],
            stack_trace=event_item["stack_trace"],
            environment=event_item["environment"],
            handled=event_item["handled"],
            level=event_item["level"],
            release=event_item["release"],
            server_name=event_item["server_name"],
            tags=event_item["tags"],
            breadcrumbs=event_item["breadcrumbs"],
            user_context=event_item["user_context"],
            request_context=event_item["request_context"],
            created_at=event_item["created_at"]
        )
        db.add(event_record)

        bucket_time = truncate_to_hour(event_item["created_at"])
        metric_query = select(HourlyMetric).where(
            HourlyMetric.project_id == event_item["project_id"],
            HourlyMetric.incident_id == event_item["incident_id"],
            HourlyMetric.bucket_time == bucket_time
        )
        metric_result = await db.execute(metric_query)
        existing_metric = metric_result.scalar_one_or_none()

        if existing_metric:
            existing_metric.count += 1
        else:
            db.add(HourlyMetric(
                project_id=event_item["project_id"],
                incident_id=event_item["incident_id"],
                environment=event_item["environment"],
                severity=event_item["severity"],
                bucket_time=bucket_time,
                count=1
            ))

    await db.commit()

    for incident_record in new_incidents_for_alerting:
        project_query = select(Project).where(Project.id == incident_record.project_id)
        project_result = await db.execute(project_query)
        project = project_result.scalar_one_or_none()
        if project and project.settings:
            webhook_url = project.settings.get("webhook_url") or project.settings.get("slack_webhook")
            if webhook_url and not webhook_url.endswith("/mock"):
                await dispatch_incident_webhook(webhook_url, {
                    "id": incident_record.id,
                    "title": incident_record.title,
                    "culprit": incident_record.culprit,
                    "severity": incident_record.severity,
                    "events_count": incident_record.events_count,
                    "status": incident_record.status
                })

    for event_item in processed_events:
        await ws_manager.broadcast({
            "type": "new_event",
            "event": {
                "id": event_item["id"],
                "incident_id": event_item["incident_id"],
                "project_id": event_item["project_id"],
                "title": event_item["title"],
                "exception_type": event_item["exception_type"],
                "message": event_item["message"],
                "environment": event_item["environment"],
                "severity": event_item["severity"],
                "culprit": event_item["culprit"],
                "created_at": event_item["created_at"].isoformat()
            }
        })

    return len(processed_events)
