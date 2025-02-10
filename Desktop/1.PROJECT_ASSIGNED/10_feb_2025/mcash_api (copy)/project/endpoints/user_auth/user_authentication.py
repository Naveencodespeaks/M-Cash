from datetime import datetime, timezone,timedelta
from sqlalchemy import and_
from datetime import datetime
from ...models.user_model import UserModel
from ...models.admin_user import AdminUser

from ...models.master_data_models import MdUserRole,MdUserStatus

from . import APIRouter, Utility, SUCCESS, FAIL, EXCEPTION ,WEB_URL, API_URL, INTERNAL_ERROR,BAD_REQUEST,BUSINESS_LOGIG_ERROR, Depends, Session, get_database_session, AuthHandler
from ...schemas.register import Register, SignupOtp,ForgotPassword,CompleteSignup,VerifyAccount,resetPassword
import re
from ...schemas.login import Login
from ...constant import messages as all_messages
from ...common.mail import Email
import json
from fastapi import BackgroundTasks


# APIRouter creates path operations for product module
router = APIRouter(
    prefix="/auth",
    tags=["User Authentication"],
    responses={404: {"description": "Not found"}},
)

@router.post("/register", response_description="User User Registration")
async def register(request: Register,background_tasks: BackgroundTasks, db: Session = Depends(get_database_session)):
    try:
        
        mobile_no = request.mobile_no
        email = request.email
        country_id = request.country_id
        email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if not re.fullmatch(email_regex, email):
            return Utility.json_response(status=BAD_REQUEST, message=all_messages.INVALIED_EMAIL, error=[], data={})
        
        
        if len(str(mobile_no)) < 7 or len(str(mobile_no)) > 15:
            return Utility.json_response(status=BAD_REQUEST, message=all_messages.INVALIED_MOBILE,error=[], data={})
        user_obj = db.query(UserModel).filter(UserModel.email == email)
        role_id = 2 # 2= Custmer, 4= Marchant, 5 =Agent
        if request.role_id in [2,4,5,6]:
            role_id = request.role_id
        if user_obj.count() <=0:
            user_data = UserModel(role_id =role_id,status_id=1, email=email,country_id=country_id, mobile_no=mobile_no,password=str(Utility.uuid()),tenant_id=1)
            #Send Mail to user with active link
            mail_data = {"body":"Welcome to M-Cash"}
            db.add(user_data)
            db.flush()
            db.commit()
            if user_data.id:
                udata =  Utility.model_to_dict(user_data)
                rowData = {}
                rowData['user_id'] = udata["id"]
                rowData['first_name'] = udata.get("first_name","")
                rowData['last_name'] = udata.get("last_name","")
                rowData['country_id'] = udata.get("country_id",None)
                rowData['mobile_no'] = udata.get("mobile_no",'')
                rowData['date_of_birth'] = udata.get("date_of_birth",'')
                rowData["country_details"] = Utility.model_to_dict(user_data.country_details)
                return Utility.json_response(status=SUCCESS, message=all_messages.REGISTER_SUCCESS, error=[],data=rowData,code="SIGNUP_PROCESS_PENDING")
            else:
                db.rollback()
                return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})
        else:
            existing_user = user_obj.one()
            udata =  Utility.model_to_dict(existing_user)
            rowData = {}
            rowData['user_id'] = udata["id"]
            rowData['email'] = udata.get("email","")
            rowData['first_name'] = udata.get("first_name","")
            rowData['last_name'] = udata.get("last_name","")
            rowData['country_id'] = udata.get("country_id",None)
            rowData['mobile_no'] = udata.get("mobile_no",'')
            rowData['date_of_birth'] = udata.get("date_of_birth",'')
            rowData['status_id'] = existing_user.status_id
            rowData["country_details"] = Utility.model_to_dict(existing_user.country_details)
            rowData["status_details"] = Utility.model_to_dict(existing_user.status_details)
            
            #del existing_user.otp
            #del existing_user.password            
            if existing_user.status_id == 1 or existing_user.status_id ==2:
                msg = all_messages.ACCOUNT_EXISTS_PENDING_EMAIL_VERIFICATION
                code = "SIGNUP_VERIFICATION_PENDING"                
                if existing_user.status_id ==2:
                    otp =str(Utility.generate_otp())
                    mail_data = {}
                    mail_data["name"]= f'''{udata.get("first_name","")} {udata.get("last_name","")}'''
                    mail_data["otp"] = otp
                    background_tasks.add_task(Email.send_mail,recipient_email=[udata["email"]], subject=all_messages.PENDING_EMAIL_VERIFICATION_OTP_SUBJ, template='email_verification_otp.html',data=mail_data )
                    user_obj.update({ UserModel.otp:str(otp)}, synchronize_session=False)
                    db.flush()
                    db.commit()
                    
                if  existing_user.status_id ==1:
                    code = "SIGNUP_PROCESS_PENDING"
                    msg =all_messages.SIGNUP_PROCESS_PENDING                           
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=msg, error=[], data=rowData,code=code)
            elif  existing_user.status_id == 3:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.ALREADY_PROFILE_IS_ACTIVE, error=[], data=rowData,code="ALREADY_PROFILE_IS_ACTIVE")
            elif existing_user.status_id == 4:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PROFILE_INACTIVE, error=[], data=rowData)
            elif existing_user.status_id == 5:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PROFILE_DELETED, error=[], data=rowData)
            else:
                db.rollback()
                return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

    except Exception as E:
        
        print(E)
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

