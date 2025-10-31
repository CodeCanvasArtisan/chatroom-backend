from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime, func, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

from passlib.context import CryptContext
# Set up a password context
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

Base = declarative_base() # base class for all models

class User(Base): # make sure to handle shit when user is deleted
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=False, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    date_joined = Column(DateTime(timezone=True), server_default=func.now())

    # relationships
    memberships = relationship("Membership", back_populates="user")
    owned_chats = relationship("Chat", back_populates="creator")
    sent_messages = relationship("Message", back_populates="creator")

    def to_dict(self):
        return {
            "id" : self.id,
            "username" : self.username,
            "email" : self.email,
        }
    
    # password methods
    def set_password(self, password: str):
        self.password_hash = pwd_context.hash(password)

    def check_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.password_hash)

   

class Chat(Base):
    __tablename__ = "chats"

    id=Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    creator_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    pinned=Column(Boolean, index=True, default=False, nullable=True)

    creator = relationship("User", back_populates="owned_chats")
    memberships = relationship("Membership", back_populates="chat", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id" : self.id,
            "name" : self.name,
            "creator_id" : self.creator_id,
        }

class Membership(Base):
    __tablename__ = "chat_memberships"

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    # relationships
    user = relationship("User", back_populates="memberships")
    chat = relationship("Chat", back_populates="memberships")

    __table_args__ = (
        UniqueConstraint("chat_id", "user_id", name="unique_chat_user"),
    )
    
    def to_dict(self):
        return {
            "id" : self.id,
            "chat_id" : self.chat_id,
            "user_id" : self.user_id,
        }

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), index=True, nullable=False)
    creator_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False) # foreign key ensures that this value matches something in users
    content = Column(Text, nullable=False)
    time_sent = Column(DateTime(timezone=True), server_default=func.now())

    # relationships
    creator = relationship("User", back_populates="sent_messages")
    chat = relationship("Chat", back_populates="messages")

    def to_dict(self):
        return {
            "id" : self.id,
            "chat_id" : self.chat_id,
            "creator_id" : self.creator_id,
            "content" : self.content,
            "time_sent" : self.time_sent
        }