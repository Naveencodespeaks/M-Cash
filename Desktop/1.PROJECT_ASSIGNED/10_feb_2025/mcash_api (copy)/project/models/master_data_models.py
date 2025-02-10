from sqlalchemy import Column, Integer,INT, String, Text, DateTime, ForeignKey,Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
#Base = declarative_base()
from  .base_model import BaseModel
class MdUserRole(BaseModel):
    __tablename__ = "md_user_roles"
    id = Column(Integer, primary_key=True, autoincrement=True)  # Ensure this is the primary key
    name = Column(Text, index=True)
    user = relationship('UserModel', back_populates='role_details')
    from_user_charges = relationship('ChargesModel', back_populates='from_role_details',foreign_keys="ChargesModel.from_role_id")
    to_user_charges = relationship('ChargesModel', back_populates='to_role_details',foreign_keys="ChargesModel.to_role_id")


    class Config:
        from_attributes = True
        str_strip_whitespace = True

class MdUserStatus(BaseModel):
    
    __tablename__ = "md_user_status"
    id = Column(Integer, primary_key=True, autoincrement=True)  # Ensure this is the primary key
    name = Column(Text )
    user_status = relationship('UserModel', back_populates='status_details')

class MdCountries(BaseModel):
    __tablename__ = "md_countries"
    id = Column(Integer, primary_key=True, autoincrement=True)
    shortName = Column(String(100), default='')
    name = Column(String(100), default='' )
    phoneCode = Column(Integer, default=None)
    order = Column(Integer, default=None)
    currencySymbol = Column(String(100), default='' )
    currencyCode = Column(String(100), default='' )
    zipcodeLength = Column(Integer, default=10)
    allowNumAndCharInZipcode = Column(String(100), default='' )
    mapName = Column(String(100), default="")
    currency_name = Column(String(100), default='' )
    #flag = Column(String(100), default='' )

    user_country = relationship("UserModel", back_populates="country_details")

    beneficiary_country = relationship("BeneficiaryModel", back_populates="beneficiary_country_details",  foreign_keys="[BeneficiaryModel.country_id]")
    beneficiary_bank_country = relationship("BeneficiaryModel", back_populates="beneficiary_bank_country_details",foreign_keys="[BeneficiaryModel.bank_country_id]")


#md_states.json
class MdStates(BaseModel):
    __tablename__ = "md_states"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name =   Column(String(100),default='' )
    mapName=  Column(String(100),default='' )
    countryId = Column(Integer, default=None)

class MdLocations(BaseModel):
    __tablename__ = "md_locations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name =   Column(String(100),default='' )
    stateId=  Column(Integer,default=None)
    countryId = Column(Integer, default=None)


#md_reminder_status
class MdReminderStatus(BaseModel):
    
    __tablename__ = "md_reminder_status"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(55) )
    


#md_task_status.json
class MdTaskStatus(BaseModel):
    __tablename__ = "md_task_status"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(55) )
    

#md_tenant_status
class MdTenantStatus(BaseModel):
    __tablename__ = "md_tenant_status"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(55) )
    

#md_timezone.json
class MdTimeZone(BaseModel):
    __tablename__ = "md_timezones"
    id = Column(Integer, primary_key=True, autoincrement=True)
    zone =  Column(String(55) )
    name = Column(String(55) )

class MdKycstatus(BaseModel):
    __tablename__ = "md_kyc_status"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(55) )
    user_kyc = relationship("UserModel", back_populates="kyc_status")
    kyc_agents = relationship("AgentModel", back_populates="agent_kyc_status_details")
    kyc_merhants = relationship("MerchantModel", back_populates="merchant_kyc_status_details")
    
class MdOccupations(BaseModel):
    __tablename__ = "md_occupations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(55) ) 
    user_occuption = relationship("UserKycDetailsModel", back_populates="occupation_details", foreign_keys="[UserKycDetailsModel.occupation_id]")   

#md_beneficiary_status
class MdBeneficiaryStatus(BaseModel):
    __tablename__ ="md_beneficiary_status"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(55) )
    beneficiary_status_details = relationship("BeneficiaryModel", back_populates="status_details",foreign_keys="[BeneficiaryModel.status_id]")


#admin_otp_configaration
class MdOtpConfigarations(BaseModel):
    __tablename__ = "md_otp_configarations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    beneficiary = Column(Integer, default=30 )



