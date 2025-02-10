from sqlalchemy import Column, Integer,INT, String, Text, DateTime, ForeignKey,Enum,Date,Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
#from project.database.database import Base
#Base = declarative_base()
from  .base_model import BaseModel
from datetime import datetime

class MdKycDocs(BaseModel):
    __tablename__ = "md_kyc_docs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(55))
    status = Column(Boolean, default=True)
    required= Column(Boolean, default=True)
    category= Column(String(25), default="USERS", comment="category should be USERS or AGENTS OR MERCHANTS")
    description = Column(Text)
    #size = Column(Integer)
    users_list = Column(Text)
    share_type = Column(String(25), default="ALL_USERS", comment="share_type should be SPECIFIC_USERS or UPCOMMING_USERS OR ALL_USERS")
    # email = Column(String(161), nullable=False )
    tenant_id = Column(Integer, ForeignKey("tenants.id"), default=None, unique=False, index=True)
    tenant_details = relationship('TenantModel', back_populates='tenant_md_kyc_docs')
    user_kycDocs = relationship("UserKycDocsModel", back_populates="master_doc_details")

    #relation with Merchant
    kycDoc_merchants = relationship("MerchantKycDocsModel", back_populates="master_doc_details")
    kycDoc_agents = relationship("AgentKycDocsModel", back_populates="master_doc_details")


class MdUserKycDocsStatus(BaseModel):
    __tablename__ = "md_user_kyc_docs_status"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(55))
    
    user_kyc_doc_status = relationship("UserKycDocsModel", back_populates="doc_status_details")

    #relation with Merchant
    merchant_kyc_doc_status = relationship("MerchantKycDocsModel", back_populates="status_details")
    agent_kyc_doc_status = relationship("AgentKycDocsModel", back_populates="status_details")


class UserKycDocsModel(BaseModel):
    __tablename__ = "user_kyc_docs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    tenant_id = Column(Integer, nullable=True)
    
    md_doc_id = Column(Integer, ForeignKey("md_kyc_docs.id"), nullable=False)
    md_doc_name =  Column(String(150),default='')
    md_doc_description = Column(String(150),default='')
    md_doc_required =  Column(Boolean,default=False)
    master_doc_details = relationship("MdKycDocs", back_populates="user_kycDocs")
    
    name = Column(String(150))
    path = Column(String(750))
    content_type = Column(String(50),default='')
    size =Column(Integer, default=None)
    
    status_id = Column(Integer, ForeignKey("md_user_kyc_docs_status.id"), nullable=False, default=1)
    doc_status_details = relationship("MdUserKycDocsStatus", back_populates="user_kyc_doc_status")
    
    user_doc_comments = relationship("KycDocsCommentsModel", back_populates="user_doc_details")


class KycDocsCommentsModel(BaseModel):
    __tablename__ = "kyc_doc_comments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_doc_id = Column(Integer, ForeignKey("user_kyc_docs.id"), nullable=False)
    
    user_doc_details = relationship("UserKycDocsModel", back_populates="user_doc_comments")
    
    comment = Column(Text)
    commented_by = Column(Integer, nullable=False)
    commented_by_role_id = Column(Integer, nullable=False)



