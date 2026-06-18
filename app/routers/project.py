import logging
import json
from fastapi import APIRouter, Depends, HTTPException, status, Response
from typing import List, Optional
from sqlalchemy.orm import Session

from ..database.database import get_db
from ..models import models
from ..schemas import schemas_projects
from ..Auth import oauth2
from ..redis_client import redis_client

logger = logging.getLogger("devcollab.project")

router = APIRouter(prefix="/project", tags=["Project"])


@router.get("/", response_model=List[schemas_projects.ProjectResponse])
def get_projects(
    search: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    query = db.query(models.Project)
    if search:
        query = query.filter(models.Project.title.ilike(f"%{search}%"))
    if status:
        query = query.filter(models.Project.status == status)
    return query.offset(skip).limit(limit).all()


@router.get("/{id}", response_model=schemas_projects.ProjectResponse)
def get_project(id: int, db: Session = Depends(get_db), curr_user: int = Depends(oauth2.get_current_user)):
    cached = redis_client.get(f"project_id:{id}")
    if cached:
        logger.debug(f"Cache hit for project {id}")
        return json.loads(cached)
    logger.debug(f"Cache miss for project {id}")

    project = db.query(models.Project).filter(models.Project.id == id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with id {id} not found")

    project_data = schemas_projects.ProjectResponse.model_validate(project).model_dump(mode="json")
    redis_client.set(f"project_id:{id}", json.dumps(project_data), ex=60)

    return project_data


@router.post("/", response_model=schemas_projects.ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(project: schemas_projects.ProjectCreate, db: Session = Depends(get_db), curr_user: int = Depends(oauth2.get_current_user)):
    new_project = models.Project(owner_id=curr_user.id, **project.model_dump())
    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    # Auto-add owner as project member with "owner" role
    owner_member = models.ProjectMember(
        project_id=new_project.id,
        user_id=curr_user.id,
        role="owner",
    )
    db.add(owner_member)
    db.commit()

    logger.info(f"User {curr_user.id} created project {new_project.id}")
    return new_project


@router.put("/{id}", response_model=schemas_projects.ProjectResponse)
def update_project(id: int, project: schemas_projects.ProjectUpdate, db: Session = Depends(get_db), curr_user: int = Depends(oauth2.get_current_user)):
    project_query = db.query(models.Project).filter(models.Project.id == id)
    existing_project = project_query.first()

    if not existing_project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with id {id} not found")
    if existing_project.owner_id != curr_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to perform this operation")

    update_data = project.model_dump(exclude_none=True)
    if update_data:
        project_query.update(update_data, synchronize_session=False)
        db.commit()

    redis_client.delete(f"project_id:{id}")

    return project_query.first()


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(id: int, db: Session = Depends(get_db), curr_user: int = Depends(oauth2.get_current_user)):
    project_query = db.query(models.Project).filter(models.Project.id == id)
    project = project_query.first()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with id {id} not found")
    if project.owner_id != curr_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to perform this operation")

    project_query.delete(synchronize_session=False)
    db.commit()
    redis_client.delete(f"project_id:{id}")

    logger.info(f"User {curr_user.id} deleted project {id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
