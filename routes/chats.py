from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session
from database.database import get_db
from database.models import User, Chat, Message, Membership

from utils.auth import get_current_user_id

import utils.pydantic_models as model
import traceback, logging, os

chats = APIRouter()



from utils.debug_utils import logger

@chats.post("/chats", status_code=status.HTTP_201_CREATED, response_model=model.ChatOut)
def new_chat(chat_info : model.ChatCreate, db:Session=Depends(get_db), user_id : int = Depends(get_current_user_id)):
    try:
        # make the chat
        new_chat = Chat(
            name = chat_info.name,
            creator_id = user_id
        )
        db.add(new_chat)
        db.flush() # PUSHES changes from the db e.g. to get an id
    
        # make the first membership
        creator_membership = Membership (
            chat_id = new_chat.id,
            user_id = new_chat.creator_id
        )
            
        db.add(creator_membership)
        db.flush()
        
        db.commit()
        db.refresh(new_chat) # PULLS changes from the db e.g. server defaults
        db.refresh(creator_membership)


        return {
            "name" : new_chat.name,
            "creator_id" : new_chat.creator_id,
            "members" : [
                model.Member(
                    id = mem.user_id,
                    username = mem.user.username,
                    email = mem.user.email,
                    creator = True if mem.user_id == creator_membership.user_id else False
                ) for mem in new_chat.memberships
            ],
            "id" : new_chat.id
        }
        
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        problem_line = tb[-1].lineno
        logging.error(f"ERROR -> {e}", exc_info=True)
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error making chat: {e} \n Line : {problem_line}")

@chats.get("/chats/{chat_id}/messages")
def get_rest_of_chat_messages(chat_id : int, user_id : int = Depends(get_current_user_id), db : Session = Depends(get_db)):
    try:
        # get the chat
        subject_chat = db.query(Chat).filter_by(id = chat_id).first()
        
        if not subject_chat or subject_chat is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requested chat was not found")

        # most recent 10 are already given to the client
        print("SCM -> ", subject_chat.messages)
        all_chat_messages = sorted(subject_chat.messages, key=lambda x: x.time_sent)[:-10]
        
        
        return all_chat_messages
    except Exception as e:
        logging.error(f"ERROR ON get all messages : {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@chats.patch("/chats/{chat_id}", response_model=model.ChatOut)
def new_chat_name(chat_id : int, chat_info_new : model.ChatIn, user_id : int = Depends(get_current_user_id), db : Session = Depends(get_db)):
    
    subject_chat = db.query(Chat).filter_by(id = chat_id).first()

    if not subject_chat or subject_chat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found.")

    # make sure they're the owner (use the JWT they sent)
    is_owner = True
    if not is_owner:
        raise HTTPException(status_code = status.HTTP_403_FORBIDDEN, detail="You must be an owner to change the chat's name")
    
    subject_chat.name = chat_info_new.new_name

    db.commit() # object is already tracked, so db.add() is not needed
    db.refresh(subject_chat)

    return {
        "name" : subject_chat.name,
        "is_creator" : True,
        "pinned" : True, # USE JWT TO DECIDE IF THE CURRENT USER HAS THIS PINNED
        "members" : [
                model.Member(
                    id = mem.user.id,
                    username = mem.user.username,
                    email = mem.user.email,
                    creator = True if mem.user.id == subject_chat.creator_id else False
                ) for mem in subject_chat.memberships
            ],
        "initial_messages" : [
            model.MessageOut(
                username = mess.creator.username,
                contents = mess.content,
                timestamp = str(mess.time_sent)
            ) for mess in sorted(subject_chat.messages, key=lambda x: x.time_sent)[-10:] 
        ],
        "id" : subject_chat.id
    }

@chats.delete("/chats/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat(chat_id : int, user_id : int = Depends(get_current_user_id), db : Session = Depends(get_db)):
    
    subject_chat = db.query(Chat).filter_by(id = chat_id).first()
    if not subject_chat or subject_chat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found.")
    
    # MAKE SURE THEY'RE AUTHORISED TO DO THIS WITH JWT
    is_owner = True if user_id == subject_chat.creator_id else False

    if not is_owner:
        raise HTTPException(status_code = status.HTTP_403_FORBIDDEN, detail="You must be an owner to delete this chat")
    
    db.delete(subject_chat)
    db.commit()

    return None
