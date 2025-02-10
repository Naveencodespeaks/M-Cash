from datetime import datetime, timezone
from sqlalchemy import and_
from datetime import datetime
from ...models.admin_user import AdminUser
from sqlalchemy.orm import  joinedload
from datetime import date
from fastapi.encoders import jsonable_encoder
from fastapi import Request
from . import APIRouter, Utility, SUCCESS, FAIL, EXCEPTION ,INTERNAL_ERROR,BAD_REQUEST,BUSINESS_LOGIG_ERROR, Depends, Session, get_database_session, AuthHandler
from ...schemas.master_data import DownloadFile
import re
from ...schemas.master_data import getMasterData,CalculateCurrency,KycDocsListReq,Kycenable,CreateKycSchema,kycDocDetailsReqSchema,EditKycSchema
from ...models.user_model import TenantModel
import os
from ...models.user_model import UserModel
from sqlalchemy.sql import select, and_, or_, not_,func
import json
from pathlib import Path
from ...models.master_data_models import  MdBeneficiaryStatus,MdOtpConfigarations,MdCountries,MdLocations,MdReminderStatus,MdStates,MdTaskStatus,MdTenantStatus,MdTimeZone,MdUserRole,MdUserStatus,MdKycstatus,MdOccupations
from sqlalchemy import desc, asc
from ...models.kyc_doc_model import MdUserKycDocsStatus, MdKycDocs
from ...models.master_data_models import MdBeneficiaryCategoryesModel,MdchargeCategoryesModel, TransactionPurposeModel,TransactionSubPurpose,MdServiceTypes
from ...models.transaction import ChargesModel
# APIRouter creates path operations for product module
from ...constant.messages import MASTER_DATA_LIST
from ...models.admin_user import AdminUser
from ...models.master_data_models import TransactionStatusModel,MdKycDocPermissions
from ...models.user_model import NotificationModel
from sqlalchemy import delete
from ...common.mail import Email
from fastapi import FastAPI, File, UploadFile,BackgroundTasks
from ...constant import messages as all_messages
from ...library.mfiles import login_user_for_mfiles,get_currency,save_file_in_mfiles,download_files_from_mfiles_to_desired_folder
from fastapi import WebSocket, WebSocketDisconnect
from ...library.webSocketConnectionManager import manager
from ...models.master_data_models import MdCurrencyTypes, MdCurrency,MdFundsRequestStatus
from ...aploger import AppLogger

router = APIRouter(
    prefix="/masterdata",
    tags=["Master Data"],
    responses={404: {"description": "Not found"}},
)
file_to_model = {
            "md_charge_categoryes.json":MdchargeCategoryesModel,
            "md_countries.json": MdCountries,
            "md_states.json": MdStates,
            "md_locations.json": MdLocations,
            "md_reminder_status.json": MdReminderStatus,
            "md_task_status.json": MdTaskStatus,
            "md_tenant_status.json": MdTenantStatus,
            "md_timezone.json": MdTimeZone,
            "md_user_roles.json": MdUserRole,
            "md_user_status.json": MdUserStatus,
            "md_kyc_status.json" :MdKycstatus,
            "md_occupations.json":MdOccupations,
            "md_otp_configaration.json":MdOtpConfigarations,
            "md_beneficiary_status.json":MdBeneficiaryStatus,
            "md_tanants.json":TenantModel,
            
            #"md_kyc_docs.json":MdKycDocs,
           "md_user_kyc_docs_status.json": MdUserKycDocsStatus,
           "md_beneficiary_categoryes.json":MdBeneficiaryCategoryesModel,
           "transaction_purpose_model.json":TransactionPurposeModel,
           "transaction_status.json":TransactionStatusModel,
           "md_service_types.json":MdServiceTypes,
           "md_currency_types.json":MdCurrencyTypes,
           "md_funds_request_status.json": MdFundsRequestStatus,
             
           
           

        }
