from datetime import datetime, timezone
from sqlalchemy import and_
from datetime import datetime
from ...models.agent import AgentModel 
from ...schemas.agent import AgentRegisterSchema, UpdateAgentPasswordSchema 

from . import APIRouter,Utility, SUCCESS, FAIL, EXCEPTION ,INTERNAL_ERROR,BAD_REQUEST,BUSINESS_LOGIG_ERROR, Depends, Session, get_database_session, AuthHandler
from ...schemas.register import ForgotPasswordLinkSchema,SetPasswordSchema,UpdateAdminPassword
import re
from ...schemas.login import Login
from fastapi import BackgroundTasks
from ...common.mail import Email
from ...constant.status_constant import WEB_URL
import os
import json
from pathlib import Path
from ...models.user_model import TenantModel
from...models.admin_configuration_model import tokensModel
from ...constant import messages as all_messages
from sqlalchemy.orm import  joinedload
from sqlalchemy import desc, asc
from sqlalchemy.sql import select, and_, or_, not_,func
from datetime import date, datetime
from ...aploger import AppLogger
from ...models.kyc_doc_model import MdKycDocs,MdUserKycDocsStatus
from ...library.webSocketConnectionManager import manager
from ...models.user_model import AdminNotificationModel,NotificationModel
from ...schemas.user_schema import UpdateKycDocStatus,kycDetailsRequest

from ...schemas.user_schema import UpdateKycDetails
from ...models.agent import AgentKycDetailsModel, AgentKycDocsModel, AgentKycDocsCommentsModel

# APIRouter creates path operations for product module
router = APIRouter( prefix="/agent", tags=["Agent Module"], responses={404: {"description": "Not found"}},)


@router.post("/signup", response_description="agent Registration")
async def register(request: AgentRegisterSchema, db: Session = Depends(get_database_session)):
    try:
        #AgentModel 
        user_name = request.user_name
        contact = request.mobile_no
        email = request.email
        password = request.password
        country_id = request.country_id
        if user_name == '' or contact == '' or email == '' or password == '':
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Provide valid detail's", error=[], data={})
        if user_name is None or contact is None or email is None or password is None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Provide valid detail's", error=[], data={})
        email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if not re.fullmatch(email_regex, email):
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Provide valid email", error=[], data={})
        # contact_digits = math.floor(math.log10(contact)) + 1
        if len(str(contact)) < 7 or len(str(contact)) > 15:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Mobile number not valid. Length must be 7-13.",error=[], data={})
        user_with_email = db.query(AgentModel).filter(AgentModel.email == email).all()
        if len(user_with_email) != 0:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Email already exists", error=[], data={})

        user_data = AgentModel  (country_id=country_id,role_id =5,status_id=3, email=email,user_name=user_name, mobile_no=contact,password=AuthHandler().get_password_hash(str(password)))
        db.add(user_data)
        db.flush()
        db.commit()
        
        if user_data.id:
            return Utility.json_response(status=SUCCESS, message="Registered Successfully", error=[],
                                         data={"user_id": user_data.id})
        else:
            return Utility.json_response(status=FAIL, message="Something went wrong", error=[], data={})
    except Exception as E:
        
        AppLogger.error(str(E))
        db.rollback()
        return Utility.json_response(status=FAIL, message="Something went wrong", error=[], data={})


@router.post("/login", response_description="agent authenticated")
async def admin_login(request: Login, db: Session = Depends(get_database_session)):
    try:
        email = request.email
        password = request.password
        user = db.query(AgentModel).filter(AgentModel.email == email)
        if user.count() != 1:
            return Utility.json_response(status=FAIL, message="Invalid credential's", error=[], data={})
        if user.one().status_id !=3:
            msg = "Agent Profile is Deleted"
            if user.one().status_id == 1:
                msg = "Agent Profile is Pending State"
            if user.one().status_id == 2:
                msg = "Agent Profile is Pending State"
            if user.one().status_id == 4:
                msg = "Agent Profile is Inactive State"    
            if user.one().status_id == 5:
                msg = "Agent Profile is Delete"
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=msg, error=[], data={})
        user_data = user.one()
        verify_password = AuthHandler().verify_password(str(password), user_data.password)

        if not verify_password:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Invalid credential's", error=[], data={})
        user_dict = Utility.model_to_dict(user_data)
        if user_dict["tenant_id"] and  user_data.merchant_tenant_details:
            user_dict["tenant_details"] = Utility.model_to_dict(user_data.merchant_tenant_details)

        #print(user_dict)
        if "password" in user_dict:
            del user_dict["password"]
        if "token" in user_dict:
            del user_dict["token"]
        login_token = AuthHandler().encode_token(user_dict)
        
        if not login_token:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Token not assigned", error=[], data={})
        user.update({AgentModel.token: login_token, AgentModel.last_login:datetime.now(timezone.utc)}, synchronize_session=False)
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
        print(E)
        db.rollback()
        return Utility.json_response(status=EXCEPTION, message="Something went wrong", error=[], data={})


