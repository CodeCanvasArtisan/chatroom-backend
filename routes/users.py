from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session
from database.database import get_db
from database.models import User

import routes.pydantic_models as models

# logger for debugging
import logging
logger = logging.getLogger(__name__)

users = APIRouter()

# use request.json() to convert JSON to a dict (request import needed from fastapi)


@users.post("/users", status_code=status.HTTP_201_CREATED, response_model=models.UserOut)
def new_user(
    user_info : models.UserCreate, 
    db: Session = Depends(get_db)
    ):

    normalised_email = user_info.email.strip().lower()

    if db.query(User).filter_by(email = normalised_email).first():
        # see if the user already exists
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="This email already exists. Please try to log in with it."
        ) # 409 = conflict error
    
    try:
        # enter the user into the database
        created_user = User(
            username = user_info.username,
            email = normalised_email
        )
        # set password
        created_user.set_password(user_info.password)

        db.add(created_user)

        

        db.commit()
        db.refresh(created_user)
        
        return created_user # return is for successful responses, raise is for errors
    
    except Exception as e:

        db.rollback()
        logger.error(f"[ERROR CREATING USER ({normalised_email})] -> {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"An error occurred while creating the user")
    


