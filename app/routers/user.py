from fastapi import APIRouter,Depends,HTTPException,status
from ..database.database import get_db
from ..schemas import schemas_user
from ..models import models
from sqlalchemy.orm import Session
from ..utils.utils import hash_password
from ..Auth.oauth2 import get_current_user,create_verification_token,verify_token,reset_token
from ..celery_worker import send_email
from ..config.config import setting
from ..utils.utils import verify_password
router = APIRouter(
    prefix="/user"
    ,tags=["User"]
)


@router.post("/",response_model=schemas_user.UserRegisterResponse,status_code=status.HTTP_201_CREATED)
def create_user(data:schemas_user.UserRegister,db : Session=Depends(get_db)):
    user = db.query(models.User).filter(models.User.email== data.email).first()
    if user :
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,detail = "Already Existed")
    
    data.password = hash_password(data.password)
    new_user = models.User(**data.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_verification_token(new_user.id)
    verification_link = f"{setting.base_url}/user/verify?token={token}"

    send_email.delay(new_user.email,"Verify your devcollab account",f"Welcome! Click this link to verify your account:\n\n{verification_link}")
    return new_user

@router.get("/verify")
def verify_email(token: str, db: Session = Depends(get_db)):
    credential_exception=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail = "invalid credential deatils")
    token_data = verify_token(token,credential_exception)

    user = db.query(models.User).filter(models.User.id == token_data.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        return {"message": "Email already verified"}

    user.is_verified = True
    db.commit()

    return {"message": "Email verified successfully! You can now log in."}

@router.get("/{id}",response_model=schemas_user.UserResponse)
def get_user(id : int ,db:Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == id).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail = f"user not found with id {id}")
    
    return user 

@router.post('/forgetpassword')
def forget_password(data:schemas_user.ForgotPassword,db :Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if user:
        token = reset_token(user.id)
        reset_password_link = f"{setting.base_url}/user/resetpassword?token={token}"
        send_email.delay(data.email,"Password Reset Link",reset_password_link)

    return {"msg":"if mail exists ,password has been sent to that mail"}

@router.post('/resetpassword')
def reset_password(data:schemas_user.ResetPassword,db:Session=Depends(get_db)):
    credential_exception=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail = "invalid credential deatils")
    token_data = verify_token(data.token,credential_exception)
    user = db.query(models.User).filter(models.User.id == token_data.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password = hash_password(data.new_password)
    db.commit()
    return {"message": "Password reset successfully! You can now log in."}


@router.put('/deactivation')
def deactivation(password:schemas_user.PasswordCredential,db:Session=Depends(get_db),curr_user=Depends(get_current_user)):
    if not verify_password(curr_user.password,password.password):
        raise HTTPException(status_code=403, detail="Incorrect password")
    owner = db.query(models.Project).filter(models.Project.owner_id == curr_user.id).first()
    if owner:
        raise HTTPException(status_code=400, detail="Transfer or delete your projects first")
    
    db.query(models.Task).filter(models.Task.assigned_to == curr_user.id).update({"assigned_to":None},synchronize_session=False)

    curr_user.is_active = False
    db.commit() 

    return {"msg":"Account deactivated succesfully"}   






    
