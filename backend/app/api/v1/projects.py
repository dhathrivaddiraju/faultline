import secrets
import re
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database import get_db
from backend.app.models.project import Project
from backend.app.schemas.project import ProjectCreate, ProjectOut
from backend.app.services.cache import set_cached_project, invalidate_cached_project

router = APIRouter()

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "-", text)

@router.get("", response_model=list[ProjectOut])
async def list_projects(db: AsyncSession = Depends(get_db)):
    """List all registered monitored projects."""
    stmt = select(Project).order_by(Project.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(data: ProjectCreate, db: AsyncSession = Depends(get_db)):
    """Create a new project and generate a high-speed ingestion API key."""
    base_slug = slugify(data.name)
    slug = base_slug
    
    # Ensure unique slug
    idx = 1
    while True:
        existing = await db.execute(select(Project).where(Project.slug == slug))
        if not existing.scalar_one_or_none():
            break
        slug = f"{base_slug}-{idx}"
        idx += 1

    api_key = f"fl_live_{secrets.token_hex(16)}"
    api_secret = f"fl_sec_{secrets.token_hex(24)}"

    project = Project(
        name=data.name,
        slug=slug,
        api_key=api_key,
        api_secret=api_secret,
        platform=data.platform,
        environment=data.environment,
        settings=data.settings or {"alert_threshold": 10}
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    # Warm Redis cache immediately for sub-millisecond first request
    await set_cached_project(api_key, {
        "id": project.id,
        "name": project.name,
        "slug": project.slug,
        "api_key": project.api_key,
        "settings": project.settings
    })

    return project

@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve project by ID."""
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    proj = result.scalar_one_or_none()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return proj

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a project and purge its cached API key."""
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    proj = result.scalar_one_or_none()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    await invalidate_cached_project(proj.api_key)
    await db.delete(proj)
    await db.commit()
    return None
