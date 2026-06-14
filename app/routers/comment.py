from fastapi import APIRouter,status,HTTPException,Depends,Response
from ..database.database import get_db
from ..Auth.oauth2 import get_current_user
from sqlalchemy.orm import Session
from ..schemas import schema_comment
from ..models import models
from typing import List

router = APIRouter(prefix= "/project",tags=["Comments"])


@router.post("/{project_id}/task/{task_id}/comment",response_model=schema_comment.CommentResponse,status_code=status.HTTP_201_CREATED)
def create_comment(project_id:int,task_id:int , comment_data :schema_comment.CommentCreate,db:Session=Depends(get_db),curr_user:int = Depends(get_current_user)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail= f"project with id {id} not found to comment")

    task= db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task or task.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail= f"task with id {task_id} not found ")
    
    member = db.query(models.ProjectMember).filter(models.ProjectMember.user_id == curr_user.id,models.ProjectMember.project_id == project_id).first()

    if not member and project.owner_id!=curr_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="not a member to comment")
    
    new_comment = models.Comment(**comment_data.dict(),task_id=task_id,
    user_id=curr_user.id)
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment


    
@router.get("/{project_id}/task/{task_id}/comment",response_model=List[schema_comment.CommentResponse])
def get_comment(project_id:int,task_id:int,db:Session=Depends(get_db),curr_user:int = Depends(get_current_user)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail= f"project with id {id} not found to comment")

    task= db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task or task.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail= f"task with id {task_id} not found ")
    
    member = db.query(models.ProjectMember).filter(models.ProjectMember.user_id == curr_user.id,models.ProjectMember.project_id == project_id).first()

    if not member and project.owner_id!=curr_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="not a member to comment")
    
    return task.comments
    


@router.delete("/{project_id}/task/{task_id}/comment/{comment_id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(project_id:int,task_id:int,comment_id:int,db:Session=Depends(get_db),curr_user:int = Depends(get_current_user)):

    comment_query= db.query(models.Comment).filter(models.Comment.id == comment_id)
    comment = comment_query.first()

    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"not found comment with id {comment_id}")


    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail= f"project with id {id} not found to comment")

    task= db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task or task.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail= f"task with id {task_id} not found ")
    
    member = db.query(models.ProjectMember).filter(models.ProjectMember.user_id == curr_user.id,models.ProjectMember.project_id == project_id).first()

    if comment.user_id != curr_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own comment")
    comment_query.delete(synchronize_session=False)
    db.commit()
    

    return Response(status_code=status.HTTP_204_NO_CONTENT)
    

