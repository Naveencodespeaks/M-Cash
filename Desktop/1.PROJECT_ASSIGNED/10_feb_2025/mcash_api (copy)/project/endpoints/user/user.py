from datetime import datetime, timezone,timedelta
from datetime import datetime
from ...models.user_model import UserModel,UserKycDetailsModel,BeneficiaryModel
from ...models.master_data_models import MdUserRole,MdUserStatus,MdCountries

from . import APIRouter, Utility, SUCCESS, FAIL, EXCEPTION ,INTERNAL_ERROR,BAD_REQUEST,BUSINESS_LOGIG_ERROR, Depends, Session, get_database_session, AuthHandler
from ...schemas.user_schema import UpdatePassword,UserFilterRequest,GetUser,PaginatedUserResponse,PaginatedBeneficiaryResponse,BeneficiaryListReq,GetUserDetailsReq,UserListResponse, UpdateKycDetails,UpdateProfile,BeneficiaryRequest,BeneficiaryEdit, GetBeneficiaryDetails, ActivateBeneficiary,UpdateBeneficiaryStatus, ResendBeneficiaryOtp,BeneficiaryResponse
from ...schemas.user_schema import UpdateKycStatus
from ...models.user_model import NotificationModel
from ...schemas.user_schema import UpdateKycDocStatus, kycDetailsRequest
import re
from ...constant import messages as all_messages
from ...common.mail import Email
from sqlalchemy.sql import select, and_, or_, not_,func
from sqlalchemy.future import select
from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, func
from sqlalchemy.ext.asyncio import AsyncSession
from ...models.admin_configuration_model import tokensModel
from sqlalchemy import desc, asc
from typing import List
from fastapi import BackgroundTasks
from fastapi_pagination import Params,paginate 
from sqlalchemy.orm import  joinedload
from ...models.admin_user import AdminUser
from ...models.kyc_doc_model import UserKycDocsModel, KycDocsCommentsModel
from ...models.user_model import AdminNotificationModel,NotificationModel
from ...models.kyc_doc_model import MdKycDocs
from ...library.webSocketConnectionManager import manager


# APIRouter creates path operations for product module
router = APIRouter(
    prefix="/user",
    tags=["User"],
    responses={404: {"description": "Not found"}},
)

@router.post("/update-profile", response_description="Update Profile")
async def update_profile(request: UpdateProfile,auth_user=Depends(AuthHandler().auth_wrapper), db: Session = Depends(get_database_session)):
    try:
        
        user_id = auth_user["id"]
        first_name = request.first_name
        last_name = request.last_name
        date_of_birth = request.date_of_birth #Utility.convert_dtring_to_date(request.date_of_birth)
        mobile_no = request.mobile_no

        user_data = db.query(UserModel).filter(UserModel.id == user_id).first()
        if user_data is None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.USER_NOT_EXISTS, error=[], data={},code="INVALIED_TOKEN")
        if user_data.role_id !=2:
            
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.NO_PERMISSIONS, error=[], data={},code="LOGOUT_ACCOUNT")

        else:
            
            if user_data.status_id ==3:                
                user_data.first_name = first_name
                user_data.last_name = last_name
                user_data.name = f'''{first_name} {last_name}'''
                user_data.date_of_birth = date_of_birth
                user_data.mobile_no = mobile_no
                db.commit()
                db.flush(UserModel)
                res_data = {
                    "first_name":user_data.first_name,
                    "last_name":user_data.last_name,
                    "date_of_birth":user_data.date_of_birth,
                    "mobile_no":user_data.mobile_no,
                }

                return Utility.json_response(status=SUCCESS, message=all_messages.PROFILE_UPDATE_SUCCESS, error=[], data={},code="")
            elif  user_data.status_id == 1:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PENDING_PROFILE_COMPLATION, error=[], data={},code="LOGOUT_ACCOUNT")
            elif  user_data.status_id == 2:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PENDING_EMAIL_VERIFICATION, error=[], data={},code="LOGOUT_ACCOUNT")
            elif user_data.status_id == 4:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PROFILE_INACTIVE, error=[], data={},code="LOGOUT_ACCOUNT")
            elif user_data.status_id == 5:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PROFILE_DELETED, error=[], data={},code="LOGOUT_ACCOUNT")
            else:
                db.rollback()
                return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

    except Exception as E:
        print(E)
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

