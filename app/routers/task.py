import logging
from fastapi import APIRouter, status, HTTPException, Depends, Response
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database.database import get_db
from ..Auth.oauth2 import get_current_user
from ..schemas import schema_task
from ..models import models

logger = logging.getLogger("devcollab.task")

router = APIRouter(prefix="/project", tags=["Tasks"])


@router.post("/{project_id}/task", status_code=status.HTTP_201_CREATED, response_model=schema_task.TaskResponse)
def create_task(project_id: int, task_data: schema_task.CreateTask, db: Session = Depends(get_db), curr_user: int = Depends(get_current_user)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with id {project_id} not found")

    member = db.query(models.ProjectMember).filter(
        models.ProjectMember.user_id == curr_user.id,
        models.ProjectMember.project_id == project_id,
    ).first()

    if not member and project.owner_id != curr_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of the project")
    if member and member.role == "member":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner or admin can create tasks")

    if task_data.assigned_to:
        assignee = db.query(models.ProjectMember).filter(
            models.ProjectMember.user_id == task_data.assigned_to,
            models.ProjectMember.project_id == project_id,
        ).first()
        if not assignee:
            raise HTTPException(status_code=403, detail="Assigned user is not a member of this project")

    new_task = models.Task(
        **task_data.model_dump(),
        project_id=project_id,
        created_by=curr_user.id,
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    logger.info(f"Task {new_task.id} created in project {project_id}")
    return new_task


@router.get("/{project_id}/tasks", response_model=List[schema_task.TaskResponse])
def get_tasks(project_id: int, skip: int = 0, limit: int = 20, db: Session = Depends(get_db), curr_user: int = Depends(get_current_user)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with id {project_id} not found")

    member = db.query(models.ProjectMember).filter(
        models.ProjectMember.user_id == curr_user.id,
        models.ProjectMember.project_id == project_id,
    ).first()
    if not member and project.owner_id != curr_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of the project")

    tasks = db.query(models.Task).filter(
        models.Task.project_id == project_id
    ).offset(skip).limit(limit).all()
    return tasks


@router.get("/task/{task_id}", response_model=schema_task.TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db), curr_user: int = Depends(get_current_user)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task with id {task_id} not found")

    project = db.query(models.Project).filter(models.Project.id == task.project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with id {task.project_id} not found")

    member = db.query(models.ProjectMember).filter(
        models.ProjectMember.user_id == curr_user.id,
        models.ProjectMember.project_id == task.project_id,
    ).first()
    if not member and project.owner_id != curr_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of the project")

    return task


@router.put("/task/{task_id}", response_model=schema_task.TaskResponse)
def update_task(task_id: int, task_data: schema_task.TaskUpdate, db: Session = Depends(get_db), curr_user: int = Depends(get_current_user)):
    task_query = db.query(models.Task).filter(models.Task.id == task_id)
    task = task_query.first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task with id {task_id} not found")

    project = db.query(models.Project).filter(models.Project.id == task.project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with id {task.project_id} not found")

    member = db.query(models.ProjectMember).filter(
        models.ProjectMember.user_id == curr_user.id,
        models.ProjectMember.project_id == task.project_id,
    ).first()
    if not member and project.owner_id != curr_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of the project")

    if project.owner_id == curr_user.id or (member and member.role in ("admin", "owner")):
        update_data = task_data.model_dump(exclude_none=True)
        if update_data:
            task_query.update(update_data, synchronize_session=False)
    elif task.assigned_to == curr_user.id:
        if task_data.status is not None:
            task.status = task_data.status
        else:
            raise HTTPException(status_code=400, detail="Assigned users can only update task status")
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this task")

    db.commit()
    return task_query.first()


@router.delete("/task/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db), curr_user: int = Depends(get_current_user)):
    task_query = db.query(models.Task).filter(models.Task.id == task_id)
    task = task_query.first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task with id {task_id} not found")

    project = db.query(models.Project).filter(models.Project.id == task.project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with id {task.project_id} not found")

    if project.owner_id != curr_user.id:
        member = db.query(models.ProjectMember).filter(
            models.ProjectMember.user_id == curr_user.id,
            models.ProjectMember.project_id == task.project_id,
        ).first()
        if not member or member.role == "member":
            raise HTTPException(status_code=403, detail="Only owner or admin can delete tasks")

    task_query.delete(synchronize_session=False)
    db.commit()

    logger.info(f"Task {task_id} deleted")
    return Response(status_code=status.HTTP_204_NO_CONTENT)