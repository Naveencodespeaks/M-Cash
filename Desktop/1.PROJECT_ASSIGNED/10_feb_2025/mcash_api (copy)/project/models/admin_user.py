from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
#from project.database.database import Base
from datetime import datetime,timezone
#Base = declarative_base()
from .base_model import BaseModel

class AdminUser(BaseModel):
    __tablename__ = "admin"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String(61))
    password = Column(Text)
    login_token = Column(Text)
    token = Column(Text)
    email = Column(String(161))
    mobile_no = Column(String(15))
    last_login = Column(DateTime, default= datetime.now(timezone.utc))
    role_id = Column(Integer, default=1)  # Ensure this matches UserRole.id
    status_id = Column(Integer, default=3)
    
    tenant_id = Column(Integer, ForeignKey("tenants.id"), default=None, unique=False, index=True)
    admin_tenant_details = relationship('TenantModel', back_populates='tenant_admin')

    admin_wallets = relationship("AdminWalletModel", back_populates="admin_details", foreign_keys="AdminWalletModel.admin_id") 
    admin_transactions = relationship("AdminTransactionModel", back_populates="admin_details", foreign_keys="AdminTransactionModel.admin_id")
  


    class Config:
        from_attributes = True
        str_strip_whitespace = True

