from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey,Boolean, Date
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
#from project.database.database import Base
from datetime import datetime,timezone
#Base = declarative_base()
from .base_model import BaseModel

  
class MerchantModel(BaseModel):
    __tablename__ = "merchants"
    id = Column(Integer, primary_key=True, autoincrement=True)

    user_name = Column(String(61))
    first_name = Column(String(50))
    last_name = Column(String(50))
    name = Column(String(150), default='')
    date_of_birth = Column(Date, nullable=True) 
    password = Column(Text)
    login_token = Column(Text)
    token = Column(Text)
    email = Column(String(161))
    mobile_no = Column(String(15))
    last_login = Column(DateTime, default= datetime.now(timezone.utc))
    role_id = Column(Integer, default=1)  # Ensure this matches UserRole.id
    status_id = Column(Integer, default=1)
    country_id = Column(Integer, default=None)
    
    kyc_status_id = Column(Integer, ForeignKey("md_kyc_status.id"), nullable=False, default=1 )
    merchant_kyc_status_details = relationship("MdKycstatus", back_populates="kyc_merhants")
    
    kyc_details_id = Column(Integer, ForeignKey("merchant_kyc_detais.id"), nullable=True, default=None)
    kyc_details = relationship("MerchantKycDetailsModel", back_populates="merchant_details")
    
    

    login_count =  Column(Integer, default=0,comment='User Login count') 
    login_fail_count =  Column(Integer, default=0,comment='User Login Fail count')
    login_attempt_date = Column(DateTime, default= None,comment='Last Login Attempt date' )
    tenant_id = Column(Integer, ForeignKey("tenants.id"), default=None, unique=False, index=True)
    merchant_tenant_details = relationship('TenantModel', back_populates='tenant_merchants')
    
    class Config:
        from_attributes = True
        str_strip_whitespace = True

class MerchantKycDetailsModel(BaseModel):
    __tablename__ = "merchant_kyc_detais"
    id = Column(Integer, primary_key=True, autoincrement=True)
    merchant_id =  Column(Integer)
    street = Column(Text)
    city = Column(Text)
    state_id =  Column(Integer,default=None)
    state = Column(Text)
    pincode = Column(String(50))
    annual_income=Column(Integer)
    merchant_details = relationship("MerchantModel", back_populates="kyc_details")
    


class MerchantKycDocsModel(BaseModel):
    __tablename__ = "merchant_kyc_docs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    merchant_id = Column(Integer, nullable=False)
    tenant_id = Column(Integer, nullable=True)
    
    md_doc_id = Column(Integer, ForeignKey("md_kyc_docs.id"), nullable=False)
    md_doc_name =  Column(String(150),default='')
    md_doc_description = Column(String(150),default='')
    md_doc_required =  Column(Boolean,default=False)
    master_doc_details = relationship("MdKycDocs", back_populates="kycDoc_merchants")
    
    
    name = Column(String(150))
    path = Column(String(750))
    content_type = Column(String(50),default='')
    size =Column(Integer, default=None)
    
    status_id = Column(Integer, ForeignKey("md_user_kyc_docs_status.id"), nullable=False, default=1)
    status_details = relationship("MdUserKycDocsStatus", back_populates="merchant_kyc_doc_status")
    
    
    doc_comments = relationship("MerchantKycDocsCommentsModel", back_populates="merchant_doc_details")


class MerchantKycDocsCommentsModel(BaseModel):
    __tablename__ = "merchant_kyc_doc_comments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    merchant_kyc_doc_id = Column(Integer, ForeignKey("merchant_kyc_docs.id"), nullable=False)
    
    merchant_doc_details = relationship("MerchantKycDocsModel", back_populates="doc_comments")
    
    comment = Column(Text)
    commented_by = Column(Integer, nullable=False)
    commented_by_role_id = Column(Integer, nullable=False)

   