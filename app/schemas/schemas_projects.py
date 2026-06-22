from pydantic import BaseModel, ConfigDict,Field
from typing import Optional
class ProjectCreate(BaseModel):
    title: str = Field(...,min_length = 2)
    description: str = Field(...,min_length = 2)
    tech_stack: str =Field(...,min_length = 2)
    required_roles: str =Field(...,min_length = 2)
    


class Project(BaseModel):
    id:int
    title:str
    description : str
    tech_stack : str
    required_roles :str
    status:str
    model_config = ConfigDict(from_attributes=True)

    
class ProjectResponse(Project):
    pass
    


class ProjectUpdate(BaseModel):
    title:Optional[str] = Field(None,min_length = 2)
    description : Optional[str] = Field(None,min_length = 2)
    tech_stack : Optional[str] = Field(None,min_length = 2)
    required_roles :Optional[str] = Field(None,min_length = 2)
    status: Optional[str] = Field(None,min_length = 2)