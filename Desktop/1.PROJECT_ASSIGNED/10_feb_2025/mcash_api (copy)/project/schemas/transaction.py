from pydantic import BaseModel, EmailStr, Field, ValidationError, validator,field_validator
import re
from datetime import date, datetime

from ..schemas.user_schema import ListRequestBase
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field, ValidationError, validator,field_validator
import re
from datetime import date, datetime


class AddWallet(BaseModel):
    amount:int
    wallet_id:Optional[int]
    currency_id:int

class GetWalletDetails(BaseModel):
    wallet_id:int
    

class paymentSuccessSchema(BaseModel):
    razorpay_payment_id:str
    razorpay_order_id:Optional[str] = None
    razorpay_signature:Optional[str] = None




class CreateCharges(BaseModel):
    name:str
    #currency:str
    md_category_id:int
    apply_to:str
    minimum_transaction_amount:Optional[int]
    maximum_transaction_amount:Optional[int]
    users_list:Optional[str] =''
    effective_date:date = Field(..., description="Must be grater than or equal today format should be YYYY-MM-DD")
    charges:float
    admin_charges:float
    agent_charges:float
    calculate_in_percentage:bool
    description:Optional[str] =''
    from_role_id:int
    to_role_id:int
    
      
    
    
    
    @field_validator('calculate_in_percentage','charges', mode='before')
    def validatorsada_charges(cls, v, info):
        
        if info.field_name == 'calculate_in_percentage':            
            charges = info.data.get('charges')
            if v:
                if charges>100:
                    raise ValueError('Charges must be less than or equal to 100.')
                elif v<0:
                    raise ValueError('Charges must be grater than or equal to 0.')

        return v 
    
    @field_validator('md_category_id', mode='before')
    def category_validator(cls, v, info):
        #v = v.strip()
        if v is None or v=="" or v<=0:
            raise ValueError('md_category_id is required and cannot be None.!')
        return v
    
    @field_validator('description', mode='before')
    def check_description(cls, v):
        if v is None or v=="":
            raise ValueError('Description is required and cannot be None.')
        return v
    @field_validator('apply_to', mode='before')
    def check_apply_to(cls, v):
        if v not in ["DOMESTIC","INTERNATIONAL","SPECIFIC_USER"]:
            raise ValueError('Apply to should be DOMESTIC OR,INTERNATIONAL or SPECIFIC_USER.')
        return v
    class Config:
        from_attributes = True
        str_strip_whitespace = True
    
class EditCharges(CreateCharges):
    charge_id:int
class UpdateStatusSchema(BaseModel):
     charge_id:int
     status:bool

class ChargesListReqSchema(ListRequestBase):
    status:bool = None
    md_category_id:Optional[int] =None

class GetWalletsList(ListRequestBase):
    user_id:Optional[int] = None


class GetSummary(BaseModel):
    # id:int
    user_wallet_id:Optional[int] =None
    currency_id:int
    transfer_amount:int
    description:Optional[str] =""
    #coupon_code:Optional[str]=''
    to_user_id:int
    class Config:
        from_attributes = True
        str_strip_whitespace = True

class transactionPorposListReq(ListRequestBase):
    status: Optional[List[bool]] = [True]
    sort_by: Optional[str] = "id"  # Default sort by 'created_on'
    sort_order: Optional[str] = "asc"
    #search_string: Optional[str] = None 

class transactionSubPorposListReq(ListRequestBase):
    status: Optional[List[bool]] = [True]
    transaction_purpose_id:Optional[int]

class transactionPorposListRes(BaseModel):
    id:int
    name:str
    description:str

class PaginatedTransactionPorposListRes(BaseModel):
    total_count: int
    #list: List[transactionPorposListRes]
    page: int
    per_page: int

class AddBankAccount(BaseModel):
    number:str
    account_name:str
    bank_name:Optional[str]=''
    cvv:Optional[int]=Field(None, description="")
    expiary_date:Optional[str]='' #Optional[date] = Field(None, description="Must be at least 18 years old.And format should be YYYY-MM-DD")
    category:str #Column(String(35), default="BANK") #BANK, CREDIT_CARD , DEBET_CARD
    ifsc:Optional[str]=''
    # @field_validator('expiary_date', mode='before')
    # def validate_date_of_birth(cls, v, info):
    #     # Ensure v is a date object
    #     if isinstance(v, str):
    #         v = date.fromisoformat(v)  # Convert from string to date if needed
    #     today = date.today()
    #     age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
    #     if age < 18:
    #         raise ValueError('You must be at least 18 years old. And format should be YYYY-MM-DD')
    #     return v
    
    # @field_validator('category', 'cvv', mode='before')
    # def passwords_match(cls, v, info):
        
    #     # Access other values from info.
    #     if info.field_name == 'category':
    #         cvv = info.data.get('cvv')
    #         if v not in ["BANK","CREDIT_CARD" ,"DEBET_CARD"]:
    #             raise ValueError('Category should be BANK or CREDIT_CARD or DEBET_CARD ')
    #         if v in ["CREDIT_CARD","DEBET_CARD" ]:
    #             if v is None or v =='':
    #                 raise ValueError('CVV is required ')
    #     return v
    # @field_validator('account_name', mode='before')
    # def valid_account_name(cls, v, info):
    #     if v is None or v=='':
    #         raise ValueError('Account Name is required')
    #     return v
    
    @field_validator('number', mode='before')
    def valid_cvv(cls, v, info):
        if v is None or v=='':
            raise ValueError('Number is required')
        return v
    
    # @field_validator('bank_name', mode='before')
    # def validate_bank_name(cls, v, info):
    #     if v is None or v=='':
    #         raise ValueError('Bank name required')
    #     return v

class BankAccountsListReq(ListRequestBase):
    category: str


class TransactionInitiate(BaseModel):
     from_currency:str
     to_currency :str
     source_amount:float
     charges_amount:float
     transfer_amount:float     
     current_exange_rate:float
     remit_charges:Optional[str]=''
     #user_id :int
     bank_acc_id:int
     beneficiary_id:int
     transaction_purpose_id:int
     description:Optional[str]=''
     coupon_id:Optional[int]=''
     service_type_id:Optional[int]=None
     
     #request_data:str
     #tenani_id = Column(Integer,default=None)
         
    
class ActivateTransactionRequest(BaseModel):
    ref_id:str
    otp:str
    
    class Config:
        from_attributes = True
        str_strip_whitespace = True

class ResendTransactionOtp(BaseModel):
    transaction_id:int
    referenc_id:str
        
    class Config:
        from_attributes = True
        str_strip_whitespace = True


class TransactionListReq(ListRequestBase):
     status_ids: Optional[List[int]] = []
     user_ids: Optional[List[int]] = [] # For Admin Login
     category:Optional[str] = "INBOX_REQUESTS" # SENT_REQUESTS

     class Config:
        from_attributes = True
        str_strip_whitespace = True


class TransactionDetailsSchema(BaseModel):
     transaction_id:int
     class Config:
        from_attributes = True
        str_strip_whitespace = True

class getOtpForFundRequestTransferSchema(BaseModel):
    transaction_request_id:int
    
    class Config:
        from_attributes = True
        str_strip_whitespace = True

class ApproveRequestedFundsTransferSchema(BaseModel):
    transaction_request_id:int
    referenc_id:str
    otp:str
    class Config:
        from_attributes = True
        str_strip_whitespace = True

class UpdateRequestStatus(BaseModel):
     transaction_id:int
     status_id:int
     class Config:
        from_attributes = True
        str_strip_whitespace = True
