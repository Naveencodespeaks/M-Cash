from pydantic import BaseModel, EmailStr, Field, ValidationError, validator,field_validator
import phonenumbers
from phonenumbers import NumberParseException, is_valid_number
import re
from datetime import date, datetime, timedelta
from typing import Optional, List
# from ..schemas.master_data import Document 


class UpdateProfile(BaseModel):    
    
    first_name: str
    last_name: str
    date_of_birth: date = Field(..., description="Must be at least 18 years old.And format should be YYYY-MM-DD")
    mobile_no: str = Field(..., description="The mobile phone number of the user, including the country code.")
   
    @field_validator('date_of_birth', mode='before')
    def validate_date_of_birth(cls, v, info):
        # Ensure v is a date object
        if isinstance(v, str):
            v = date.fromisoformat(v)  # Convert from string to date if needed
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 18:
            raise ValueError('You must be at least 18 years old. And format should be YYYY-MM-DD')
        return v

    
    @field_validator('first_name', mode='before')
    def validate_first_name(cls, v, info):
        v = v.strip()
        if not re.match(r'^[A-Za-z]+$', v):
            raise ValueError('First name must only contain alphabetic characters and cannot include numbers, special characters, or spaces.')
        return v
    
    @field_validator('last_name', mode='before')
    def validate_last_name(cls, v, info):
        v = v.strip()
        if not re.match(r'^[A-Za-z]+$', v):
            raise ValueError('Last name must only contain alphabetic characters and cannot include numbers, special characters, or spaces.')
        return v

    @field_validator('mobile_no', mode='before')
    def validate_mobile_no(cls, v, info):
        try:
            phone_number = phonenumbers.parse(v)
            if not is_valid_number(phone_number):
                raise ValueError('Invalid phone number.')
        except NumberParseException:
            raise ValueError('Invalid phone number format.')
        return v
    
   

class UpdatePassword(BaseModel):
    old_password:str
    password: str 
    confirm_password: str = Field(..., description="Test Search")
    
    @field_validator('password', 'confirm_password', mode='before')
    def passwords_match(cls, v, info):
        v = v.strip()
        # Access other values from info.
        if info.field_name == 'confirm_password':
            password = info.data.get('password')
            if v != password:
                raise ValueError('Password and Confirm Password do not match.')
        return v
    
    @field_validator('password', 'old_password', mode='before')
    def password(cls, v, info):
        v = v.strip()
        # Access other values from info.
        if info.field_name == 'old_password':
            password = info.data.get('password')
            if v == password:
                raise ValueError('New Password Should not same with Old Password.')
        return v

    # class Config:
    #     #orm_mode = True
    #     from_attributes = True
    #     str_strip_whitespace = True

class ListRequestBase(BaseModel):
    search_string: Optional[str] = None  # Search string on string based columns
    page:int = 1
    per_page:int =25
    created_on: Optional[date] = Field(default_factory=lambda: date(1970, 1, 1))  # Default to '1970-01-01' if None
    created_to: Optional[date] = Field(default_factory=date.today)  # Default to today's date if None
    # created_on: Optional[date] = date(1970, 1, 1)
    # created_to: Optional[date] = date.today()
    sort_by: Optional[str] = "id"  # Default sort by 'created_on'
    sort_order: Optional[str] = "desc"
    
    @field_validator('created_on', mode='before')
    def created_on_convert_datetime_to_date(cls, v):
        if isinstance(v, datetime):
            return (v - timedelta(days=1)).date()
        elif isinstance(v, date):
            return (v - timedelta(days=1))
        else:  # Handle None or empty string inputs
            return date(1970, 1, 1)  # Default value
        
        return v
    @field_validator('created_to', mode='before')
    def created_to_convert_datetime_to_date(cls, v):
        if isinstance(v, datetime):
            return (v + timedelta(days=1)).date()
        elif isinstance(v, date):
            return (v + timedelta(days=1))
        else:
            return date.today() + timedelta(days=1) # Default value
        return v
    # @field_validator('created_to', mode='before')
    # def created_to_convert_datetime_to_date(cls, v):
    #     if v in (None, ''):  # Handle None or empty string inputs
    #         print("sfhgsd sdgajsg dasg")
    #         return date.today()+ timedelta(days=1)  # Default value
    #     if isinstance(v, datetime):
    #         return (v + timedelta(days=1)).date()
    #     elif isinstance(v, date):
    #         return (v + timedelta(days=1))
    #     return v

    # @field_validator('created_on',mode='before' )
    # def created_on_convert_datetime_to_date(cls, v):
    #     if v is not None or v !='':        
    #         if isinstance(v, datetime):
    #             return (v - timedelta(days=1)).date()
    #         elif isinstance(v, date):
    #              return (v - timedelta(days=1))
    #         else:
    #             return v
    #     return v
        
    # @field_validator( 'created_to',mode='before' )
    # def created_to_convert_datetime_to_date(cls, v):
        
    #     if isinstance(v, datetime):           
    #        return (v + timedelta(days=1)).date()
    #     elif isinstance(v, date):           
    #        return (v + timedelta(days=1))
    #     else:
    #         return v   
           
        
        
