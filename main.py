import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
from dotenv import load_dotenv

from routes.users import users as users_router
from routes.sessions import sessions as sessions_router
from routes.chats import chats as chats_router
from routes.websocket import router as websocket_router

app = FastAPI()

# add CORS middlware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # ONLY DURING DEVELOPMENT - LIMIT FOR PRODUCTION    
    allow_credentials=True,
    allow_methods=["*"],  # Allows GET, POST, PUT, DELETE, etc.
    allow_headers=["*"]
)

from database.database import engine
from database.models import Base

Base.metadata.create_all(bind=engine)



# Include routes
app.include_router(users_router)
app.include_router(sessions_router)
app.include_router(chats_router)
app.include_router(websocket_router)

@app.get("/")
def root():
    return {"message": "Chatroom API"}