from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey,Boolean,DECIMAL,Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
#from project.database.database import Base
from datetime import datetime,timezone
#Base = declarative_base()
from .base_model import BaseModel

class CouponModel(BaseModel):
    __tablename__ = "coupons"
    id = Column(Integer, primary_key=True, autoincrement=True)
    coupon_code= Column(String(10), unique=True)
    description = Column(Text)
    coupon_amount = Column(Float)
    currency=Column(String(4))
    discount_type=Column(String(61), default="PERCENTAGE",comment="'FIXED_AMOUNT' or 'PERCENTAGE'")
    coupon_expiry_date=Column(DateTime,default=datetime.now(timezone.utc))
    usage_limit_per_person=Column(Integer, default=1)
    created_by=Column(Integer)
    updated_by=Column(Integer)
    tenant_id=Column(Integer,default=None)
    status = Column(Boolean, default=1,comment='1 active and 0 inactive')

    

    class Config:
        from_attributes = True
        str_strip_whitespace = True
       

    


    
