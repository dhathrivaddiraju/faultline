from fastapi import APIRouter
from backend.app.api.v1.capture import router as capture_router
from backend.app.api.v1.incidents import router as incidents_router
from backend.app.api.v1.projects import router as projects_router
from backend.app.api.v1.analytics import router as analytics_router
from backend.app.api.v1.websockets import router as ws_router

api_v1_router = APIRouter()

api_v1_router.include_router(capture_router, tags=["Ingestion"])
api_v1_router.include_router(incidents_router, prefix="/incidents", tags=["Incidents"])
api_v1_router.include_router(projects_router, prefix="/projects", tags=["Projects"])
api_v1_router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
api_v1_router.include_router(ws_router, prefix="/ws", tags=["Live Stream"])
