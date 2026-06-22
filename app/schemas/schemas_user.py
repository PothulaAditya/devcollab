from pydantic import BaseModel,EmailStr,ConfigDict,Field,field_validator
from datetime import datetime
class UserRegister(BaseModel):
    username : str = Field(...,min_length=4)
    email : EmailStr
    password : str 
    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        if not any(c in "!@#$%^&*()-_+=[]{}|;:,.<>?" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v


class UserRegisterResponse(BaseModel):
    id : int
    username : str
    role : str
    is_verified : bool
    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    email : EmailStr
    password : str = Field(...,min_length=4)


class UserResponse(BaseModel):
    id:int
    username :str



class ResetPassword(BaseModel):
    token: str
    new_password: str

class ForgotPassword(BaseModel):
    email: EmailStr

class PasswordCredential(BaseModel):
    password:str

class AdminUserResponse(BaseModel):
    email :str
    username :str
    role :str
    is_verified :bool
    is_active :bool  
    is_banned :bool
    created_at : datetime 
    model_config = ConfigDict(from_attributes=True)
