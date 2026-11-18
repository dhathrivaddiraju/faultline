import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Index
from backend.app.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class HourlyMetric(Base):
    __tablename__ = "hourly_metrics"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), nullable=False, index=True)
    incident_id = Column(String(36), nullable=True, index=True)
    environment = Column(String(50), default="production", index=True)
    severity = Column(String(50), default="error")
    bucket_time = Column(DateTime(timezone=True), nullable=False, index=True)
    count = Column(Integer, default=1)

    __table_args__ = (
        Index("idx_metrics_proj_bucket", "project_id", "bucket_time"),
        Index("idx_metrics_inc_bucket", "incident_id", "bucket_time"),
    )
