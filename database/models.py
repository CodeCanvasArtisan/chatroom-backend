from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base() # base class for all models

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    display_name = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=False, index=True, nullable=False)

    def to_dict(self):
        return {
            "id" : self.id,
            "display_name" : self.display_name,
            "email" : self.email
        }
    