@router.post("/update-password", response_description="Update Password")
async def update_password(request: UpdatePassword,auth_user=Depends(AuthHandler().auth_wrapper), db: Session = Depends(get_database_session)):
    try:
        
        user_id = auth_user["id"]
        old_password = str(request.old_password)
        password =  request.password
        user_data = db.query(UserModel).filter(UserModel.id == user_id).first()
        if user_data is None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.USER_NOT_EXISTS, error=[], data={},code="USER_NOT_EXISTS")
        else:
            
            verify_password = AuthHandler().verify_password(str(old_password), user_data.password)
            if not verify_password:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.INVALIED_OLD_PASSWORD, error=[], data={})
            if user_data.status_id ==3:
                has_password = AuthHandler().get_password_hash(password)
                user_data.password = has_password
                db.commit()
                #db.flush(user_obj) ## Optionally, refresh the instance from the database to get the updated values
                  #Email.send_mail(recipient_email=[user_obj.email], subject="Reset Password OTP", template='',data=mail_data )
                return Utility.json_response(status=SUCCESS, message=all_messages.UPDATE_PASSWORD_SUCCESS, error=[], data={},code="")
            elif  user_data.status_id == 1:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PENDING_PROFILE_COMPLATION, error=[], data={},code="LOGOUT_ACCOUNT")
            elif  user_data.status_id == 2:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PENDING_EMAIL_VERIFICATION, error=[], data={},code="LOGOUT_ACCOUNT")
            elif user_data.status_id == 4:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PROFILE_INACTIVE, error=[], data={},code="LOGOUT_ACCOUNT")
            elif user_data.status_id == 5:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PROFILE_DELETED, error=[], data={},code="LOGOUT_ACCOUNT")
            else:
                db.rollback()
                return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

    except Exception as E:
        print(E)
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})


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

        if auth_user["role_id"] in [1,3]:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.NO_PERMISSIONS, error=[], data={},code="NO_PERMISSIONS")

        user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
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
        
        
        
        user_kyc_details = db.query(UserKycDetailsModel).filter(UserKycDetailsModel.user_id == user_id).first()
        user_obj.updated_on = datetime.now(timezone.utc)
        if user_kyc_details is None:
            details = UserKycDetailsModel(user_id=user_id,street =street,city=city, state=state,occupation_id=occupation_id,annual_income=annual_income,pincode=pincode,state_id = state_id,created_on = datetime.now(timezone.utc),updated_on = datetime.now(timezone.utc))
            
            #UserKycDocsModel
            user_kyc_docs =[]
            
            if len(documents)>0:
                for document in documents:
                    #md_doc_name
                    #md_doc_description 
                    #md_doc_required
                    

                    udoc = UserKycDocsModel(user_id=user_id, tenant_id=tenant_id, md_doc_id=document["md_doc_id"], name=document["name"], path=document["path"],content_type=document["content_type"],size=document["size"], status_id=2)
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
            user_kyc_details.occupation_id = occupation_id
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
                    db_doc = db.query(UserKycDocsModel).filter(UserKycDocsModel.md_doc_id == document["md_doc_id"],UserKycDocsModel.user_id==user_id).first()
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
                        udoc = UserKycDocsModel(user_id=user_id, tenant_id=tenant_id, md_doc_id=document["md_doc_id"], name=document["name"], path=document["path"],content_type=document["content_type"], size=document["size"],status_id=2)
                        
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
                        db_doc = db.query(UserKycDocsModel).filter(UserKycDocsModel.md_doc_id == document["md_doc_id"],UserKycDocsModel.user_id==user_id).first()
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
                        # else:
                        #     db_doc.status_id = 2        
                        
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
                db.flush(UserModel)
                if "tenant_admin_details" in auth_user:
                        socket_id = Utility.generate_websocket_id(auth_user["tenant_admin_details"])
                        await manager.send_message(socket_id,{"message":"","category":"UPDATED_USER_KYC_DOCUMENTS","path":"RELOAD_KYC_APPROVE_FORM_IN_ADMIN"})
                        background_tasks.add_task(manager.send_message,"superuser_1_1", {"message":"","category":"UPDATED_USER_KYC_DOCUMENTS","path":"RELOAD_KYC_APPROVE_FORM_IN_ADMIN"})
                    
                return Utility.json_response(status=SUCCESS, message=all_messages.USER_ADDED_KYC_DETAILS, error=[], data={},code="")
        
    except Exception as E:
        print(E)
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
        user_kyc_details = db.query(UserKycDetailsModel).filter(UserKycDetailsModel.user_id == user_id).first()
        if user_kyc_details is not None:
            user_kyc_details.updated_on = datetime.now(timezone.utc)
            
        if status_id<=2:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.INVALID_SATUS_SELECTED, error=[], data={},code="INVALID_SATUS_SELECTED")
        db_doc = db.query(UserKycDocsModel).filter(UserKycDocsModel.id == document_id,UserKycDocsModel.user_id==user_id, UserKycDocsModel.md_doc_id==md_doc_id).first()
        if db_doc is None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.KYC_DOCUMENT_NOT_EXISTS, error=[], data={},code="KYC_DOCUMENT_NOT_EXISTS")

        if db_doc.status_id == status_id:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.KYC_IS_SAME_STATUS, error=[], data={},code="KYC_IS_SAME_STATUS")
        db_doc.status_id = status_id
        db_doc.updated_on = datetime.now(timezone.utc)
        
        user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
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

        user_notification = NotificationModel(user_id=user_id,tenant_id=user_obj.tenant_id,description=notification_msg,category="UPDATED_KYC_STATUS",ref_id=auth_user["id"],status_category=status_category)
        if description:
            comment = KycDocsCommentsModel(user_doc_id=document_id,comment=description,commented_by=admin_id,commented_by_role_id=role_id)
            db.add(comment)
        db.add(user_notification)
        db.commit()
        user_data = Utility.model_to_dict(user_obj)
        socket_id = Utility.generate_websocket_id(user_data)
        await manager.send_message(socket_id,{"message":notification_msg,"category":"UPDATED_KYC_STATUS","path":"RELOAD_SETTINGS"})
        
        return Utility.json_response(status=SUCCESS, message=msg, error=[], data={},code="")


    except Exception as E:
        print(E)
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

#kycDetailsRequest
@router.post("/kyc-details", response_description="KYC details")
async def kyc_details(request:kycDetailsRequest,background_tasks: BackgroundTasks,auth_user=Depends(AuthHandler().auth_wrapper), db: Session = Depends(get_database_session)):
    try:
        user_id = auth_user["id"]
        if auth_user.get("role_id", -1) in [1,3]:
            user_id = request.user_id
        else:
            user_id = auth_user["id"]
        user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
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
        user_kyc_details = db.query(UserKycDetailsModel).filter(UserKycDetailsModel.user_id == user_id,UserKycDetailsModel.id == user_details["kyc_details_id"]).first()
        if user_kyc_details is None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Kyc details are not found!", error=[], data={})
        
        kyc_details = Utility.model_to_dict(user_kyc_details)
        
        if "password" in user_details:
            del user_details["password"]
        if "token" in user_details:
            del user_details["token"]    
        if "otp" in user_details:
            del user_details["otp"]
        kyc_status_details = Utility.model_to_dict(user_obj.kyc_status)
        #kyc_details["user_details"]["user_id"] = user_details["id"]
        kyc_details["user_details"] = user_details 
        kyc_details["user_details"]["kyc_status_details"] = kyc_status_details
        kyc_details["user_details"]["status_details"] = Utility.model_to_dict(user_obj.status_details)
        kyc_details["user_details"]["role_details"] = Utility.model_to_dict(user_obj.role_details)
        kyc_details["user_details"]["kyc_details"] = Utility.model_to_dict(user_obj.kyc_details)
        if user_kyc_details.occupation_details:
            kyc_details["user_details"]["kyc_details"]["occupation_details"] = Utility.model_to_dict(user_kyc_details.occupation_details)
        kyc_details["user_details"]["tenant_details"] = Utility.model_to_dict(user_obj.tenant_details)
        kyc_details["user_details"]["country_details"] = Utility.model_to_dict(user_obj.country_details)
        kyc_details["user_details"]["kyc_documents"] =[]
        #now get kyc documents list
        db_docs = db.query(UserKycDocsModel).filter(UserKycDocsModel.user_id==user_id).all()
        document_id_list = []
        for doument in db_docs:
            masterDocQuery = db.query(MdKycDocs).filter(MdKycDocs.id==doument.md_doc_id)
            if user_obj.tenant_id:
                masterDocQuery = masterDocQuery.filter(MdKycDocs.tenant_id ==user_obj.tenant_id)
            masterDoc = masterDocQuery.first()
            
            document_id_list.append(doument.id)
            db_doc = db.query(UserKycDocsModel).filter(UserKycDocsModel.user_id==user_id,UserKycDocsModel.id==doument.id).first()
            document_dict = Utility.model_to_dict(doument)
            if masterDoc is not None:
                document_dict["md_doc_description"] =masterDoc.description
                document_dict["md_doc_name"] =masterDoc.name
                document_dict["md_doc_required"] =masterDoc.required


            if db_doc is not None:
                document_dict["doc_status_details"] =Utility.model_to_dict(db_doc.doc_status_details)

            kyc_details["user_details"]["kyc_documents"].append(document_dict)
        #get document comments
        kyc_details["user_details"]["kyc_document_comments"] =[]
        if len(document_id_list) > 0:
            all_comments = (db.query(KycDocsCommentsModel)
                .filter(KycDocsCommentsModel.user_doc_id.in_(document_id_list))
                .order_by(desc(KycDocsCommentsModel.id))
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
        print(E)
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})