@router.post("/complete-signup", response_description="Basic Information")
async def signup(request: CompleteSignup,background_tasks: BackgroundTasks, db: Session = Depends(get_database_session)):
    try:
               
        user_id = request.user_id
        first_name = request.first_name
        last_name = request.last_name
        country_id = request.country_id
        date_of_birth = request.date_of_birth #Utility.convert_dtring_to_date(request.date_of_birth)
        mobile_no = request.mobile_no
        password =  AuthHandler().get_password_hash(request.password)
        user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
        
        if user_obj is None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.USER_NOT_EXISTS, error=[], data={},code="USER_NOT_EXISTS")
        else:
            rowData = {}
            rowData['user_id'] = user_obj.id
            rowData['email'] = user_obj.email
            rowData['first_name'] = user_obj.first_name
            rowData['last_name'] = user_obj.last_name
            rowData['country_id'] = user_obj.country_id
            rowData['mobile_no'] = user_obj.mobile_no
            rowData['date_of_birth'] = str(user_obj.date_of_birth)
            rowData['status_id'] = user_obj.status_id
            rowData["country_details"] = Utility.model_to_dict(user_obj.country_details)
            rowData["status_details"] = Utility.model_to_dict(user_obj.status_details)
            otp =Utility.generate_otp()
            mail_data = {}
            mail_data["name"]= f'''{first_name} {last_name}'''
            mail_data["otp"] = otp
            
            if user_obj.status_id == 1:
                user_obj.first_name = first_name
                user_obj.last_name = last_name
                user_obj.country_id = country_id
                if date_of_birth:
                    user_obj.date_of_birth = date_of_birth
                user_obj.mobile_no = mobile_no
                user_obj.password = password
                user_obj.accepted_terms = True
                user_obj.status_id = 2 #profile complete verification pending
                user_obj.kyc_status_id = 1               
                user_obj.otp =otp
                user_obj.name = f'''{first_name} {last_name}'''
                db.commit()
                db.flush(UserModel)
                rowData['first_name'] = user_obj.first_name
                rowData['last_name'] = user_obj.last_name
                rowData['country_id'] = user_obj.country_id
                rowData['mobile_no'] = user_obj.mobile_no
                rowData['date_of_birth'] = str(user_obj.date_of_birth)
                rowData['status_id'] = user_obj.status_id
                rowData["country_details"] = Utility.model_to_dict(user_obj.country_details)
                rowData["status_details"] = Utility.model_to_dict(user_obj.status_details)
                background_tasks.add_task(Email.send_mail,recipient_email=[user_obj.email], subject=all_messages.PENDING_EMAIL_VERIFICATION_OTP_SUBJ, template='email_verification_otp.html',data=mail_data )
                return Utility.json_response(status=SUCCESS, message=all_messages.REGISTER_SUCCESS, error=[], data=rowData,code="OTP_VERIVICARION_PENDING")
            elif user_obj.status_id == 2:
                 mail_data["name"]= f'''{user_obj.first_name} {user_obj.last_name}'''
                 user_obj.otp =otp
                 background_tasks.add_task(Email.send_mail,recipient_email=[user_obj.email], subject=all_messages.PENDING_EMAIL_VERIFICATION_OTP_SUBJ, template='email_verification_otp.html',data=mail_data )
                 db.commit()
                 return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PENDING_EMAIL_VERIFICATION, error=[], data=rowData,code="OTP_VERIVICARION_PENDING")
            elif  user_obj.status_id == 3:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.ALREADY_PROFILE_IS_ACTIVE, error=[], data=rowData,code="ALREADY_PROFILE_IS_ACTIVE")
            elif user_obj.status_id == 4:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PROFILE_INACTIVE, error=[], data=rowData,code="PROFILE_INACTIVE")
            elif user_obj.status_id == 5:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PROFILE_DELETED, error=[], data=rowData,code="PROFILE_DELETED")
            else:
                db.rollback()
                return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

    except Exception as E:
        print(E)
        
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

