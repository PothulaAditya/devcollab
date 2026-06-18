import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..websocket.manager import manager
from ..Auth.oauth2 import get_current_user_ws, get_current_user
from ..models import models
from ..database.database import get_db
from ..schemas import schema_message

logger = logging.getLogger("devcollab.chat")

router = APIRouter()


@router.websocket("/ws/project/{project_id}")
async def chat(websocket: WebSocket, project_id: int, token: str, db: Session = Depends(get_db)):
    try:
        curr_user = get_current_user_ws(token, db)
    except Exception:
        await websocket.close(code=1008)
        return

    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    member = db.query(models.ProjectMember).filter(
        models.ProjectMember.user_id == curr_user.id,
        models.ProjectMember.project_id == project_id,
    ).first()

    if not project or (not member and project.owner_id != curr_user.id):
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, project_id)
    try:
        while True:
            data = await websocket.receive_text()
            new_message = models.Message(
                project_id=project_id,
                user_id=curr_user.id,
                content=data,
            )
            db.add(new_message)
            db.commit()

            # Broadcast with sender metadata as JSON
            broadcast_payload = json.dumps({
                "user_id": curr_user.id,
                "username": curr_user.username,
                "content": data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            await manager.broadcast(broadcast_payload, project_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, project_id)


@router.get("/project/{project_id}/messages", response_model=List[schema_message.MessageResponse])
def get_messages(project_id: int, skip: int = 0, limit: int = 50, db: Session = Depends(get_db), curr_user: int = Depends(get_current_user)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    member = db.query(models.ProjectMember).filter(
        models.ProjectMember.user_id == curr_user.id,
        models.ProjectMember.project_id == project_id,
    ).first()
    if not member and project.owner_id != curr_user.id:
        raise HTTPException(status_code=403, detail="Not a member of this project")

    messages = (
        db.query(models.Message)
        .filter(models.Message.project_id == project_id)
        .order_by(models.Message.created_at)
        .offset(skip)
        .limit(limit)
        .all()
    )

    # Enrich messages with username for response
    result = []
    for msg in messages:
        user = db.query(models.User).filter(models.User.id == msg.user_id).first()
        result.append({
            "id": msg.id,
            "project_id": msg.project_id,
            "user_id": msg.user_id,
            "username": user.username if user else "Unknown",
            "content": msg.content,
            "created_at": msg.created_at,
        })

    return result
