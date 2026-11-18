from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class TimeSeriesPoint(BaseModel):
    timestamp: datetime
    count: int
    error_count: int = 0
    critical_count: int = 0
    warning_count: int = 0

class ProjectStatsOut(BaseModel):
    total_events_today: int
    active_incidents: int
    resolved_incidents: int
    error_rate_per_min: float
    mttr_minutes: float
    p99_ingest_latency_ms: float
    timeseries: list[TimeSeriesPoint]