class MdBeneficiaryCategoryesModel(BaseModel):
    __tablename__ ="md_beneficiary_categoryes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(55) )
    beneficiary_category = relationship("BeneficiaryModel", back_populates="beneficiary_category_details",foreign_keys="[BeneficiaryModel.beneficiary_category_id]")

'''
class MdchargeCategoryesModel(BaseModel):
    __tablename__ = "md_charge_categoryes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(55))
    master_category = relationship("ChargesModel", back_populates="charge_category_details")
'''
class MdchargeCategoryesModel(BaseModel):
    __tablename__ = "md_charge_categoryes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(55), nullable=False)
    charges = relationship("ChargesModel", back_populates="charge_category_details")

class TransactionPurposeModel(BaseModel):
    __tablename__ = "transaction_purpose"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(700), default='')
    status = Column(Boolean, default=True)
    description = Column(Text, default='')
    flag =  Column(Text, default='')
    

    # Assuming you are using Config for custom purposes
    class Config:
        from_attributes = True
        str_strip_whitespace = True

class TransactionSubPurpose(BaseModel):
    __tablename__ = "transaction_sub_purpose"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(700), default='')
    status = Column(Boolean, default=True)
    description = Column(Text, default='')
    flag =  Column(Text, default='')
    #transaction_purpose_id = Column(Integer, ForeignKey("transaction_purpose.id"), nullable=False, unique=False)
    #transaction_purpose_details = relationship("TransactionPurposeModel", back_populates="transaction_subpurpose")

    # Assuming you are using Config for custom purposes
    class Config:
        from_attributes = True
        str_strip_whitespace = True


class MdFundsRequestStatus(BaseModel):
    __tablename__ = "md_funds_request_status"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), default='')
    all_requests = relationship("TransactionRequestModel", back_populates="status_details")


    class Config:
        from_attributes = True
        str_strip_whitespace = True     

class TransactionStatusModel(BaseModel):
    __tablename__ = "md_transaction_status"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), default='')
    transactions = relationship("TransactionModel", back_populates="status_details")
    admin_transactions = relationship("AdminTransactionModel", back_populates="status_details",foreign_keys="AdminTransactionModel.status_id")



    class Config:
        from_attributes = True
        str_strip_whitespace = True     

class MdKycDocPermissions(BaseModel):
    __tablename__ = "md_kyc_docs_permissions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    md_doc_id = Column(Integer)
    user_id = Column(Integer)
    
    tenant_id = Column(Integer, default=None)
    class Config:
        from_attributes = True
        str_strip_whitespace = True     


class MdServiceTypes(BaseModel):
    __tablename__ = "md_service_types"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), default='')
    status = Column(Boolean, default=True)
    description = Column(Text, default='')
    charges =  Column(Integer, default='')
    tenant_id = Column(Integer, default=1)
    
    class Config:
        from_attributes = True
        str_strip_whitespace = True

class MdCurrencyTypes(BaseModel):
    __tablename__ = "md_currency_types" #md_currency_types.json MdCurrencyTypes
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), default='')
    description = Column(Text, default='')
    currency_list = relationship("MdCurrency", back_populates="currency_type_details")
    tenant_id = Column(Integer, default=1)

    
    class Config:
        from_attributes = True
        str_strip_whitespace = True


class MdCurrency(BaseModel):
    __tablename__ = "md_currencies" #md_currencies.json MdCurrency
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), default='')
    description = Column(Text, default='')
    iso_code = Column(String(50), default='')
    currency_symbol  = Column(String(50), default='')
    default = Column(Boolean, default=False)
    status = Column(Boolean, default=True)
    subunits=Column(Integer, nullable=False)
    currency_type_id = Column(Integer, ForeignKey("md_currency_types.id"), index=True, default=None)
    currency_type_details = relationship("MdCurrencyTypes", back_populates="currency_list")
    
    currency_wallets = relationship("UserWalletModel", back_populates="currency_detils")
    currency_payment_gateway_ransaction = relationship("PaymentGatewayTransactionModel", back_populates="currency_detils")
    currency_transactions = relationship("TransactionModel", back_populates="currency_detils")
    admin_currency_wallets = relationship("AdminWalletModel", back_populates="currency_detils", foreign_keys="AdminWalletModel.currency_id")
    admin_currency_transactions = relationship("AdminTransactionModel", back_populates="currency_detils",foreign_keys="AdminTransactionModel.currency_id")


    tenant_id = Column(Integer, default=1)
    class Config:
        from_attributes = True
        str_strip_whitespace = True

