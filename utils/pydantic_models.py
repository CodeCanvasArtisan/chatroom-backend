from pydantic import BaseModel, model_validator, field_validator

# Users
class UserIn(BaseModel):
    username : str = ""
    email : str = ""
    password : str

    @model_validator(mode='after')
    def check_at_least_one(self):
        if not self.username.strip() and not self.email.strip():
            raise ValueError("Either email or username must be provided")
        return self
    
class UserCreate(BaseModel):
    username : str
    email : str
    password : str

    @field_validator('username', 'email', 'password')
    @classmethod
    def check_not_empty(cls, v, info):
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} cannot be empty.")
        return v.strip()
   
class UserOut(BaseModel):
    id : int
    username : str
    email : str

# Chats
class Member(BaseModel):
    id : int
    username : str
    email : str
    creator : bool = False

class ChatOut(BaseModel):
    name : str
    creator_id : int
    members : list[Member]
    pinned : bool = False

class ChatCreate(BaseModel):
    name : str
    creator_id : int
    member_ids : list[int] = []

# Messages
class MessageCreate(BaseModel):
    user_id : int
    contents : str

class MessageOut(BaseModel):
    id : int
    username : str
    contents : str
    timestamp : str

# Chats

# Memberships
