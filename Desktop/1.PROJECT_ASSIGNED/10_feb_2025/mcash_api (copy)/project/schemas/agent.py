from pydantic import BaseModel, EmailStr, Field, ValidationError, validator,field_validator
from typing import Optional
import phonenumbers
from phonenumbers import NumberParseException, is_valid_number
import re
from datetime import date, datetime



class AgentRegisterSchema(BaseModel):
    email: EmailStr
    mobile_no: str
    country_id:int
    user_name: str #constr(min_length=3, max_length=50)
    password: str #constr(min_length=8)
    confirm_password: str
    @field_validator('password', 'confirm_password', mode='before')
    def passwords_match(cls, v, info):
        v = v.strip()
        # Access other values from info.
        if info.field_name == 'confirm_password':
            password = info.data.get('password')
            if v != password:
                raise ValueError('Password and Confirm Password do not match.')
        return v

class UpdateAgentPasswordSchema(BaseModel):
    user_id: int
    old_password: str
    password: str
    confirm_password: str
    
    @field_validator('user_id', mode='before')
    def check_user_id(cls, v, info):
        if v is None or v<=0:
            raise ValueError('User ID is required and cannot be None.')
        return v

    @field_validator('password', 'confirm_password', mode='before')
    def passwords_match(cls, v, info):
        v = v.strip()
        # Access other values from info.
        if info.field_name == 'confirm_password':
            password = info.data.get('password')
            if v != password:
                raise ValueError('Password and Confirm Password do not match.')
        return v


    
