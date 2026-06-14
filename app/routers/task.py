from fastapi import APIRouter,status,HTTPException,Depends,Response
from ..database.database import get_db
from ..Auth.oauth2 import get_current_user
from sqlalchemy.orm import Session
from ..schemas import schema_task
from ..models import models
from typing import List



router = APIRouter(prefix="/project",tags = ["Tasks"])


@router.post("/{project_id}/task",status_code=status.HTTP_201_CREATED)
def create_task(project_id:int,task_data:schema_task.CreateTask,db:Session = Depends(get_db),curr_user:int=Depends(get_current_user)):

    project = db.query(models.Project).filter(models.Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail= f"project with id {id} not found to create task")
    
    member = db.query(models.ProjectMember).filter(models.ProjectMember.user_id == curr_user.id,models.ProjectMember.project_id == project_id).first()

    if not member and project.owner_id != curr_user.id :
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail = "Not a member of the project")
    if member and member.role == "member":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail = "Not owner/admin of the project")
    if task_data.assigned_to:
        assignee = db.query(models.ProjectMember).filter(models.ProjectMember.user_id == task_data.assigned_to,models.ProjectMember.project_id == project_id).first()
        if not assignee:
            raise HTTPException(403, "Assigned user is not a member of this project")
    new_task = models.Task(
    **task_data.dict(),
    project_id=project_id,
    created_by=curr_user.id
)

    db.add(new_task)
    db.commit()
    return new_task


@router.get("/{project_id}/tasks",response_model=List[schema_task.TaskResponse])
def get_tasks(project_id:int,db:Session = Depends(get_db),curr_user:int=Depends(get_current_user)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail= f"project with id {project_id} not found ")
    
    member = db.query(models.ProjectMember).filter(models.ProjectMember.user_id == curr_user.id,models.ProjectMember.project_id == project_id).first()
    if not member and project.owner_id != curr_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail = "Not a member of the project")
    
    return project.tasks


@router.get("/task/{task_id}",response_model=schema_task.TaskResponse)
def get_tasks(task_id:int ,db:Session = Depends(get_db),curr_user:int=Depends(get_current_user)):
    task= db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail= f"task with id {task_id} not found ")
    project = db.query(models.Project).filter(models.Project.id == task.project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail= f"project with id {project.id} not found ")
    member = db.query(models.ProjectMember).filter(models.ProjectMember.user_id == curr_user.id,models.ProjectMember.project_id == task.project_id).first()
    if not member and project.owner_id != curr_user.id :
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail = "Not a member of the project")
    
    return task


@router.put("/task/{task_id}",response_model=schema_task.TaskResponse)
def update_tasks(task_id:int,task_data : schema_task.TaskUpdate ,db:Session = Depends(get_db),curr_user:int=Depends(get_current_user)):

    task_query= db.query(models.Task).filter(models.Task.id == task_id)
    task = task_query.first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail= f"task with id {task_id} not found ")
    
    project = db.query(models.Project).filter(models.Project.id == task.project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail= f"project with id {project.id} not found ")
    
    member = db.query(models.ProjectMember).filter(models.ProjectMember.user_id == curr_user.id,models.ProjectMember.project_id == task.project_id).first()
    if not member and project.owner_id != curr_user.id :
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail = "Not a member of the project")
    if project.owner_id == curr_user.id or (member and member.role == "admin"):
        task_query.update(task_data.dict(exclude_none=True), synchronize_session=False)
    elif task.assigned_to == curr_user.id:
        if task_data.status is not None:
            task.status = task_data.status
        else:
            raise HTTPException(400, "Assigned users can only update status")
    db.commit()

    return task_query.first()




@router.delete("/task/{task_id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_tasks(task_id:int,db:Session = Depends(get_db),curr_user:int=Depends(get_current_user)):

    task_query= db.query(models.Task).filter(models.Task.id == task_id)
    task = task_query.first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail= f"task with id {task_id} not found ")
    
    project = db.query(models.Project).filter(models.Project.id == task.project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail= f"project with id {project.id} not found ")
    
    member = db.query(models.ProjectMember).filter(models.ProjectMember.user_id == curr_user.id,models.ProjectMember.project_id == task.project_id).first()
    if project.owner_id != curr_user.id:
        if not member or member.role == "member":
            raise HTTPException(403, "Only owner or admin can delete")
    
    task_query.delete(synchronize_session=False)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)





    


    




    


    