from fastapi import APIRouter,status,HTTPException,Depends,Response
from ..database.database import get_db
from ..Auth.oauth2 import get_current_user
from sqlalchemy.orm import Session
from ..schemas import schema_projectmember
from ..models import models
from typing import List

router =APIRouter(prefix="/project",tags=["ProjectMember"])


@router.get("/{project_id}/projectmembers",response_model=List[schema_projectmember.ProjectMemberResponse])
def get_projectmembers(project_id:int,db:Session=Depends(get_db),curr_user:int=Depends(get_current_user)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"did not found project with id {project_id}")
    member = db.query(models.ProjectMember).filter(models.ProjectMember.project_id == project_id,models.ProjectMember.user_id == curr_user.id).first()
    if project.owner_id != curr_user.id and not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="only project owner can get details")
    
    return project.members





@router.put("/projectmember/{projectmember_id}",response_model=schema_projectmember.ProjectMemberResponse)
def update_projectmember(role:schema_projectmember.ProjectMemberUpdate,projectmember_id:int,db :Session=Depends(get_db),curr_user:int = Depends(get_current_user)):
    projectmember_query = db.query(models.ProjectMember).filter(models.ProjectMember.id == projectmember_id)
    projectmember = projectmember_query.first()


    if not projectmember :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"no member with id {projectmember_id}")
    
    project = db.query(models.Project).filter(models.Project.id == projectmember.project_id).first()

    if project.owner_id != curr_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="only project owner can update")
    
    projectmember_query.update(role.dict(),synchronize_session=False)
    db.commit()
    
    return projectmember_query.first()

@router.delete("/projectmember/{projectmember_id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_projectmember(projectmember_id:int,db :Session=Depends(get_db),curr_user:int = Depends(get_current_user)):
    projectmember_query = db.query(models.ProjectMember).filter(models.ProjectMember.id == projectmember_id)
    projectmember = projectmember_query.first()


    if not projectmember :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"no member with id {projectmember_id}")
    
    project = db.query(models.Project).filter(models.Project.id == projectmember.project_id).first()

    if project.owner_id != curr_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="only project owner can delete")
    
    projectmember_query.delete(synchronize_session=False)
    db.commit()
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)





     