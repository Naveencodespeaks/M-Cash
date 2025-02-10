from datetime import datetime, timezone,timedelta
from datetime import datetime
from ...models.user_model import UserModel,BeneficiaryModel,NotificationModel
from ...models.admin_user import AdminUser

from ...models.master_data_models import MdUserRole,MdUserStatus,MdCountries

from . import APIRouter, Utility, SUCCESS, FAIL, EXCEPTION ,INTERNAL_ERROR,BAD_REQUEST,BUSINESS_LOGIG_ERROR, Depends, Session, get_database_session, AuthHandler
from ...schemas.notifications_schema import PaginatedNotificationsResponse,NotificationsListReq,userDetails,NotificationResponse
from pydantic import BaseModel, Field,field_validator,EmailStr,model_validator

import re
from ...constant import messages as all_messages
from ...common.mail import Email
from sqlalchemy.sql import select, and_, or_, not_,func
from sqlalchemy.future import select
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from ...models.admin_configuration_model import tokensModel
from sqlalchemy import desc, asc
from typing import List
from fastapi import BackgroundTasks
from fastapi_pagination import Params,paginate 
from sqlalchemy.orm import  joinedload
from fastapi import HTTPException, Depends, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from fastapi import HTTPException
from ...models.master_data_models import MdCurrency
from ...aploger import AppLogger
from ...schemas.master_data import CurrencyListReq,AddCurrency ,EditCurrency,update_currency_status_schema,MakeAsDefaultSchema

router = APIRouter(
    prefix="/currency",
    tags=["currency"],
    responses={404: {"description": "Not found"}},
)

@router.post("/list", response_description="Fetch currency List")
async def get_currency_list(filter_data:CurrencyListReq, auth_user=Depends(AuthHandler().auth_wrapper), db: Session = Depends(get_database_session)):
    try:

        user_id = auth_user["id"]
        tenant_id = None
        if "tenant_id" in auth_user:
            tenant_id = auth_user["tenant_id"]
        elif filter_data.tenant_id is not None:
            tenant_id = filter_data.tenant_id
        
        query = db.query(MdCurrency).options(joinedload(MdCurrency.currency_type_details)).filter(MdCurrency.status==filter_data.status)
        
        
        if tenant_id is not None:
            query = query.filter(MdCurrency.tenant_id == tenant_id)
        
        
        if filter_data.search_string:
            search = f"%{filter_data.search_string}%"
            query = query.filter(
                or_(
                    MdCurrency.name.ilike(search),
                    MdCurrency.iso_code.ilike(search),
                    MdCurrency.currency_symbol.ilike(search),
                    MdCurrency.description.ilike(search),
                
                    
                )
            )
        
        
        # Total count of users matching the filters
        total_count = query.count()
        sort_column = getattr(MdCurrency, filter_data.sort_by, None)
        if sort_column:
            if filter_data.sort_order == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc("created_on"))

        # Apply pagination
        offset = (filter_data.page - 1) * filter_data.per_page
        paginated_query = query.offset(offset).limit(filter_data.per_page).all()
        response_list = []
        for curncy in paginated_query:
            item = Utility.model_to_dict(curncy)
            if curncy.currency_type_id is not None and curncy.currency_type_details:
                item["currency_type_details"] =  Utility.model_to_dict(curncy.currency_type_details)
            response_list.append(item)


        res_data = { "total_count":total_count, "list":response_list,  "page":filter_data.page,  "per_page":filter_data.per_page }
        return Utility.json_response(status=SUCCESS, message="", error=[], data=res_data)

    except Exception as e:
        print(e)
        AppLogger.error(e)
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data=[])


@router.post("/add-currency", response_description="Add currency")
async def add_currency(request: AddCurrency, background_tasks: BackgroundTasks,auth_user=Depends(AuthHandler().auth_wrapper), db: Session = Depends(get_database_session)):
   
    try:
        
        user_id = auth_user["id"]
        role_id = auth_user["role_id"]
        tenant_id= None
        
        admin_email=auth_user["email"]
        if "tenant_id" in auth_user:
            tenant_id = auth_user["tenant_id"]
        elif request.tenant_id is not None:
            tenant_id = request.tenant_id

        user_obj = db.query(AdminUser).filter(AdminUser.id == user_id).first()
        if user_obj is None:            
            return Utility.json_response(status=500, message=all_messages.USER_NOT_EXISTS, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id !=3:            
            return Utility.json_response(status=500, message=all_messages.NO_PERMISSIONS, error=[], data={},code="LOGOUT_ACCOUNT")            
        
        exists_cur = db.query(MdCurrency).filter(MdCurrency.iso_code==request.iso_code).first()
        if exists_cur is not None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.CURRENCY_ALREADY_EXISTS, error=[], data={},code="CURRENCY_ALREADY_EXISTS")
        details = MdCurrency(
                              
                              name = request.name,
                              iso_code = request.iso_code,
                              currency_symbol= request.currency_symbol,
                              #default =request.default,
                              status =True,
                              currency_type_id =request.currency_type_id,
                              subunits= request.subunits,
                              tenant_id=tenant_id
                              
                            )
        db.add(details)
        db.commit()
        
        #db.flush()
        if details.id:
            return Utility.json_response(status=SUCCESS, message=all_messages.CURRENCY_CREATED, error=[], data={"id":details.id},code="")
        else:
            db.rollback()
            return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

    except Exception as E:
        print(E)
        AppLogger.error(E)
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})
    

