from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session
from database.database import get_db
from database.models import User, Chat, Message, Membership

import utils.pydantic_models as model
import traceback, logging

chats = APIRouter()

from utils.debug_utils import logger

@chats.post("/chats", status_code=status.HTTP_201_CREATED, response_model=model.ChatOut)
def new_chat(chat_info : model.ChatCreate, db:Session=Depends(get_db)):
    try:
        # make the chat
        new_chat = Chat(
            name = chat_info.name,
            creator_id = chat_info.creator_id
        )
        db.add(new_chat)
        db.flush() # PUSHES changes from the db e.g. to get an id
    
        # make the memberships
        all_member_ids = chat_info.member_ids + [chat_info.creator_id]
        if all_member_ids:
            new_memberships = [
                Membership (
                    chat_id = new_chat.id,
                    user_id = id
                ) for id in all_member_ids
            ]
            db.add_all(new_memberships)
        
        db.commit()
        db.refresh(new_chat) # PULLS changes from the db e.g. server defaults

        creator_membership = [member for member in new_memberships if member.user_id == new_chat.creator_id][0]
        print("CM -> ", creator_membership)

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
            ]
        }
        
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        problem_line = tb[-1].lineno
        logging.error(f"ERROR -> {e}", exc_info=True)
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error making chat: {e} \n Line : {problem_line}")