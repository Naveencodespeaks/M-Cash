from sqlalchemy import Column, Integer,INT, String, Text, DateTime, ForeignKey,Enum,Date,Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
#from project.database.database import Base
#Base = declarative_base()
from  .base_model import BaseModel
from datetime import datetime,timezone
from enum import Enum as PyEnum
class kycStatus(PyEnum):
    PENDING = 0
    COMPLETED = 1



class TenantModel(BaseModel):
    __tablename__ = "tenants" 
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), default='')
    email = Column(String(161), nullable=False )
    mobile_no = Column(String(15), default="")
    tenant_user = relationship('UserModel', back_populates='tenant_details')
    tenant_admin = relationship('AdminUser', back_populates='admin_tenant_details')
    tenant_transactions = relationship('TransactionModel', back_populates='tenant_details')
    tenant_md_kyc_docs = relationship('MdKycDocs', back_populates='tenant_details')
    tenant_agents = relationship('AgentModel', back_populates='agent_tenant_details') 
    tenant_merchants = relationship('MerchantModel', back_populates='merchant_tenant_details')
    admin_tenant_transactions = relationship('AdminTransactionModel', back_populates='tenant_details', foreign_keys="AdminTransactionModel.tenant_id")
     
    
    class Config:
        from_attributes = True
        str_strip_whitespace = True
   
class NotificationModel(BaseModel):
    __tablename__ = "user_notificatuions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    tenant_id = Column(Integer, default=None)
    category = Column(String(50), default = None)
    status_category= Column(String(50), default = None)
    ref_id = Column(Integer,default=None)
    user_details = relationship('UserModel', back_populates='user_notifications',foreign_keys=[user_id] )
    
    class Config:
        from_attributes = True
        str_strip_whitespace = True
class AdminNotificationModel(BaseModel):
    __tablename__ = "admin_notificatuions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    admin_id = Column(Integer, ForeignKey("admin.id"), unique=False, index=True)
    user_id = Column(Integer,ForeignKey("users.id"), index=True)
    category = Column(String(50), default = None)
    status_category= Column(String(50), default = None)
    ref_id = Column(Integer,default=None)
    user_details = relationship('UserModel',  back_populates='admin_notificatuions',foreign_keys=[user_id])
    

    
    class Config:
        from_attributes = True
        str_strip_whitespace = True
   


class UserKycDetailsModel(BaseModel):
    __tablename__ = "kyc_detais"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id =  Column(Integer)
    street = Column(Text)
    city = Column(Text)
    state_id =  Column(Integer,default=None)
    state = Column(Text)
    pincode = Column(String(50))
   
    annual_income=Column(Integer)
    occupation_id = Column(Integer, ForeignKey("md_occupations.id"), nullable=False, default=None )
    occupation_details = relationship("MdOccupations", back_populates="user_occuption")
    
    kyc_user_details = relationship("UserModel", back_populates="kyc_details")
    

