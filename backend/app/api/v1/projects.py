import secrets
import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.models.project import Project
from backend.app.schemas.project import ProjectCreate, ProjectOut
from backend.app.services.cache import set_cached_project, invalidate_cached_project

router = APIRouter()


def slugify_name(value: str) -> str:
    cleaned = value.lower().strip()
    cleaned = re.sub(r"[^\w\s-]", "", cleaned)
    return re.sub(r"[-\s]+", "-", cleaned)


@router.get("", response_model=list[ProjectOut])
async def list_projects(db: AsyncSession = Depends(get_db)):
    query = select(Project).order_by(Project.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(data: ProjectCreate, db: AsyncSession = Depends(get_db)):
    base_slug = slugify_name(data.name)
    resolved_slug = base_slug

    suffix_index = 1
    while True:
        existing = await db.execute(select(Project).where(Project.slug == resolved_slug))
        if not existing.scalar_one_or_none():
            break
        resolved_slug = f"{base_slug}-{suffix_index}"
        suffix_index += 1

    api_key = f"fl_live_{secrets.token_hex(16)}"
    api_secret = f"fl_sec_{secrets.token_hex(24)}"

    project = Project(
        name=data.name,
        slug=resolved_slug,
        api_key=api_key,
        api_secret=api_secret,
        platform=data.platform,
        environment=data.environment,
        settings=data.settings or {"alert_threshold": 10}
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

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
    query = select(Project).where(Project.id == project_id)
    result = await db.execute(query)
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    query = select(Project).where(Project.id == project_id)
    result = await db.execute(query)
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    await invalidate_cached_project(project.api_key)
    await db.delete(project)
    await db.commit()
    return None
