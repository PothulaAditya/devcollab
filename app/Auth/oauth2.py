from jose import jwt,JWTError
from ..config.config import setting
from datetime import datetime,timedelta

from fastapi.security import OAuth2PasswordBearer

from fastapi import Depends,HTTPException,status
from sqlalchemy.orm import Session
from ..database.database import get_db

from ..schemas import schema_token
from ..models import models


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


SECRET_KEY=setting.secret_key
ALGORITHM=setting.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES=setting.access_token_expire_minutes


def create_token(data:dict):
    encoded_data=data.copy()
    expiration_time = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    encoded_data.update({'exp':expiration_time})
    token = jwt.encode(encoded_data,SECRET_KEY,algorithm=ALGORITHM)

    return token 


def verify_token(token : str,credential_exception):
    
    try :
        payload = jwt.decode(token , SECRET_KEY,algorithms=ALGORITHM)
        id = str(payload.get("user_id"))
        if id is None:
            raise credential_exception
        token_data = schema_token.TokenData(id=id)
    except JWTError:
        raise credential_exception
    return token_data




def get_current_user(token :str = Depends(oauth2_scheme),db :Session = Depends(get_db)):

    credential_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail = "invalid credential deatils")
    token = verify_token(token,credential_exception)
    user = db.query(models.User).filter(models.User.id == token.id).first()
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")
    if user.is_banned:
        raise HTTPException(status_code=403, detail="Account is banned")
    return user

def get_current_user_ws(token: str, db: Session):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail = "invalid credential deatils")
    token_data = verify_token(token, credentials_exception)
    user = db.query(models.User).filter(models.User.id == token_data.id).first()

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")
    if user.is_banned:
        raise HTTPException(status_code=403, detail="Account is banned")
    return user

def create_verification_token(user_id:int):

    data={"user_id":user_id}
    expire = datetime.utcnow() + timedelta(hours=24)
    data.update({"exp":expire})
    token = jwt.encode(data,SECRET_KEY,algorithm=ALGORITHM)
    return token 

def reset_token(user_id:int):

    data={"user_id":user_id}
    expire = datetime.utcnow() + timedelta(minutes=15)
    data.update({"exp":expire})
    token = jwt.encode(data,SECRET_KEY,algorithm=ALGORITHM)
    return token 

def create_refresh_token(data: dict):
    encoded = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)   
    encoded.update({"exp": expire})
    return jwt.encode(encoded, SECRET_KEY, algorithm=ALGORITHM)



def require_admin(curr_user=Depends(get_current_user)):
    if curr_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="not admin")
    return curr_user




