from datetime import datetime, timezone,timedelta
from datetime import datetime
from ...models.user_model import UserModel,BeneficiaryModel,AdminNotificationModel
 

from ...models.master_data_models import MdUserRole,MdUserStatus,MdCountries

from . import APIRouter, Utility, SUCCESS, FAIL, EXCEPTION ,INTERNAL_ERROR,BAD_REQUEST,BUSINESS_LOGIG_ERROR, Depends, Session, get_database_session, AuthHandler
from ...schemas.notifications_schema import PaginatedNotificationsResponse,NotificationsListReq,userDetails,NotificationResponse
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
from ...models.admin_user import AdminUser
router = APIRouter(
    prefix="/admin-notifications",
    tags=["Notifications"],
    responses={404: {"description": "Not found"}},
)
@router.post("/list", response_description="Fetch Notifications List")
async def get_benficiary_list(filter_data: NotificationsListReq,auth_user=Depends(AuthHandler().auth_wrapper),db: Session = Depends(get_database_session)):
    user_id = auth_user["id"]
    user_obj = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if user_obj is None:            
            return Utility.json_response(status=500, message=all_messages.USER_NOT_EXISTS, error=[], data={},code="LOGOUT_ACCOUNT")            
    elif user_obj.status_id == 2:
        return Utility.json_response(status=500, message=all_messages.PENDING_EMAIL_VERIFICATION, error=[], data={},code="LOGOUT_ACCOUNT")            
    elif user_obj.status_id == 4:
        return Utility.json_response(status=500, message=all_messages.PROFILE_INACTIVE, error=[], data={},code="LOGOUT_ACCOUNT")            
    elif user_obj.status_id == 5:
        return Utility.json_response(status=500, message=all_messages.PROFILE_DELETED, error=[], data={},code="LOGOUT_ACCOUNT")
    if auth_user.get("role_id", -1) not in [1,3]:
        return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.NO_PERMISSIONS, error=[], data={},code="NO_PERMISSIONS")
    
    query = db.query(AdminNotificationModel).options(joinedload(AdminNotificationModel.user_details)).filter(AdminNotificationModel.user_id==user_id,AdminNotificationModel.is_active==True)
    if filter_data.status and len(filter_data.status)>0:
        if False in filter_data.status and True in filter_data.status:
            query = db.query(AdminNotificationModel).options(joinedload(AdminNotificationModel.user_details))
            query = query.filter(AdminNotificationModel.user_id==user_id,AdminNotificationModel.is_active.in_([True,False]))
            print("TRUE AND FALSE")
        elif False in filter_data.status:
            
            query = db.query(AdminNotificationModel).options(joinedload(AdminNotificationModel.user_details))
            query = query.filter(AdminNotificationModel.user_id==user_id,AdminNotificationModel.is_active.in_([False]))
    
    
    # query = db.query(AdminNotificationModel).options(
    #     joinedload(AdminNotificationModel.user_details)
    #     #joinedload(model.beneficiary_country_details),
    #     #joinedload(model.beneficiary_country_details),
        
    # )
    
    # query = query.filter(AdminNotificationModel.user_id==user_id)
    if filter_data.search_string:
        search = f"%{filter_data.search_string}%"
        query = query.filter(
            or_(
                AdminNotificationModel.description.ilike(search),
                
            )
        )
     
    
     # Total count of users matching the filters
    total_count = query.count()
    print(total_count)
    sort_column = getattr(AdminNotificationModel, filter_data.sort_by, None)
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
    response_list = [
        NotificationResponse(
            id=notification.id,
            description=notification.description,
            category=notification.category,
            created_on=notification.created_on,
            ref_id=notification.ref_id,
            user_details=userDetails(
                user_id=notification.user_details.id,
                first_name=notification.user_details.first_name,
                last_name=notification.user_details.last_name,
                email=notification.user_details.email
            )
        )
        for notification in paginated_query
    ]
    
    # Create a paginated response
    return PaginatedNotificationsResponse(
        total_count=total_count,
        list=response_list,
        page=filter_data.page,
        per_page=filter_data.per_page
    )

