from pydantic import BaseModel, ConfigDict
from datetime import datetime


class MessageResponse(BaseModel):
    id: int
    project_id: int
    user_id: int
    username: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)