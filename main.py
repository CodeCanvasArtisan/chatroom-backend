import os
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv

from routes.users import users as users_router
from routes.sessions import sessions as sessions_router

import pytz, datetime

APP_TZ = pytz.timezone("Australia/Brisbane")

app = FastAPI()

from database.database import engine
from database.models import Base

Base.metadata.create_all(bind=engine)



# Include routes
app.include_router(users_router)
app.include_router(sessions_router)
