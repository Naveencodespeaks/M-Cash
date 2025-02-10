from sqlalchemy import Column, Integer,INT, String, Text, DateTime, ForeignKey,Enum,Date,Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
#from project.database.database import Base
#Base = declarative_base()
from  .base_model import BaseModel
from datetime import datetime
from enum import Enum as PyEnum
class kycStatus(PyEnum):
    PENDING = 0
    COMPLETED = 1
    

class tokensModel(BaseModel):
    __tablename__ = "tokens"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ref_id = Column(Integer,nullable=False) # like value of UserModel.id,BeneficiaryModel.id 
    user_id = Column(Integer,nullable=False)
    otp=Column(String(61))
    catrgory = Column(String(150), nullable = False) # model name of  string (UserModel,BeneficiaryModel)
    token = Column(Text)
    active =Column(Boolean, default=True)
    
    
    
    
    class Config:
        from_attributes = True
        str_strip_whitespace = True

