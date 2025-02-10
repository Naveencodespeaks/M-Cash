import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from datetime import datetime, timedelta,timezone
import ast
import json
import jsonpickle
#from ..constant.status_constant import FAIL
from ..common.utility import Utility
from ..constant import messages as all_messages 

class AuthHandler:
    security = HTTPBearer()
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    secret = 'SECRET_CASH'

    def get_password_hash(self, password):
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password, hashed_password):
        try:
            return self.pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            return False
    

    def datetime_handler(self,x):
        if isinstance(x, datetime):
            return x.isoformat()
        return x #TypeError("Type not serializable")
    
    def encode_token(self, user_dict,minutes=60 ):
        payload = {
        'exp': datetime.now(timezone.utc) + timedelta(minutes=minutes),
        'iat': datetime.now(timezone.utc),
        'sub': jsonpickle.dumps(user_dict)  # Use jsonpickle to handle complex objects
       }
        return jwt.encode(
            payload,
            self.secret,
            algorithm='HS256'
        )
    
    def decode_otp_token(self, token):
        try:
            payload = jwt.decode(token, self.secret, algorithms=['HS256'])
            return json.loads(payload['sub'], )
            
        except jwt.ExpiredSignatureError:
            response = {}
            response.update(status=401, message="The time you were taken has expired!", error=[], data={},code="OTP_EXPIRED")
            raise HTTPException(status_code=401, detail=response)
        except jwt.InvalidTokenError as e:
            print(e)
            response = {}
            response.update(status=401, message="Invalied otp", error=[], data={},code="INVALIED_OTP")
            raise HTTPException(status_code=401, detail=response)

    def decode_token(self, token):
        try:
            payload = jwt.decode(token, self.secret, algorithms=['HS256'])
            return json.loads(payload['sub'], )
            
        except jwt.ExpiredSignatureError:
            response = {}
            response.update(status=401, message="The time you were taken has expired!", error=[], data={},code="LOGIN_TOKEN_EXPIRED")
            raise HTTPException(status_code=401, detail=response)
        except jwt.InvalidTokenError as e:
            print(e)
            response = {}
            response.update(status=401, message="Invalid taken", error=[], data={},code="INVALIED_TOKEN")
            raise HTTPException(status_code=401, detail=response)
    def verify_ws_token(self, token):
        try:
            payload = jwt.decode(token, self.secret, algorithms=['HS256'])
            return json.loads(payload['sub'], )
            
        except jwt.ExpiredSignatureError:
            return None
            
        except jwt.InvalidTokenError as e:
            print(e)
            return None
    
    def auth_wrapper(self, auth: HTTPAuthorizationCredentials = Security(security)):
        return self.decode_token(auth.credentials)
    
    def user_validate(self,user_obj):
        response = {}
        if user_obj is None:
            response.update(status=409, message=all_messages.USER_NOT_EXISTS, error=[], data={},code="LOGOUT_ACCOUNT")
            raise HTTPException(status_code=409, detail=response)
        elif user_obj.role_id !=2:            
            response.update(status=409, message=all_messages.NO_PERMISSIONS, error=[], data={},code="LOGOUT_ACCOUNT")
            raise HTTPException(status_code=409, detail=response)
        if user_obj.status_id == 2:
            response.update(status=409, message=all_messages.PENDING_EMAIL_VERIFICATION, error=[], data={},code="LOGOUT_ACCOUNT")
            raise HTTPException(status_code=409, detail=response)
        elif user_obj.status_id == 4:
            response.update(status=409, message=all_messages.PROFILE_INACTIVE, error=[], data={},code="LOGOUT_ACCOUNT")
            raise HTTPException(status_code=409, detail=response)
        elif user_obj.status_id == 5:
            response.update(status=409, message=all_messages.PROFILE_DELETED, error=[], data={},code="LOGOUT_ACCOUNT")
            raise HTTPException(status_code=409, detail=response)
        return True