@router.post("/verify-account", response_description="Send User Signup OTP")
async def verify_account(request: VerifyAccount,background_tasks: BackgroundTasks, db: Session = Depends(get_database_session)):
    try:
               
        user_id = request.user_id
        otp = str(request.otp)
        user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
        
        if user_obj is None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.USER_NOT_EXISTS, error=[], data={},code="USER_NOT_EXISTS")
        else:
            rowData = {}
            udata = Utility.model_to_dict(user_obj.country_details)
            rowData['user_id'] = user_obj.id
            rowData['email'] = user_obj.email
            rowData['first_name'] = user_obj.first_name
            rowData['last_name'] = user_obj.last_name
            rowData['country_id'] = user_obj.country_id
            #rowData['mobile_no'] = udata.get("mobile_no",'')
            #rowData['date_of_birth'] = udata.get("date_of_birth",'')
            rowData['status_id'] = user_obj.status_id
            rowData["country_details"] = Utility.model_to_dict(user_obj.country_details)
            rowData["status_details"] = Utility.model_to_dict(user_obj.status_details)
            if  user_obj.status_id ==1:
                code = "SIGNUP_PROCESS_PENDING"
                msg =all_messages.SIGNUP_PROCESS_PENDING                           
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=msg, error=[], data=rowData,code=code)
            elif user_obj.status_id == 2:
                if otp ==  user_obj.otp:
                    user_obj.status_id = 3
                    user_obj.otp = ''
                    db.commit()
                    mail_data ={"name": user_obj.first_name+" "+user_obj.last_name }
                    background_tasks.add_task(Email.send_mail,recipient_email=[user_obj.email], subject="Welcome to M-Cash!", template='signup_welcome.html',data=mail_data )
                    return Utility.json_response(status=SUCCESS, message=all_messages.OTP_VERIVICARION_SUCCESS, error=[], data=rowData,code="OTP_VERIVICARION_SUCCESS")
           
                else:
                    return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.INVALIED_OTP, error=[], data={},code="INVALIED_OTP")
                
            elif  user_obj.status_id == 3:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.ALREADY_PROFILE_IS_ACTIVE, error=[], data=rowData,code="ALREADY_PROFILE_IS_ACTIVE")
            elif user_obj.status_id == 4:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PROFILE_INACTIVE, error=[], data=rowData,code="PROFILE_INACTIVE")
            elif user_obj.status_id == 5:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PROFILE_DELETED, error=[], data=rowData,code="PROFILE_DELETED")
            else:
                db.rollback()
                return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

    except Exception as E:
        
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

