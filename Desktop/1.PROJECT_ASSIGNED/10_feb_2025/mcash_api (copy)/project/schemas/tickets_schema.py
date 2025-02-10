from pydantic import BaseModel, EmailStr, Field, ValidationError, validator,field_validator
import re
from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field, ValidationError, validator,field_validator
import phonenumbers
from phonenumbers import NumberParseException, is_valid_number
import re
from datetime import date, datetime, timedelta
from typing import Optional, List
from ..schemas.master_data import Document 


class ListRequestBase(BaseModel):
    search_string: Optional[str] = None  # Search string on string based columns
    page:int = 1
    per_page:int =25
    created_on: Optional[date] = Field(default_factory=lambda: date(1970, 1, 1))  # Default to '1970-01-01' if None
    created_to: Optional[date] = Field(default_factory=date.today)  # Default to today's date if None
    # created_on: Optional[date] = date(1970, 1, 1)
    # created_to: Optional[date] = date.today()
    sort_by: Optional[str] = "created_on"  # Default sort by 'created_on'
    sort_order: Optional[str] = "desc"

    @field_validator('created_on', mode='before')
    def created_on_convert_datetime_to_date(cls, v):
        if v in (None, '') or not isinstance(v, datetime):  # Handle None or empty string inputs
            return date(1970, 1, 1)  # Default value
        if isinstance(v, datetime):
            return (v - timedelta(days=1)).date()
        elif isinstance(v, date):
            return (v - timedelta(days=1))
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


class TicketRequest(BaseModel):
    # id:int
    user_id:int
    description:str



    @field_validator('user_id', mode='before')
    def check_user_id(cls, v, info):
        if v is None or v<=0:
            raise ValueError('User ID is required and cannot be None.')
        return v
    
    @field_validator('description', mode='before')
    def check_description(cls, v):
        if v is None:
            raise ValueError('Description is required and cannot be None.')
        return v

class TicketListRequest(ListRequestBase):
    # id:int
    user_id:int
    description:str


class TicketResponse(BaseModel):
    id: int
    user_id: int
    description: str
    reference :str

    class Config:
        from_attributes = True
        str_strip_whitespace = True

class PaginatedTicketResponse(BaseModel):
    total_count: int
    list: List[TicketResponse]
    page: int
    per_page: int
