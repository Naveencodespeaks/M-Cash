from sqlalchemy import Column, Integer,Float, String, Float, Text, DateTime, Date,ForeignKey,Boolean,Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
#from project.database.database import Base
from datetime import datetime,timezone

#Base = declarative_base()
from .base_model import BaseModel

from sqlalchemy import Column, Integer, String, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
import time


'''
class ChargesModel(BaseModel):
    __tablename__ = "remittance_charges"
    id = Column(Integer, primary_key=True, autoincrement=True)
    #md_category_id = Column(Integer)
    md_category_id = Column(Integer, ForeignKey("md_charge_categoryes.id"), nullable=False)
    charge_category_details = relationship("MdchargeCategoryesModel", back_populates="master_category")
    
    
    status = Column(Boolean, default=True)
    charges = Column(Integer, default=0)
    calculate_in_percentage = Column(Boolean, default=True)
    description = Column(Text, default='')
    tenant_id =  Column(Integer, default=None)

    class Config:
        from_attributes = True
        str_strip_whitespace = True
        extend_existing=True
'''        
class ChargesModel(BaseModel):
    __tablename__ = "remittance_charges"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(25), default='')
    md_category_id = Column(Integer, ForeignKey("md_charge_categoryes.id"), nullable=False)
    charge_category_details = relationship("MdchargeCategoryesModel", back_populates="charges")
    #currency = Column(String(25), default='')
    apply_to = Column(String(25), default='' ,comment="VALUES SHOULD BE DOMESTIC OR,INTERNATIONAL or SPECIFIC_USER")
    minimum_transaction_amount = Column(Integer, default=None)
    maximum_transaction_amount = Column(Integer, default=None)
    users_list = Column(Text, default='')
    effective_date = Column(DateTime, default= datetime.now(timezone.utc) )
    status = Column(Boolean, default=True)
    charges = Column(Float, default=0)
    admin_charges=Column(Float, default=0)
    agent_charges=Column(Float, default=0)
    calculate_in_percentage = Column(Boolean, default=True)
    description = Column(Text, default='')
    
    from_role_id = Column(Integer, ForeignKey('md_user_roles.id'), nullable=False,default=None)  # Ensure this matches UserRole.id
    from_role_details = relationship('MdUserRole', back_populates='from_user_charges',foreign_keys=[from_role_id])
    
    to_role_id = Column(Integer, ForeignKey('md_user_roles.id'), nullable=False,default=None)  # Ensure this matches UserRole.id
    to_role_details = relationship('MdUserRole', back_populates='to_user_charges',foreign_keys=[to_role_id])

    tenant_id = Column(Integer, nullable=True)


    class Config:
        from_attributes = True
        str_strip_whitespace = True
        extend_existing = True
     
class UserWalletModel(BaseModel):
    __tablename__ = "user_wallets"
    id = Column(Integer, primary_key=True, autoincrement=True)
    #md_currencies MdCurrency
    currency_id = Column(Integer, ForeignKey("md_currencies.id"), default=None, nullable=True)
    currency_detils = relationship("MdCurrency", back_populates="currency_wallets")
    balance = Column(Numeric(precision=10, scale=2), default=0.0)
    status = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    credited_by = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Specify the foreign_keys argument for the relationship back to the UserModel
    user_details = relationship("UserModel", back_populates="wallets", foreign_keys=[user_id])
    credeted_user_details = relationship("UserModel", back_populates="wallets", foreign_keys=[credited_by])

    
