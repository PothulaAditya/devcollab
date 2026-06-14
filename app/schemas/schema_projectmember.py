from pydantic import BaseModel
from typing import Literal

class ProjectMemberResponse(BaseModel):
    user_id:int
    role:str

    class Config:
        from_attribute=True

class ProjectMemberUpdate(BaseModel):
    role:Literal["member", "admin"]