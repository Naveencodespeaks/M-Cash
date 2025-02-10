
from pydantic import BaseModel, EmailStr, Field, ValidationError, validator,field_validator
import phonenumbers
from phonenumbers import NumberParseException, is_valid_number
import re
from datetime import date, datetime, timedelta
from typing import Optional, List
from sqlalchemy import Column, Integer,INT, String, Text, DateTime, ForeignKey,Enum,Date,Boolean

from ..schemas.user_schema import ListRequestBase,UserListResponse
      


class NotificationsListReq(ListRequestBase):    
    user_id: Optional[List[int]] = None
    status:Optional[List[bool]] = [True]
    
class userDetails(BaseModel):
    user_id:int
    first_name:str
    last_name:str
    email:str
class NotificationResponse(BaseModel):
    id:int
    description:str
    #is_active:Optional[Boolean] = True
    #tenant_id:int
    created_on :datetime
    category:str
    ref_id:int
    user_details:userDetails

class PaginatedNotificationsResponse(BaseModel):
    total_count: int
    list: List[NotificationResponse]
    page: int
    per_page: int