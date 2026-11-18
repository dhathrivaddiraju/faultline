from typing import Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class StackFrame(BaseModel):
    filename: str
    function: str
    lineno: Optional[int] = None
    colno: Optional[int] = None
    code_context: Optional[str] = None
    pre_context: Optional[list[str]] = Field(default_factory=list)
    post_context: Optional[list[str]] = Field(default_factory=list)
    vars: Optional[dict[str, Any]] = Field(default_factory=dict)
    in_app: Optional[bool] = True

class Breadcrumb(BaseModel):
    timestamp: Optional[datetime] = Field(default_factory=utc_now)
    category: str = "default"
    message: str
    level: str = "info"  # debug, info, warning, error
    data: Optional[dict[str, Any]] = Field(default_factory=dict)

class UserContext(BaseModel):
    id: Optional[str] = None
    email: Optional[str] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None

class RequestContext(BaseModel):
    url: Optional[str] = None
    method: Optional[str] = None
    headers: Optional[dict[str, str]] = Field(default_factory=dict)
    query_params: Optional[dict[str, Any]] = Field(default_factory=dict)

class EventIngestPayload(BaseModel):
    # Core exception data
    exception_type: str = Field(..., examples=["ValueError"])
    message: str = Field(..., examples=["Invalid payment token received from gateway"])
    stack_trace: list[StackFrame] = Field(default_factory=list)
    
    # Metadata
    environment: str = Field(default="production", examples=["production"])
    handled: bool = Field(default=False)
    level: str = Field(default="error", examples=["error"])
    release: Optional[str] = Field(default=None, examples=["v1.0.4"])
    server_name: Optional[str] = Field(default=None)
    
    # Contexts
    tags: dict[str, str] = Field(default_factory=dict)
    breadcrumbs: list[Breadcrumb] = Field(default_factory=list)
    user: Optional[UserContext] = None
    request: Optional[RequestContext] = None
    timestamp: Optional[datetime] = Field(default_factory=utc_now)

class EventIngestResponse(BaseModel):
    status: str = "accepted"
    event_id: str
    fingerprint: Optional[str] = None
    message: str = "Event accepted for ingestion"