@router.post("/update-password", response_description="Update Agent Password")
async def reset_password(request: UpdateAgentPasswordSchema,background_tasks: BackgroundTasks, db: Session = Depends(get_database_session)):
    try:
        user_id = request.user_id
        old_password=request.old_password
        password =  request.password
        user_obj = db.query(AgentModel).filter(AgentModel.id == user_id).first()
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
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})
    
@router.post("/forgot-password", response_description="Agent Forgot password")
async def forgot_password(request:ForgotPasswordLinkSchema,background_tasks: BackgroundTasks,db: Session = Depends(get_database_session)):
    try:
        email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if not re.fullmatch(email_regex, request.email):
            return Utility.json_response(status=BAD_REQUEST, message=all_messages.INVALIED_EMAIL, error=[], data={})
        user_obj = db.query(AgentModel).filter(AgentModel.email == request.email).first()
        if user_obj is None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Admin doesnot exit", error=[], data={},code="MERCHANT_NOT_EXISTS")
        category="MERCHANT_FORGOT_PASSWORD"
        otp=str(Utility.generate_otp())
        token = AuthHandler().encode_token({"email":request.email,"user_id":user_obj.id,"catrgory":category,"otp":otp,"invite_role_id":user_obj.role_id})
        data={}
        data["reset_link"] = f'''{WEB_URL}merchat/ForgotPassword?token={token}&user_id={user_obj.id}'''
        data["name"]=user_obj.user_name
        user_dict={"user_id":user_obj.id,"catrgory":category,"otp":otp}
        user_dict["token"]=token
        user_dict["ref_id"]=user_obj.id
        db.add(tokensModel(**user_dict))
        db.commit()
        background_tasks.add_task(Email.send_mail,recipient_email=[request.email], subject="Reset Password link", template='forgot_password.html',data=data )               
        return Utility.json_response(status=SUCCESS, message="Reset Password link is sent to your email", error=[], data=data,code="")
    except Exception as E:
        print(E)
        db.rollback()
        return Utility.json_response(status=EXCEPTION, message="Something went wrong", error=[], data={})


@router.post("/reset-password", response_description="Set Agent password")
async def set_password(request:SetPasswordSchema,background_tasks: BackgroundTasks,db: Session = Depends(get_database_session)):
    try:
        token_data=db.query(tokensModel).filter(tokensModel.token ==request.token).first() 
        if not token_data:
            return Utility.json_response(status=401, message="Invalid Token", error=[], data={},code="INVALID_TOKEN")
        if token_data.active==False:
            return Utility.json_response(status=401, message="Token is expired", error=[], data={},code="TOKEN_EXPIRED")
        user_dict=AuthHandler().decode_token(request.token)
        user_obj = db.query(AgentModel).filter(AgentModel.email == user_dict["email"]).first()
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
        print(E)
        db.rollback()
        return Utility.json_response(status=EXCEPTION, message="Something went wrong", error=[], data={})
    

