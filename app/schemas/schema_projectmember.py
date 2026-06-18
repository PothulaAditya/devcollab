from pydantic import BaseModel, ConfigDict
from typing import Literal
from datetime import datetime


class ProjectMemberResponse(BaseModel):
    id: int
    user_id: int
    project_id: int
    role: str
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectMemberUpdate(BaseModel):
    role: Literal["member", "admin"]