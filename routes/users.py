from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session
from database.database import get_db
from database.models import User, Chat, Message, Membership

import utils.pydantic_models as models

# logger for debugging
from utils.debug_utils import logger

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
    
@users.get("/users/{user_id}/chats", response_model=list[models.ChatOut])
def get_all_user_chats(user_id : int, db : Session = Depends(get_db)):
    # find all chats for this user
    try:
        user_chats = [chat for chat in (
            db.query(Chat, Membership.pinned)
            .join(Membership, Chat.id == Membership.chat_id)
            .filter(
                Membership.user_id == user_id
            )
            .order_by(
                Membership.pinned.desc(),
                Chat.name
            )
        )]
        
        if not user_chats or len(user_chats) == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No chats could be found for this user")
        
        for chat in user_chats:
            print("CHAT -> ", chat)

        results = [
            models.ChatOut(
                name=chat[0].name,
                creator_id=chat[0].creator_id,
                members = [
                    models.Member(
                        id = mem.user.id,
                        username = mem.user.username,
                        email = mem.user.email,
                        creator = True if mem.user.id == chat[0].creator_id else False
                    ) for mem in chat[0].memberships
                ],
                pinned = chat[1]
            ) for chat in user_chats
        ]
        return results  
    except Exception as e:
        logger.error(f"unexpected error -> {e}")
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"unexpected error -> {e}")
    

    
    
    # find last 20 messages
