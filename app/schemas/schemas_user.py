from pydantic import BaseModel,EmailStr,ConfigDict,Field

class UserRegister(BaseModel):
    username : str = Field(...,min_length=4)
    email : EmailStr
    password : str = Field(...,min_length=4)

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