@router.post("/login", response_description="Login")
def login(request: Login, background_tasks:BackgroundTasks,db: Session = Depends(get_database_session)):
    try:
               
        email = request.email
        password = request.password
        user_obj = db.query(UserModel,
                        #UserModel.email,
                        #UserModel.status_id,
                        #UserModel.user_name,
                        #UserModel.token,
                        #UserModel.password,
                        #UserModel.id
                        ).filter(UserModel.email == email)
      
        login_count =0
        if user_obj.count() <= 0:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.EMAIL_NOT_REGISTERED, error=[], data={})
        user_data = user_obj.one()
        
        
        if user_data.status_id !=3:
            if user_data.status_id == 4:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PROFILE_INACTIVE, error=[], data=rowData,code="PROFILE_INACTIVE")
            elif user_data.status_id == 5:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PROFILE_DELETED, error=[], data=rowData,code="PROFILE_DELETED")
            
            
            udata =  Utility.model_to_dict(user_data)
            rowData = {}
            rowData['user_id'] = udata["id"]
            rowData['email'] = udata.get("email","")
            rowData['first_name'] = udata.get("first_name","")
            rowData['last_name'] = udata.get("last_name","")
            rowData['country_id'] = udata.get("country_id",None)
            rowData['mobile_no'] = udata.get("mobile_no",'')
            rowData['date_of_birth'] = udata.get("date_of_birth",'')
            rowData['status_id'] = user_data.status_id
            rowData["country_details"] = Utility.model_to_dict(user_data.country_details)
            rowData["status_details"] = Utility.model_to_dict(user_data.status_details)
            
            #del existing_user.otp
            #del existing_user.password            
            if user_data.status_id == 1 or user_data.status_id ==2:
                msg = all_messages.ACCOUNT_EXISTS_PENDING_EMAIL_VERIFICATION
                code = "SIGNUP_VERIFICATION_PENDING"                
                if user_data.status_id ==2:
                    otp =str(Utility.generate_otp())
                    mail_data = {}
                    mail_data["name"]= f'''{udata.get("first_name","")} {udata.get("last_name","")}'''
                    mail_data["otp"] = otp
                    background_tasks.add_task(Email.send_mail,recipient_email=[udata["email"]], subject=all_messages.PENDING_EMAIL_VERIFICATION_OTP_SUBJ, template='email_verification_otp.html',data=mail_data )
                    user_obj.update({ UserModel.otp:str(otp)}, synchronize_session=False)
                    db.flush()
                    db.commit()
                    
                if  user_data.status_id ==1:
                    code = "SIGNUP_PROCESS_PENDING"
                    msg =all_messages.SIGNUP_PROCESS_PENDING                           
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=msg, error=[], data=rowData,code=code)
        else:
            user_dict = Utility.model_to_dict(user_data)
            user_dict["country_details"] =  Utility.model_to_dict(user_data.country_details)
            user_dict["kyc_status"] = Utility.model_to_dict(user_data.kyc_status)
            if user_data.tenant_details:
                user_dict["tenant_details"] = Utility.model_to_dict(user_data.tenant_details)
            
            verify_password = AuthHandler().verify_password(str(password), user_data.password)
            current_time = datetime.now(timezone.utc)
            naive_datetime = datetime.now()
            naive_datetime_aware = naive_datetime.replace(tzinfo=timezone.utc)
            if user_data.login_attempt_date is None:
                user_data.login_attempt_date = datetime.now(timezone.utc)


            if user_data.login_attempt_date is not None and user_data.login_attempt_date.tzinfo is None:
                user_data.login_attempt_date = user_data.login_attempt_date.replace(tzinfo=timezone.utc)

            
            if not verify_password:
                login_fail_count = user_data.login_fail_count
                
                if login_fail_count >=3:
                    time_difference = current_time - user_data.login_attempt_date
                    
                    if time_difference >= timedelta(hours=24):
                        print("24 Completed")
                        user_obj.update({ UserModel.login_attempt_date:datetime.now(timezone.utc),UserModel.login_fail_count:0}, synchronize_session=False)
                        db.flush()
                        db.commit()
                    else:
                        print("24 Not Completed")
                        # Access denied (less than 24 hours since last login)
                        otp =Utility.generate_otp()
                        token = AuthHandler().encode_token({"otp":otp})
                        user_data.token = token
                        user_data.otp = otp
                        rowData ={}
                        #db.flush(user_obj) ## Optionally, refresh the instance from the database to get the updated values
                        rowData["otp"] = otp
                        rowData["user_id"] = user_data.id
                        rowData['name'] = f"""{user_data.first_name} {user_data.last_name}"""
                        rowData["reset_link"] = f'''{WEB_URL}forgotPassword?token={token}&user_id={user_data.id}'''
                        if user_data.role_id==2:
                            rowData["reset_link"] = f'''{WEB_URL}user/forgotPassword?token={token}&user_id={user_data.id}'''
                        if user_data.role_id==4:
                            rowData["reset_link"] = f'''{WEB_URL}merchant/forgotPassword?token={token}&user_id={user_data.id}'''
                        if user_data.role_id==5:
                            rowData["reset_link"] = f'''{WEB_URL}agent/forgotPassword?token={token}&user_id={user_data.id}'''
                            
                        user_obj.update({ UserModel.otp:otp,UserModel.token:token}, synchronize_session=False)
                        db.commit()
                        background_tasks.add_task(Email.send_mail,recipient_email=[user_data.email], subject="Account Locked & Reset Password link", template='invalid_login_attempts.html',data=rowData )               
                    
                        user_obj.update({UserModel.login_fail_count:UserModel.login_fail_count+1}, synchronize_session=False)
                        db.flush()
                        db.commit()
                        #ACCOUNT_LOCKED
                        return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.ACCOUNT_LOCKED, error=[], data={})
                    #Wit for 24 Hourse
                else:
                    
                    user_obj.update({ UserModel.login_attempt_date:datetime.now(timezone.utc),UserModel.login_fail_count:login_fail_count+1}, synchronize_session=False)
                    #db.flush(UserModel)
                    db.commit()
                    
                return Utility.json_response(status=BAD_REQUEST, message=all_messages.INVALIED_CREDENTIALS, error=[], data={})
            else:
               
                
                if user_data.login_fail_count >=3:
                
                    time_difference = current_time - user_data.login_attempt_date
                    
                    if time_difference >= timedelta(hours=24):
                        print("24 Completed")
                        
                        user_obj.update({ UserModel.login_attempt_date:datetime.now(timezone.utc),UserModel.login_fail_count:0}, synchronize_session=False)
                        db.commit()
                    else:        
                        return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.ACCOUNT_LOCKED, error=[], data={})
                tenant_id = user_data.tenant_id  # Retrieve tenant ID here
                # Fetch details from admin table based on tenant ID and role ID 3
                admin_details = db.query(AdminUser).filter(AdminUser.tenant_id == tenant_id, AdminUser.role_id == 3).first()
                if admin_details is not None:
                    user_dict["tenant_admin_details"] = {}
                    user_dict["tenant_admin_details"]["id"] = admin_details.id
                    user_dict["tenant_admin_details"]["user_name"] = admin_details.user_name
                    user_dict["tenant_admin_details"]["email"] = admin_details.email
                    user_dict["tenant_admin_details"]["role_id"] = admin_details.role_id
                    user_dict["tenant_admin_details"]["status_id"] = admin_details.status_id
                    user_dict["tenant_admin_details"]["tenant_id"] = admin_details.tenant_id

                
                login_token = AuthHandler().encode_token(user_dict)
                if not login_token:
                    # return Utility.json_response(status=FAIL, message=all_messages.INVALIED_CREDENTIALS, error=[], data={})

                    return Utility.json_response(status=FAIL, message=all_messages.SOMTHING_WRONG, error=[], data={})
                    
                else:
                    print("1")                    
                    login_count = user_data.login_count+1                    
                    user_obj.update({ UserModel.login_fail_count:0,UserModel.login_count:login_count,UserModel.last_login:datetime.now(timezone.utc)}, synchronize_session=False)
                    db.commit()
                    print("2")

                    
                    
                    #user_dict = {c.name: getattr(user_data, c.name) for c in user_data.__table__.columns}
                    #print(user_dict)
                    if "password" in user_dict:
                        del user_dict["password"]
                    if "token" in user_dict:
                        del user_dict["token"]
                    if "otp" in user_dict:
                        del user_dict["otp"]
                    if "login_fail_count" in user_dict:
                        del user_dict["login_fail_count"]
                    if "login_attempt_date" in user_dict:
                        del user_dict["login_attempt_date"]
                    user_dict["token"] = login_token
                    if user_data.date_of_birth is not None:
                        user_dict["date_of_birth"] = str(user_data.date_of_birth)
                    #del user_dict.password
                    #del user_dict.otp
                    return Utility.dict_response(status=SUCCESS, message=all_messages.SUCCESS_LOGIN, error=[], data=user_dict)

    except Exception as E:
        print(E)
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})