class UserFilterRequest(ListRequestBase):
    
    tenant_id: Optional[List[int]] = None
    #role_id: Optional[List[int]] = None
    status_ids: Optional[List[int]] = None  # List of status IDs
    country_id: Optional[List[int]] = None
    #state_id: Optional[List[int]] = None
    #location_id: Optional[List[int]] = None
    kyc_status_id: Optional[List[int]] = None
    get_kyc_users:Optional[bool] = False
    #accepted_terms: Optional[bool] = None
    role_ids:Optional[List[int]]=None

class GetUser(BaseModel):
    email:str
    tenant_id: Optional[int] = None
    

class BeneficiaryListReq(ListRequestBase):
    
    status_ids: Optional[List[int]] = None
    country_ids: Optional[List[int]] = None
    bank_country_ids:Optional[List[int]] = None
    beneficiary_category_ids:Optional[List[int]] = None
    #user_id:Optional[int]
    
class transactionPorposList(ListRequestBase):
    status_ids: Optional[List[int]] = [1]
    #search_string: Optional[str] = None 


class CountryResponse(BaseModel):
    id: int
    name: str

    class Config:
        #orm_mode = True
        from_attributes = True
        str_strip_whitespace = True

class MasterDataResponse(BaseModel):
    id: int
    name: str

    class Config:
        #orm_mode = True
        from_attributes = True
        str_strip_whitespace = True


class UserListResponse(BaseModel):
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: str
    mobile_no: Optional[str] = None
    tenant_id: Optional[int] = None
    role_id: int
    status_id: int
    country_id: Optional[int] = None
    state_id: Optional[int] = None
    location_id: Optional[int] = None
    kyc_status_id: int
    accepted_terms: bool
    tenant_details: Optional[MasterDataResponse] = None
    role_details: Optional[MasterDataResponse] = None
    status_details: Optional[MasterDataResponse] = None
    country_details: Optional[CountryResponse] = None
    #state_details: Optional[MasterDataResponse] = None
    #location_details: Optional[MasterDataResponse] = None
    kyc_status: Optional[MasterDataResponse] = None
    created_on:Optional[date]
    updated_on:Optional[date]
    #6787425996

    @field_validator('created_on', 'updated_on', mode='before' )
    def convert_datetime_to_date(cls, v):
        if isinstance(v, datetime):
            return v.date()
        return v
    class Config:
        #orm_mode = True
        from_attributes = True
        str_strip_whitespace = True
class PaginatedUserResponse(BaseModel):
    total_count: int
    list: List[UserListResponse]
    page: int
    per_page: int
    
class GetUserDetailsReq(BaseModel):
    user_id:int
    class Config:
        from_attributes = True
        str_strip_whitespace = True

class KycDocument(BaseModel):
    md_doc_id: int
    name: str
    content_type: str
    path: str
    size: int
    class Config:
        from_attributes = True
        str_strip_whitespace = True

class UpdateKycDetails(BaseModel):

    first_name: str
    last_name: str
    email:Optional[EmailStr] =None
    date_of_birth: date = Field(..., description="Must be at least 18 years old.And format should be YYYY-MM-DD")
    mobile_no: str = Field(..., description="The mobile phone number of the user, including the country code.")
    street: str
    city: str
    state_id:int
    state:str
    pincode: str
    occupation_id: int
    annual_income:int
    accepted_terms:bool
    documents: List = Field(..., description="A list of documents with each document represented as a dictionary with 'name', 'ext', 'path', and 'size'.")
    override_existing_docs:Optional[bool] = Field(False, description="To override existing docs send override_existing_docs= true ")

