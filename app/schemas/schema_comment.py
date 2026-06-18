from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1)


class CommentResponse(BaseModel):
    id: int
    user_id: int
    task_id: int
    content: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
