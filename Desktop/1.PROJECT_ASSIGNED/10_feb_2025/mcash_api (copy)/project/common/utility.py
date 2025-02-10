from fastapi.responses import JSONResponse
import uuid
import random
import string
from datetime import datetime,date
from sqlalchemy import desc, asc
from typing import List, Tuple
import string
from ..models.admin_configuration_model import tokensModel
#import qrcode
import base64
from io import BytesIO
import os
from ..aploger import AppLogger
from decimal import Decimal
import time

class Utility:

    @staticmethod
    def generatecode(code_for=''):
        code = f'MCASH-{int(time.time())}-{random.randint(1000, 9999999)}'
        if code_for == "INVOICE":
            code = f'INV-{datetime.now().strftime("%d%m%Y")}-{int(time.time())}-{random.randint(1000, 9999999)}'
        elif code_for =="TRANSFER_MONEY":
            code = f'TRANSFER_MONEY-{datetime.now().strftime("%d%m%Y")}-{int(time.time())}-{random.randint(1000, 9999999)}'
        elif code_for == "REQUEST_FOR_FUNDS": 
            code = f'REQ_FUND-{datetime.now().strftime("%d%m%Y")}-{int(time.time())}-{random.randint(1000, 9999999)}'
        elif code_for == "CREDIT": 
            code = f'CR{datetime.now().strftime("%d%m%Y")}-{int(time.time())}-{random.randint(1000, 9999999)}'
        elif code_for == "DEBIT": 
            code = f'DE-{datetime.now().strftime("%d%m%Y")}-{int(time.time())}-{random.randint(1000, 9999999)}'
        
        
        return code
    @staticmethod
    def json_response(status, message, error, data,code=''):
        return JSONResponse({
            'status': status,
            'message': message,
            'error': error,
            'result': data,
            "code": code if code else''
        },status_code=status if status else 500)

    # @staticmethod
    # def json_response(status, message, error, data, code=''):
    #     # Ensure status is an integer for HTTP status code
    #     http_status_code = status if isinstance(status, int) else 500
    #     return JSONResponse({
    #         'status': "SUCCESS" if status == 200 else "FAILURE",  # Use appropriate string representation
    #         'message': message,
    #         'error': error,
    #         'result': data,
    #         "code": code if code else ''
    #     }, status_code=http_status_code)

    

    
    @staticmethod
    def dict_response(status, message, error, data,code=''):
        return ({
            'status': status,
            'message': message,
            'error': error,
            'result': data,
            "code": code if code else'',
            "status_code":status if status else 500
        })
    @staticmethod
    def generate_otp(n: int=6) -> int:
        range_start = 10**(n-1)
        range_end = (10**n) - 1
        otp = random.randint(range_start, range_end)
        return otp
    
    @staticmethod
    def generate_random_string(length=10):
        if length < 10:
            length = 10  # Ensure minimum length of 10 characters
        # Alphanumeric characters: A-Z, a-z, 0-9
        characters=string.ascii_uppercase + string.digits
        # Generate a random coupon code
        coupon_code = ''.join(random.choice(characters) for _ in range(length))
        return coupon_code

    @staticmethod
    def uuid():
        return str(uuid.uuid4())

    @staticmethod
    def generate_remit_id():
        date_part = datetime.now().strftime('%Y%m%d')
        alphanumeric_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        remit_id = f"{date_part}{alphanumeric_part}"
        return remit_id
    @staticmethod
    def model_to_dict(model_instance):
        
        if model_instance is None:
            return {}
    
        result = {}
        for column in model_instance.__table__.columns:
            value = getattr(model_instance, column.name)
            # if column.name !="created_on" and column.name !="updated_on" and column.name !="date_of_birth" :
            #     
            #     if isinstance(value, datetime):
            #         result[column.name] = value.isoformat()  # Convert datetime to ISO 8601 string
            #     else:
            #         result[column.name] = value
            if isinstance(value, datetime):
                result[column.name] =value.isoformat()
            elif isinstance(value, date):
                result[column.name] =value.isoformat()
            elif isinstance(value, Decimal):
                result[column.name] =float(value)
            else:
                result[column.name] = value
            
            
        return result

    @staticmethod
    def convert_dtring_to_date(string_date=''):
        result =""
        if string_date is None:
            return result
        date_format = "%Y-%m-%d" # format YYYY-DD-MM
        datetime_obj = datetime.strptime(string_date, date_format)
        result = datetime_obj.date()        
        return result

    @staticmethod
    def list_query(Session=None,page=1,par_page=25,sort_by="id",sort_order="asc",response_schema=None,modelRef=None,filters={}):

        def get_data(db: Session,page: int = page,per_page: int = par_page,sort_by: str = sort_by,sort_order: str = sort_order,filters={}) -> Tuple[List[response_schema], int]:
            sort_column = desc(sort_by) if sort_order == "desc" else asc(sort_by)
            # Calculate offset and limit
            offset = (page - 1) * per_page
            filters = []
            if filters.search_text:
                filters.append(modelRef.email.ilike(f"%{filters.search_text}%"))
            
            query = db.query(modelRef)
            for key, value in filters.items():
                query = query.filter(getattr(modelRef, key) == value)

            total_count = db.query(modelRef).count()
            results = query.order_by(sort_column).offset(offset).limit(per_page).all()
            list = [response_schema.from_orm(result) for result in results]
            return total_count, list
        
        return get_data(Session=Session,page=page,par_page=par_page,sort_by=sort_by,sort_order=sort_order,response_schema=response_schema,modelRef=modelRef,filters=filters)

    # Function to check if current date is greater than or equal to given month/year
    @staticmethod
    def is_current_date_greater_or_equal(mm_yyyy_str):
        # Parse the input string
        return_data = {"status":False, "message":''}
        try:
            month, year = map(int, mm_yyyy_str.split('/'))
        except ValueError:
            return_data["message"] = "The input string must be in 'mm/YYYY' format"
        
        # Validate month and year
        if not (1 <= month <= 12):
            return_data["message"] = "Month must be between 01 and 12"
        
        elif year < 0:
            return_data["message"] = "Year must be a positive integer"
        
        # Get current month and year
        now = datetime.now()
        current_month = now.month
        current_year = now.year
        print(f"CURRENT current_month = {current_month} current_year {current_year}")
        print(f'year={year} month{month}')
        year = year+2000
        # Compare
        if year>current_year:
            return_data["status"] =   True
        elif year<current_year:
            return_data["status"] =  False
            return_data["message"] = "Expiry date must be feature month"

        elif year==current_year and month <= current_month:
            return_data["status"] =  False
            return_data["message"] = "Expiry date must be feature month"

        elif year < current_year or (month < current_month):
            return_data["status"] =  False
            return_data["message"] = "Expiry date must be feature month"
        else:
            return_data["status"] =   True
        return return_data
    
    @staticmethod
    def inactive_previous_tokens(db=None, catrgory = '', user_id = 0):
        try:
            if db is not None and catrgory and user_id > 0:
            # Query to get all active tokens for the given category and user_id
             tokens = db.query(tokensModel).filter(tokensModel.catrgory == catrgory, tokensModel.user_id == user_id, tokensModel.active == True).all()

             if tokens:
                for token in tokens:
                    token.active = False
                db.commit()  # Commit once after the loop to avoid multiple commits

            return True
            return False  # Return False if db, category, or user_id are invalid
        except Exception as e:
            db.rollback()  # Rollback in case of an error
            print("Error at inactive_previous_tokens")
            print(e)
            return False


    @staticmethod
    def generate_websocket_id(user_data=None):
        socket_id =None
        if "role_id" in user_data and user_data["role_id"] in [1]:
           socket_id = f'''superuser_{user_data["id"]}_{user_data["role_id"]}'''
        elif (user_data["role_id"] ==3):
            socket_id = f'''tenant_admin_{user_data["id"]}_{user_data["role_id"]}'''
            if "tenant_id" in user_data and user_data["tenant_id"] is not None:
                socket_id = f'''tenant_admin_{user_data['tenant_id']}_{user_data["id"]}_{user_data["role_id"]}'''

        elif "tenant_id" in user_data and user_data["tenant_id"] is not None:
            socket_id = f'''{user_data['tenant_id']}_{user_data["id"]}_{user_data["role_id"]}'''
        else:
            socket_id = f'''{user_data["id"]}_{user_data["role_id"]}'''

        return socket_id    

    # def inactive_previous_tokens(db =None,category:str='',user_id:int=0):
    #     try:
    #         if db is not None and category and user_id>0:
    #             query = db.query(tokensModel).filter(tokensModel.catrgory == category, tokensModel.user_id == user_id,item.active==True ).all()
    #             if query is not None:
    #                 for item in query:
    #                     item.active =False
    #                     db.commit()

    #         return True
    #     except Exception as E:
    #         db.rollback()
    #         print("Error at inactive_previous_tokens")
    #         print(E)
    #         return False


#print(Utility.uuid())

    # @staticmethod
    # def generate_qr_code_base64(data: str) -> str:
    #     qr = qrcode.QRCode(
    #         version=1,
    #         error_correction=qrcode.constants.ERROR_CORRECT_L,
    #         box_size=10,
    #         border=4
    #     )
    #     qr.add_data(data)
    #     qr.make(fit=True)

    #     # Create an image of the QR code
    #     img = qr.make_image(fill='black', back_color='white')

    #     # Convert to Base64
    #     buffer = BytesIO()
    #     img.save(buffer)
    #     img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    #     image_path = f"user_qr.png"
    #     img.save(image_path)

    #     return img_base64