class PaymentGatewayTransactionModel(BaseModel):
    __tablename__ = "payment_gateway_transactions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    razorpay_payment_id = Column(String(500), default=None, nullable=True)
    razorpay_order_id = Column(String(500), default=None, nullable=True)
    razorpay_signature = Column(String(500), default=None, nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user_details = relationship("UserModel", back_populates="payment_gateway_transactions")
    amount = Column(Numeric(precision=10, scale=2), default=0.00, comment="")
    payment_gateway_status = Column(String(100), default="Initiated", nullable=True)
    currency_id = Column(Integer, ForeignKey("md_currencies.id"), default=None, nullable=True)
    currency_detils = relationship("MdCurrency", back_populates="currency_payment_gateway_ransaction")
    status = Column(Boolean, default= False, comment="If status == False payment not completed  if status==True Payment Completed" )
    
 
class TransactionRequestModel(BaseModel):
    __tablename__ = "transactionrequests"
    id = Column(Integer, primary_key=True, autoincrement=True )
    shared_transaction_id=Column(String(55), nullable=True, comment="", default=None)
    amount = Column(Numeric(precision=10, scale=2), default=0.00, comment="This amount is user want to send")
    charges_amount = Column(Numeric(precision=10, scale=2), default=0.00,comment="This amount is all charges amount")
    referenc_id =Column(String(50), default=time.time())
    http_request_data = Column(Text,default='')
    to_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    to_user_details = relationship("UserModel", back_populates="to_user_transaction_requests", foreign_keys=[to_user_id])
    currency_id = Column(Integer, default=None, nullable=True)
    from_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    from_user_details = relationship("UserModel", back_populates="from_user_transaction_requests", foreign_keys=[from_user_id])
    transactions = relationship("TransactionModel", back_populates="transaction_request_details", foreign_keys="TransactionModel.transaction_request_id")
    is_active = Column(Boolean, default=True, nullable=False)
    description = Column(Text,default='')

    status_id = Column(Integer, ForeignKey('md_funds_request_status.id'), nullable=False, default=1)
    status_details = relationship("MdFundsRequestStatus", back_populates="all_requests")
    status_updated_by = Column(Integer, default=None)

    admin_transactions = relationship("AdminTransactionModel", back_populates="transaction_request_details", foreign_keys="AdminTransactionModel.transaction_request_id")
     
    

class TransactionModel(BaseModel):
     __tablename__ = "transactions"
     id = Column(Integer, primary_key=True, autoincrement=True)
     shared_transaction_id=Column(String(55), nullable=True, comment="", default=None)
     transaction_type = Column(String(10), nullable=False, comment="CREDIT or DEBIT")# 'credit' or 'debit'
     amount = Column(Numeric(precision=10, scale=2), default=0.00, comment="This amount is user want to send")
     charges_amount = Column(Numeric(precision=10, scale=2), default=0.00,comment="This amount is all charges amount")
     ledger_amount = Column(Numeric(precision=10, scale=2), default=0.00, comment="This is converted exange amount. beneficiary will get this amount in to_currency")
     credit_type = Column(String(10), nullable=False, default="", comment="")# 'credit' or 'debit'
     referenc_id =Column(String(50), default=time.time())
     request_data = Column(Text,default='')
     payment_gateway_data = Column(Text,default='')
     payment_gateway_status =Column(Text, default='')
     
     track_id =Column(String(50), default = None)   
     
     

    # Relationships
     transaction_request_id = Column(Integer, ForeignKey('transactionrequests.id'), nullable=True, default=None)
     transaction_request_details = relationship("TransactionRequestModel", back_populates="transactions", foreign_keys=[transaction_request_id])
     
     user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
     user = relationship("UserModel", back_populates="transactions", foreign_keys=[user_id])

     credited_from_user_id = Column(Integer, ForeignKey('users.id'), nullable=True, default=None)
     credited_from_user_details = relationship("UserModel", back_populates="credited_from_transactions", foreign_keys=[credited_from_user_id])
     
     currency_id = Column(Integer, ForeignKey("md_currencies.id"), default=None, nullable=True)
     currency_detils = relationship("MdCurrency", back_populates="currency_transactions")

     status_id = Column(Integer, ForeignKey('md_transaction_status.id'), nullable=False, default=1)
     status_details = relationship("TransactionStatusModel", back_populates="transactions")


     
     tenant_id = Column(Integer, ForeignKey("tenants.id"), default=None, unique=False, index=True)
     tenant_details = relationship('TenantModel', back_populates='tenant_transactions')
     

     
     description = Column(Text,default='')
     class Config:
        from_attributes = True
        str_strip_whitespace = True
        extend_existing=True
  
    
class BankAccountModel(BaseModel):
    __tablename__ = "bank_accounts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    number = Column(String(35), nullable=False)
    account_name = Column(String(35), nullable=False)
    bank_name = Column(String(35), default='')
    cvv = Column(String(4), default=None)  # CVV as a string
    expiary_date = Column(String(35), default='') #Column(Date, default=None)  # Use Date for just the date
    category = Column(String(35), default="BANK")  # BANK, CREDIT_CARD, DEBIT_CARD
    ifsc = Column(String(15), default='') #this is required if BANK
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Relationships
    user = relationship("UserModel", back_populates="bank_accounts")  # Assuming UserModel exists
    

    class Config:
        from_attributes = True
        str_strip_whitespace = True
        extend_existing=True
   

##Admin Wallets and transactions

class AdminWalletModel(BaseModel):
    __tablename__ = "admin_wallets"
    id = Column(Integer, primary_key=True, autoincrement=True)
    #md_currencies MdCurrency
    currency_id = Column(Integer, ForeignKey("md_currencies.id"), default=None, nullable=True)
    currency_detils = relationship("MdCurrency", back_populates="admin_currency_wallets")
    balance = Column(Numeric(precision=10, scale=2), default=0.0)
    status = Column(Boolean, default=True)
    
    

    # Specify the foreign_keys argument for the relationship back to the UserModel
    admin_id = Column(Integer, ForeignKey('admin.id'), nullable=False)
    admin_details = relationship("AdminUser", back_populates="admin_wallets", foreign_keys=[admin_id])
    

    credited_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    credeted_user_details = relationship("UserModel", back_populates="admin_wallets", foreign_keys=[credited_by])
    
class AdminTransactionModel(BaseModel):
     __tablename__ = "admin_transactions"
     id = Column(Integer, primary_key=True, autoincrement=True)
     shared_transaction_id=Column(String(55), nullable=True, comment="", default=None)
     transaction_type = Column(String(10), nullable=False, comment="CREDIT or DEBIT")# 'credit' or 'debit'
     amount = Column(Numeric(precision=10, scale=2), default=0.00, comment="This amount is user want to send")
     charges_amount = Column(Numeric(precision=10, scale=2), default=0.00,comment="This amount is all charges amount")
     ledger_amount = Column(Numeric(precision=10, scale=2), default=0.00, comment="This is converted exange amount. beneficiary will get this amount in to_currency")
     
     referenc_id =Column(String(50), default=time.time())
     request_data = Column(Text,default='')
     payment_gateway_data = Column(Text,default='')
     payment_gateway_status =Column(Text, default='')
     
     track_id =Column(String(50), default = None)   
     
     

    # Relationships
     transaction_request_id = Column(Integer, ForeignKey('transactionrequests.id'), nullable=True, default=None)
     transaction_request_details = relationship("TransactionRequestModel", back_populates="admin_transactions", foreign_keys=[transaction_request_id])
     

     admin_id = Column(Integer, ForeignKey('admin.id'), nullable=False)
     admin_details = relationship("AdminUser", back_populates="admin_transactions", foreign_keys=[admin_id])
     
     credited_from_user_id = Column(Integer, ForeignKey('users.id'), nullable=True, default=None)
     credited_from_user_details = relationship("UserModel", back_populates="credited_from_admin_transactions", foreign_keys=[credited_from_user_id])
     

     currency_id = Column(Integer, ForeignKey("md_currencies.id"), default=None, nullable=True)
     currency_detils = relationship("MdCurrency", back_populates="admin_currency_transactions",foreign_keys=[currency_id])
     
     status_id = Column(Integer, ForeignKey('md_transaction_status.id'), nullable=False, default=1)
     status_details = relationship("TransactionStatusModel", back_populates="admin_transactions",foreign_keys=[status_id])
     

     
     tenant_id = Column(Integer, ForeignKey("tenants.id"), default=None, unique=False, index=True)
     tenant_details = relationship('TenantModel', back_populates='admin_tenant_transactions', foreign_keys=[tenant_id])
     

     
     description = Column(Text,default='')
     class Config:
        from_attributes = True
        str_strip_whitespace = True
        extend_existing=True
    



    
    

    




  