related_tables ={
   
    "transaction_sub_purpose.json":TransactionSubPurpose,
    "default_admin.json":AdminUser,
    }
super_related_tables ={
    "md_kyc_docs.json":MdKycDocs,
     "md_default_charges.json":ChargesModel,
     "md_currencies.json": MdCurrency     
}


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token:str):
    user_data = AuthHandler().verify_ws_token(token)
    if user_data is None or "id" not in user_data:
        return
    else:
        
        socket_id = Utility.generate_websocket_id(user_data)
        print(socket_id)
        await manager.connect(socket_id, websocket)
        try:
            while True:
                await websocket.receive_text()  # Keep connection open
        except WebSocketDisconnect:           
            manager.disconnect(socket_id)

@router.get("/test", response_description="Test Socket")
async def test_socket(auth_user=Depends(AuthHandler().auth_wrapper),db: Session = Depends(get_database_session)):
    socket_id = Utility.generate_websocket_id(auth_user)
    await manager.send_message(socket_id,{"message":"HI first Message","category":"`REDIRECT` or GET_UPDATED_DATA","path":"SETTINGS"})
    return "Success"

       
 
@router.get("/migrate", response_description="Migrate Master Data")
def get_users(db: Session = Depends(get_database_session)):
       
    try:
            
            #return {"status": "FAIL", "message": "Data migrated successfully"}
        def insertBulkData(file_to_model):    
            json_directory = Path(__file__).resolve().parent.parent.parent / "master_data"
            batch_size = 500
            for filename in os.listdir(json_directory):
                
                if filename in file_to_model:
                    model = file_to_model[filename]
                    file_path = json_directory / filename
                    with open(file_path, 'r') as file:
                        data = json.load(file)

                    batch = []
                    for entry in data:
                        # Filter out any keys not matching the model's attributes
                        filtered_entry = {key: value for key, value in entry.items() if hasattr(model, key)}
                        if(filename=="md_countries.json"):
                                            
                            if "zipcodeLength" in filtered_entry and (filtered_entry.get("zipcodeLength",10)):
                                filtered_entry["zipcodeLength"] = int(filtered_entry["zipcodeLength"])
                            else:
                                filtered_entry["zipcodeLength"] = 10

                        
                        record = model(**filtered_entry)
                        batch.append(record)

                        if len(batch) >= batch_size:
                            db.bulk_save_objects(batch)
                            batch.clear()

                    if batch:
                        db.bulk_save_objects(batch)

                    db.commit()
        #insert Main data
        insertBulkData(file_to_model)
        insertBulkData(related_tables)
        insertBulkData(super_related_tables)

        return {"status": "SUCCESS", "message": "Data migrated successfully"}
    except Exception as e:
        AppLogger.error(str(e))        
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=str(e), error=[], data=[])


@router.post("/get-master-data", response_description="Migrate Master Data")
def get_users(request: getMasterData ,db: Session = Depends(get_database_session)):
       
    try:
        categories = request.categories
        country_id = None
        state_id = None
        if request.country_id:
            country_id = request.country_id
        if request.state_id :
            state_id = request.state_id    

        
        output ={}
        
        for category in categories:
            if category+".json" in file_to_model:
                model = file_to_model[category+".json"]
                if category=="md_states" and country_id:
                    query = db.query(model).filter(model.countryId==int(country_id))
                    sort_column = getattr(model, "name", None)
                    if sort_column:
                        query = query.order_by(asc(sort_column))
                    else:
                        query = query.order_by(asc("id"))    
                    records = query.all()  
                    output[category] =  [Utility.model_to_dict(record) for record in records]
                elif category=="md_locations" and state_id:
                    query = db.query(model).filter(model.stateId==int(state_id))
                    sort_column = getattr(model, "name", None)
                    if sort_column:
                        query = query.order_by(asc(sort_column))
                    else:
                        query = query.order_by(asc("id"))    
                    records =  query.all()
                    output[category] =  [Utility.model_to_dict(record) for record in records]
                elif category=="transaction_purpose_model":
                    records = db.query(model).order_by(asc("id")) .all()
                    output[category] =  [Utility.model_to_dict(record) for record in records]
                elif category=="md_service_types":
                    records = db.query(model).order_by(asc("id")) .all()
                    output[category] =  [Utility.model_to_dict(record) for record in records]
                
                else:    
                    query = db.query(model)
                    sort_column = getattr(model, "name", None)
                    if sort_column:
                        query = query.order_by(asc(sort_column))
                    else:
                        query = query.order_by(asc("id"))

                    records  = query.all()    
                    output[category] =  [Utility.model_to_dict(record) for record in records]

        return Utility.json_response(status=SUCCESS, message=MASTER_DATA_LIST, error=[], data=output)
    except Exception as e:
        AppLogger.error(str(e))        
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data=[])



