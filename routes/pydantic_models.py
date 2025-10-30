from pydantic import BaseModel

# Users
class UserCreate(BaseModel):
    display_name : str
    email : str
    password : str

class UserOut(BaseModel):
    id : int
    display_name : str
    email : str

# Messages
class MessageCreate(BaseModel):
    user_id : int
    contents : str

class MessageOut(BaseModel):
    id : int
    display_name : str
    contents : str
    timestamp : str

# Chats

# Memberships