@router.post("/list", response_model=PaginatedUserResponse, response_description="Fetch Users List")
async def get_users(filter_data: UserFilterRequest,auth_user=Depends(AuthHandler().auth_wrapper),db: Session = Depends(get_database_session)):
    #user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
    #AuthHandler().user_validate(user_obj)
    if auth_user.get("role_id", -1) not in [1,3]:
        return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.NO_PERMISSIONS, error=[], data={},code="NO_PERMISSIONS")

    
    query = db.query(UserModel).options(
        joinedload(UserModel.tenant_details),
        joinedload(UserModel.role_details),
        joinedload(UserModel.status_details),
        joinedload(UserModel.country_details),
        #joinedload(UserModel.state_details),
        #joinedload(UserModel.location_details),
        joinedload(UserModel.kyc_status)
    )

    if filter_data.search_string:
        search = f"%{filter_data.search_string}%"
        query = query.filter(
            or_(
                UserModel.first_name.ilike(search),
                UserModel.last_name.ilike(search),
                UserModel.email.ilike(search),
                UserModel.mobile_no.ilike(search)
            )
        )
    if filter_data.tenant_id:
        query = query.filter(UserModel.tenant_id.in_(filter_data.tenant_id))
    if filter_data.role_ids is not None:
        if len(filter_data.role_ids)>0:
            query = query.filter(UserModel.role_id.in_(filter_data.role_ids))


    #if filter_data.role_id:
        #query = query.filter(UserModel.role_id == filter_data.role_id)
    if filter_data.status_ids:
        query = query.filter(UserModel.status_id.in_(filter_data.status_ids))
    if filter_data.country_id:
        query = query.filter(UserModel.country_id.in_(filter_data.country_id))
    if filter_data.kyc_status_id:
        query = query.filter(UserModel.kyc_status_id.in_(filter_data.kyc_status_id))
    # if filter_data.created_on and filter_data.created_to and ( isinstance(filter_data.created_on, date) and isinstance(filter_data.created_to, date)):
    #     query = query.filter(UserModel.created_on > filter_data.created_on)
    #     query = query.filter(UserModel.created_on < filter_data.created_to)
      
     # Total count of users matching the filters
    if filter_data.get_kyc_users:
        query = query.filter(UserModel.kyc_details_id>0)
        

    total_count = query.count()
    sort_column = getattr(UserModel, filter_data.sort_by, None)
    if sort_column:
        
        if filter_data.sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc("id"))

    # Apply pagination
    offset = (filter_data.page - 1) * filter_data.per_page
    paginated_query = query.offset(offset).limit(filter_data.per_page).all()
    # Create a paginated response
    return PaginatedUserResponse(
        total_count=total_count,
        list=paginated_query,
        page=filter_data.page,
        per_page=filter_data.per_page
    )


@router.post("/get-user", response_model=PaginatedUserResponse, response_description="Fetch Users List")
async def get_users(filter_data: GetUser,auth_user=Depends(AuthHandler().auth_wrapper),db: Session = Depends(get_database_session)):
    #user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
    #AuthHandler().user_validate(user_obj)
    try:
        tenant_id = None
        query = db.query(UserModel).options(
            joinedload(UserModel.tenant_details),
            joinedload(UserModel.role_details),
            joinedload(UserModel.status_details),
            joinedload(UserModel.country_details),
            #joinedload(UserModel.state_details),
            #joinedload(UserModel.location_details),
            joinedload(UserModel.kyc_status)
        ).filter(UserModel.kyc_status_id==3, UserModel.email==filter_data.email)

        if auth_user["role_id"] ==5:
            query = query.filter(UserModel.role_id !=5)


        tenant_id = auth_user.get("tenant_id", None)
        if filter_data.tenant_id:
            tenant_id = filter_data.tenant_id

        if tenant_id is not None:
            query = query.filter(UserModel.tenant_id == tenant_id)
        
        #if auth_user["role_id"] not in [1,3]:
        query = query.filter(UserModel.id != auth_user["id"] )
            
        result_set = query.first()   
        if result_set is not None:
            res_data = {}
            res_data["user_id"] =result_set.id
            res_data["name"] =result_set.name
            res_data["email"] =result_set.email
            res_data["mobile_no"] =result_set.mobile_no
            return Utility.json_response(status=SUCCESS, message="Success", error=[], data=res_data,code="BENEFICIARY_DETAILS")
        else:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.USER_NOT_EXISTS, error=[], data={},code="USER_NOT_EXISTS")
                
    except Exception as E:
        print(E)
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

     


