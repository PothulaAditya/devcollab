from fastapi import APIRouter, WebSocket, WebSocketDisconnect,Depends,HTTPException,status
from sqlalchemy.orm import Session
from ..websocket.manager import manager
from ..Auth.oauth2 import get_current_user_ws,get_current_user
from ..models import models
from ..database.database import get_db
from ..schemas import schema_message
from typing import List


router = APIRouter()

@router.websocket("/ws/project/{project_id}")
async def chat(websocket:WebSocket,project_id:int,token :str,db:Session = Depends(get_db)):
    try:
        curr_user = get_current_user_ws(token, db)
    except Exception:
        await websocket.close(code=1008)
        return
    
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    member = db.query(models.ProjectMember).filter(
        models.ProjectMember.user_id == curr_user.id,
        models.ProjectMember.project_id == project_id
    ).first()
    
    if not project or (not member and project.owner_id!=curr_user.id):
        await websocket.close(code=1008)
        return
    
    
    await manager.connect(websocket,project_id)
    try:
        while True:
            data = await websocket.receive_text()
            new_message = models.Message(
            project_id=project_id,
            user_id=curr_user.id,
            content=data
        )
            
            db.add(new_message)
            db.commit()

            await manager.broadcast(data,project_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket,project_id)



@router.get("/project/{project_id}/messages", response_model=List[schema_message.MessageResponse])
def get_messages(project_id: int, db: Session = Depends(get_db), curr_user: int = Depends(get_current_user)):
    
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

   
    member = db.query(models.ProjectMember).filter(
        models.ProjectMember.user_id == curr_user.id,
        models.ProjectMember.project_id == project_id
    ).first()
    if not member and project.owner_id != curr_user.id:
        raise HTTPException(status_code=403, detail="Not a member of this project")

    
    messages = db.query(models.Message).filter(
        models.Message.project_id == project_id
    ).order_by(models.Message.created_at).all()

    return messages

    
