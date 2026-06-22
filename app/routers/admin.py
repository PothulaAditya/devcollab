from fastapi import APIRouter,Depends,HTTPException,status
from ..database.database import get_db
from sqlalchemy.orm import Session
from ..models import models
from ..utils import utils
from ..Auth.oauth2 import require_admin
from ..schemas.schemas_user import AdminUserResponse
from typing import List
router = APIRouter(prefix="/admin",tags = ["Admin"])

@router.get("/users",response_model=List[AdminUserResponse])
def admin_get_users(admin = Depends(require_admin),db:Session=Depends(get_db)):

    users = db.query(models.User).all()
    return users


@router.put("/user/{user_id}/ban")
def ban_user(user_id:int,admin = Depends(require_admin),db :Session=Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"user with id {user_id} not found ")
    if user.role == "admin":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="cannot ban admin")
    
    user.is_banned = True

    db.commit()
    return f" user with id {user_id} is banned "

@router.put("/user/{user_id}/unban")
def unban_user(user_id:int,admin = Depends(require_admin),db :Session=Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"user with id {user_id} not found ")
    
    user.is_banned = False

    db.commit()
    return f" user with id {user_id} is unbanned "

@router.put("/user/{user_id}/admin")
def user_to_admin(user_id:int,admin = Depends(require_admin),db :Session=Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"user with id {user_id} not found ")
    if user.role == "admin":
        raise HTTPException(status_code=400, detail="User is already an admin")
    

    user.role = "admin"

    db.commit()
    return f" user with id {user_id} has been promoted to admin "



@router.get("/projects")
def admin_get_projects(admin = Depends(require_admin),db:Session=Depends(get_db)):

    return db.query(models.Project).all()


@router.get("/stats")
def admin_get_stats(admin = Depends(require_admin),db:Session=Depends(get_db)):

    return {
        "total_users" : db.query(models.User).count(),
        "total_projects" : db.query(models.Project).count(),
        "total_tasks" : db.query(models.Task).count(),
        "total_banned_users" : db.query(models.User).filter(models.User.is_banned == True).count(),

    }