@router.post("/kyc-docs-list", response_description="KYC en_dis list")
def get_kyc_docs(request: KycDocsListReq, auth_user=Depends(AuthHandler().auth_wrapper),db: Session = Depends(get_database_session)):
    try:
        user_id = auth_user["id"]
        tenant_id =1
        if "tenant_id" in auth_user:
            tenant_id =auth_user["tenant_id"]
        if auth_user["role_id"] in [1]:
            tenant_id = 1
        status = request.status
        query = db.query(MdKycDocs).filter(MdKycDocs.tenant_id==tenant_id)
         
        if status == False:
            query = query.filter(MdKycDocs.status==False)
        elif status == True:
            query = query.filter(MdKycDocs.status==True)

        total_count = query.count()
        sort_column = getattr(MdKycDocs, request.sort_by, None)
        if sort_column:
            if request.sort_order == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc("id"))

        # Apply pagination MdKycDocPermissions(user_id=use_id,md_doc_id=new_doc.id,tenant_id=tenant_id)
        offset = (request.page - 1) * request.per_page
        paginated_query = query.offset(offset).limit(request.per_page).all()
        if auth_user["role_id"] in [2]:
             paginated_query = query.filter(MdKycDocs.status==True,MdKycDocs.tenant_id==tenant_id).order_by(desc("id")).all()

        res_data ={ "total_count": total_count,"list":[],"page":request.page,"per_page":request.per_page}
        for item in paginated_query:
            item_dict = Utility.model_to_dict(item)
            if item.tenant_id:
                item_dict["tenant_details"] =  Utility.model_to_dict(item.tenant_details)
            if auth_user["role_id"] in [2]:
                if item.share_type =="SPECIFIC_USERS":
                    qr =  db.query(MdKycDocPermissions).filter(MdKycDocPermissions.md_doc_id==item.id,MdKycDocPermissions.user_id==user_id,MdKycDocPermissions.tenant_id==tenant_id).first()
                    if qr is not None:
                        res_data["list"].append(item_dict)
                if item.share_type =="UPCOMMING_USERS":
                    #user created date and  kyc document created date
                    #if effective_date.date() >= datetime.now(timezone.utc).date():
                    user_obj =db.query(UserModel).filter(UserModel.id==user_id,UserModel.status_id==3).first()
                    if user_obj is not None:
                        if user_obj.created_on.date()>=item.created_on.date():
                            res_data["list"].append(item_dict)

                    pass
                if item.share_type =="ALL_USERS":
                    res_data["list"].append(item_dict)
                
            else:
               res_data["list"].append(item_dict)

        
        return Utility.json_response(status=SUCCESS, message="", error=[], data=res_data)

    except Exception as e:
        AppLogger.error(str(e))
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data=[])
              
