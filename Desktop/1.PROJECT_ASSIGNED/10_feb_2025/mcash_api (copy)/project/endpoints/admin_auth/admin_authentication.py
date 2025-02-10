from datetime import datetime, timezone
from sqlalchemy import and_
from datetime import datetime
from ...models.admin_user import AdminUser  
from ...models.master_data_models import MdUserRole,MdUserStatus

from . import APIRouter,Utility, SUCCESS, FAIL, EXCEPTION ,INTERNAL_ERROR,BAD_REQUEST,BUSINESS_LOGIG_ERROR, Depends, Session, get_database_session, AuthHandler
from ...schemas.register import TenantSchema,TenantInvitationSchema,AdminRegister,InvitationSchema,TenantUserSchema,resetPassword,ForgotPasswordLinkSchema,SetPasswordSchema,UpdateAdminPassword
import re
from ...schemas.login import Login
from fastapi import BackgroundTasks
from ...common.mail import Email
from ...constant.status_constant import WEB_URL
import os
import json
from pathlib import Path
from ...models.user_model import TenantModel
from ...models.master_data_models import MdCountries,MdLocations,MdReminderStatus,MdStates,MdTaskStatus,MdTenantStatus,MdTimeZone,MdUserRole,MdUserStatus
from ...models.transaction import ChargesModel
from...models.admin_configuration_model import tokensModel
from ...models.kyc_doc_model import MdKycDocs,MdUserKycDocsStatus
from ...schemas.transaction import CreateCharges,EditCharges, ChargesListReqSchema,UpdateStatusSchema
from ...constant import messages as all_messages
from sqlalchemy.orm import  joinedload
from sqlalchemy import desc, asc
from sqlalchemy.sql import select, and_, or_, not_,func
from datetime import date, datetime
from ...aploger import AppLogger
# APIRouter creates path operations for product module
router = APIRouter( prefix="/admin", tags=["Admin Authentication"], responses={404: {"description": "Not found"}},)



@router.post("/login", response_description="Admin authenticated")
async def admin_login(request: Login, db: Session = Depends(get_database_session)):
    try:
        email = request.email
        password = request.password
        user = db.query(AdminUser,
                        #AdminUser.email,
                        #AdminUser.status_id,
                        #AdminUser.user_name,
                        #AdminUser.login_token,
                        #AdminUser.password,
                        #AdminUser.id
                        ).filter(AdminUser.email == email)
        if user.count() != 1:
            return Utility.json_response(status=FAIL, message="Invalid credential's", error=[], data={})
        if user.one().status_id !=3:
            msg = "Admin Profile is Deleted"
            if user.one().status_id == 1:
                msg = "Admin Profile is Pending State"
            if user.one().status_id == 2:
                msg = "Admin Profile is Pending State"
            if user.one().status_id == 4:
                msg = "Admin Profile is Inactive State"    
            if user.one().status_id == 5:
                msg = "Admin Profile is Delete"
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=msg, error=[], data={})
        user_data = user.one()
        verify_password = AuthHandler().verify_password(str(password), user_data.password)

        if not verify_password:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Invalid credential's", error=[], data={})
        user_dict = {c.name: getattr(user_data, c.name) for c in user_data.__table__.columns}
        if user_dict["tenant_id"] and  user_data.admin_tenant_details:
            user_dict["tenant_details"] = Utility.model_to_dict(user_data.admin_tenant_details)

        #print(user_dict)
        if "password" in user_dict:
            del user_dict["password"]
        if "token" in user_dict:
            del user_dict["token"]
        login_token = AuthHandler().encode_token(user_dict)
        
        if not login_token:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Token not assigned", error=[], data={})
        user.update({AdminUser.token: login_token, AdminUser.last_login:datetime.now(timezone.utc)}, synchronize_session=False)
        db.flush()
        db.commit()
        
        #print(user_data.status_details)
        #print(user_data.role)
        user_data.token = login_token
        del user_data.password
        del user_data.login_token
        user_dict["token"] = login_token
        return Utility.dict_response(status=SUCCESS, message="Logged in successfully", error=[], data=user_dict)
    except Exception as E:
        AppLogger.error(str(E))
        db.rollback()
        return Utility.json_response(status=EXCEPTION, message="Something went wrong", error=[], data={})