@router.post("/update-kyc-details", response_description="Update KYC DETAILS")
async def update_kyc_details(request: UpdateKycDetails,background_tasks: BackgroundTasks,auth_user=Depends(AuthHandler().auth_wrapper), db: Session = Depends(get_database_session)):
    try:        
        
        user_id = auth_user["id"]
        tenant_id = auth_user["tenant_id"]
        first_name = request.first_name
        last_name = request.last_name
        email = request.email
        date_of_birth = request.date_of_birth
        mobile_no = request.mobile_no
        street = request.street
        city = request.city
        state = request.state
        state_id = request.state_id
        occupation_id = request.occupation_id
        annual_income = request.annual_income
        pincode = request.pincode
        documents = request.documents

        def sendmails(type="ADD"):
            #send Mail to user
            mail_data = {"name":auth_user["name"] }
            background_tasks.add_task(Email.send_mail,recipient_email=[auth_user["email"]],subject=all_messages.KYC_UPDATE_SUCCESS,template='kyc_documents_uploaded.html',data=mail_data)
            #send mail to admin
            #Utility.model_to_dict()
            if auth_user.get("tenant_details",False):
                if auth_user["tenant_details"].get("email",False):
                    admin_id = auth_user["tenant_details"]["id"]
                    tenant_email = auth_user["tenant_details"]["email"]
                    admin_name = auth_user["tenant_details"]["name"]
                    admin_mail_data = {"user_name":user_obj.name, "name":admin_name}
                    subject= f'''{user_obj.name} uploaded KYC documents'''
                    background_tasks.add_task(Email.send_mail,recipient_email=tenant_email, subject=subject, template='kyc_docs_user_uploaded_admin.html',data=admin_mail_data )
                    description = subject
                    admin_notification = AdminNotificationModel(user_id=user_id,admin_id=admin_id,description=description,category="USER_DETAILS",ref_id=auth_user["id"])
                    db.add(admin_notification)
                    db.commit()

        if auth_user["role_id"] !=5:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.NO_PERMISSIONS, error=[], data={},code="NO_PERMISSIONS")

        user_obj = db.query(AgentModel).filter(AgentModel.id == user_id).first()
        if user_obj is None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.USER_NOT_EXISTS, error=[], data={},code="INVALIED_TOKEN")
        elif user_obj.status_id == 1:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PENDING_PROFILE_COMPLATION, error=[], data={},code="LOGOUT_ACCOUNT")
        
        if user_obj.status_id == 2:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PENDING_EMAIL_VERIFICATION, error=[], data={},code="LOGOUT_ACCOUNT")
    
        elif user_obj.status_id == 4:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PROFILE_INACTIVE, error=[], data={},code="LOGOUT_ACCOUNT")
        elif user_obj.status_id == 5:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PROFILE_DELETED, error=[], data={},code="LOGOUT_ACCOUNT")
        
        
        #AgentKycDetailsModel, AgentKycDocsModel, KycDocsCommentsModel
        user_kyc_details = db.query(AgentKycDetailsModel).filter(AgentKycDetailsModel.agent_id == user_id).first()
        user_obj.updated_on = datetime.now(timezone.utc)
        if user_kyc_details is None:
            details = AgentKycDetailsModel(agent_id=user_id,street =street,city=city, state=state,occupation_id=occupation_id,annual_income=annual_income,pincode=pincode,state_id = state_id,created_on = datetime.now(timezone.utc),updated_on = datetime.now(timezone.utc))
            
            #UserKycDocsModel
            user_kyc_docs =[]
            
            if len(documents)>0:
                for document in documents:
                    #md_doc_name
                    #md_doc_description 
                    #md_doc_required
                    

                    udoc = AgentKycDocsModel(agent_id=user_id, tenant_id=tenant_id, md_doc_id=document["md_doc_id"], name=document["name"], path=document["path"],content_type=document["content_type"],size=document["size"], status_id=2)
                    masterDocQuery = db.query(MdKycDocs).filter(MdKycDocs.id==document["md_doc_id"])
                    if user_obj.tenant_id:
                        masterDocQuery = masterDocQuery.filter(MdKycDocs.tenant_id==user_obj.tenant_id)

                    masterDoc = masterDocQuery.first()
                    if masterDoc is not None:
                        udoc.md_doc_name = masterDoc.name
                        udoc.md_doc_description = masterDoc.description
                        udoc.md_doc_required = masterDoc.required

                          
                    user_kyc_docs.append(udoc)

            if len(user_kyc_docs)>0:                
                db.bulk_save_objects(user_kyc_docs)

            db.add(details)
            db.flush()
            db.commit()
            if details.id:
                #update user details
                user_obj.first_name = first_name
                user_obj.last_name = last_name
                user_obj.name = f'''{first_name} {last_name}'''
                user_obj.date_of_birth = date_of_birth
                user_obj.mobile_no = mobile_no
                user_obj.kyc_details_id = details.id
                sendmails(type="ADD")
                db.commit()
                return Utility.json_response(status=SUCCESS, message=all_messages.USER_ADDED_KYC_DETAILS, error=[], data={},code="")
            else:
                db.rollback()
                return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

        else:
            #update user details
            user_obj.first_name = first_name
            user_obj.last_name = last_name
            user_obj.name = f'''{first_name} {last_name}'''
            user_obj.date_of_birth = date_of_birth
            user_obj.mobile_no = mobile_no       
                      
            user_kyc_details.street = street
            user_kyc_details.city = city
            user_kyc_details.state = state
            user_kyc_details.state_id= state_id
            #user_kyc_details.occupation_id = occupation_id
            user_kyc_details.annual_income =annual_income
            user_kyc_details.pincode = pincode
            user_obj.kyc_details_id = user_kyc_details.id
            user_kyc_details.updated_on = datetime.now(timezone.utc)
            new_kyc_docs =[]
            existing_docs = []
            if len(documents)>0:
                for document in documents:
                    masterDocQuery = db.query(MdKycDocs).filter(MdKycDocs.id==document["md_doc_id"])
                    if user_obj.tenant_id:
                        masterDocQuery = masterDocQuery.filter(MdKycDocs.tenant_id==user_obj.tenant_id)
                    masterDoc = masterDocQuery.first()
                    db_doc = db.query(AgentKycDocsModel).filter(AgentKycDocsModel.md_doc_id == document["md_doc_id"],AgentKycDocsModel.agent_id==user_id).first()
                     #check Document is exists or not
                    if db_doc is not None:
                        if db_doc.path !=document["path"]:
                            existing_docs.append(Utility.model_to_dict(db_doc))
                        if db_doc.status_id !=3 and db_doc.status_id !=4:
                            db_doc.status_id = 2
                        if masterDoc is not None:
                            db_doc.md_doc_name = masterDoc.name
                            db_doc.md_doc_description = masterDoc.description
                            db_doc.md_doc_required = masterDoc.required       

                    else:
                        udoc = AgentKycDocsModel(agent_id=user_id, tenant_id=tenant_id, md_doc_id=document["md_doc_id"], name=document["name"], path=document["path"],content_type=document["content_type"], size=document["size"],status_id=2)
                        
                        if masterDoc is not None:
                            udoc.md_doc_name = masterDoc.name
                            udoc.md_doc_description = masterDoc.description
                            udoc.md_doc_required = masterDoc.required
                        new_kyc_docs.append(udoc)

            if len(new_kyc_docs)>0:
                db.bulk_save_objects(new_kyc_docs)
            if len(existing_docs)>0:
                if request.override_existing_docs:
                    for document in documents:
                        masterDocQuery = db.query(MdKycDocs).filter(MdKycDocs.id==document["md_doc_id"])
                        if user_obj.tenant_id:
                            masterDocQuery = masterDocQuery.filter(MdKycDocs.tenant_id==user_obj.tenant_id)
                        masterDoc = masterDocQuery.first()
                        db_doc = db.query(AgentKycDocsModel).filter(AgentKycDocsModel.md_doc_id == document["md_doc_id"],AgentKycDocsModel.agent_id==user_id).first()
                        db_doc.md_doc_id = document["md_doc_id"]
                        db_doc.name = document["name"]
                        db_doc.path = document["path"]
                        db_doc.content_type = document["content_type"]
                        db_doc.size = document["size"]
                        if masterDoc is not None:
                            db_doc.md_doc_name = masterDoc.name
                            db_doc.md_doc_required = masterDoc.required
                            db_doc.md_doc_description = masterDoc.description
                        if db_doc is not None:
                            if db_doc.path !=document["path"]:
                                db_doc.status_id = 2  
                            if db_doc.status_id !=3 and db_doc.status_id !=4:
                                db_doc.status_id = 2 
                        else:
                            db_doc.status_id = 2        
                        
                    user_obj.kyc_status_id = 1
                    sendmails(type="EDIT")
                    db.commit()
                    if "tenant_admin_details" in auth_user:
                        socket_id = Utility.generate_websocket_id(auth_user["tenant_admin_details"])
                        await manager.send_message(socket_id,{"message":"","category":"UPDATED_USER_KYC_DOCUMENTS","path":"RELOAD_KYC_APPROVE_FORM_IN_ADMIN"})
                        background_tasks.add_task(manager.send_message,"superuser_1_1", {"message":"","category":"UPDATED_USER_KYC_DOCUMENTS","path":"RELOAD_KYC_APPROVE_FORM_IN_ADMIN"})
                    #send mail to admi and user
                    return Utility.json_response(status=SUCCESS, message=all_messages.USER_ADDED_KYC_DETAILS, error=[], data={},code="")
                else:
                    db.rollback()
                    return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.CONFORMATION_REQUIRED, error=[], data={"existing_docs":existing_docs},code="CONFORMATION_REQUIRED")

            else:
                #send mail to user and admin
                sendmails(type="ADD")
                user_obj.kyc_status_id = 1
                db.commit()
                db.flush(AgentModel)
                if "tenant_admin_details" in auth_user:
                        socket_id = Utility.generate_websocket_id(auth_user["tenant_admin_details"])
                        await manager.send_message(socket_id,{"message":"","category":"UPDATED_USER_KYC_DOCUMENTS","path":"RELOAD_KYC_APPROVE_FORM_IN_ADMIN"})
                        background_tasks.add_task(manager.send_message,"superuser_1_1", {"message":"","category":"UPDATED_USER_KYC_DOCUMENTS","path":"RELOAD_KYC_APPROVE_FORM_IN_ADMIN"})
                    
                return Utility.json_response(status=SUCCESS, message=all_messages.USER_ADDED_KYC_DETAILS, error=[], data={},code="")
        
    except Exception as E:
        AppLogger.error(str(E))
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})


