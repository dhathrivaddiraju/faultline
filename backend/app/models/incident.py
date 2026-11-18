import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.app.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    fingerprint = Column(String(64), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    culprit = Column(String(500), nullable=True)
    exception_type = Column(String(200), nullable=False, index=True)
    status = Column(String(50), default="unresolved", index=True)  # unresolved, investigating, resolved, ignored
    severity = Column(String(50), default="error", index=True)      # critical, error, warning, info
    
    first_seen = Column(DateTime(timezone=True), default=utc_now)
    last_seen = Column(DateTime(timezone=True), default=utc_now, index=True)
    events_count = Column(Integer, default=1)
    users_impacted = Column(Integer, default=1)
    
    # Claude 3.5 Sonnet analysis payload
    # { "hypothesis": "...", "vulnerable_code": "...", "remediation_steps": [...], "suggested_fix_diff": "...", "confidence": 0.95, "analyzed_at": "..." }
    ai_analysis = Column(JSON, nullable=True)
    
    assigned_to = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    project = relationship("Project", back_populates="incidents")
    events = relationship("Event", back_populates="incident", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_incident_project_fingerprint", "project_id", "fingerprint", unique=True),
        Index("idx_incident_project_status_last_seen", "project_id", "status", "last_seen"),
    )
