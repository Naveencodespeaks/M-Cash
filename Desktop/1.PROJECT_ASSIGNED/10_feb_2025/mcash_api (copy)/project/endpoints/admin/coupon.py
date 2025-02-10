from fastapi import FastAPI, APIRouter, HTTPException
from datetime import datetime, timezone,timedelta
from datetime import date, datetime

from ...schemas.coupon_schema import CouponSchema,CouponStatusSchema,CouponUpdateSchema
from ...models.coupon_model import CouponModel
from ...models.user_model import UserModel
from ...constant import messages
from sqlalchemy import and_
from sqlalchemy.orm import Session
from .. import APIRouter, Utility, SUCCESS, FAIL, EXCEPTION ,INTERNAL_ERROR,BAD_REQUEST,BUSINESS_LOGIG_ERROR, Depends, Session, get_database_session, AuthHandler
from fastapi import BackgroundTasks
from ...common.mail import Email
from ...schemas.coupon_schema import CouponFilterRequest,CouponListResponse,PaginatedCouponResponse,CouponListRequestBase
from sqlalchemy import desc, asc
from fastapi_pagination import Params,paginate 
from sqlalchemy.orm import  joinedload
from sqlalchemy.sql import select, and_, or_, not_,func
from sqlalchemy.future import select

from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, func

# APIRouter creates path for coupon

router=APIRouter(prefix="/admin",
    tags=["coupon"],
    responses={404: {"description": "Not found"}},)

@router.post('/coupon-create',response_description="create a coupon")
async def create_coupon(request: CouponSchema,background_tasks: BackgroundTasks,auth_user=Depends(AuthHandler().auth_wrapper), db: Session = Depends(get_database_session)):
    try:
        user_id = auth_user["id"]
        role_id = auth_user["role_id"]
        tenant_id=auth_user['tenant_id']
        user_obj=auth_user['user_name']
        admin_email=auth_user["email"]
        if role_id!=1:
            raise Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=messages.NO_PERMISSIONS,error=[],data={})
        existing_coupon = db.query(CouponModel).filter(CouponModel.coupon_code== request.coupon_code).first()
        if existing_coupon:
            raise Utility.json_response(status=BUSINESS_LOGIG_ERROR,message=messages.COUPON_ALREADY_EXITS,error=[],data={})
        coupon_data = CouponModel(coupon_code= request.coupon_code,description=request.description,coupon_amount=request.coupon_amount,currency=request.currency,discount_type=request.discount_type,coupon_expiry_date=request.coupon_expiry_date,usage_limit_per_person=request.usage_limit_per_person,created_by=user_id,updated_by=user_id,status=True,tenant_id=tenant_id)
        db.add(coupon_data)
        db.flush()
        db.commit()

        mail_data = {"user_name":user_obj,"coupon_code":request.coupon_code,"coupon_amount":request.coupon_amount,"coupon_expiry_date":request.coupon_expiry_date}
        background_tasks.add_task(Email.send_mail, recipient_email=[admin_email], subject="Exciting News! Grab Your New Discount Coupon Now!", template='admin_coupon.html',data=mail_data )

        user_email=[email[0] for email in db.query(UserModel.email).filter(UserModel.status_id==3).all()]
        if len(user_email)>0:
            mail_data = {"coupon_code":request.coupon_code,"coupon_amount":request.coupon_amount,"coupon_expiry_date":request.coupon_expiry_date}
            background_tasks.add_task(Email.send_mail, recipient_email=user_email, subject="Exciting News! Grab Your New Discount Coupon Now!", template='user_coupon.html',data=mail_data )
       
        
        if coupon_data.id:
            return Utility.json_response(status=SUCCESS, message=messages.COUPON_CREATED, error=[],
                                         data={"coupon_id": coupon_data.id})
        else:
            return Utility.json_response(status=FAIL, message=messages.SOMTHING_WRONG, error=[], data={})
    except Exception as E:
        print(E)
        db.rollback()
        return Utility.json_response(status=FAIL, message=messages.SOMTHING_WRONG, error=[], data={})
    
@router.post('/coupon-update',response_description="update a coupon")
async def update_coupon(request: CouponUpdateSchema,background_tasks: BackgroundTasks,auth_user=Depends(AuthHandler().auth_wrapper), db: Session = Depends(get_database_session)):
    try:
        user_id = auth_user["id"]
        role_id = auth_user["role_id"]
        tenant_id=auth_user['tenant_id']
        user_obj=auth_user['user_name']
        user_email=auth_user["email"]
        if role_id!=1:
            raise Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=messages.NO_PERMISSIONS,error=[],data={})
        coupon = db.query(CouponModel).filter(CouponModel.id ==request.coupon_id).first()

        if not coupon:
            raise Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=messages.COUPON_NOT_FOUND,error=[],data={})
        coupon.coupon_code = request.coupon_code
        coupon.description = request.description
        coupon.coupon_amount = request.coupon_amount
        coupon.currency = request.currency
        coupon.discount_type = request.discount_type
        coupon.coupon_expiry_date = request.coupon_expiry_date
        coupon.usage_limit_per_person = request.usage_limit_per_person
        coupon.status = request.status  # Updating status
        coupon.tenant_id=tenant_id
        db.commit()
        mail_data = {"user_name":user_obj,"coupon_code":request.coupon_code,"coupon_amount":request.coupon_amount,"coupon_expiry_date":request.coupon_expiry_date}
        background_tasks.add_task(Email.send_mail, recipient_email=[user_email], subject="Exciting News! Grab Your New Discount Coupon Now!", template='admin_coupon_update.html',data=mail_data )

        if coupon.id:
            return Utility.json_response(status=SUCCESS, message=messages.COUPON_UPDATED, error=[],
                                         data={"coupon_id": coupon.id})
        else:
            return Utility.json_response(status=FAIL, message=messages.SOMTHING_WRONG, error=[], data={})
    except Exception as E:
        print(E)
        db.rollback()
        return Utility.json_response(status=FAIL, message=messages.SOMTHING_WRONG, error=[], data={})
    