#Annual Income field cannot be empty.

    @field_validator('date_of_birth', mode='before')
    def validate_date_of_birth(cls, v, info):
        # Ensure v is a date object
        if isinstance(v, str):
            v = date.fromisoformat(v)  # Convert from string to date if needed
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 18:
            raise ValueError('You must be at least 18 years old. And format should be YYYY-MM-DD')
        return v

    
    @field_validator('first_name', mode='before')
    def validate_first_name(cls, v, info):
        v = v.strip()
        if not re.match(r'^[A-Za-z ]+$', v):
            raise ValueError('First name must only contain alphabetic characters and cannot include numbers, special characters.')
        return v
    
    @field_validator('last_name', mode='before')
    def validate_last_name(cls, v, info):
        v = v.strip()
        if not re.match(r'^[A-Za-z ]+$', v):
            raise ValueError('Last name must only contain alphabetic characters and cannot include numbers, special characters.')
        return v

    @field_validator('mobile_no', mode='before')
    def validate_mobile_no(cls, v, info):
        try:
            phone_number = phonenumbers.parse(v)
            if not is_valid_number(phone_number):
                raise ValueError('Invalid phone number.')
        except NumberParseException:
            raise ValueError('Invalid phone number format.')
        return v
    

    @field_validator('accepted_terms', mode='before')
    def validate_accepted_terms(cls, v, info):
        if not v:
            raise ValueError('You must accept the terms and conditions.')
        return v

    class Config:
        #orm_mode = True
        from_attributes = True
        str_strip_whitespace = True

class UpdateKycDocStatus(BaseModel):
    user_id:int
    document_id:int
    md_doc_id:int
    status_id:int
    description:Optional[str]

class kycDetailsRequest(BaseModel):
    user_id:Optional[int]



class BeneficiaryRequest(BaseModel):
    
    #user_id: int
    full_name: str
    nick_name: Optional[str]
    email:Optional[EmailStr] =None
    mobile_no: str = None    
    country_id: int
    city: str
    state_province: str
    beneficiary_category_id:int
    postal_code: Optional[str]
    swift_code: Optional[str]
    routing_number:Optional[str]
    use_routing_number:bool =False
    iban: str
    conform_iban: str
    bank_name: str
    bank_currency:str
    bank_country_id: int
    bank_address: str

    @field_validator('full_name', mode='before')
    def validate_full_name(cls, v, info):
        v = v.strip()
        if v is None or v=='':
            raise ValueError('Full name required!')
        if not re.match(r'^[A-Za-z ]+$', v):
            raise ValueError('full name must only contain alphabetic characters and cannot include numbers, special characters, or spaces.')
        return v
    
    @field_validator('country_id', mode='before')
    def validate_country_id(cls, v, info):
         if v is None or v <= 0:
            raise ValueError('Country code is required!')
         
         return v

    @field_validator('nick_name', mode='before')
    def validate_nick_name(cls, v, info):
        v = v.strip()
        min_length = 2
        max_length = 35

        if v is not None and v!='':            
            if not re.match(r'^[A-Za-z0-9 ]+$', v):
                raise ValueError('full name must only contain alphabetic characters and cannot include numbers, special characters, or spaces.')
            if len(v) < min_length:
                        raise ValueError(f'Nick Name must be at least {min_length} characters long.')
            if len(v) > max_length:
                        raise ValueError(f'Nick Name must be at most {max_length} characters long.')
        return v


    @field_validator('mobile_no', mode='before')
    def validate_mobile_no(cls, v, info):
        try:
            phone_number = phonenumbers.parse(v)
            if not is_valid_number(phone_number):
                raise ValueError('Invalid phone number.')
        except NumberParseException:
            raise ValueError('Invalid phone number format.')
        return v
    
    @field_validator('city', mode='before')
    def validate_city(cls, v, info):
        v = v.strip()
        if v is None or v=='':
            raise ValueError('City required!')
        return v
    
    @field_validator('state_province', mode='before')
    def validate_state_province(cls, v, info):
        v = v.strip()
        if v is None or v=='':
            raise ValueError('State/ Province required!')
        return v
    
    @field_validator('postal_code', mode='before')
    def validate_postal_code(cls, v, info):
        v = v.strip()
        # if v is None or v=='':
        #     raise ValueError('postal_code required!')
        return v
     
    @field_validator( 'use_routing_number','routing_number', mode='before')
    def validate_routing_number(cls, v, info):
        min_length = 9
        max_length = 16
        
        routing_number = info.data.get('routing_number')
        if info.field_name == 'use_routing_number':
             if v:
                 if routing_number is None or routing_number=='':
                     raise ValueError('Routing number is required!')
                 if len(routing_number) < min_length:
                    raise ValueError(f'Routing number  must be at least {min_length} characters long.')
        
                 if len(routing_number) > max_length:
                    raise ValueError(f'Routing number must be at most {max_length} characters long.')
        
        return v     
    
    @field_validator( 'use_routing_number','swift_code', mode='before')
    def validate_swift_code(cls, v, info):
        min_length = 8
        max_length = 11
        
        swift_code = info.data.get('swift_code')
        if info.field_name == 'use_routing_number':
             if v==False:
                 if swift_code is None or swift_code=='':
                     raise ValueError('swift code is required!')
                 if len(swift_code) < min_length:
                    raise ValueError(f'swift code must be at least {min_length} characters long.')
        
                 if len(swift_code) > max_length:
                    raise ValueError(f'swift code must be at most {max_length} characters long.')
        
        return v  

    #bank_currency
    @field_validator('bank_currency',  mode='before')
    def bank_currency_validate(cls, v, info):
        max_length = 4
        min_length = 3
        if v is None or v=='':
            raise ValueError('Bank currency is required!')
        if len(v) < min_length:
            raise ValueError(f'Bank currency must be at least {min_length} characters long.')
        
        if len(v) > max_length:
            raise ValueError(f'Bank currency must be at most {max_length} characters long.')

        return v
   
    @field_validator('iban',  mode='before')
    def iban_validate(cls, v, info):
        max_length = 16
        min_length = 8
        v = v.strip()
        if v is None or v=='':
            raise ValueError('iban is required!')
        if len(v) < min_length:
            raise ValueError(f'iban must be at least {min_length} characters long.')
        
        if len(v) > max_length:
            raise ValueError(f'iban must be at most {max_length} characters long.')
        
        return v
    
    @field_validator('iban', 'conform_iban', mode='before')
    def passwords_match(cls, v, info):
        v = v.strip()
        if v is None or v=='':
            raise ValueError('iban is required!')
        
        elif info.field_name == 'confirm_password':
            iban = info.data.get('iban')
            if v != iban:
                raise ValueError('iban and Confirm iban do not match.')
        return v

    
    @field_validator('bank_name', mode='before')
    def validate_bank_name(cls, v, info):
        v = v.strip()
        if v is None or v=='':
            raise ValueError('Bank  Name required!')
        return v
    
    @field_validator('bank_address', mode='before')
    def validate_bank_address(cls, v, info):
        v = v.strip()
        if v is None or v=='':
            raise ValueError('Bank  Address required!')
        return v
    
    
    
         
    

    
    
    class Config:
        from_attributes = True
        str_strip_whitespace = True

