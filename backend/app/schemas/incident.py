from typing import Optional, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class AiAnalysisPayload(BaseModel):
    hypothesis: str
    vulnerable_code: Optional[str] = None
    remediation_steps: list[str]
    suggested_fix_diff: Optional[str] = None
    confidence: float = 0.95
    analyzed_at: Optional[datetime] = None

class IncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    fingerprint: str
    title: str
    culprit: Optional[str] = None
    exception_type: str
    status: str
    severity: str
    first_seen: datetime
    last_seen: datetime
    events_count: int
    users_impacted: int
    ai_analysis: Optional[dict[str, Any]] = None
    assigned_to: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class IncidentStatusUpdate(BaseModel):
    status: Optional[str] = None  # unresolved, investigating, resolved, ignored
    severity: Optional[str] = None
    assigned_to: Optional[str] = None

class IncidentFilterParams(BaseModel):
    status: Optional[str] = None
    severity: Optional[str] = None
    environment: Optional[str] = None
    search: Optional[str] = None
    page: int = 1
    page_size: int = 25
