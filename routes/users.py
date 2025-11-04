from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session
from database.database import get_db
from database.models import User, Chat, Message, Membership

import utils.pydantic_models as models

from utils.auth import get_current_user_id

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

@users.get("/users/memberships", response_model=list[models.ChatOut])
def get_all_user_chats(user_id : int = Depends(get_current_user_id), db : Session = Depends(get_db)):
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

        results = [
            models.ChatOut(
                name=chat[0].name,
                is_creator = True if chat[0].creator_id == user_id else False,
                pinned = chat[1],
                members = [
                    models.Member(
                        id = mem.user.id,
                        username = mem.user.username,
                        email = mem.user.email,
                        creator = True if mem.user.id == chat[0].creator_id else False
                    ) for mem in chat[0].memberships
                ],
                initial_messages = [
                    models.MessageOut(
                        sender = mess.creator.username,
                        contents = mess.content,
                        timestamp = str(mess.time_sent)
                    ) for mess in sorted(chat[0].messages, key=lambda x: x.time_sent)[-10:] 
                ]
            ) for chat in user_chats
        ]
        return results  
    except Exception as e:
        logger.error(f"unexpected error -> {e}")
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"unexpected error -> {e}")
    

    
    
    # find last 20 messages

@users.post("/users/membership/{chat_id}", status_code = status.HTTP_201_CREATED, response_model=models.Member)
def join_chat(
    chat_id : int, 
    user_id : int = Depends(get_current_user_id), 
    db : Session=Depends(get_db)
    ):

    joining_chat = db.query(Chat).filter_by(id = chat_id).first()

    if not joining_chat or joining_chat == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = "Chat could not be found")
    
    new_membership = Membership(
        chat_id = joining_chat.id,
        user_id = user_id
    )
    db.add(new_membership)
    db.commit()
    db.refresh(new_membership)

    return {
        "id" : new_membership.user.id,
        "username" : new_membership.user.username,
        "email" : new_membership.user.email,
        "creator" : False,
        "chat_name" : new_membership.chat.name
    }
    
@users.patch("/users/memberships/{chat_id}", response_model=models.ChatOut)
def change_pinned_status(
    chat_id : int, 
    new_chat_info : models.ChatIn, 
    user_id : int = Depends(get_current_user_id),
    db : Session=Depends(get_db)
    ):

    subject_chat = db.query(Chat).filter_by(id = chat_id).first()

    if not subject_chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    
    # USE JWT TO EXTRACT USER ID
    subject_chat_membership = next(
        (mem for mem in subject_chat.memberships if mem.user_id == user_id),
        None
    )

    if not subject_chat_membership or subject_chat_membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You must be a member to pin this chat.")
    
    subject_chat_membership.pinned = new_chat_info.pinned

    db.commit()
    db.refresh(subject_chat_membership)

    return {
        "name" : subject_chat.name,
        "is_creator" : True if user_id == subject_chat.creator_id else False, # USE JWT TO DECIDE IF THE CURRENT USER IS CREATOR
        "pinned" : subject_chat_membership.pinned, 
        "members" : [
                models.Member(
                    id = mem.user.id,
                    username = mem.user.username,
                    email = mem.user.email,
                    creator = True if mem.user.id == subject_chat.creator_id else False
                ) for mem in subject_chat.memberships
            ],
        "initial_messages" : [
            models.MessageOut(
                username = mess.creator.username,
                contents = mess.content,
                timestamp = str(mess.time_sent)
            ) for mess in sorted(subject_chat.messages, key=lambda x: x.time_sent)[-10:] 
        ]
    }

@users.delete("/users/memberships/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def leave_chat(
    chat_id : int, 
    user_id : int = Depends(get_current_user_id),
    db : Session=Depends(get_db)
    ):
    
    subject_membership = db.query(Membership).filter_by(
        chat_id = chat_id,
        user_id = user_id
    ).first()

    if not subject_membership or subject_membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found.")
    
    if subject_membership.chat.creator_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You cannot leave this chat as the owner. Try deleting it instead.")
    
    db.delete(subject_membership)
    db.commit()

    return None