#ChargesModel
@router.post("/create-charge", response_description="Create New Charges")
async def create_charge(request: CreateCharges, admin_user=Depends(AuthHandler().auth_wrapper),db: Session = Depends(get_database_session)):
    try:
        admin_role_id = admin_user["role_id"]
        tenant_id = admin_user["tenant_id"]
        if admin_role_id not in [1,3]:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.NO_PERMISSIONS, error=[], data={},code="NO_PERMISSIONS")
        charges=0
        admin_charges=0
        agent_charges=0
        if calculate_in_percentage==True:
            charges=request.charges
            admin_charges=(request.admin_charges/100 )* charges
            agent_charges=(request.agent_charges/100)*charges
        else:
            charges=request.charges
            admin_charges=request.admin_charges
            agent_charges=request.agent_charges
        if charges!=admin_charges+agent_charges:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.CHARGES_NOT_MATCH, error=[], data={},code="CHARGES_NOT_MATCH")

        calculate_in_percentage = request.calculate_in_percentage
        md_category_id = request.md_category_id
        name = request.name.strip()
        charges = request.charges
        apply_to =request.apply_to
        minimum_transaction_amount =request.minimum_transaction_amount
        maximum_transaction_amount = request.maximum_transaction_amount
        users_list= request.users_list
        effective_date =request.effective_date
        #currency = request.currency
        description = request.description
       
        cleaned_name = ' '.join(request.name.strip().split()).lower()
        existing_count = db.query(ChargesModel).filter(func.lower(ChargesModel.name) == cleaned_name).count()
        charges_obj = db.query(ChargesModel).filter(ChargesModel.md_category_id == md_category_id,tenant_id==tenant_id).first()
        #if charges_obj is not None:
        if existing_count>0:
            return Utility.json_response(status=500, message=all_messages.CHARGE_EXISTS, error=[], data={},code="CHARGE_EXISTS")            
        else:
            new_charges = ChargesModel(
                                       name=name,
                                       apply_to =apply_to,
                                       minimum_transaction_amount =minimum_transaction_amount,
                                       maximum_transaction_amount = maximum_transaction_amount,
                                       users_list=users_list,
                                       effective_date=effective_date,
                                       admin_charges=admin_charges,
                                       agent_charges=agent_charges,
                                       #currency=currency,
                                       calculate_in_percentage =calculate_in_percentage,
                                       md_category_id=md_category_id,
                                       charges=charges,description=description,
                                       status=True,
                                       tenant_id=tenant_id,
                                       from_role_id= request.from_role_id,
                                       to_role_id= request.to_role_id
                                       )
            db.add(new_charges)
            db.commit()
            if new_charges.id:
                return Utility.json_response(status=SUCCESS, message=all_messages.NEW_CHARGE_ADDED_SUCCESS, error=[], data={"new_charges_id":new_charges.id})
            else:
                db.rollback()
                return Utility.json_response(status=EXCEPTION, message="Something went wrong", error=[], data={})

    except Exception as E:
        AppLogger.error(str(E))
        db.rollback()
        return Utility.json_response(status=EXCEPTION, message="Something went wrong", error=[], data={})