@router.post("/resend-otp", response_description="Re-send Signup OTP")
async def resend_otp(request: SignupOtp,background_tasks: BackgroundTasks, db: Session = Depends(get_database_session)):
    try:
        
        email = request.email
        user_obj = db.query(UserModel).filter(UserModel.email == email).first()
        
        if user_obj is None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.USER_NOT_EXISTS, error=[], data={},code="USER_NOT_EXISTS")
        else:
            rowData = {}
            rowData['user_id'] = user_obj.id
            rowData['email'] = user_obj.email
            rowData['first_name'] = user_obj.first_name
            rowData['last_name'] = user_obj.last_name
            rowData['country_id'] = user_obj.country_id
            #rowData['mobile_no'] = udata.get("mobile_no",'')
            #rowData['date_of_birth'] = udata.get("date_of_birth",'')
            rowData['status_id'] = user_obj.status_id
            #rowData["country_details"] = Utility.model_to_dict(user_obj.country_details)
            #rowData["status_details"] = Utility.model_to_dict(user_obj.status_details)
            if  user_obj.status_id ==1:
                code = "SIGNUP_PROCESS_PENDING"
                msg =all_messages.SIGNUP_PROCESS_PENDING                           
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=msg, error=[], data=rowData,code=code)
            
            elif user_obj.status_id == 4:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PROFILE_INACTIVE, error=[], data={})
            elif user_obj.status_id == 5:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PROFILE_DELETED, error=[], data={})
            
            elif  user_obj.status_id ==2 or user_obj.status_id ==3:
                otp =Utility.generate_otp()
                mail_data = {"otp":str(otp),"name":user_obj.first_name +" "+user_obj.last_name}
                user_obj.token = AuthHandler().encode_token({"otp":otp})
                user_obj.otp = otp
                db.commit()
                #db.flush(user_obj) ## Optionally, refresh the instance from the database to get the updated values
                background_tasks.add_task(Email.send_mail,recipient_email=[user_obj.email], subject=all_messages.PENDING_EMAIL_VERIFICATION_OTP_SUBJ, template='email_verification_otp.html',data=mail_data )
                return Utility.json_response(status=SUCCESS, message=all_messages.RESEND_EMAIL_VERIFICATION_OTP, error=[], data=rowData,code="")
            else:
                db.rollback()
                return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

    except Exception as E:
        print(E)
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