@router.post("/update-kyc-doc-status", response_description="Update KYC document status")
async def update_kyc_doc_details(request: UpdateKycDocStatus,background_tasks: BackgroundTasks,auth_user=Depends(AuthHandler().auth_wrapper), db: Session = Depends(get_database_session)):
    try:
        if auth_user.get("role_id", -1) not in [1,3]:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.NO_PERMISSIONS, error=[], data={},code="NO_PERMISSIONS")
        admin_id = auth_user["id"]
        role_id = auth_user["role_id"]
        user_id = request.user_id
        document_id = request.document_id
        md_doc_id = request.md_doc_id
        status_id = request.status_id
        description = request.description
        user_kyc_details = db.query(AgentKycDetailsModel).filter(AgentKycDetailsModel.agent_id == user_id).first()
        if user_kyc_details is not None:
            user_kyc_details.updated_on = datetime.now(timezone.utc)
            
        if status_id<=2:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.INVALID_SATUS_SELECTED, error=[], data={},code="INVALID_SATUS_SELECTED")
        db_doc = db.query(AgentKycDocsModel).filter(AgentKycDocsModel.id == document_id,AgentKycDocsModel.agent_id==user_id, AgentKycDocsModel.md_doc_id==md_doc_id).first()
        if db_doc is None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.KYC_DOCUMENT_NOT_EXISTS, error=[], data={},code="KYC_DOCUMENT_NOT_EXISTS")

        if db_doc.status_id == status_id:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.KYC_IS_SAME_STATUS, error=[], data={},code="KYC_IS_SAME_STATUS")
        db_doc.status_id = status_id
        db_doc.updated_on = datetime.now(timezone.utc)
        
        user_obj = db.query(AgentModel).filter(AgentModel.id == user_id).first()
        if user_obj is None:
            db.rollback()
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.USER_NOT_EXISTS, error=[], data={},code="USER_NOT_EXISTS")
        elif user_obj.status_id == 1:
                db.rollback()
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PENDING_PROFILE_COMPLATION, error=[], data={},code="PENDING_PROFILE_COMPLATION")
        if user_obj.status_id == 2:
            db.rollback()
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PENDING_EMAIL_VERIFICATION, error=[], data={},code="PENDING_EMAIL_VERIFICATION")
        elif user_obj.status_id == 4:
            db.rollback()
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PROFILE_INACTIVE, error=[], data={},code="PROFILE_INACTIVE")
        elif user_obj.status_id == 5:
            db.rollback()
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PROFILE_DELETED, error=[], data={},code="PROFILE_DELETED")
        
        
        
        #send mail to user  and admin

        mail_data = {"name":user_obj.name,"admin_comment":description, "mail_content":'' }
        mail_data["mail_content"] =""
        mail_subject = all_messages.KYC_DOC_STATUS_UPDATE_SUCCESS
        docname = db_doc.name
        if db_doc.md_doc_name:
            docname = f'''{db_doc.md_doc_name} ({db_doc.name})'''

        msg =  "KYC document status updated successfully"
        notification_msg =description           
        
        status_category = None  # Ensure status_category is initialized

        if status_id == 3:
            mail_subject = f'''{mail_subject} Approved'''
            notification_msg = "Congratulations! Your KYC document has been successfully approved."
            mail_data["mail_content"] = f'''Your KYC  {docname} document is Approved'''
            msg =  "KYC document Approved successfully"
            status_category="SUCCESS"

        elif status_id == 4:
            msg =  "KYC document successfully On-Hold "
            mail_subject = f'''{mail_subject} On-Hold'''
            mail_data["mail_content"] = f'''Your KYC {docname} document is On-Hold'''
        elif status_id == 5:
            mail_subject = f'''{mail_subject} Rejected'''
            msg =  "KYC document successfully Rejected"
            mail_data["mail_content"] = f'''Your KYC {docname} document Rejected'''
            status_category="ERROR"
        else:
            db.rollback()
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.INVALID_SATUS_SELECTED, error=[], data={},code="INVALID_SATUS_SELECTED")
        background_tasks.add_task(Email.send_mail,recipient_email=[user_obj.email],subject=mail_subject,template='kyc_doc_status_updated.html',data=mail_data)
        print("TESTSTTS")
        user_notification = NotificationModel(user_id=user_id,tenant_id=user_obj.tenant_id,description=notification_msg,category="UPDATED_KYC_STATUS",ref_id=auth_user["id"],status_category=status_category)
        if description:
            comment = AgentKycDocsCommentsModel(merchant_kyc_doc_id=document_id,comment=description,commented_by=admin_id,commented_by_role_id=role_id)
            db.add(comment)
        db.add(user_notification)
        db.commit()
        user_data = Utility.model_to_dict(user_obj)
        socket_id = Utility.generate_websocket_id(user_data)
        await manager.send_message(socket_id,{"message":notification_msg,"category":"UPDATED_KYC_STATUS","path":"RELOAD_SETTINGS"})
        
        return Utility.json_response(status=SUCCESS, message=msg, error=[], data={},code="")


    except Exception as E:
        AppLogger.error(str(E))
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})


