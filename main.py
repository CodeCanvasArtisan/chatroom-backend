import os
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from routes.users import users_router



app = FastAPI()

from database.database import engine
from database.models import Base

Base.metadata.create_all(bind=engine)

# Include routes
app.include_router(users_router)
