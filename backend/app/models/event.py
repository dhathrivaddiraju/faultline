import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, JSON, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from backend.app.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Event(Base):
    __tablename__ = "events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=True, index=True)
    fingerprint = Column(String(64), nullable=False, index=True)
    
    exception_type = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    # Normalized & rich stack trace: list of frames
    # [{filename, lineno, colno, function, code_context: [...], pre_context: [...], post_context: [...], locals: {}, in_app: bool}]
    stack_trace = Column(JSON, nullable=False, default=list)
    
    environment = Column(String(50), default="production", index=True)
    handled = Column(Boolean, default=False)
    level = Column(String(20), default="error")  # fatal, error, warning, info
    release = Column(String(100), nullable=True)
    server_name = Column(String(255), nullable=True)
    
    tags = Column(JSON, default=dict)
    breadcrumbs = Column(JSON, default=list)
    user_context = Column(JSON, default=dict)       # {id, email, username, ip_address}
    request_context = Column(JSON, default=dict)    # {url, method, headers, query_params}
    
    created_at = Column(DateTime(timezone=True), default=utc_now, index=True)

    # Relationships
    project = relationship("Project", back_populates="events")
    incident = relationship("Incident", back_populates="events")

    __table_args__ = (
        Index("idx_events_project_created_at", "project_id", "created_at"),
        Index("idx_events_incident_created_at", "incident_id", "created_at"),
        Index("idx_events_fingerprint_created_at", "fingerprint", "created_at"),
    )
