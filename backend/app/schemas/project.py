from typing import Optional, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class ProjectCreate(BaseModel):
    name: str
    platform: str = "python"
    environment: str = "production"
    settings: Optional[dict[str, Any]] = None

class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    api_key: str
    platform: str
    environment: str
    settings: dict[str, Any]
    created_at: datetime
