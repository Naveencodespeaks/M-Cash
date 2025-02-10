from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
#from project.database.database import Base
from datetime import datetime,timezone
#Base = declarative_base()
from .base_model import BaseModel

class AgentModel(BaseModel):
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String(61), default='' )
    first_name = Column(String(50),  default='')
    last_name = Column(String(50),  default='')
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
    
    kyc_details_id = Column(Integer, ForeignKey("agent_kyc_detais.id"), nullable=True, default=None)
    kyc_details = relationship("AgentKycDetailsModel", back_populates="agent_details")
    
    kyc_status_id = Column(Integer, ForeignKey("md_kyc_status.id"), nullable=False, default=1 )
    agent_kyc_status_details = relationship("MdKycstatus", back_populates="kyc_agents")
    

    login_count =  Column(Integer, default=0,comment='User Login count') 
    login_fail_count =  Column(Integer, default=0,comment='User Login Fail count')
    login_attempt_date = Column(DateTime, default= None,comment='Last Login Attempt date' )
    tenant_id = Column(Integer, ForeignKey("tenants.id"), default=None, unique=False, index=True)
    agent_tenant_details = relationship('TenantModel', back_populates='tenant_agents')
    
        
class AgentKycDetailsModel(BaseModel):
    __tablename__ = "agent_kyc_detais"
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id =  Column(Integer)
    street = Column(Text)
    city = Column(Text)
    state_id =  Column(Integer,default=None)
    state = Column(Text)
    pincode = Column(String(50))
    annual_income=Column(Integer)
    agent_details = relationship("AgentModel", back_populates="kyc_details")
    

class AgentKycDocsModel(BaseModel):
    __tablename__ = "agent_kyc_docs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, nullable=False)
    tenant_id = Column(Integer, nullable=True)
    
    md_doc_id = Column(Integer, ForeignKey("md_kyc_docs.id"), nullable=False)
    md_doc_name =  Column(String(150),default='')
    md_doc_description = Column(String(150),default='')
    md_doc_required =  Column(Boolean,default=False)
    master_doc_details = relationship("MdKycDocs", back_populates="kycDoc_agents")
    
    
    
    name = Column(String(150))
    path = Column(String(750))
    content_type = Column(String(50),default='')
    size =Column(Integer, default=None)
    
    status_id = Column(Integer, ForeignKey("md_user_kyc_docs_status.id"), nullable=False, default=1)
    status_details = relationship("MdUserKycDocsStatus", back_populates="agent_kyc_doc_status")
        
    
    doc_comments = relationship("AgentKycDocsCommentsModel", back_populates="agent_doc_details")
    


class AgentKycDocsCommentsModel(BaseModel):
    __tablename__ = "agent_kyc_doc_comments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_kyc_doc_id = Column(Integer, ForeignKey("agent_kyc_docs.id"), nullable=False)
    
    agent_doc_details = relationship("AgentKycDocsModel", back_populates="doc_comments")
    
    
    comment = Column(Text)
    commented_by = Column(Integer, nullable=False)
    commented_by_role_id = Column(Integer, nullable=False)

