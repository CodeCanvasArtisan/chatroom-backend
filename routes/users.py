from fastapi import APIRouter
from pydantic import BaseModel

from database.database import SessionLocal

class User(BaseModel):
    id: int
    name: str
    email: str
    # all of these are required

users_router = APIRouter()

@users_router.get("/")
def root():
    return {"message" : "hi"}

@users_router.post("/post")
def post():
    return {"message" : "hi"}