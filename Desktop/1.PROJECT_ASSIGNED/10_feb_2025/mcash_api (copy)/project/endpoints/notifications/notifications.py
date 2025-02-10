from datetime import datetime, timezone,timedelta
from datetime import datetime
from ...models.user_model import UserModel,BeneficiaryModel,NotificationModel
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

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
    responses={404: {"description": "Not found"}},
)
@router.post("/list", response_description="Fetch Notifications List")
async def get_notifications_list(filter_data: NotificationsListReq,auth_user=Depends(AuthHandler().auth_wrapper),db: Session = Depends(get_database_session)):
    user_id = auth_user["id"]
    user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
    if user_obj is None:            
            return Utility.json_response(status=500, message=all_messages.USER_NOT_EXISTS, error=[], data={},code="LOGOUT_ACCOUNT")            
    elif user_obj.role_id !=2:            
        return Utility.json_response(status=500, message=all_messages.NO_PERMISSIONS, error=[], data={},code="LOGOUT_ACCOUNT")            
    elif user_obj.status_id == 2:
        return Utility.json_response(status=500, message=all_messages.PENDING_EMAIL_VERIFICATION, error=[], data={},code="LOGOUT_ACCOUNT")            
    elif user_obj.status_id == 4:
        return Utility.json_response(status=500, message=all_messages.PROFILE_INACTIVE, error=[], data={},code="LOGOUT_ACCOUNT")            
    elif user_obj.status_id == 5:
        return Utility.json_response(status=500, message=all_messages.PROFILE_DELETED, error=[], data={},code="LOGOUT_ACCOUNT")
        
    if auth_user.get("role_id", -1) not in [2]:
        return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.NO_PERMISSIONS, error=[], data={},code="NO_PERMISSIONS")
    query = db.query(NotificationModel).options(joinedload(NotificationModel.user_details)).filter(NotificationModel.user_id==user_id,NotificationModel.is_active==True)
    if filter_data.status and len(filter_data.status)>0:
        if False in filter_data.status and True in filter_data.status:
            query = db.query(NotificationModel).options(joinedload(NotificationModel.user_details))
            query = query.filter(NotificationModel.user_id==user_id,NotificationModel.is_active.in_([True,False]))
            print("TRUE AND FALSE")
        elif False in filter_data.status:
            
            query = db.query(NotificationModel).options(joinedload(NotificationModel.user_details))
            query = query.filter(NotificationModel.user_id==user_id,NotificationModel.is_active.in_([False]))
            
    
    if filter_data.search_string:
        search = f"%{filter_data.search_string}%"
        query = query.filter(
            or_(
                NotificationModel.description.ilike(search),
                
            )
        )
     
    
     # Total count of users matching the filters
    total_count = query.count()
    print(total_count)
    sort_column = getattr(NotificationModel, filter_data.sort_by, None)
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
            created_on=notification.created_on,
            category=notification.category,
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

# Define a Pydantic model for the request body
class DeactivateNotificationsRequest(BaseModel):
    notification_ids: Optional[List[int]] = None  # List of notification IDs to deactivate

    @field_validator('notification_ids')
    def check_notification_ids(cls, v):
        if v is not None and len(v) == 0:
            raise ValueError('At least one notification ID is required.')
        return v

@router.post("/inactive-notifications", response_description="Deactivate Notifications")
async def deactivate_notifications(
    request: DeactivateNotificationsRequest = Body(...),  # Request body
    auth_user=Depends(AuthHandler().auth_wrapper),
    db: Session = Depends(get_database_session)
):
    user_id = auth_user["id"]

    # Check if the user exists
    user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
    if user_obj is None:
        raise HTTPException(status_code=404, detail=all_messages.USER_NOT_EXISTS)

    notification_ids = request.notification_ids

    if notification_ids is None or len(notification_ids) == 0:
        # If no notification IDs are provided, deactivate all notifications for the user
        user_notificatuions = db.query(NotificationModel).filter(NotificationModel.user_id == user_id).all()
        
        if not user_notificatuions:
            return {
                "status": "success",
                "message": "No notifications to deactivate."
            }

        # Deactivate all notifications
        for notification in user_notificatuions:
            notification.is_active = False  # Set to False

    else:
        # Get all notification IDs for the user
        user_notificatuions = db.query(NotificationModel).filter(NotificationModel.user_id == user_id).all()
        user_notification_ids = {notification.id for notification in user_notificatuions}

        # Check if the provided notification IDs are valid
        invalid_ids = [nid for nid in notification_ids if nid not in user_notification_ids]
        if invalid_ids:
            raise HTTPException(status_code=404, detail=f"Notifications not found or do not belong to the user: {invalid_ids}")

        # Deactivate the specific notifications
        for notification_id in notification_ids:
            notification = db.query(NotificationModel).filter(
                NotificationModel.id == notification_id,
                NotificationModel.user_id == user_id
            ).first()
            if notification:
                notification.is_active = False  # Set to False

    # Commit the changes to the database
    try:
        db.commit()
    except Exception as e:
        db.rollback()  # Rollback in case of any error
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "status": "success",
        "message": "Notifications deactivated successfully.",
        "data": {"notification_ids": notification_ids if notification_ids else "all"}
    }