@router.post("/get-user-details",response_model=UserListResponse, response_description="Get User Details")
async def get_benficiary( request: GetUserDetailsReq,auth_user=Depends(AuthHandler().auth_wrapper), db: Session = Depends(get_database_session)):
    try:
        
        user_id = auth_user["id"]
        if auth_user.get("role_id", -1) in [1,3]:
            user_id = request.user_id
        elif auth_user.get("role_id", -1) in [2]:
            user_id = auth_user["id"]
        if auth_user.get("role_id", -1) in [2] and user_id !=request.user_id:
            return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.NO_PERMISSIONS, error=[], data={})

        user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
        response_data = Utility.model_to_dict(user_obj)
        response_data["user_id"] = response_data["id"]
        response_data["tenant_details"] = Utility.model_to_dict(user_obj.tenant_details)
        response_data["role_details"] = Utility.model_to_dict(user_obj.role_details)
        response_data["status_details"] = Utility.model_to_dict(user_obj.status_details)
        response_data["country_details"] = Utility.model_to_dict(user_obj.country_details)
        response_data["kyc_status"] = Utility.model_to_dict(user_obj.kyc_status)
        if user_obj.kyc_details is not None:
            response_data["kyc_details"] = Utility.model_to_dict(user_obj.kyc_details)
        
        if "login_fail_count" in response_data:
            del response_data["login_fail_count"]
        if "password" in response_data:
            del response_data["password"]
        if "otp" in response_data:
            del response_data["otp"]
        if "login_attempt_date" in response_data:
            del response_data["login_attempt_date"]    
                
        return Utility.json_response(status=SUCCESS, message="User Details successfully retrieved", error=[], data=response_data,code="")

    except Exception as E:
        print(E)
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

#@router.post("/add-benficiary", response_description="Add Benficiary")
async def add_benficiary(request: BeneficiaryRequest, background_tasks: BackgroundTasks,auth_user=Depends(AuthHandler().auth_wrapper), db: Session = Depends(get_database_session)):
   
    try:
        
        user_id = auth_user["id"]
        full_name = request.full_name
        nick_name = request.nick_name
        mobile_no = request.mobile_no
        email = request.email
        country_id = request.country_id
        beneficiary_category_id = request.beneficiary_category_id
        city = request.city
        state_province = request.state_province
        postal_code = request.postal_code
        swift_code = request.swift_code
        iban = request.iban
        bank_name = request.bank_name
        bank_currency = request.bank_currency
        bank_country_id = request.bank_country_id
        bank_address = request.bank_address
        routing_number = request.routing_number
        use_routing_number = request.use_routing_number

        user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
        if user_obj is None:            
            return Utility.json_response(status=500, message=all_messages.USER_NOT_EXISTS, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.role_id !=2:            
            return Utility.json_response(status=500, message=all_messages.NO_PERMISSIONS, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 1:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PENDING_PROFILE_COMPLATION, error=[], data={},code="LOGOUT_ACCOUNT")
        
        elif user_obj.status_id == 2:
            return Utility.json_response(status=500, message=all_messages.PENDING_EMAIL_VERIFICATION, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 4:
            return Utility.json_response(status=500, message=all_messages.PROFILE_INACTIVE, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 5:
            return Utility.json_response(status=500, message=all_messages.PROFILE_DELETED, error=[], data={},code="LOGOUT_ACCOUNT")
        elif user_obj.kyc_status_id != 3:
            return Utility.json_response(status=500, message=all_messages.KYC_NOT_COMPLETED, error=[], data={},code="KYC_NOT_COMPLETED")
          
        exists_ben = db.query(BeneficiaryModel).filter(BeneficiaryModel.iban == iban,BeneficiaryModel.user_id==user_id).first()
        if exists_ben is not None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.BENEFICIARY_ALREADY_EXISTS, error=[], data={},code="BENEFICIARY_ALREADY_EXISTS")
        otp =Utility.generate_otp()
        
        details = BeneficiaryModel(user_id=user_id,
                                   beneficiary_category_id=beneficiary_category_id,
                                   full_name =full_name,
                                   nick_name = nick_name,
                                   mobile_no =mobile_no,
                                   email=email,
                                   city=city,
                                   country_id=country_id,
                                   state_province=state_province,
                                   postal_code=postal_code,
                                   swift_code=swift_code,
                                   use_routing_number =use_routing_number,
                                   routing_number =routing_number,
                                   iban=iban,
                                   bank_name=bank_name,
                                   bank_currency = bank_currency,
                                   bank_country_id=bank_country_id,
                                   bank_address=bank_address,
                                   status_id=1
                                   )
        db.add(details)
        db.commit()
        
        #db.flush()
        if details.id:
            mail_data = {"otp":str(otp),"name":user_obj.first_name +" "+user_obj.last_name,"beneficiary_name":full_name}
            background_tasks.add_task(
            Email.send_mail,
            recipient_email=[user_obj.email],
            subject="Beneficiary added successfully",
            template='beneficiary_beneficiary_added.html',
            data=mail_data
           )
            
            otpdata = { "ref_id":details.id,"catrgory":"BeneficiaryModel","otp":otp,"user_id":user_id,"token":'' }
            otpdata["token"] = AuthHandler().encode_token(otpdata,minutes=6)
            if Utility.inactive_previous_tokens(db=db, catrgory="BeneficiaryModel", user_id=user_id) is False:
               db.rollback()
               return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

            # if Utility.inactive_previous_tokens(db=db, catrgory="BeneficiaryModel", user_id=user_id) == False:
            #     db.rollback()
            #     return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

            token_data = tokensModel(ref_id=details.id,token=otpdata["token"],catrgory="BeneficiaryModel",user_id=user_id,otp=otp,active=True)
            db.add(token_data)
            db.commit()
            if token_data.id:
                return Utility.json_response(status=SUCCESS, message=all_messages.BENEFICIARY_OTP_SENT, error=[], data={"beneficiary_id":details.id},code="")
            else:
                db.rollback()
                return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})
       
        else:
            db.rollback()
            return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})
       
    except Exception as E:
        print(E)
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

