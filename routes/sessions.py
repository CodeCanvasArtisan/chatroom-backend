from fastapi import APIRouter, Depends, HTTPException, status
import utils.pydantic_models as model 

from sqlalchemy.orm import Session
from sqlalchemy import or_
from database.database import get_db
from database.models import User

from utils.auth import create_access_token, verify_access_token

sessions = APIRouter()

@sessions.post("/sessions")
def new_session(user_info : model.UserIn, db : Session = Depends(get_db)):
    user_db = db.query(User).filter(
        or_(
            User.email==user_info.email, 
            User.username == user_info.username
        )
    ).first()

    # deny the user access if not the right email or pwd
    if not user_db or not user_db.check_password(user_info.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username/email or password.")
    
    # Create JWT token & return it
    access_token = create_access_token(data= {"user_id" : user_db.id})

    return {
        "access_token" : access_token,
        "token-type" : "bearer",
        "user": user_db.to_dict()
    }