@router.post("/update-kyc-doc-status", response_description="Update status")
def get_users(request: Kycenable,auth_user=Depends(AuthHandler().auth_wrapper), db: Session = Depends(get_database_session)):
    try:
        status = request.status  
        id = request.id
        tenant_id =1
        if "tenant_id" in auth_user:
            tenant_id =auth_user["tenant_id"]
        if auth_user["role_id"] in [1]:
            tenant_id = 1

        kyc_doc = db.query(MdKycDocs).filter(MdKycDocs.id == id,tenant_id==tenant_id).first()
        if not kyc_doc:
            return Utility.json_response(status=FAIL, message="KYC document not found", error=["Invalid ID"], data={})
        if status == False:
            kyc_doc.status = 0  # Disable the KYC document
        elif status == True:
            kyc_doc.status = 1  # Enable the KYC document
        else:
            return Utility.json_response(status=FAIL, message="Invalid status value", error=["Status should be 0 or 1"], data={})
        
        db.commit()
        return Utility.json_response(status=SUCCESS, message="KYC document status updated", error=[], data={"id": id, "status": kyc_doc.status})



    except Exception as e:
        AppLogger.error(str(e))
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data=[])

@router.post("/create-kyc-doc", response_description="Create doc")
def create_doc(request: CreateKycSchema,background_tasks: BackgroundTasks,auth_user=Depends(AuthHandler().auth_wrapper), db: Session = Depends(get_database_session)):
    try:
        
        user_id = auth_user["id"]
        tenant_id =1

        if "tenant_id" in auth_user:
            tenant_id =auth_user["tenant_id"]
        # role_id = auth_user["role_id"]
        # user_obj=auth_user['user_name']
        # user_email=auth_user["email"]
        if auth_user["role_id"] not in [1]:
             return Utility.json_response(status=BUSINESS_LOGIG_ERROR,message=all_messages.NO_PERMISSIONS,error=all_messages.NO_PERMISSIONS, data={})
        if auth_user["role_id"] in [1]:
            tenant_id = 1

        cleaned_name = ' '.join(request.name.strip().split()).lower()

     
        existing_doc = db.query(MdKycDocs).filter(func.lower(MdKycDocs.name) == cleaned_name, MdKycDocs.category==request.category).first()

        if existing_doc is not None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR,message="Document with this name already exists",error=[], data={"doc_id": existing_doc.id})
        
        new_doc = MdKycDocs(
            category=request.category,
            name=cleaned_name,  
            status=request.status,
            required=request.required,
            #doc_type=request.doc_type,
            #size=int(request.size),
            description=request.description,
            #users_list=users_list_str,
            share_type=request.share_type,
            tenant_id= tenant_id
        )
        
        
        db.add(new_doc)
        db.commit()
        batch =[]
        
        #db.bulk_save_objects(batch)
        
        notifications = []
        user_emails = []
        user_websocket_ids =[]
        if new_doc.id:
            if request.share_type =="ALL_USERS":
                for user in db.query(UserModel).filter(UserModel.status_id==3,UserModel.tenant_id==tenant_id,UserModel.kyc_status_id>=1).all():
                    user_data = Utility.model_to_dict(user)
                    #print(user_data)
                    socket_id = Utility.generate_websocket_id(user_data)
                    if socket_id in manager.active_connections:
                        user_websocket_ids.append(socket_id)
                    user_emails.append(user.email)
                    batch.append(MdKycDocPermissions(user_id=user_data["id"],md_doc_id=new_doc.id,tenant_id=tenant_id))
                    notifications.append(NotificationModel(user_id=user_data["id"],description=request.description,category="REQUIRED_NEW_KYC_DOC",ref_id=user_id,tenant_id=tenant_id))
                if len(batch)>0:
                    db.bulk_save_objects(batch)
                    db.commit()
                if len(notifications)>0:
                    db.bulk_save_objects(notifications)
                    db.commit()
                
                if len(user_websocket_ids)>0:
                    background_tasks.add_task(manager.send_message_to_multiple,user_ids=user_websocket_ids,message= {"message":"Hi user new kyc document is required.","category":"REQUIRED_NEW_KYC_DOC","path":"REQUIRED_NEW_KYC_DOC"} )

                #user_emails = [email[0] for email in db.query(UserModel.email).filter(UserModel.id.in_(request.users_list)).all()]
                if len(user_emails)>0:
                    mail_data = {"name":request.name,"required":request.required,"description":request.description,"users_list":request.users_list}
                    background_tasks.add_task(Email.send_mail, recipient_email=user_emails, subject="Update Your KYC Documents", template='kyc.html',data=mail_data )
                
                

        return Utility.json_response(
            status=SUCCESS,
            message="Document created successfully",
            error=[],
            data={"doc_id": new_doc.id}
        )

    except Exception as E:
        AppLogger.error(str(E))
        db.rollback()  
        return Utility.json_response(status=EXCEPTION, message="Failed to create document",error='', data={} )