@router.post("/forgot-password", response_description="Forgot Password")
async def forgot_password(request: ForgotPassword,background_tasks: BackgroundTasks, db: Session = Depends(get_database_session)):
    try:
        
        email = request.email
        #date_of_birth = request.date_of_birth
        user_obj = db.query(UserModel).filter(UserModel.email == email).first()
        
        if user_obj is None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.USER_NOT_EXISTS, error=[], data={},code="USER_NOT_EXISTS")
        else:
            if user_obj.status_id ==3:
                # if user_obj.date_of_birth != date_of_birth:
                #     return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.INVALID_BIRTHDATE, error=[], data={},code="")
                
                rowData = {}
                udata = Utility.model_to_dict(user_obj.country_details)
                rowData['user_id'] = udata["id"]
                rowData['email'] = user_obj.email
                rowData['first_name'] = user_obj.first_name
                rowData['last_name'] = user_obj.last_name
                rowData['country_id'] = user_obj.country_id
                #rowData['mobile_no'] = udata.get("mobile_no",'')
                #rowData['date_of_birth'] = udata.get("date_of_birth",'')
                rowData['status_id'] = user_obj.status_id            
                otp =Utility.generate_otp()
                token = AuthHandler().encode_token({"otp":otp})
                user_obj.token = token
                user_obj.otp = otp
                db.commit()
                #db.flush(user_obj) ## Optionally, refresh the instance from the database to get the updated values
                rowData["otp"] = otp
                rowData["user_id"] = user_obj.id
                rowData['name'] = f"""{user_obj.first_name} {user_obj.last_name}"""
                # 2= Custmer, 4= Marchant, 5 =Agent
                rowData["reset_link"] = f'''{WEB_URL}forgotPassword?token={token}&user_id={user_obj.id}'''
                if user_obj.role_id==2:
                        rowData["reset_link"] = f'''{WEB_URL}user/forgotPassword?token={token}&user_id={user_obj.id}'''
                if user_obj.role_id==4:
                    rowData["reset_link"] = f'''{WEB_URL}merchant/forgotPassword?token={token}&user_id={user_obj.id}'''
                if user_obj.role_id==5:
                    rowData["reset_link"] = f'''{WEB_URL}agent/forgotPassword?token={token}&user_id={user_obj.id}'''

                background_tasks.add_task(Email.send_mail,recipient_email=[user_obj.email], subject="Reset Password link", template='forgot_password.html',data=rowData )               
                return Utility.json_response(status=SUCCESS, message="Reset Password link is sent to your email", error=[], data={"user_id":user_obj.id},code="")
            
            
            elif  user_obj.status_id == 1:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PENDING_PROFILE_COMPLATION, error=[], data={},code="PROFILE_COMPLATION_PENDING")
            elif  user_obj.status_id == 2:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PENDING_EMAIL_VERIFICATION, error=[], data={},code="EMAIL_VERIFICATION_PENDING")
            elif user_obj.status_id == 3:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PROFILE_INACTIVE, error=[], data={})
            elif user_obj.status_id == 4:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PROFILE_DELETED, error=[], data={})
            else:
                db.rollback()
                return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

    except Exception as E:
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})