#@router.post("/update-benficiary", response_description="Update Benficiary")
async def update_benficiary(request: BeneficiaryEdit,background_tasks: BackgroundTasks,auth_user=Depends(AuthHandler().auth_wrapper), db: Session = Depends(get_database_session)):
    try:
        beneficiary_id = request.beneficiary_id
        user_id = auth_user["id"]
        full_name = request.full_name
        nick_name=request.nick_name
        mobile_no = request.mobile_no
        email=request.email
        country_id = request.country_id
        city = request.city
        state_province = request.state_province
        postal_code = request.postal_code
        swift_code = request.swift_code
        iban = request.iban
        bank_name = request.bank_name
        bank_currency = request.bank_currency,
        bank_country_id = request.bank_country_id
        bank_address = request.bank_address
        routing_number = request.routing_number
        use_routing_number = request.use_routing_number
        
        user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
        if user_obj is None:            
            return Utility.json_response(status=500, message=all_messages.USER_NOT_EXISTS, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.role_id !=2:            
            return Utility.json_response(status=500, message=all_messages.NO_PERMISSIONS, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 1:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PENDING_PROFILE_COMPLATION, error=[], data={},code="LOGOUT_ACCOUNT")
        
        elif user_obj.status_id == 2:
            return Utility.json_response(status=500, message=all_messages.PENDING_EMAIL_VERIFICATION, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 4:
            return Utility.json_response(status=500, message=all_messages.PROFILE_INACTIVE, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 5:
            return Utility.json_response(status=500, message=all_messages.PROFILE_DELETED, error=[], data={},code="LOGOUT_ACCOUNT")
        elif user_obj.kyc_status_id != 3:
            return Utility.json_response(status=500, message=all_messages.KYC_NOT_COMPLETED, error=[], data={},code="KYC_NOT_COMPLETED")
        
        exists_ben = db.query(BeneficiaryModel).filter(BeneficiaryModel.id == beneficiary_id,BeneficiaryModel.user_id==user_id).first()
        if exists_ben is None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.BENEFICIARY_NOT_EXISTS, error=[], data={},code="BENEFICIARY_NOT_EXISTS")

        beneficiary = db.query(BeneficiaryModel).filter(BeneficiaryModel.id != beneficiary_id , BeneficiaryModel.iban == iban,BeneficiaryModel.user_id==user_id).first()
        if beneficiary is not None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.BENEFICIARY_ALREADY_EXISTS, error=[], data={},code="BENEFICIARY_ALREADY_EXISTS")
        otp =Utility.generate_otp()
        exists_ben.full_name =full_name
        exists_ben.nick_name=nick_name
        exists_ben.email= email
        exists_ben.mobile_no=mobile_no
        exists_ben.city=city
        exists_ben.country_id=country_id
        exists_ben.state_province=state_province
        exists_ben.postal_code=postal_code
        exists_ben.swift_code=swift_code
        exists_ben.routing_number=routing_number
        exists_ben.use_routing_number=use_routing_number
        
        exists_ben.iban=iban
        exists_ben.bank_name=bank_name
        exists_ben.bank_currency = bank_currency
        exists_ben.bank_country_id=bank_country_id
        exists_ben.bank_address=bank_address
        exists_ben.status_id = 1
        otpdata = { "ref_id":exists_ben.id,"catrgory":"BeneficiaryModel","otp":otp,"user_id":user_id,"token":'' }
        otpdata["token"] = AuthHandler().encode_token(otpdata,minutes=6)        
        token_data = tokensModel(ref_id=exists_ben.id,token=otpdata["token"],catrgory="BeneficiaryModel", user_id=user_id,otp=otp,active=True)
        db.add(token_data)
        db.commit()
        if token_data.id:
            mail_data = {"otp":str(otp),"name":user_obj.first_name +" "+user_obj.last_name,"beneficiary_name":exists_ben.full_name}
            background_tasks.add_task(Email.send_mail,recipient_email=[user_obj.email], subject=all_messages.BENEFICIARY_UPDATED_SUCCESS, template='beneficiary_beneficiary_update.html',data=mail_data )
            return Utility.json_response(status=SUCCESS, message=all_messages.BENEFICIARY_UPDATED_SUCCESS, error=[], data={"beneficiary_id":exists_ben.id},code="")
        else:
            db.rollback()
            return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})
    

    except Exception as E:
        print(E)
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

