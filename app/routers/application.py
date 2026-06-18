import logging
from fastapi import APIRouter, status, HTTPException, Depends, Response
from sqlalchemy.orm import Session
from typing import List

from ..database.database import get_db
from ..Auth.oauth2 import get_current_user
from ..schemas import schema_application
from ..models import models
from ..celery_worker import send_email

logger = logging.getLogger("devcollab.application")

router = APIRouter(prefix="/project", tags=["Applications"])


@router.post("/{project_id}/application", status_code=status.HTTP_201_CREATED, response_model=schema_application.ApplicationResponse)
def apply(project_id: int, message: schema_application.ApplicationCreate, db: Session = Depends(get_db), curr_user: int = Depends(get_current_user)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with id {project_id} not found")

    if project.owner_id == curr_user.id:
        raise HTTPException(status_code=403, detail="Owner cannot apply to own project")

    application = db.query(models.Application).filter(
        models.Application.project_id == project_id,
        models.Application.user_id == curr_user.id,
    ).first()
    if application:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Already applied to project with id {project_id}")

    member = db.query(models.ProjectMember).filter(
        models.ProjectMember.project_id == project_id,
        models.ProjectMember.user_id == curr_user.id,
    ).first()
    if member:
        raise HTTPException(status_code=409, detail="Already a member of this project")

    new_application = models.Application(
        **message.model_dump(),
        project_id=project_id,
        user_id=curr_user.id,
    )
    db.add(new_application)
    db.commit()
    db.refresh(new_application)

    return new_application


@router.get("/{project_id}/applications", response_model=List[schema_application.ApplicationResponse])
def get_applications(project_id: int, db: Session = Depends(get_db), curr_user: int = Depends(get_current_user)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with id {project_id} not found")
    if project.owner_id != curr_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the project owner can view applications")

    return project.applications


@router.put("/application/{application_id}", response_model=schema_application.ApplicationResponse)
def update_application(status_value: schema_application.ApplicationUpdate, application_id: int, db: Session = Depends(get_db), curr_user: int = Depends(get_current_user)):
    application_query = db.query(models.Application).filter(models.Application.id == application_id)
    application = application_query.first()

    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Application with id {application_id} not found")

    project = db.query(models.Project).filter(models.Project.id == application.project_id).first()

    if project.owner_id != curr_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the project owner can manage applications")

    if status_value.status.lower() == "accepted":
        # Enforce max_members limit
        current_member_count = db.query(models.ProjectMember).filter(
            models.ProjectMember.project_id == application.project_id
        ).count()
        if project.max_members and current_member_count >= project.max_members:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project has reached maximum member limit of {project.max_members}",
            )

        member = db.query(models.ProjectMember).filter(
            models.ProjectMember.project_id == application.project_id,
            models.ProjectMember.user_id == application.user_id,
        ).first()
        if not member:
            new_member = models.ProjectMember(
                project_id=application.project_id,
                user_id=application.user_id,
            )
            db.add(new_member)

        user = db.query(models.User).filter(models.User.id == application.user_id).first()
        send_email.delay(user.email, "Application Accepted", "Your application has been accepted! You are now a member of the project.")
        logger.info(f"Application {application_id} accepted, user {application.user_id} added to project {application.project_id}")

    application_query.update(status_value.model_dump(), synchronize_session=False)
    db.commit()
    return application_query.first()


@router.delete("/application/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(application_id: int, db: Session = Depends(get_db), curr_user: int = Depends(get_current_user)):
    application_query = db.query(models.Application).filter(models.Application.id == application_id)
    application = application_query.first()

    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Application with id {application_id} not found")

    if application.user_id != curr_user.id:
        raise HTTPException(status_code=403, detail="Cannot delete another user's application")

    application_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