#kycDetailsRequest
@router.post("/get-agent-details", response_description="KYC details")
async def kyc_details(request:kycDetailsRequest,background_tasks: BackgroundTasks,auth_user=Depends(AuthHandler().auth_wrapper), db: Session = Depends(get_database_session)):
    try:
        user_id = auth_user["id"]
        if auth_user.get("role_id", -1) in [1,3]:
            user_id = request.user_id
        else:
            user_id = auth_user["id"]
        user_obj = db.query(AgentModel).filter(AgentModel.id == user_id).first()
        if user_obj is None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.USER_NOT_EXISTS, error=[], data={},code="INVALIED_TOKEN")
        elif user_obj.status_id == 1:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PENDING_PROFILE_COMPLATION, error=[], data={},code= "LOGOUT_ACCOUNT" if auth_user["role_id"]==2 else "PENDING_PROFILE_COMPLATION")
        if user_obj.status_id == 2:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PENDING_EMAIL_VERIFICATION, error=[], data={},code="LOGOUT_ACCOUNT" if auth_user["role_id"]==2 else "PENDING_EMAIL_VERIFICATION")
        elif user_obj.status_id == 4:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PROFILE_INACTIVE, error=[], data={},code="LOGOUT_ACCOUNT" if auth_user["role_id"]==2 else "PROFILE_INACTIVE")
        elif user_obj.status_id == 5:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PROFILE_DELETED, error=[], data={},code="LOGOUT_ACCOUNT" if auth_user["role_id"]==2 else "PROFILE_DELETED")
        user_details = Utility.model_to_dict(user_obj)
        user_kyc_details = db.query(AgentKycDetailsModel).filter(AgentKycDetailsModel.agent_id == user_id,AgentKycDetailsModel.id == user_details["kyc_details_id"]).first()
        if user_kyc_details is None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Kyc details are not found!", error=[], data={})
        
        kyc_details = Utility.model_to_dict(user_kyc_details)
        
        if "password" in user_details:
            del user_details["password"]
        if "token" in user_details:
            del user_details["token"]    
        if "otp" in user_details:
            del user_details["otp"]
        kyc_status_details = Utility.model_to_dict(user_obj.merchant_kyc_status_details)
        #kyc_details["user_details"]["user_id"] = user_details["id"]
        kyc_details["user_details"] = user_details 
        kyc_details["user_details"]["kyc_status_details"] = kyc_status_details
        #kyc_details["user_details"]["status_details"] = Utility.model_to_dict(user_obj.status_details)
        #kyc_details["user_details"]["role_details"] = Utility.model_to_dict(user_obj.role_details)
        kyc_details["user_details"]["kyc_details"] = Utility.model_to_dict(user_obj.kyc_details)
        #kyc_details["user_details"]["tenant_details"] = Utility.model_to_dict(user_obj.tenant_details)
        #kyc_details["user_details"]["country_details"] = Utility.model_to_dict(user_obj.country_details)
        kyc_details["user_details"]["kyc_documents"] =[]
        #now get kyc documents list
        db_docs = db.query(AgentKycDocsModel).filter(AgentKycDocsModel.agent_id==user_id).all()
        document_id_list = []
        for doument in db_docs:
            masterDocQuery = db.query(MdKycDocs).filter(MdKycDocs.id==doument.md_doc_id)
            if user_obj.tenant_id:
                masterDocQuery = masterDocQuery.filter(MdKycDocs.tenant_id ==user_obj.tenant_id)
            masterDoc = masterDocQuery.first()
            
            document_id_list.append(doument.id)
            db_doc = db.query(AgentKycDocsModel).filter(AgentKycDocsModel.agent_id==user_id,AgentKycDocsModel.id==doument.id).first()
            document_dict = Utility.model_to_dict(doument)
            if masterDoc is not None:
                document_dict["md_doc_description"] =masterDoc.description
                document_dict["md_doc_name"] =masterDoc.name
                document_dict["md_doc_required"] =masterDoc.required


            if db_doc is not None:
                document_dict["doc_status_details"] =Utility.model_to_dict(db_doc.status_details)

            kyc_details["user_details"]["kyc_documents"].append(document_dict)
        #get document comments
        kyc_details["user_details"]["kyc_document_comments"] =[]
        if len(document_id_list) > 0:
            all_comments = (db.query(AgentKycDocsCommentsModel)
                .filter(AgentKycDocsCommentsModel.agent_kyc_doc_id.in_(document_id_list))
                .order_by(desc(AgentKycDocsCommentsModel.id))
                .all())
            if all_comments:
                for comment in all_comments:
                    kyc_details["user_details"]["kyc_document_comments"].append(Utility.model_to_dict(comment))

        #NotificationModel(user_id=user_id,category="UPDATED_KYC_STATUS",ref_id=user_id)
        kyc_details["user_details"]["admin_kyc_status_comment"] =""
        nquery = db.query(NotificationModel).filter(NotificationModel.user_id == user_id,NotificationModel.category=="UPDATED_KYC_STATUS").order_by(desc("created_on")).first()
        if nquery is not None:
            kyc_details["user_details"]["admin_kyc_status_comment"] = Utility.model_to_dict(nquery)

        return Utility.json_response(status=SUCCESS, message="KYC retrived successfully", error=[], data=kyc_details["user_details"])
        
    except Exception as E:
        AppLogger.error(str(E))
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})