#@router.post("/benficiary-list", response_model=PaginatedBeneficiaryResponse, response_description="Fetch Benficiary List")
async def get_benficiary_list(filter_data: BeneficiaryListReq,auth_user=Depends(AuthHandler().auth_wrapper),db: Session = Depends(get_database_session)):
    user_id = auth_user["id"]
    user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
    if user_obj is None:            
            return Utility.json_response(status=500, message=all_messages.USER_NOT_EXISTS, error=[], data={},code="LOGOUT_ACCOUNT")            
    elif user_obj.role_id !=2:            
        return Utility.json_response(status=500, message=all_messages.NO_PERMISSIONS, error=[], data={},code="LOGOUT_ACCOUNT")            
    elif user_obj.status_id == 1:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PENDING_PROFILE_COMPLATION, error=[], data={},code="LOGOUT_ACCOUNT")
        
    elif user_obj.status_id == 2:
        return Utility.json_response(status=500, message=all_messages.PENDING_EMAIL_VERIFICATION, error=[], data={},code="LOGOUT_ACCOUNT")            
    elif user_obj.status_id == 4:
        return Utility.json_response(status=500, message=all_messages.PROFILE_INACTIVE, error=[], data={},code="LOGOUT_ACCOUNT")            
    elif user_obj.status_id == 5:
        return Utility.json_response(status=500, message=all_messages.PROFILE_DELETED, error=[], data={},code="LOGOUT_ACCOUNT")
        
    # if auth_user.get("role_id", -1)  in [1]:
    #     user_id  = filter_data.user_id
    #     #return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.NO_PERMISSIONS, error=[], data={},code="NO_PERMISSIONS")

    
    query = db.query(BeneficiaryModel).options(
        joinedload(BeneficiaryModel.status_details),
        joinedload(BeneficiaryModel.beneficiary_country_details),
        joinedload(BeneficiaryModel.beneficiary_country_details),
        joinedload(BeneficiaryModel.beneficiary_category_details),
        
        
    )
    query = query.filter(BeneficiaryModel.user_id==user_id)

    if filter_data.search_string:
        search = f"%{filter_data.search_string}%"
        query = query.filter(
            or_(
                BeneficiaryModel.full_name.ilike(search),
                BeneficiaryModel.nick_name.ilike(search),
                BeneficiaryModel.email.ilike(search),
                BeneficiaryModel.mobile_no.ilike(search),
                BeneficiaryModel.city.ilike(search),
                BeneficiaryModel.state_province.ilike(search),
                BeneficiaryModel.postal_code.ilike(search),
                BeneficiaryModel.swift_code.ilike(search),
                BeneficiaryModel.iban.ilike(search),
                BeneficiaryModel.bank_name.ilike(search),
                BeneficiaryModel.routing_number.ilike(search),
                
            )
        )
    if len(filter_data.status_ids)>0:
        query = query.filter(BeneficiaryModel.status_id.in_(filter_data.status_ids))

    else:
        query = query.filter(BeneficiaryModel.status_id.in_([2]))
    if filter_data.country_ids:
        query = query.filter(BeneficiaryModel.country_id.in_(filter_data.country_ids))
    if filter_data.bank_country_ids:
        query = query.filter(BeneficiaryModel.bank_country_id.in_(filter_data.bank_country_ids))
        
    
     # Total count of users matching the filters
    total_count = query.count()
    sort_column = getattr(BeneficiaryModel, filter_data.sort_by, None)
    if sort_column:
        if filter_data.sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc("id"))

    # Apply pagination
    offset = (filter_data.page - 1) * filter_data.per_page
    paginated_query = query.offset(offset).limit(filter_data.per_page).all()
    # Create a paginated response
    return PaginatedBeneficiaryResponse(
        total_count=total_count,
        list=paginated_query,
        page=filter_data.page,
        per_page=filter_data.per_page
    )

#@router.post("/get-beneficiary",response_description="Get Beneficiary Details")
async def get_benficiary( request: GetBeneficiaryDetails,background_tasks: BackgroundTasks,auth_user=Depends(AuthHandler().auth_wrapper), db: Session = Depends(get_database_session)):
    try:
        beneficiary_id = request.beneficiary_id
        user_id = auth_user["id"]
        user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
        if user_obj is None:            
            return Utility.json_response(status=500, message=all_messages.USER_NOT_EXISTS, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.role_id !=2:            
            return Utility.json_response(status=500, message=all_messages.NO_PERMISSIONS, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 1:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PENDING_PROFILE_COMPLATION, error=[], data={},code="LOGOUT_ACCOUNT")
        elif user_obj.status_id == 2:
            return Utility.json_response(status=500, message=all_messages.PENDING_EMAIL_VERIFICATION, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 4:
            return Utility.json_response(status=500, message=all_messages.PROFILE_INACTIVE, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 5:
            return Utility.json_response(status=500, message=all_messages.PROFILE_DELETED, error=[], data={},code="LOGOUT_ACCOUNT")
         
        exists_ben = db.query(BeneficiaryModel).filter(BeneficiaryModel.id == beneficiary_id,BeneficiaryModel.user_id==user_id).first()
        if exists_ben is None:            
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.BENEFICIARY_NOT_EXISTS, error=[], data={},code="BENEFICIARY_NOT_EXISTS")
        else:
            response_data = Utility.model_to_dict(exists_ben)
            response_data["beneficiary_id"] = response_data["id"]
            response_data["beneficiary_country_details"] = Utility.model_to_dict(exists_ben.beneficiary_country_details)
            response_data["beneficiary_bank_country_details"] = Utility.model_to_dict(exists_ben.beneficiary_bank_country_details)
            response_data["status_details"] = Utility.model_to_dict(exists_ben.status_details)
            if exists_ben.beneficiary_category_details:
                response_data["beneficiary_category_details"] = Utility.model_to_dict(exists_ben.beneficiary_category_details)
            return Utility.json_response(status=SUCCESS, message="Beneficiary Details", error=[], data=response_data,code="")

    except Exception as E:
        print(E)
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

#@router.post("/activate-benficiary", response_description="Activate Benficiary ")
async def activate_benficiary_status(request: ActivateBeneficiary,background_tasks: BackgroundTasks,auth_user=Depends(AuthHandler().auth_wrapper), db: Session = Depends(get_database_session)):
    try:
        beneficiary_id = request.beneficiary_id
        user_id = auth_user["id"]
        otp = request.otp
        
        user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
        if user_obj is None:            
            return Utility.json_response(status=500, message=all_messages.USER_NOT_EXISTS, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.role_id !=2:            
            return Utility.json_response(status=500, message=all_messages.NO_PERMISSIONS, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 1:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PENDING_PROFILE_COMPLATION, error=[], data={},code="LOGOUT_ACCOUNT")
        elif user_obj.status_id == 2:
            return Utility.json_response(status=500, message=all_messages.PENDING_EMAIL_VERIFICATION, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 4:
            return Utility.json_response(status=500, message=all_messages.PROFILE_INACTIVE, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 5:
            return Utility.json_response(status=500, message=all_messages.PROFILE_DELETED, error=[], data={},code="LOGOUT_ACCOUNT")
         
        exists_ben = db.query(BeneficiaryModel).filter(BeneficiaryModel.id == beneficiary_id,BeneficiaryModel.user_id==user_id).first()
        if exists_ben is None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.BENEFICIARY_NOT_EXISTS, error=[], data={},code="BENEFICIARY_NOT_EXISTS")
        
        
        token_query = db.query(tokensModel).filter(tokensModel.catrgory =="BeneficiaryModel", tokensModel.user_id==user_id, tokensModel.otp == otp,tokensModel.active==True).first()
        if token_query is None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.INVALIED_OTP, error=[], data={},code="")
        else:
            token_data = AuthHandler().decode_otp_token(token_query.token)
            
            if str(token_data["otp"]) == str(otp):
                exists_ben.status_id = 2
                token_query.active = False
                db.commit()
                status_msg = "Added"
                msg = f"Beneficiary {status_msg} successfully"
                mail_data = {"user_name":user_obj.name,"message":f'''{exists_ben.full_name} has been Added successfully!'''}
                background_tasks.add_task(Email.send_mail, recipient_email=[user_obj.email], subject="Beneficiary Added", template='beneficiary_status_changed.html',data=mail_data )
        
                return Utility.json_response(status=SUCCESS, message=msg, error=[], data={"beneficiary_id":exists_ben.id},code="")
            else:
                
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.INVALIED_OTP, error=[], data={},code="")
        
    except Exception as E:
        print(E)
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

#@router.post("/update-benficiary-status", response_description="Update Benficiary Status")
async def update_benficiary_status(request: UpdateBeneficiaryStatus,background_tasks: BackgroundTasks,auth_user=Depends(AuthHandler().auth_wrapper), db: Session = Depends(get_database_session)):
    try:
        beneficiary_id = request.beneficiary_id
        user_id = auth_user["id"]
        status_id = request.status_id
        #otp = request.otp
        if status_id<=2:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.INVALID_SATUS_SELECTED, error=[], data={},code="INVALID_SATUS_SELECTED")
        
        user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
        if user_obj is None:            
            return Utility.json_response(status=500, message=all_messages.USER_NOT_EXISTS, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.role_id !=2:            
            return Utility.json_response(status=500, message=all_messages.NO_PERMISSIONS, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 1:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.PENDING_PROFILE_COMPLATION, error=[], data={},code="LOGOUT_ACCOUNT")
        
        elif user_obj.status_id == 2:
            return Utility.json_response(status=500, message=all_messages.PENDING_EMAIL_VERIFICATION, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 4:
            return Utility.json_response(status=500, message=all_messages.PROFILE_INACTIVE, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 5:
            return Utility.json_response(status=500, message=all_messages.PROFILE_DELETED, error=[], data={},code="LOGOUT_ACCOUNT")
         
        exists_ben = db.query(BeneficiaryModel).filter(BeneficiaryModel.id == beneficiary_id,BeneficiaryModel.user_id==user_id).first()
        if exists_ben is None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.BENEFICIARY_NOT_EXISTS, error=[], data={},code="BENEFICIARY_NOT_EXISTS")
        
        if exists_ben.status_id == status_id:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.BENEFICIARY_IS_SAME_STATUS, error=[], data={},code="BENEFICIARY_IS_SAME_STATUS")
        
        # token_query = db.query(tokensModel).filter(tokensModel.catrgory =="BeneficiaryModel", tokensModel.user_id==user_id, tokensModel.otp == otp,tokensModel.active==True).first()
        # if token_query is None:
        #     return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.INVALIED_OTP, error=[], data={},code="")
        
        exists_ben.status_id = status_id
        #token_query.active = False
        db.commit()
        mail_data = {"user_name":user_obj.name,"message":f'''{exists_ben.full_name} has been updated successfully!'''}
        status_msg = "updated"
        if status_id==2:
            status_msg ="Activated"
            
        if status_id==3:
            status_msg ="Deleted"

        mail_data["message"] = f'''{exists_ben.full_name} has been {status_msg} successfully!'''

        background_tasks.add_task(Email.send_mail, recipient_email=[user_obj.email], subject=f'''Beneficiary {status_msg}''', template='beneficiary_status_changed.html',data=mail_data )
        msg = f"Beneficiary {status_msg} successfully"
        return Utility.json_response(status=SUCCESS, message=msg, error=[], data={"beneficiary_id":exists_ben.id},code="")
    
    except Exception as E:
        print(E)
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})


