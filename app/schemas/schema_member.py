from pydantic import BaseModel


class MembershipResponse(BaseModel):
    project_id:int
    role :str