@router.post("/update-charge", response_description="Update Charge")
async def update_charge(request: EditCharges, admin_user=Depends(AuthHandler().auth_wrapper),db: Session = Depends(get_database_session)):
    try:
        admin_role_id = admin_user["role_id"]
        if admin_role_id not in [1,3]:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.NO_PERMISSIONS, error=[], data={},code="NO_PERMISSIONS")
        
        name = request.name.strip()
        charge_id = request.charge_id
        calculate_in_percentage = request.calculate_in_percentage
        md_category_id = request.md_category_id
        charges = request.charges
        apply_to =request.apply_to
        minimum_transaction_amount =request.minimum_transaction_amount
        maximum_transaction_amount = request.maximum_transaction_amount
        users_list= request.users_list
        effective_date =request.effective_date
        #currency = request.currency
        description = request.description
        cleaned_name = ' '.join(request.name.strip().split()).lower()
        existing_count = db.query(ChargesModel).filter(func.lower(ChargesModel.name) == cleaned_name, ChargesModel.id !=charge_id).count()
        charges_obj = db.query(ChargesModel).filter(ChargesModel.id == charge_id).first()
        if charges_obj is None:            
            return Utility.json_response(status=500, message=all_messages.CHARGE_NOT_EXISTS, error=[], data={},code="CHARGE_NOT_EXISTS")            
        elif existing_count>0:
            return Utility.json_response(status=500, message=all_messages.CHARGE_EXISTS, error=[], data={},code="CHARGE_EXISTS")  

        else:

            charges_obj.name = name
            charges_obj.calculate_in_percentage = calculate_in_percentage
            charges_obj.md_category_id = md_category_id
            charges_obj.charges = charges
            charges_obj.apply_to = apply_to
            charges_obj.minimum_transaction_amount = minimum_transaction_amount
            charges_obj.maximum_transaction_amount = maximum_transaction_amount
            charges_obj.users_list = users_list
            charges_obj.effective_date= effective_date
            #charges_obj.currency = currency
            charges_obj.description = description
            db.commit()
            return Utility.json_response(status=SUCCESS, message=all_messages.CHARGE_UPDATE_SUCCESS, error=[], data={})
            
    except Exception as E:
        AppLogger.error(str(E))
        db.rollback()
        return Utility.json_response(status=EXCEPTION, message="Something went wrong", error=[], data={})

@router.post("/update-status", response_description="Update Charge")
async def update_charge(request: UpdateStatusSchema, admin_user=Depends(AuthHandler().auth_wrapper),db: Session = Depends(get_database_session)):
    try:
        admin_role_id = admin_user["role_id"]
        if admin_role_id not in [1,3]:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.NO_PERMISSIONS, error=[], data={},code="NO_PERMISSIONS")
        
        status = request.status
        charge_id = request.charge_id
        charges_obj = db.query(ChargesModel).filter(ChargesModel.id == charge_id).first()
        if charges_obj is None:            
            return Utility.json_response(status=500, message=all_messages.CHARGE_NOT_EXISTS, error=[], data={},code="CHARGE_NOT_EXISTS")            
        else:

            charges_obj.status = status
            
            db.commit()
            return Utility.json_response(status=SUCCESS, message=all_messages.CHARGE_UPDATE_SUCCESS, error=[], data={})
            
    except Exception as E:
        AppLogger.error(str(E))
        db.rollback()
        return Utility.json_response(status=EXCEPTION, message="Something went wrong", error=[], data={})

@router.post("/charges-list", response_description="Charges List")
async def charge_list(request: ChargesListReqSchema, admin_user=Depends(AuthHandler().auth_wrapper),db: Session = Depends(get_database_session)):
    try:
        
        query = db.query(ChargesModel).options(joinedload(ChargesModel.charge_category_details))    

        if request.search_string:
            search = f"%{request.search_string}%"
            query = query.filter(or_(ChargesModel.name.ilike(search),
                                     ChargesModel.description.ilike(search),
                                     ChargesModel.charge_category_details.name.ilike(search)
                                    ))
            
               
        if request.status==False:
            query = query.filter(ChargesModel.status ==False)
        elif request.status==True:
            query = query.filter(ChargesModel.status ==True)

        if request.created_on and request.created_to and ( isinstance(request.created_on, date) and isinstance(request.created_to, date)):
            query = query.filter(ChargesModel.created_on > request.created_on)
            query = query.filter(ChargesModel.created_on < request.created_to)
        total_count = query.count()
        sort_column = getattr(ChargesModel, request.sort_by, None)
        if sort_column:
            if request.sort_order == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc("id"))

        # Apply pagination
        offset = (request.page - 1) * request.per_page
        paginated_query = query.offset(offset).limit(request.per_page).all()
        res_data ={ "total_count": total_count,"list":[],"page":request.page,"per_page":request.per_page}
        for item in paginated_query:
            temp_item = Utility.model_to_dict(item)
            if item.charge_category_details:
                temp_item["charge_category_details"] = Utility.model_to_dict(item.charge_category_details)
            res_data["list"].append(temp_item)
        
        return Utility.json_response(status=SUCCESS, message="List retrived", error=[], data=res_data)
    except Exception as E:
        AppLogger.error(str(E))
        db.rollback()
        return Utility.json_response(status=EXCEPTION, message="Something went wrong", error=[], data={})