#@router.post("/resend-benficiary-otp", response_description="Generate new otp")
async def send_benficiary_otp(request: ResendBeneficiaryOtp,background_tasks: BackgroundTasks,auth_user=Depends(AuthHandler().auth_wrapper), db: Session = Depends(get_database_session)):
    try:
        beneficiary_id = request.beneficiary_id
        user_id = auth_user["id"]
        user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
        if user_obj is None:            
            return Utility.json_response(status=500, message=all_messages.USER_NOT_EXISTS, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.role_id !=2:            
            return Utility.json_response(status=500, message=all_messages.NO_PERMISSIONS, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 1:
                return Utility.json_response(status=500, message=all_messages.PENDING_PROFILE_COMPLATION, error=[], data={},code="LOGOUT_ACCOUNT")
        
        elif user_obj.status_id == 2:
            return Utility.json_response(status=500, message=all_messages.PENDING_EMAIL_VERIFICATION, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 4:
            return Utility.json_response(status=500, message=all_messages.PROFILE_INACTIVE, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 5:
            return Utility.json_response(status=500, message=all_messages.PROFILE_DELETED, error=[], data={},code="LOGOUT_ACCOUNT")
        elif user_obj.kyc_status_id != 3:
            return Utility.json_response(status=500, message=all_messages.KYC_NOT_COMPLETED, error=[], data={},code="KYC_NOT_COMPLETED")
         
        otp =Utility.generate_otp()
        mail_data = {"otp":str(otp),"name":user_obj.first_name +" "+user_obj.last_name}
        background_tasks.add_task(Email.send_mail,recipient_email=[user_obj.email], subject=all_messages.PENDING_EMAIL_VERIFICATION_OTP_SUBJ, template='beneficiary_verification_otp.html',data=mail_data )
        otpdata = { "ref_id":beneficiary_id,"catrgory":"BeneficiaryModel","otp":otp,"user_id":user_id,"token":'' }
        otpdata["token"] = AuthHandler().encode_token(otpdata,minutes=6)
        if Utility.inactive_previous_tokens(db=db, catrgory="BeneficiaryModel", user_id=user_id) == False:
                db.rollback()
                return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})
        token_data = tokensModel(ref_id=beneficiary_id,token=otpdata["token"],catrgory="BeneficiaryModel",user_id=user_id,otp=otp)
        db.add(token_data)
        db.commit()
        if token_data.id:
            return Utility.json_response(status=SUCCESS, message=all_messages.RESEND_VERIFICATION_OTP, error=[], data={"beneficiary_id":beneficiary_id},code="")
        else:
            db.rollback()
            return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})
    
        
    except Exception as E:
        print(E)
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})