class UserModel(BaseModel):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    name = Column(String(150), default='')
    password = Column(Text)
    token = Column(Text)
    email = Column(String(161), nullable=False )
    mobile_no = Column(String(15), default="")
    
    date_of_birth = Column(Date, nullable=True) 
    last_login = Column(DateTime, default= datetime.now(timezone.utc) )

    login_count =  Column(Integer, default=0,comment='User Login count') 
    login_fail_count =  Column(Integer, default=0,comment='User Login Fail count')
    login_attempt_date = Column(DateTime, default= None,comment='Last Login Attempt date' )
    otp=Column(String(61))
    #tenant_id = Column(Integer, nullable=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), default=None, unique=False, index=True)
    tenant_details = relationship('TenantModel', back_populates='tenant_user')

    role_id = Column(Integer, ForeignKey('md_user_roles.id'), nullable=False,default=1)  # Ensure this matches UserRole.id
    role_details = relationship('MdUserRole', back_populates='user')
    status_id = Column(Integer, ForeignKey('md_user_status.id'),  nullable=False,default=1)
    status_details = relationship('MdUserStatus', back_populates='user_status')
    
    kyc_details_id =  Column(Integer, ForeignKey("kyc_detais.id"), nullable=True, unique=False,default=None )
    kyc_details = relationship("UserKycDetailsModel", back_populates="kyc_user_details")

    country_id = Column(Integer, ForeignKey("md_countries.id"), nullable=False, default=None )
    country_details = relationship("MdCountries", back_populates="user_country")
    

    state_id = Column(Integer, ForeignKey("md_states.id"), nullable=True, default=None )
    location_id = Column(Integer, ForeignKey("md_locations.id"), nullable=True, index=True )

    #KYC STATUS
    kyc_status_id = Column(Integer, ForeignKey("md_kyc_status.id"), nullable=False, default=1 )
    kyc_status = relationship("MdKycstatus", back_populates="user_kyc")
    
    user_notifications = relationship('NotificationModel', back_populates='user_details',foreign_keys='NotificationModel.user_id' )
    admin_notificatuions = relationship('AdminNotificationModel',  back_populates='user_details', foreign_keys='AdminNotificationModel.user_id')
    transactions = relationship("TransactionModel", back_populates="user", foreign_keys="TransactionModel.user_id")  # Access transactions from user
    bank_accounts = relationship("BankAccountModel", back_populates="user")  # Access bank accounts from user
    
    wallets = relationship("UserWalletModel", back_populates="user_details", foreign_keys="UserWalletModel.user_id")

    payment_gateway_transactions = relationship("PaymentGatewayTransactionModel", back_populates="user_details")
    to_user_transaction_requests = relationship("TransactionRequestModel", back_populates="to_user_details", foreign_keys="TransactionRequestModel.to_user_id")
    from_user_transaction_requests = relationship("TransactionRequestModel", back_populates="from_user_details", foreign_keys="TransactionRequestModel.from_user_id")
    credited_from_transactions = relationship("TransactionModel", back_populates="credited_from_user_details", foreign_keys="TransactionModel.credited_from_user_id")

    admin_wallets = relationship("AdminWalletModel", back_populates="credeted_user_details", foreign_keys="AdminWalletModel.credited_by")
    credited_from_admin_transactions = relationship("AdminTransactionModel", back_populates="credited_from_user_details", foreign_keys="AdminTransactionModel.credited_from_user_id")
     

    accepted_terms = Column(Boolean, default=False)

    class Config:
        from_attributes = True
        str_strip_whitespace = True




class BeneficiaryModel(BaseModel):
    __tablename__ = "beneficiaries"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=False, index=True)

    full_name = Column(String(50), index=True)
    nick_name = Column(String(50), default="")
    email = Column(String(161), nullable=True )
    mobile_no = Column(String(15), nullable=True)

    beneficiary_category_id = Column(Integer, ForeignKey("md_beneficiary_categoryes.id"), nullable=False)
    beneficiary_category_details = relationship("MdBeneficiaryCategoryesModel", back_populates="beneficiary_category",foreign_keys=[beneficiary_category_id] )
    
    country_id = Column(Integer, ForeignKey("md_countries.id"), nullable=False)
    beneficiary_country_details = relationship(
        "MdCountries", 
        back_populates="beneficiary_country",
        foreign_keys=[country_id]
    )
    
    city = Column(String(50), index=True)
    state_province = Column(String(50))
    postal_code = Column(String(50),default="")
    swift_code = Column(String(20))
    iban = Column(String(20))
    bank_name = Column(String(50))
    routing_number = Column(String(20))
    use_routing_number = Column(Boolean,default=False)
    bank_currency = Column(String(5))
    bank_country_id = Column(Integer, ForeignKey("md_countries.id"), nullable=False)
    beneficiary_bank_country_details = relationship(
        "MdCountries", 
        back_populates="beneficiary_bank_country",
        foreign_keys=[bank_country_id]
    )
    
    bank_address = Column(String(1500))
    status_id = Column(Integer, ForeignKey("md_beneficiary_status.id"), nullable=False)
    status_details = relationship(
        "MdBeneficiaryStatus",
        back_populates="beneficiary_status_details",
        foreign_keys=[status_id]
    )
    

