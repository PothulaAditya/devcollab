from pydantic import BaseModel, ConfigDict
from typing import Literal


class ApplicationCreate(BaseModel):
    message: str


class ProjectTitle(BaseModel):
    title: str

    model_config = ConfigDict(from_attributes=True)


class ApplicationResponse(BaseModel):
    id: int
    project_id: int
    user_id: int
    message: str
    status: str
    project: ProjectTitle

    model_config = ConfigDict(from_attributes=True)


class ApplicationUpdate(BaseModel):
    status: Literal["pending", "accepted", "rejected"]