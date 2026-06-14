from fastapi import APIRouter,Depends,HTTPException,status,Response
from typing import List
from ..database.database import get_db
from sqlalchemy.orm import Session
from ..models import models
from ..schemas import schemas_projects
from ..Auth import oauth2
from ..redis_client import redis_client
import json
from typing import Optional

router = APIRouter(prefix = "/project",tags = ["Project"])


@router.get("/", response_model=List[schemas_projects.ProjectResponse])
def get_projects(
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Project)
    if search:
        query = query.filter(models.Project.title.ilike(f"%{search}%"))
    if status:
        query = query.filter(models.Project.status == status)
    return query.all()




@router.get("/{id}",response_model=schemas_projects.ProjectResponse,status_code=status.HTTP_200_OK)
def get_project(id:int,db:Session = Depends(get_db),curr_user : int =Depends(oauth2.get_current_user)):
    
    cached = redis_client.get(f"project_id :{id}")
    if cached:
        print("cached hit")
        return json.loads(cached)
    print("cached miss")
    
    project = db.query(models.Project).filter(models.Project.id==id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT,detail = f"no projects with id {id}")
    
    project_data = schemas_projects.ProjectResponse.model_validate(project).model_dump(mode="json")
    redis_client.set(f"project_id :{id}",json.dumps(project_data),ex=60)
    
    return project_data




@router.post("/",response_model=schemas_projects.ProjectResponse,status_code=status.HTTP_201_CREATED)
def create_project(project : schemas_projects.ProjectCreate,db:Session = Depends(get_db),curr_user : int =Depends(oauth2.get_current_user)):
    new_project = models.Project(owner_id = curr_user.id,**project.dict())
    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    return new_project





@router.put("/{id}",response_model=schemas_projects.ProjectResponse)
def update_application(id:int,project : schemas_projects.ProjectUpdate,db:Session = Depends(get_db),curr_user : int =Depends(oauth2.get_current_user)):
    project_query = db.query(models.Project).filter(models.Project.id == id)
    if not project_query.first() :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f'project with id {id} not found')
    if project_query.first().owner_id != curr_user.id:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail=f"Not Authorized to perform required operation")
    project_query.update(project.dict(),synchronize_session=False)
    db.commit()

    redis_client.delete(f"project_d :{id}")

    return project_query.first()
    


@router.delete("/{id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id:int,db:Session=Depends(get_db),curr_user:int = Depends(oauth2.get_current_user)):
    project_query=db.query(models.Project).filter(models.Project.id == id)
    project=project_query.first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Couldnt find post with {id} to delete")
    if project.owner_id != curr_user.id:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail=f"Not Authorized to perform required operation")
    project_query.delete(synchronize_session=False)
    db.commit()
    redis_client.delete(f"project_id :{id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)