class BeneficiaryEdit(BeneficiaryRequest):
    beneficiary_id:int
    
class GetBeneficiaryDetails(BaseModel):
    beneficiary_id:int
    class Config:
        from_attributes = True
        str_strip_whitespace = True

class UpdateBeneficiaryStatus(BaseModel):
    beneficiary_id:int
    #otp:str
    status_id:int
    class Config:
        from_attributes = True
        str_strip_whitespace = True
class ActivateBeneficiary(BaseModel):
    beneficiary_id:int
    otp:str
    
    class Config:
        from_attributes = True
        str_strip_whitespace = True



class ResendBeneficiaryOtp(BaseModel):
    beneficiary_id:int


class UpdateKycStatus(BaseModel):
    user_id:int
    kyc_status_id:int
    description:Optional[str] =''
    class Config:
        from_attributes = True
        str_strip_whitespace = True


class BeneficiaryResponse(BaseModel):
    id: int
    user_id: int
    full_name: Optional[str] = None
    nick_name: Optional[str] = ""
    email:str=""
    mobile_no: str = ''
    country_id: int
    beneficiary_country_details: Optional[CountryResponse] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    postal_code: Optional[str] = None
    swift_code: Optional[str] = None
    routing_number:Optional[str] =None
    use_routing_number:bool =False
    iban: Optional[str] = None
    bank_name: Optional[str] = None
    bank_country_id: int
    bank_currency:str
    beneficiary_bank_country_details:Optional[CountryResponse] = None
    bank_address: Optional[str] = None
    beneficiary_category_details:Optional[MasterDataResponse] = None

    class Config:
        from_attributes = True
        str_strip_whitespace = True

class PaginatedBeneficiaryResponse(BaseModel):
    total_count: int
    list: List[BeneficiaryResponse]
    page: int
    per_page: int
   