@router.post("/invitation", response_description="invitation mail for maker checker")
async def invitation_mail(request:InvitationSchema,background_tasks: BackgroundTasks,admin_user=Depends(AuthHandler().auth_wrapper),db: Session = Depends(get_database_session)):
    try:
        email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if not re.fullmatch(email_regex, request.email):
            return Utility.json_response(status=BAD_REQUEST, message=all_messages.INVALIED_EMAIL, error=[], data={})
       
        role_id = admin_user["role_id"]
        user_id=admin_user["id"]
        tenant_id=admin_user["tenant_id"]
        if role_id not in [3]:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.NO_PERMISSIONS, error=[], data={},code="NO_PERMISSIONS")
        user_email=db.query(AdminUser).filter(AdminUser.email==request.email).first()
        if user_email:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Email already exists", error=[], data={})
        
        
        category="INVITE_USER"
        otp=str(Utility.generate_otp())
        user_dict={"user_id":user_id,"catrgory":category,"otp":otp}
        token = AuthHandler().encode_token({"tenant_id":tenant_id,"user_id":user_id,"catrgory":category,"otp":otp,"invite_role_id":request.role_id,"email":request.email})
        user_dict["token"]=token
        user_dict["ref_id"]=user_id
        
        db.add(tokensModel(**user_dict))
        db.commit()
        link=f'''{WEB_URL}Admin/InvitationMail?token={token}'''
        background_tasks.add_task(Email.send_mail, recipient_email=[request.email], subject="Invitation Link", template='invitation_template.html',data={"link":link})
        return Utility.json_response(status=SUCCESS, message="Invitation Sent to the mail", error=[], data={"email":request.email})   
    except Exception as E:
        AppLogger.error(str(E))
        db.rollback()
        return Utility.json_response(status=EXCEPTION, message="Something went wrong", error=[], data={})
    
@router.post("/signup-tenant-user", response_description="Register tenant user")
async def signup_tenant_user(request:TenantUserSchema,background_tasks: BackgroundTasks,db: Session = Depends(get_database_session)):
    try:
        token_data=db.query(tokensModel).filter(tokensModel.token ==request.token).first() 
        if not token_data:
            return Utility.json_response(status=401, message="Invalid Token", error=[], data={},code="INVALID_TOKEN")
        if token_data.active==False:
            return Utility.json_response(status=401, message="Token is expired", error=[], data={},code="TOKEN_EXPIRED")
        user_dict=AuthHandler().decode_token(request.token)
        print(user_dict)
        role_id=user_dict["invite_role_id"]
        email=user_dict["email"]
        tenant_id=user_dict["tenant_id"]
        print(request.password)
        password=AuthHandler().get_password_hash(request.password)
        user_data={"tenant_id":tenant_id,"user_name":request.first_name+" "+request.last_name,"password":password,"email":email,"mobile_no":request.mobile_no,"role_id":role_id,"status_id":3}
        db.add(AdminUser(**user_data))
        db.commit()
        background_tasks.add_task(Email.send_mail, recipient_email=[email], subject="Invitation Link", template='signup_welcome.html',data={"name":user_data["user_name"]})
        token_data.active=False
        db.commit()
        return Utility.json_response(status=SUCCESS, message="User Registered Successfully", error=[], data=user_data)   
    except Exception as E:
        AppLogger.error(str(E))
        db.rollback()
        return Utility.json_response(status=EXCEPTION, message="Something went wrong", error=[], data={})

@router.post("/update-password", response_description="Update Admin Password")
async def reset_password(request: UpdateAdminPassword,background_tasks: BackgroundTasks, db: Session = Depends(get_database_session)):
    try:
        user_id = request.user_id
        old_password=request.old_password
        password =  request.password
        user_obj = db.query(AdminUser).filter(AdminUser.id == user_id).first()
        if user_obj is None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.USER_NOT_EXISTS, error=[], data={},code="USER_NOT_EXISTS")
        valid=AuthHandler().verify_password(old_password,user_obj.password)
        if not valid:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Invalid current Password", error=[], data={},code="INVALID_PASSWORD")
        user_obj.password =AuthHandler().get_password_hash(password)
        db.commit()
        rowData = {}                
        rowData["user_id"] = user_obj.id
        rowData['name'] = user_obj.user_name
        background_tasks.add_task(Email.send_mail,recipient_email=[user_obj.email], subject=all_messages.RESET_PASSWORD_SUCCESS, template='reset_password_success.html',data=rowData )               
        db.flush(user_obj) ## Optionally, refresh the instance from the database to get the updated values
        return Utility.json_response(status=SUCCESS, message=all_messages.RESET_PASSWORD_SUCCESS, error=[], data={"user_id":user_obj.id,"email":user_obj.email},code="")
    except Exception as E:
        AppLogger.error(str(E))
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})
    
