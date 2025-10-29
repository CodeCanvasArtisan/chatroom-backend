from fastapi import APIRouter
from pydantic import BaseModel

from database.database import SessionLocal

class User(BaseModel):
    id: int
    name: str
    email: str
    # all of these are required

users_router = APIRouter()
