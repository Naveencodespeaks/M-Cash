from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
#from project.database.database import Base
from datetime import datetime
#Base = declarative_base()
from .base_model import BaseModel



class TicketsModel(BaseModel):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer,index=True,nullable=False,unique=False)
    description = Column(Text)
    reference=Column(String(150))
   

  