@router.post("/forgot-password", response_description="Admin Forgot password")
async def forgot_password(request:ForgotPasswordLinkSchema,background_tasks: BackgroundTasks,db: Session = Depends(get_database_session)):
    try:
        email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if not re.fullmatch(email_regex, request.email):
            return Utility.json_response(status=BAD_REQUEST, message=all_messages.INVALIED_EMAIL, error=[], data={})
        user_obj = db.query(AdminUser).filter(AdminUser.email == request.email).first()
        if user_obj is None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Admin doesnot exit", error=[], data={},code="ADMIN_NOT_EXISTS")
        category="ADMIN_FORGOT_PASSWORD"
        otp=str(Utility.generate_otp())
        token = AuthHandler().encode_token({"email":request.email,"user_id":user_obj.id,"catrgory":category,"otp":otp,"invite_role_id":user_obj.role_id})
        data={}
        data["reset_link"] = f'''{WEB_URL}Admin/ForgotPassword?token={token}&user_id={user_obj.id}'''
        data["name"]=user_obj.user_name
        user_dict={"user_id":user_obj.id,"catrgory":category,"otp":otp}
        user_dict["token"]=token
        user_dict["ref_id"]=user_obj.id
        db.add(tokensModel(**user_dict))
        db.commit()
        background_tasks.add_task(Email.send_mail,recipient_email=[request.email], subject="Reset Password link", template='forgot_password.html',data=data )               
        return Utility.json_response(status=SUCCESS, message="Reset Password link is sent to your email", error=[], data=data,code="")
    except Exception as E:
        AppLogger.error(str(E))
        db.rollback()
        return Utility.json_response(status=EXCEPTION, message="Something went wrong", error=[], data={})


@router.post("/reset-password", response_description="Set admin password")
async def set_password(request:SetPasswordSchema,background_tasks: BackgroundTasks,db: Session = Depends(get_database_session)):
    try:
        token_data=db.query(tokensModel).filter(tokensModel.token ==request.token).first() 
        if not token_data:
            return Utility.json_response(status=401, message="Invalid Token", error=[], data={},code="INVALID_TOKEN")
        if token_data.active==False:
            return Utility.json_response(status=401, message="Token is expired", error=[], data={},code="TOKEN_EXPIRED")
        user_dict=AuthHandler().decode_token(request.token)
        user_obj = db.query(AdminUser).filter(AdminUser.email == user_dict["email"]).first()
        if user_obj is None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Admin doesnot exit", error=[], data={},code="ADMIN_NOT_EXISTS")
        user_obj.token = request.token
        user_obj.password =AuthHandler().get_password_hash(request.password)
        db.commit()
        row_data={}
        row_data['name'] = user_obj.user_name
        background_tasks.add_task(Email.send_mail,recipient_email=[user_obj.email], subject="Reset Password successfull", template='reset_password_success.html',data=row_data )               
        db.flush(user_obj)
        token_data.active=False
        db.commit()
        return Utility.json_response(status=SUCCESS, message=all_messages.RESET_PASSWORD_SUCCESS, error=[], data={},code="")
    except Exception as E:
        AppLogger.error(str(E))
        db.rollback()
        return Utility.json_response(status=EXCEPTION, message="Something went wrong", error=[], data={})
    
