from pydantic import BaseModel, EmailStr, Field, ValidationError, validator,field_validator
import re
from datetime import  datetime
from typing import Optional, List
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

class CouponSchema(BaseModel):    
    coupon_code:str
    description:str
    coupon_amount:int
    currency:str
    discount_type:str=Field(..., description="must be 'FIXED_AMOUNT' or 'PERCENTAGE'")
    coupon_expiry_date:str
    usage_limit_per_person:int

    @field_validator('coupon_code', mode='before')
    def validate_coupon_code(cls, v, info):
        cleaned_string = re.sub(r'[^a-zA-Z0-9]', '', v)
        
        # Check if the cleaned string is alphanumeric and not empty
        if not cleaned_string.isalnum() or not cleaned_string :
            raise ValueError("Coupon code must be alphanumeric.")
        
        return cleaned_string
    @field_validator('coupon_amount',mode='before')
    def validate_coupon_amount(cls, v, info):
        #check if the coupon amount is greater than zero
        if (v<0 or (v is None)):
            raise ValueError("Coupon amount must be greater than zero.")
        return v
    @field_validator('discount_type', mode='before')
    def validate_discount_type(cls,v,info):
        #check if the discount_type in list or not
        discount_type_list=["FIXED_AMOUNT","PERCENTAGE"]
        if v not in discount_type_list:
            raise ValueError("Discount type not in list")
        return v
    @field_validator('coupon_expiry_date',mode='before')
    def validate_coupon_expiry_date(cls,v,info):
        print(type(v))
        # expiration_date = datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
        expiry_date = datetime.strptime(v, "%Y-%m-%d %H:%M")
        if expiry_date< datetime.now():
            raise ValueError("Coupon expiry date must be in the future.")
        return v
    @field_validator('usage_limit_per_person', mode='before')
    def validate_usage_limit_per_person(cls, v, info):
        if v<0 or (v is None):
            raise ValueError("Usage limit per person must be greater than zero.")
        return v

class CouponUpdateSchema(CouponSchema):
    coupon_id:int
    status:bool
class CouponStatusSchema(BaseModel):
    coupon_id: int
    status: bool 

class CouponListRequestBase(BaseModel):
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
        if v in (None, ''):  # Handle None or empty string inputs
            return date(1970, 1, 1)  # Default value
        if isinstance(v, datetime):
            return (v - timedelta(days=1)).date()
        elif isinstance(v, date):
            return (v - timedelta(days=1))
        return v
        
    @field_validator('created_to', mode='before')
    def created_to_convert_datetime_to_date(cls, v):
        if v in (None, ''):  # Handle None or empty string inputs
            return (date.today()+timedelta(days=1))  # Default value
        if isinstance(v, datetime):
            return (v + timedelta(days=1)).date()
        elif isinstance(v, date):
            return (v + timedelta(days=1))
        return v
    

class CouponFilterRequest(CouponListRequestBase):
    
    coupon_code: Optional[List[str]] = None    
    status: Optional[List[int]] = None  # List of status IDs


class CouponListResponse(BaseModel):
    id: int
    coupon_code: Optional[str] = None
    description: Optional[str] = None
    coupon_amount: Optional[float] = None
    currency: Optional[str] = None
    discount_type: Optional[str] = None    
    coupon_expiry_date: Optional[datetime] = None    
    usage_limit_per_person: Optional[int] = None
    status: Optional[int] = None    
    created_on:Optional[date]
    updated_on:Optional[date]
    

    @field_validator('created_on', 'updated_on', mode='before' )
    def convert_datetime_to_date(cls, v):
        if isinstance(v, datetime):
            return v.date()
        return v
    class Config:
        #orm_mode = True
        from_attributes = True
        str_strip_whitespace = True

class PaginatedCouponResponse(BaseModel):
    total_count: int
    list: List[CouponListResponse]
    page: int
    per_page: int
    



    


    