@router.post("/update-kyc-status", response_description="Update User Kyc Status")
async def update_kyc_status(
    request: UpdateKycStatus,
    background_tasks: BackgroundTasks,
    admin_user=Depends(AuthHandler().auth_wrapper),
    db: Session = Depends(get_database_session)
):
    user_kyc_docs = []  # Initialize the variable
    try:
        user_id = request.user_id  # Assuming you are passing a single user_id
        admin_id = admin_user["id"]
        kyc_status_id = request.kyc_status_id
        description = request.description
        
        if kyc_status_id <= 1:
            return Utility.json_response(
                status=BUSINESS_LOGIG_ERROR,
                message=all_messages.INVALID_STATUS_SELECTED,
                error=[],
                data={},
                code="INVALID_STATUS_SELECTED"
            )
        
        if admin_user["role_id"] not in [1,3]:
            
            return Utility.json_response(
                status=BUSINESS_LOGIG_ERROR,
                message=all_messages.NO_PERMISSIONS,
                error=[],
                data={},
                code="LOGOUT_ACCOUNT"
            )

        # ADMIN user validation
        admin_details = db.query(AdminUser).filter(AdminUser.id == admin_id).first()
        if admin_details is None:            
            return Utility.json_response(status=500, message=all_messages.USER_NOT_EXISTS, error=[], data={}, code="LOGOUT_ACCOUNT")            
        elif admin_details.status_id == 1:            
            return Utility.json_response(status=500, message=all_messages.NO_PERMISSIONS, error=[], data={}, code="LOGOUT_ACCOUNT")            
        elif admin_details.status_id == 2:
            return Utility.json_response(status=500, message=all_messages.PENDING_EMAIL_VERIFICATION, error=[], data={}, code="LOGOUT_ACCOUNT")            
        elif admin_details.status_id == 4:
            return Utility.json_response(status=500, message=all_messages.PROFILE_INACTIVE, error=[], data={}, code="LOGOUT_ACCOUNT")            
        elif admin_details.status_id == 5:
            return Utility.json_response(status=500, message=all_messages.PROFILE_DELETED, error=[], data={}, code="LOGOUT_ACCOUNT")

        
        
         # Check user KYC docs status
        total_uploadeddocs = db.query(func.count(UserKycDocsModel.id)).filter(UserKycDocsModel.user_id == user_id).count()
        if total_uploadeddocs<=0:
            return Utility.json_response(status=500, message=all_messages.KYC_DOCUMENTS_NOT_UPLOADED,error=[], data={},code="KYC_DOCUMENTS_NOT_UPLOADED")
        approved_docs = db.query(func.count(UserKycDocsModel.id)).filter(UserKycDocsModel.user_id == user_id, UserKycDocsModel.status_id == 3).count()
        # print(status_3_docs)
        # print(total_docs)
        # Check the conditionss
        if total_uploadeddocs != approved_docs :
         return Utility.json_response(
        status=500,
        message=all_messages.KYC_STATUS_UPDATE_NOT_ALLOWED,
        error=[],
        data={},
        code="KYC_STATUS_UPDATE_NOT_ALLOWED"
    )


        user_kyc_details = db.query(UserKycDetailsModel).filter(UserKycDetailsModel.user_id == user_id).first()
        if user_kyc_details is not None:
            user_kyc_details.updated_on = datetime.now(timezone.utc)

        user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
        if user_obj is None:            
            return Utility.json_response(status=500, message=all_messages.USER_NOT_EXISTS, error=[], data={}, code="USER_NOT_EXISTS")            
        elif user_obj.status_id != 3:
            return Utility.json_response(status=500, message=all_messages.PENDING_EMAIL_VERIFICATION, error=[], data={}, code="LOGOUT_ACCOUNT")            
        
        if user_obj.kyc_status_id == kyc_status_id:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.KYC_IS_SAME_STATUS, error=[], data={}, code="BENEFICIARY_IS_SAME_STATUS")
        
        # Update KYC status
        user_obj.kyc_status_id = kyc_status_id
        notification_msg = description
        
        if kyc_status_id == 2:                
            msg = "User KYC on hold successfully"
        elif kyc_status_id == 3:                
            msg = "User KYC Approved successfully"
            notification_msg = "Congratulations! Your KYC has been successfully approved."
        elif kyc_status_id == 4:                
            msg = "User KYC Rejected successfully"

        #status category
        if kyc_status_id == 3:
            status_category = "SUCCESS"
        elif kyc_status_id == 5:
            status_category = "ERROR"


        user_notification = NotificationModel(
            user_id=user_id,
            description=notification_msg,
            category="UPDATED_KYC_STATUS",
            ref_id=user_id,
            status_category=status_category
            
        )
        db.add(user_notification)
        db.commit()

        # Prepare email details
        if kyc_status_id == 2:
            message = "KYC has been put On-Hold"
            template_body = 'user_kyc_status_onhold.html'
            sub = "Your KYC has been put On-Hold"
        elif kyc_status_id == 3:
            message = "Your KYC has been Approved successfully"
            template_body = 'user_kyc_status_approved.html'
            sub = "Your KYC details have been Approved"
        elif kyc_status_id == 4:
            message = "Your KYC has been Rejected"
            template_body = 'user_kyc_status_rejection.html'
            sub = "Your KYC details have Been Rejected."

        mail_data = {
            "name": user_obj.first_name + " " + user_obj.last_name,
            "description": description,
            "message": message
        }

        background_tasks.add_task(
            Email.send_mail,
            recipient_email=[user_obj.email],
            subject=sub,
            template=template_body,
            data=mail_data
        )

        user_data = Utility.model_to_dict(user_obj)
        socket_id = Utility.generate_websocket_id(user_data)
        await manager.send_message(socket_id, {
            "message": notification_msg,
            "category": "UPDATED_KYC_STATUS",
            "path": "RELOAD_SETTINGS"
        })
        
        return Utility.json_response(status=SUCCESS, message=msg, error=[], data={"user_id": user_obj.id}, code="")
    
    except Exception as e:
        print(e)
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})




# {
  
#   "page": 1,
#   "per_page": 25,
 
#   "sort_by": "created_on",
#   "sort_order": "desc"
  
# }