@router.post("/update-kyc-doc", response_description="Update status")
def get_users(request: EditKycSchema,background_tasks: BackgroundTasks,auth_user=Depends(AuthHandler().auth_wrapper), db: Session = Depends(get_database_session)):
    try:
       
        md_doc_id = request.md_doc_id
        
        user_id = auth_user["id"]
        tenant_id =1
        if "tenant_id" in auth_user:
            tenant_id =auth_user["tenant_id"]
            
        if auth_user["role_id"] in [1]:
            tenant_id = 1

        cleaned_name = ' '.join(request.name.strip().split()).lower()
     
        existing_doc = db.query(MdKycDocs).filter(func.lower(MdKycDocs.name) == cleaned_name,MdKycDocs.id!=md_doc_id).first()
        if existing_doc is not None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR,message="Document with this name already exists",error=[], data={})

        kyc_doc = db.query(MdKycDocs).filter(MdKycDocs.id == md_doc_id,tenant_id==tenant_id).first()
        if not kyc_doc:
            return Utility.json_response(status=FAIL, message="KYC document not found", error=["Invalid ID"], data={})
        
        
        #remove all existing permessions
        if kyc_doc.share_type =="SPECIFIC_USERS":
            stmt = delete(MdKycDocPermissions).where(MdKycDocPermissions.md_doc_id == kyc_doc.id,MdKycDocPermissions.tenant_id == tenant_id)
            result = db.execute(stmt)
        #print(cleaned_name)
        kyc_doc.name=request.name.strip()
        kyc_doc.required=request.required
        #kyc_doc.doc_type=request.doc_type,
        if request.status==True:
            kyc_doc.status = True
        elif request.status ==False:
             kyc_doc.status = False


        #kyc_doc.size=int(request.size),
        kyc_doc.description=request.description,
        kyc_doc.share_type=request.share_type,
        kyc_doc.tenant_id= tenant_id
        notifications = []
        batch =[]
       

        if request.share_type =="SPECIFIC_USERS" and request.users_list and len(request.users_list) > 0:
                for use_id in request.users_list:
                    batch.append(MdKycDocPermissions(user_id=use_id,md_doc_id=md_doc_id,tenant_id=tenant_id))
                    notifications.append(NotificationModel(user_id=user_id,description=request.description,category="REQUIRED_NEW_KYC_DOC",ref_id=user_id,tenant_id=tenant_id))
                if len(batch)>0:
                    db.bulk_save_objects(batch)
                    
                if len(notifications)>0:
                    db.bulk_save_objects(notifications)
                    
                
                user_emails = [email[0] for email in db.query(UserModel.email).filter(UserModel.id.in_(request.users_list)).all()]
                if len(user_emails)>0:
                    mail_data = {"name":request.name,"required":request.required,"description":request.description,"users_list":request.users_list}
                    background_tasks.add_task(Email.send_mail, recipient_email=user_emails, subject="Update Your KYC Documents", template='kyc.html',data=mail_data )
            
        
        db.commit()
        return Utility.json_response(status=SUCCESS, message="KYC document updated", error=[], data={})



    except Exception as e:
        AppLogger.error(str(e))
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data=[])