@router.post("/update-currency", response_description="Update Currency")
async def update_currency(request:EditCurrency , admin_user=Depends(AuthHandler().auth_wrapper),db: Session = Depends(get_database_session)):
    try:
        admin_role_id = admin_user["role_id"]
        if admin_role_id not in [1]:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.NO_PERMISSIONS, error=[], data={},code="NO_PERMISSIONS")
        
        name = request.name,
        iso_code = request.iso_code,
        currency_symbol= request.currency_symbol,
        #default =request.default,
        #status =request.status,
        currency_type_id =request.currency_type_id,
        existing_count = db.query(MdCurrency).filter(func.lower(MdCurrency.name) == name, MdCurrency.iso_code !=iso_code).count()
        currency_obj = db.query(MdCurrency).filter(MdCurrency.iso_code == request.iso_code).first()
        if currency_obj is None:            
            return Utility.json_response(status=500, message=all_messages.CHARGE_NOT_EXISTS, error=[], data={},code="CHARGE_NOT_EXISTS")            
        elif existing_count>0:
            return Utility.json_response(status=500, message=all_messages.CHARGE_EXISTS, error=[], data={},code="CHARGE_EXISTS")  

        else:

            currency_obj.name = name
            currency_obj.iso_code = iso_code
            currency_obj.currency_symbol = currency_symbol
            #currency_obj.default = bool(request.default)  # If it's a string like '1' or '0'
            #currency_obj.status = int(request.status)
            currency_obj.currency_type_id = currency_type_id
            currency_obj.subunits= request.subunits,
          
            db.commit()
            return Utility.json_response(status=SUCCESS, message=all_messages.CURRENCY_UPDATE_SUCCESS, error=[], data={})
            
    except Exception as E:
        print(E)
        db.rollback()
        return Utility.json_response(status=EXCEPTION, message="Something went wrong", error=[], data={})

@router.post("/update-currency-status", response_description="Update Currency")
async def update_currency_status(request:update_currency_status_schema , admin_user=Depends(AuthHandler().auth_wrapper),db: Session = Depends(get_database_session)):
    try:
        admin_role_id = admin_user["role_id"]
        if admin_role_id not in [1]:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.NO_PERMISSIONS, error=[], data={},code="NO_PERMISSIONS")
        
        
        tenant_id = admin_user.get("tenant_id", None)
        query = db.query(MdCurrency).filter(MdCurrency.id ==request.currency_id)
        if tenant_id is not None:
            query = query.filter(MdCurrency.tenant_id == tenant_id)

        currency_obj = query.first()
        if currency_obj is None:            
            return Utility.json_response(status=500, message=all_messages.CHARGE_NOT_EXISTS, error=[], data={},code="CHARGE_NOT_EXISTS")            
        else:
            if currency_obj.status == request.status:
                return Utility.json_response(status=500, message=all_messages.CURRENCY_IS_SAME_STATUS, error=[], data={},code="CURRENCY_IS_SAME_STATUS")   

            currency_obj.status = request.status            
            db.commit()
            return Utility.json_response(status=SUCCESS, message=all_messages.CURRENCY_UPDATE_SUCCESS, error=[], data={})
            
    except Exception as E:
        AppLogger.error(str(E))
        db.rollback()
        return Utility.json_response(status=EXCEPTION, message="Something went wrong", error=[], data={})

@router.post("/update-default-status", response_description="Update default status")
async def update_default_status(request:MakeAsDefaultSchema , admin_user=Depends(AuthHandler().auth_wrapper),db: Session = Depends(get_database_session)):
    try:
        admin_role_id = admin_user["role_id"]
        if admin_role_id not in [1]:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.NO_PERMISSIONS, error=[], data={},code="NO_PERMISSIONS")
        
        tenant_id = admin_user.get("tenant_id", None)
        query = db.query(MdCurrency).filter(MdCurrency.id ==request.currency_id)
        if tenant_id is not None:
            query = query.filter(MdCurrency.tenant_id == tenant_id)

        currency_obj = query.first()
        if currency_obj is None:            
            return Utility.json_response(status=500, message=all_messages.CHARGE_NOT_EXISTS, error=[], data={},code="CHARGE_NOT_EXISTS")            
        else:
            db.query(MdCurrency).filter(MdCurrency.tenant_id == tenant_id).update({MdCurrency.default: False}, synchronize_session=False)
            db.commit()
            currency_obj.default = True            
            db.commit()
            return Utility.json_response(status=SUCCESS, message=all_messages.CURRENCY_UPDATE_SUCCESS, error=[], data={})
            
    except Exception as E:
        AppLogger.error(str(E))
        db.rollback()
        return Utility.json_response(status=EXCEPTION, message="Something went wrong", error=[], data={})
