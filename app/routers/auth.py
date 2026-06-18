import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from ..database.database import get_db
from ..models import models
from ..utils import utils
from ..Auth.oauth2 import create_token, verify_token, create_refresh_token
from ..limiter import limiter

logger = logging.getLogger("devcollab.auth")

router = APIRouter(
    prefix="/login",
    tags=["Authentication"],
)


@router.post("/")
@limiter.limit("10/minute")
def login(request: Request, data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.username).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Please verify your email before logging in")
    if not utils.verify_password(user.password, data.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if user.is_banned:
        raise HTTPException(status_code=403, detail="Account is banned")
    if not user.is_active:
        user.is_active = True
        db.commit()

    access_token = create_token(data={"user_id": user.id})
    refresh_token = create_refresh_token(data={"user_id": user.id})

    new_refresh = models.RefreshToken(
        token=refresh_token,
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(new_refresh)
    db.commit()

    logger.info(f"User {user.id} logged in")
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/refresh")
def refresh_access_token(refresh_token: str, db: Session = Depends(get_db)):
    credential_exception = HTTPException(status_code=401, detail="Invalid refresh token")
    user_data = verify_token(refresh_token, credential_exception)

    db_token = db.query(models.RefreshToken).filter(
        models.RefreshToken.token == refresh_token
    ).first()
    if not db_token:
        raise credential_exception

    new_access = create_token(data={"user_id": user_data.id})
    return {"access_token": new_access, "token_type": "bearer"}


@router.post("/logout")
def logout(refresh_token: str, db: Session = Depends(get_db)):
    deleted_count = db.query(models.RefreshToken).filter(
        models.RefreshToken.token == refresh_token
    ).delete(synchronize_session=False)
    db.commit()

    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="Invalid or already logged out token")

    return {"message": "Logged out successfully"}