@router.post("/kyc-doc-details", response_description="Create doc")
def kyc_doc_details(request: kycDocDetailsReqSchema,background_tasks: BackgroundTasks,auth_user=Depends(AuthHandler().auth_wrapper), db: Session = Depends(get_database_session)):
    try:
        user_id = auth_user["id"]
        tenant_id =1
        if "tenant_id" in auth_user:
            tenant_id =auth_user["tenant_id"]
        md_doc_id = request.md_doc_id

        result = db.query(MdKycDocs).filter(MdKycDocs.tenant_id==tenant_id,MdKycDocs.id==md_doc_id).one()
        data = {}
        if result is not None:
            data = Utility.model_to_dict(result)
            qr =  db.query(MdKycDocPermissions).filter(MdKycDocPermissions.md_doc_id==result.id,MdKycDocPermissions.tenant_id==tenant_id).all()
            
            all_user_ids = []
            if qr is not None:
                for item in qr:
                    all_user_ids.append(item.user_id)
                   
            if len(all_user_ids)>0:
                users_result = db.query(UserModel).filter(UserModel.id.in_(all_user_ids)).all()
                
                if users_result is not None:
                    data["users"] = []
                    for user in users_result:
                        user_dict = Utility.model_to_dict(user)
                        data["users"].append({"id":user_dict["id"],"email":user_dict["email"],"name":user_dict["name"],"first_name":user_dict["first_name"],"last_name":user_dict["last_name"]})
                        


        return Utility.json_response(status=EXCEPTION,message="Details retrived succefully!", error='', data=data )
      



    except Exception as e:
        AppLogger.error(str(e))
        db.rollback()  
        return Utility.json_response(status=EXCEPTION,message="Failed to create document", error=[str(e)], data={} )    


@router.post("/upload-file", response_description="UploadFIles")
async def upload_file(file: UploadFile = File(...),auth_user=Depends(AuthHandler().auth_wrapper), db: Session = Depends(get_database_session)):
    try:
        #data = await login_user_for_mfiles()
        #save_in_mfiles_using_directly_file(data["response"],)
        req ={'request_data':{}}
        req["request_data"]["username"] = "mRemit"
        content = await file.read()
        final_result = {"name":'',"content_type":"","size":0}
        final_result["name"] = file.filename
        final_result["content_type"] = file.content_type
        final_result["size"] = len(content)
        data  =  await save_file_in_mfiles(req, content)
        if data is not None:
            final_result["path"] = data["file_name"]
            return Utility.json_response(status=SUCCESS, message=all_messages.FILE_UPLOAD_SUCCESS, error=[], data=final_result)
        else:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

    except Exception as E:
        AppLogger.error(str(E))
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

@router.post("/download-file", response_description="Download File")
async def download_file(request: DownloadFile):
    try:
        #"415b9ebac05e5e8e15a87d88b3e146882e2d9053bb2b72112bb1481823aa212996820b25"
        path = request.path
        final_result = {"file_data":''}
        data  =  await download_files_from_mfiles_to_desired_folder(path)
        if data is not None:
            final_result["file_data"] = data
            return Utility.json_response(status=SUCCESS, message=all_messages.FILE_DOWNLOAD_SUCCESS, error=[], data=final_result)
        else:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

    except Exception as E:
        AppLogger.error(str(E))
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

@router.post("/get-currency-reates", response_description="Download File")
async def get_currency_rates(request: CalculateCurrency):
    try:
        
        result = await get_currency(request.from_currency,request.to_currency)
        return Utility.json_response(status=SUCCESS, message="", error=[], data=result)                          
                        
    except Exception as E:
        AppLogger.error(str(E))        
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data=[])




