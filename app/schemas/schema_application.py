from pydantic import BaseModel


class ApplicationCreate(BaseModel):
    message : str


class ProjectTitle(BaseModel):
    title:str
    class config :
        from_attribute=True
class ApplicationResponse(BaseModel):
    project_id:int
    status: str
    project :ProjectTitle
    class Config:
        from_attribute=True

from typing import Literal
class ApplicationUpdate(BaseModel):
    status: Literal["pending", "accepted", "rejected"]