@router.post("/tenant-invitation", response_description="invitation mail for Tenant")
async def tenant_invitation_mail(request:TenantInvitationSchema,background_tasks: BackgroundTasks,admin_user=Depends(AuthHandler().auth_wrapper),db: Session = Depends(get_database_session)):
    try:
        email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if not re.fullmatch(email_regex, request.email):
            return Utility.json_response(status=BAD_REQUEST, message=all_messages.INVALIED_EMAIL, error=[], data={})
        
        role_id = admin_user["role_id"]
        user_id=admin_user["id"]
        if role_id not in [1]:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.NO_PERMISSIONS, error=[], data={},code="NO_PERMISSIONS")
        user_email=db.query(AdminUser).filter(AdminUser.email==request.email).first()
        if user_email:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Email already exists", error=[], data={})

        
        category="INVITE_TENANT"
        otp=str(Utility.generate_otp())
        user_dict={"user_id":user_id,"catrgory":category,"otp":otp}
        token = AuthHandler().encode_token({"catrgory":category,"otp":otp,"invite_role_id":3,"email":request.email,"name":request.name})
        user_dict["token"]=token
        user_dict["ref_id"]=user_id
        db.add(tokensModel(**user_dict))
        db.commit()
        link=f'''{WEB_URL}Admin/TenantInvitationMail?token={token}'''
        background_tasks.add_task(Email.send_mail, recipient_email=[request.email], subject="Invitation Link", template='invitation_template.html',data={"link":link})
        return Utility.json_response(status=SUCCESS, message="Invitation Sent to the mail", error=[], data={"email":request.email})   
    except Exception as E:
        AppLogger.error(str(E))
        db.rollback()


file_to_model = {
            "md_kyc_docs.json":MdKycDocs,
            
        }

@router.post("/signup-tenant", response_description="Register tenant")
async def signup_tenant_user(request:TenantSchema,background_tasks: BackgroundTasks,db: Session = Depends(get_database_session)):
    try:
        token_data=db.query(tokensModel).filter(tokensModel.token ==request.token).first() 
        if not token_data:
            return Utility.json_response(status=401, message="Invalid Token", error=[], data={},code="INVALID_TOKEN")
        if token_data.active==False:
            return Utility.json_response(status=401, message="Token is expired", error=[], data={},code="TOKEN_EXPIRED")
        user_dict=AuthHandler().decode_token(request.token)
        role_id=user_dict["invite_role_id"]
        email=user_dict["email"]
        row_data={"name":user_dict["name"],"email":email,"mobile_no":request.mobile_no}
        new_tenant=TenantModel(**row_data)
        db.add(new_tenant)
        db.commit()
        tenant_id=new_tenant.id
        password=AuthHandler().get_password_hash(request.password)
        user_data={"user_name":user_dict["name"],"login_token":request.token,"token":request.token,"password":password,"email":email,"mobile_no":request.mobile_no,"role_id":role_id,"status_id":3,"tenant_id":tenant_id}
        db.add(AdminUser(**user_data))
        db.commit()
        def insertBulkData(file_to_model):
            json_directory=Path(__file__).resolve().parent.parent.parent/"master_data"
            batch_size = 500
            print("tyu")
            for filename in os.listdir(json_directory):
                if filename in file_to_model:
                    model=file_to_model[filename]
                    file_path=json_directory / filename
                    with open(file_path, 'r') as file:
                        data = json.load(file)
                    batch=[]
                    for entry in data:
                    # Filter out any keys not matching the model's attributes
                        filtered_entry = {key: value for key, value in entry.items() if hasattr(model, key)}
                        if(filename=="md_kyc_docs.json")and ("tenant_id" in filtered_entry):
                            if "id" in filtered_entry:
                                del filtered_entry["id"]
                                filtered_entry["tenant_id"] = tenant_id
                    
                        print(filtered_entry)
                        record = model(**filtered_entry)
                        batch.append(record)
                        print(batch)
                        if len(batch) >= batch_size:
                            db.bulk_save_objects(batch)
                            batch.clear()

                    if batch:
                        db.bulk_save_objects(batch)
                    db.commit()
        insertBulkData(file_to_model)
        background_tasks.add_task(Email.send_mail, recipient_email=[email], subject="Invitation Link", template='signup_welcome.html',data={"name":user_data["user_name"]})
        token_data.active=False
        db.commit()
        return Utility.json_response(status=SUCCESS, message="User Registered Successfully", error=[], data=user_data)   
    except Exception as E:
        AppLogger.error(str(E))
        db.rollback()
        return Utility.json_response(status=EXCEPTION, message="Something went wrong", error=[], data={})