@router.post('/coupons-list',response_description="get coupons list")
async def get_coupons_list(filter_data: CouponFilterRequest,auth_user=Depends(AuthHandler().auth_wrapper),db: Session = Depends(get_database_session)):
    try:
        user_id = auth_user["id"]
        role_id = auth_user["role_id"]
        if role_id!=1:
            raise Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=messages.NO_PERMISSIONS,error=[],data={})
        
        query = db.query(CouponModel)
        print(query)

        if filter_data.search_string:
            search = f"%{filter_data.search_string}%"
            query = query.filter(
                or_(
                    CouponModel.coupon_code.ilike(search),
                    CouponModel.currency.ilike(search),
                    CouponModel.discount_type.ilike(search),
                    CouponModel.description.ilike(search),
                    
                )
            )
    
        if filter_data.status:
            query = query.filter(CouponModel.status.in_(filter_data.status))
        
        # if filter_data.created_on and filter_data.created_to and ( isinstance(filter_data.created_on, date) and isinstance(filter_data.created_to, date)):
        #     query = query.filter(CouponModel.created_on > filter_data.created_on)
        #     query = query.filter(CouponModel.created_on < filter_data.created_to)
            
        
        # Total count of users matching the filters
        total_count = query.count()
        sort_column = getattr(CouponModel, filter_data.sort_by, None)
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
        return PaginatedCouponResponse(
            total_count=total_count,
            list=paginated_query,
            page=filter_data.page,
            per_page=filter_data.per_page
        )
    except Exception as E:
        print(E)
        db.rollback()
        return Utility.json_response(status=FAIL, message=messages.SOMTHING_WRONG, error=[], data={})
        
   
@router.get('/generate-coupon-code',response_description="generate coupon code")
async def get_coupon_code(auth_user=Depends(AuthHandler().auth_wrapper),db:Session=Depends(get_database_session)):
    try:
        user_id = auth_user["id"]
        role_id = auth_user["role_id"]
        if role_id!=1:
            raise Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=messages.NO_PERMISSIONS,error=[],data={})
        coupon_code = Utility.generate_random_string(10)
        is_exists =0
        def check_coupon_code():
            global is_exists
            global coupon_code
            coupon_code = Utility.generate_random_string(10)
            is_exists= db.query(CouponModel).filter(CouponModel.coupon_code== coupon_code).count()
            
        check_coupon_code()
        if is_exists>0:
            check_coupon_code()
            
        return Utility.json_response(status=SUCCESS, message='', error=[], data={"coupon_code":coupon_code})
    except Exception as E:
        print(E)
        return Utility.json_response(status=FAIL, message=messages.SOMTHING_WRONG, error=[], data={})

@router.post('/coupon-status-update',response_description="Coupon status updation")
async def status_updation_for_coupons(request:CouponStatusSchema,background_tasks:BackgroundTasks,auth_user=Depends(AuthHandler().auth_wrapper),db: Session=Depends(get_database_session)):
    try:
        user_id = auth_user["id"]
        user_name=auth_user["user_name"]
        role_id = auth_user["role_id"]
        email=auth_user["email"]
        if role_id!=1:
            raise Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=messages.NO_PERMISSIONS, error=[],data={})
        coupon_id = request.coupon_id
        coupon_obj = db.query(CouponModel).filter(CouponModel.id==coupon_id).first()
        if coupon_obj:
            coupon_obj.status = request.status
            db.commit()
            status=""
            if coupon_obj.status==1 or coupon_obj.status==True:
                status="Enabled"
            else:
                status="Disabled"
            mail_data = {"status":status,"user_name":user_name,"coupon_code":coupon_obj.coupon_code,"coupon_amount":coupon_obj.coupon_amount,"coupon_expiry_date":coupon_obj.coupon_expiry_date}
            background_tasks.add_task(Email.send_mail, recipient_email=[email], subject="Coupon Status Update!", template='admin_coupon_status.html',data=mail_data )           
            return Utility.json_response(status=SUCCESS, message=messages.COUPON_STATUS_UPDATED, error=[], data={})
        else:
            return Utility.json_response(status=FAIL, message=messages.COUPON_NOT_FOUND, error=[], data={})
    except Exception as E:
        print(E)
        db.rollback()
        return Utility.json_response(status=FAIL, message=messages.SOMTHING_WRONG, error=[], data={})
    



# login request
# {
#   "email": "remit_admin@yopmail.com",
#   "password": "Machint@123"
# }
# #coupon creation
# {
#   "coupon_code": "ACD123",
#   "description": "hello",
#   "coupon_amount": 200,
#   "currency": "$",
#   "discount_type": "PERCENTAGE",
#   "coupon_expiry_date": "2024-09-14 09:40:21.635",
#   "status_id":1,
#   "usage_limit_per_person": 3
# }
# #status coupon
# {
#   "coupon_code": "ACD123",
#   "description": "hello",
#   "coupon_amount": 200,
#   "currency": "$",
#  "discount_type": "PERCENTAGE",
#    "coupon_expiry_date": "2024-09-14 09:40:21.635",
#   "usage_limit_per_person": 1,
#   "status_id": 0
# }
# if filter_data.search_string:
#         search = f"%{filter_data.search_string}%"
#         query = query.filter(
#             or_(
#                 UserModel.first_name.ilike(search),
#                 UserModel.last_name.ilike(search),
#                 UserModel.email.ilike(search),
#                 UserModel.mobile_no.ilike(search)
#             )
#         )