@router.post("/reset-password", response_description="Forgot Password")
async def reset_password(request: resetPassword,background_tasks: BackgroundTasks, db: Session = Depends(get_database_session)):
    try:
        user_id = request.user_id
        token = str(request.token)
        password =  request.password
        user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
        if user_obj is None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.USER_NOT_EXISTS, error=[], data={},code="USER_NOT_EXISTS")
        else:
            if token !=user_obj.token:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Invalid Token", error=[], data={},code="INVALIED_TOKEN")
            if user_obj.status_id ==3:
                user_obj.token = ''
                user_obj.otp = ''
                user_obj.password =AuthHandler().get_password_hash(password)
                user_obj.login_fail_count = 0
                db.commit()
                rowData = {}                
                rowData["user_id"] = user_obj.id
                rowData['name'] = f"""{user_obj.first_name} {user_obj.last_name}"""
                background_tasks.add_task(Email.send_mail,recipient_email=[user_obj.email], subject=all_messages.RESET_PASSWORD_SUCCESS, template='reset_password_success.html',data=rowData )               
                #db.flush(user_obj) ## Optionally, refresh the instance from the database to get the updated values
                return Utility.json_response(status=SUCCESS, message=all_messages.RESET_PASSWORD_SUCCESS, error=[], data={"user_id":user_obj.id,"email":user_obj.email},code="")
            elif  user_obj.status_id == 1:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PENDING_PROFILE_COMPLATION, error=[], data={},code="PENDING_PROFILE_COMPLATION")
            elif  user_obj.status_id == 2:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PENDING_EMAIL_VERIFICATION, error=[], data={},code="PENDING_EMAIL_VERIFICATION")
            elif user_obj.status_id == 3:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PROFILE_INACTIVE, error=[], data={})
            elif user_obj.status_id == 4:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PROFILE_DELETED, error=[], data={})
            else:
                db.rollback()
                return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

    except Exception as E:
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})


