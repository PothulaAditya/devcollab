from fastapi import APIRouter,status,HTTPException,Depends,Response
from ..database.database import get_db
from ..Auth.oauth2 import get_current_user
from sqlalchemy.orm import Session
from ..schemas import schema_application,schemas_projects
from ..models import models
from typing import List
from ..celery_worker import send_email
router = APIRouter(prefix="/project",tags=["Applications"])


@router.post("/{project_id}/application",status_code=status.HTTP_201_CREATED,response_model=schema_application.ApplicationResponse)
def apply(project_id:int ,message :schema_application.ApplicationCreate,db :Session =Depends(get_db),curr_user :int =Depends(get_current_user)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail = f"project with id {project_id} not available")
    
    application = db.query(models.Application).filter(models.Application.project_id == project_id , models.Application.user_id == curr_user.id).first()
    if application :
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail = f"Already applied to project with id {project_id}")
    # Add this after the application check
    member = db.query(models.ProjectMember).filter(
        models.ProjectMember.project_id == project_id,
        models.ProjectMember.user_id == curr_user.id
    ).first()
    if member:
        raise HTTPException(status_code=403, detail="Already a member of this project")
    
    if project.owner_id == curr_user.id:
        raise HTTPException(403, "Owner cannot apply to own project")
    apply = models.Application(**message.dict(),
    project_id=project_id,
    user_id=curr_user.id)

    db.add(apply)
    
    db.commit()
    db.refresh(apply)

    return apply


@router.get("/{project_id}/applications",response_model=List[schema_application.ApplicationResponse])
def get_applications(project_id:int,db :Session =Depends(get_db),curr_user :int =Depends(get_current_user)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail = f"project with id {project_id} not available")
    if project.owner_id != curr_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="only owner can access the application")
    
    return project.applications


@router.put("/application/{application_id}",response_model=schema_application.ApplicationResponse)
def update_application(status_value :schema_application.ApplicationUpdate,application_id:int,db:Session=Depends(get_db),curr_user:int =Depends(get_current_user)):
    application_query = db.query(models.Application).filter(models.Application.id == application_id)
    application = application_query.first()
    if not application :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail = f"application with id {application_id} not found ")
    
    project = db.query(models.Project).filter(models.Project.id == application.project_id).first()

    if project.owner_id != curr_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="only owner can access the application")
    if status_value.status.lower() == "accepted":
        member = db.query(models.ProjectMember).filter(
            models.ProjectMember.project_id == application.project_id,
            models.ProjectMember.user_id == application.user_id
        ).first()
        if not member:
            new_member = models.ProjectMember(
                project_id=application.project_id,
                user_id=application.user_id
            )
            db.add(new_member)
        user = db.query(models.User).filter(models.User.id == application.user_id).first()
        send_email.delay(user.email,"Application Accepted","Your Application has been accepted")
    application_query.update(status_value.dict(),synchronize_session=False)
    db.commit()
    return application_query.first()




@router.delete("/application/{application_id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_application(application_id:int,db:Session=Depends(get_db),curr_user:int =Depends(get_current_user)):
    application_query = db.query(models.Application).filter(models.Application.id == application_id)
    application = application_query.first()
    if not application :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail = f"application with id {application_id} not found ")
    
    project = db.query(models.Project).filter(models.Project.id == application.project_id).first()

    if application.user_id != curr_user.id: 
        raise HTTPException(status_code=403, detail="Cannot delete others application")

    application_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
        

    
