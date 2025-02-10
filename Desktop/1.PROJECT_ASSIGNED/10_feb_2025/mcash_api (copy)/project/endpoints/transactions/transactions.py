from datetime import datetime, timezone,timedelta
from sqlalchemy import and_
from sqlalchemy.sql import select, and_, or_, not_,func
from sqlalchemy.future import select
from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from ...models.tickets_model import TicketsModel
from ...models.user_model import UserModel,BeneficiaryModel
from ...models.master_data_models import MdUserRole,MdUserStatus,MdServiceTypes,MdCurrency
from ...models.admin_configuration_model import tokensModel
from . import APIRouter, Utility, SUCCESS, FAIL, EXCEPTION ,WEB_URL, API_URL, INTERNAL_ERROR,BAD_REQUEST,BUSINESS_LOGIG_ERROR, Depends, Session, get_database_session, AuthHandler
import re
from ...schemas.transaction import GetSummary
from fastapi import BackgroundTasks
from ...schemas.login import Login
from ...constant import messages as all_messages
from ...common.mail import Email
import json
from ...models.user_model import AdminNotificationModel, NotificationModel
from ...library.mfiles import get_currency
from ...models.transaction import ChargesModel
from ...models.master_data_models import TransactionPurposeModel, TransactionSubPurpose
from sqlalchemy.orm import  joinedload
from ...schemas.transaction import AddWallet,paymentSuccessSchema, transactionPorposListReq,PaginatedTransactionPorposListRes,transactionSubPorposListReq,ResendTransactionOtp,TransactionListReq
from sqlalchemy import desc, asc
from ...models.transaction import BankAccountModel, TransactionRequestModel, TransactionModel,PaymentGatewayTransactionModel, UserWalletModel,AdminWalletModel,AdminTransactionModel
from ...schemas.transaction import AddBankAccount, GetWalletsList, TransactionInitiate,ActivateTransactionRequest,TransactionDetailsSchema,GetWalletDetails,getOtpForFundRequestTransferSchema,ApproveRequestedFundsTransferSchema,UpdateRequestStatus
import pickle
import time
from ...models.coupon_model import CouponModel
from decimal import Decimal
from typing import Any
from decimal import Decimal, InvalidOperation
from ...aploger import AppLogger
from ...common.razorpay_service import get_razorpay_client, RazorpayClient
from ...models.admin_user import AdminUser
import decimal
import copy

# APIRouter creates path operations for product module

router = APIRouter(
    prefix="/transaction",
    tags=["Transactions"],
    responses={404: {"description": "Not found"}},
)

@router.post("/add-wallet")
def add_wallet(request:AddWallet,uth_user=Depends(AuthHandler().auth_wrapper), razorpay_client: RazorpayClient = Depends(get_razorpay_client),db: Session = Depends(get_database_session)):
    try:
        #PaymentGatewayTransactionModel
        # UserWalletModel 
        
        
        curr = db.query(MdCurrency).filter(MdCurrency.id==request.currency_id).first()
        if curr is None:
            return Utility.json_response(status=INTERNAL_ERROR, message="Selected Currency not found!", error=[], data=[])

        order = razorpay_client.create_order(amount=request.amount,currency=curr.iso_code)
        if "razorpay_order_id" in order:
            new_order =PaymentGatewayTransactionModel(
                razorpay_payment_id = "",#order["razorpay_payment_id"],
                razorpay_order_id = order["razorpay_order_id"],
                razorpay_signature = "", #order["razorpay_signature"],
                user_id = uth_user["id"],
                amount = request.amount,
                currency_id = request.currency_id
            )
            db.add(new_order)
            db.commit()
            return Utility.json_response(status=SUCCESS, message="Success Fully Order Created", error=[], data=dict(order))
        else:
            AppLogger.error("Order is Not Created")        
            return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data=[])



    except Exception as E:
            print(str(E))
            AppLogger.error(str(E))        
            return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data=[])

@router.post("/payment_success")
def payment_success(request:paymentSuccessSchema, uth_user=Depends(AuthHandler().auth_wrapper), razorpay_client: RazorpayClient = Depends(get_razorpay_client),db: Session = Depends(get_database_session)):
    try:
        
        payment_id = request.razorpay_payment_id
        order_id = request.razorpay_order_id
        signature = request.razorpay_signature
          

        
        order = db.query(PaymentGatewayTransactionModel).filter(PaymentGatewayTransactionModel.razorpay_order_id==order_id ).first()
        if order is None:
            return Utility.json_response(status=INTERNAL_ERROR, message="Order Details are not found", error=[], data={'status': 'failed'})
        if order.status == True:
            return Utility.json_response(status=SUCCESS, message="this Order is already settled! ", error=[], data={'status': 'failed'})
        
        is_valid = razorpay_client._validate_signature(razorpay_order_id = order_id, razorpay_payment_id = payment_id, razorpay_signature= signature )
        
        if is_valid:
            user = db.query(UserModel).filter(UserModel.id==order.user_id).first()
            
            
            if user is None:
                return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.USER_NOT_EXISTS, error=[], data={'status': 'failed'})
            user_wallet = db.query(UserWalletModel).filter(UserWalletModel.user_id==user.id, UserWalletModel.currency_id== order.currency_id).first()
            new_transaction = TransactionModel(transaction_type="CREDIT",
                                               amount=order.amount,
                                               ledger_amount=0,
                                               referenc_id=Utility.uuid(),
                                               user_id = order.user_id,
                                               currency_id = order.currency_id,
                                               status_id =3

                                               )
            db.add(new_transaction)
            if user_wallet is None:
                user_wallet = UserWalletModel(user_id=user.id,currency_id=order.currency_id,balance = order.amount,credited_by=user.id )
                db.add(user_wallet)
                order.status = 1
                order.payment_gateway_status="Completed"
                db.commit()
            else:
                new_transaction.ledger_amount = user_wallet.balance
                user_wallet.balance += order.amount
                order.status = 1
                order.payment_gateway_status="Completed"
                db.commit()     
            return Utility.json_response(status=SUCCESS, message=all_messages.SOMTHING_WRONG, error=[], data={'status': 'success'})
        else:
            return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={'status': 'failed'})
            
    except Exception as E:
            print(str(E))
            AppLogger.error(str(E))        
            return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data=[])


@router.post("/get-wallets-list", response_description="accounts-list")
def account_list(request: GetWalletsList,auth_user=Depends(AuthHandler().auth_wrapper),db: Session = Depends(get_database_session)):
    try:

        user_id = auth_user["id"]
        user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
        if user_obj is None:            
            return Utility.json_response(status=500, message=all_messages.USER_NOT_EXISTS, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 1:
                return Utility.json_response(status=500, message=all_messages.PENDING_PROFILE_COMPLATION, error=[], data={},code="LOGOUT_ACCOUNT")
        
        elif user_obj.status_id == 2:
            return Utility.json_response(status=500, message=all_messages.PENDING_EMAIL_VERIFICATION, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 4:
            return Utility.json_response(status=500, message=all_messages.PROFILE_INACTIVE, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 5:
            return Utility.json_response(status=500, message=all_messages.PROFILE_DELETED, error=[], data={},code="LOGOUT_ACCOUNT")
        
        query = db.query(UserWalletModel)
        if request.user_id is not None:
            query = query.filter(UserWalletModel.user_id==request.user_id)
        else:
            query = query.filter(UserWalletModel.user_id==user_id)

        total_count = query.count()
        sort_column = getattr(UserWalletModel, request.sort_by, None)
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
            acc = Utility.model_to_dict(item)
            if item.user_id:
                acc["user_details"] = Utility.model_to_dict(item.user_details)
                if "password" in acc["user_details"]:
                    del acc["user_details"]["password"]
            if item.currency_id:
                acc["currency_detils"] = Utility.model_to_dict(item.currency_detils)
            res_data["list"].append(acc)

        return Utility.json_response(status=SUCCESS, message="", error=[], data=res_data,code="")

    except Exception as E:
        AppLogger.error(E)
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

@router.post("/get-wallets-details", response_description="get wallets details")
def get_wallets_details(request: GetWalletDetails,auth_user=Depends(AuthHandler().auth_wrapper),db: Session = Depends(get_database_session)):
    try:

        user_id = auth_user["id"]
        wallet_id  = request.wallet_id
        user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
        if user_obj is None:            
            return Utility.json_response(status=500, message=all_messages.USER_NOT_EXISTS, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 1:
                return Utility.json_response(status=500, message=all_messages.PENDING_PROFILE_COMPLATION, error=[], data={},code="LOGOUT_ACCOUNT")
        
        elif user_obj.status_id == 2:
            return Utility.json_response(status=500, message=all_messages.PENDING_EMAIL_VERIFICATION, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 4:
            return Utility.json_response(status=500, message=all_messages.PROFILE_INACTIVE, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 5:
            return Utility.json_response(status=500, message=all_messages.PROFILE_DELETED, error=[], data={},code="LOGOUT_ACCOUNT")
        
        query = db.query(UserWalletModel).filter(UserWalletModel.id==wallet_id) 
        result_set =  query.first()        
        res_data = Utility.model_to_dict(result_set)

        if result_set.user_id:
            res_data["user_details"] = Utility.model_to_dict(result_set.user_details)
            if "password" in res_data["user_details"]:
                del res_data["user_details"]["password"]
        if result_set.currency_id:
            res_data["currency_detils"] = Utility.model_to_dict(result_set.currency_detils)

        return Utility.json_response(status=SUCCESS, message="", error=[], data=res_data,code="")

    except Exception as E:
        AppLogger.error(E)
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})


@router.post("/list", response_description="List")
def account_list(request: TransactionListReq,auth_user=Depends(AuthHandler().auth_wrapper),db: Session = Depends(get_database_session)):
    try:
        
        user_id = auth_user["id"]
        user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
        if user_obj is None:            
            return Utility.json_response(status=500, message=all_messages.USER_NOT_EXISTS, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 1:
                return Utility.json_response(status=500, message=all_messages.PENDING_PROFILE_COMPLATION, error=[], data={},code="LOGOUT_ACCOUNT")
        
        elif user_obj.status_id == 2:
            return Utility.json_response(status=500, message=all_messages.PENDING_EMAIL_VERIFICATION, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 4:
            return Utility.json_response(status=500, message=all_messages.PROFILE_INACTIVE, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 5:
            return Utility.json_response(status=500, message=all_messages.PROFILE_DELETED, error=[], data={},code="LOGOUT_ACCOUNT")
        
        
        #print("sdfsdf",latest_debit.amount)
        query = db.query(TransactionModel)
        query = query.filter(TransactionModel.user_id==user_id) 
        total_count = query.count()
        sort_column = getattr(TransactionModel, request.sort_by, None)
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
            acc = Utility.model_to_dict(item)
            if item.user_id:
                acc["user_details"] = Utility.model_to_dict(item.user)
                if "password" in acc["user_details"]:
                    del acc["user_details"]["password"]

            if item.credited_from_user_id:
                acc["credited_from_user_details"] = Utility.model_to_dict(item.credited_from_user_details)
                if "password" in acc["credited_from_user_details"]:
                    del acc["credited_from_user_details"]["password"]
                    
            if item.currency_id:
                acc["currency_detils"] = Utility.model_to_dict(item.currency_detils)
            if item.status_id:
                acc["status_details"] = Utility.model_to_dict(item.status_details)
            if item.tenant_id:
                acc["tenant_details"] = Utility.model_to_dict(item.tenant_details)
            
            res_data["list"].append(acc)

        latest_cridit = db.query(TransactionModel).filter(TransactionModel.user_id==user_id,TransactionModel.transaction_type=="CREDIT").order_by(desc("id")).first()
        latest_debit = db.query(TransactionModel).filter(TransactionModel.user_id==user_id,TransactionModel.transaction_type=="DEBIT").order_by(desc("id")).first()
        if latest_cridit is not None:
            latestcridit = Utility.model_to_dict(latest_cridit)

            res_data["latest_credit"] = {
                "amount":latestcridit["amount"],
                "created_on":latestcridit["created_on"],
                "currency_detils" : Utility.model_to_dict(latest_cridit.currency_detils)

            }
            
        if latest_debit is not None:
            latestdebit = Utility.model_to_dict(latest_debit)
            res_data["latest_debit"] = {
                "amount":latestdebit["amount"],
                "created_on":latestdebit["created_on"],
                "currency_detils" : Utility.model_to_dict(latest_debit.currency_detils)
            }
        

        return Utility.json_response(status=SUCCESS, message="", error=[], data=res_data,code="")

    except Exception as E:
        print(E)
        AppLogger.error(E)
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

def get_charges(db:Session,request:GetSummary,logiedin_user,from_role_id,to_role_id):
    all_charges = []
    transfer_amount = request.transfer_amount
    tenant_id = logiedin_user.get("tenant_id",1)
    query = db.query(ChargesModel).options(joinedload(ChargesModel.charge_category_details) )
    query  = query.filter(ChargesModel.status==True,ChargesModel.tenant_id == tenant_id)
    if from_role_id is not None and to_role_id is not None:
        
        query = query.filter(ChargesModel.from_role_id == from_role_id, ChargesModel.to_role_id == to_role_id )

    allactive_charges = query.all()
    return_data = {
        "all_charges":[],
        "charges_amount":0,
        "agent_charges":0,
        "admin_charges":0,
        "transfer_amount":request.transfer_amount
    }
    
    for item in allactive_charges:
       
        
        category =  item.charge_category_details
        charges = item.charges
        calculate_in_percentage = item.calculate_in_percentage
       
        minimum_transaction_amount = item.minimum_transaction_amount
        maximum_transaction_amount = item.maximum_transaction_amount
        #currency = charge.currency
        users_list = item.users_list
        effective_date = item.effective_date
        if effective_date.tzinfo is None:
            # Make it timezone-aware by assuming it's in UTC (or adjust based on your system)
            effective_date = effective_date.replace(tzinfo=timezone.utc)

        #print(effective_date.date() >= datetime.now(timezone.utc).date())
        if (effective_date.date() >= datetime.now(timezone.utc).date() or True) and ( minimum_transaction_amount is not None and maximum_transaction_amount is not None ) and ( transfer_amount>=minimum_transaction_amount or transfer_amount <= maximum_transaction_amount):
            #deduct percentage                    
            if calculate_in_percentage:
                
                
                percentage_amount = (charges / 100) * request.transfer_amount
                admin_charges = 0
                agent_charges = 0
                return_data["charges_amount"] += percentage_amount
                if item.agent_charges and item.agent_charges >0:
                    agent_charges = (item.agent_charges / 100) * percentage_amount
                    
                if item.admin_charges and item.admin_charges >0:
                    admin_charges = (item.admin_charges / 100) * percentage_amount
                
                return_data["admin_charges"] += admin_charges
                return_data["agent_charges"] += agent_charges

                
                
                all_charges.append({"name":item.name, "charges":f'{charges}%', "in_percentage":True,"charges_amount": percentage_amount,"admin_charges":admin_charges, "agent_charges":agent_charges  })
            else:
                
                return_data["charges_amount"] += charges
                admin_charges = 0
                agent_charges =  0
                if item.admin_charges and item.admin_charges >0:
                    admin_charges = charges-item.admin_charges
                if item.agent_charges and item.agent_charges >0:
                    agent_charges = charges-item.agent_charges    

                all_charges.append({"name":item.name, "charges":charges, "in_percentage":False,"charges_amount": charges,"admin_charges":admin_charges, "agent_charges":agent_charges    })
        
    return_data["all_charges"] = all_charges
    
    return return_data
    

@router.post("/get-summary", response_description="get summary")
async def get_summary(request: GetSummary, auth_user=Depends(AuthHandler().auth_wrapper),db: Session = Depends(get_database_session)):
    try:
        all_charges = []
        response_data ={}
        
        #coupon_code =  request.coupon_code
        transfer_amount = request.transfer_amount
        coupon_amount =0
        currency_id = request.currency_id
        
            
        
        allactive_charges = db.query(ChargesModel).options(joinedload(ChargesModel.charge_category_details) ).filter(ChargesModel.status==True).all()
        total_amount = request.transfer_amount
        
        allcharges = get_charges(db,request,auth_user,auth_user["role_id"] ,request.to_user_id)
        response_data["transfer_amount"] = total_amount
        response_data["applied_charges"] = allcharges
        
        return Utility.json_response(status=SUCCESS, message="Success", error=[], data=response_data)
    
    except Exception as E:
        print(E)
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

@router.post("/details", response_description="Transaction Details")
def transaction_details(request: TransactionDetailsSchema,auth_user=Depends(AuthHandler().auth_wrapper),db: Session = Depends(get_database_session)):
    try:
        transaction_id = request.transaction_id
        user_id = auth_user["id"]
        user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
        if user_obj is None:            
            return Utility.json_response(status=500, message=all_messages.USER_NOT_EXISTS, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 1:
                return Utility.json_response(status=500, message=all_messages.PENDING_PROFILE_COMPLATION, error=[], data={},code="LOGOUT_ACCOUNT")
        
        elif user_obj.status_id == 2:
            return Utility.json_response(status=500, message=all_messages.PENDING_EMAIL_VERIFICATION, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 4:
            return Utility.json_response(status=500, message=all_messages.PROFILE_INACTIVE, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 5:
            return Utility.json_response(status=500, message=all_messages.PROFILE_DELETED, error=[], data={},code="LOGOUT_ACCOUNT")
        
        
        query = db.query(TransactionModel)
        query = query.filter(TransactionModel.id==transaction_id)        
        
        result = query.options(
            
                        joinedload(TransactionModel.credited_from_user_details),
                        joinedload(TransactionModel.status_details),
                        joinedload(TransactionModel.tenant_details)
            ).first()   
        if result is None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Transaction Not Found", error=[], data={})

        
        
        acc = Utility.model_to_dict(result)
        acc["amount"] = float(acc["amount"])
        acc["charges_amount"] = float(acc["charges_amount"])
        acc["ledger_amount"] = float(acc["ledger_amount"])
        if "request_data" in acc:
            del acc["request_data"]
        type_transaction ="credited_from"    
        if (acc["transaction_type"] =="CREDIT" or acc["transaction_type"] =="DEBIT") and result.credited_from_user_id:
            if acc["transaction_type"] =="DEBIT":
                type_transaction ="credited_to" 

            beneficiary_details = Utility.model_to_dict(result.credited_from_user_details)
            acc[type_transaction] = {}
            acc[type_transaction]["id"] = beneficiary_details["id"]
            acc[type_transaction]["full_name"] = beneficiary_details["full_name"]
            acc[type_transaction]["nick_name"] = beneficiary_details["nick_name"]
            acc[type_transaction]["email"] = beneficiary_details["email"]
            acc[type_transaction]["mobile_no"] = beneficiary_details["mobile_no"]

        acc["status_details"] = Utility.model_to_dict(result.status_details)
        if result.tenant_id:
            acc["tenant_details"] = Utility.model_to_dict(result.tenant_details)
        acc["transaction_purpose_details"] = Utility.model_to_dict(result.tenant_details)
        if result.user_id != auth_user["id"]:
            user_details = Utility.model_to_dict(result.user)
            acc["user_details"] = {}
            acc["user_details"]["id"] = user_details["id"]
            acc["user_details"]["first_name"] = user_details["first_name"]
            acc["user_details"]["last_name"] = user_details["last_name"]
            acc["user_details"]["name"] = user_details["name"]
            acc["user_details"]["email"] = user_details["email"]
            acc["user_details"]["status_id"] = user_details["status_id"]            
        

        return Utility.json_response(status=SUCCESS, message="Details are retrived successfully", error=[], data=acc)

    except Exception as E:
        print(E)        
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

@router.post("/transfer-funds", response_description="transfer funds")
def transfer_funds(request:GetSummary,background_tasks: BackgroundTasks,auth_user=Depends(AuthHandler().auth_wrapper), db: Session = Depends(get_database_session)):
    try:
        user_id = auth_user["id"]
        tenant_id = auth_user["tenant_id"]
        currency_id = request.currency_id
        amount = request.transfer_amount
        to_user_id = request.to_user_id
        

        
        user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
        if user_obj is None:            
            return Utility.json_response(status=500, message=all_messages.USER_NOT_EXISTS, error=[], data={},code="LOGOUT_ACCOUNT")            
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
        
        exists_ben = db.query(UserModel).filter(UserModel.id == to_user_id).first()
        if exists_ben is None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.BENEFICIARY_NOT_EXISTS, error=[], data={},code="BENEFICIARY_NOT_EXISTS")

        elif exists_ben.status_id != 3:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Beneficiary is Not active", error=[], data={},code="BENEFICIARY_NOT_ACTIVE")

        from_userwallet =  db.query(UserWalletModel).filter(UserWalletModel.user_id==user_id, UserWalletModel.currency_id == currency_id).first()  
        if from_userwallet is None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Account has no sufficient balance", error=[], data={},code="NO_SUFFICIENT_BALANCE")
        if from_userwallet.balance<amount:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Account has no sufficient balance", error=[], data={},code="NO_SUFFICIENT_BALANCE")
        referenc_id = Utility.generatecode(code_for="TRANSFER_MONEY")
        
        
        allcharges = get_charges(db,request,auth_user,user_obj.role_id, exists_ben.role_id)
        print(allcharges)
        otp = Utility.generate_otp()
        category = "TRANSFER_MONEY"
        otpdata = { 
           
            
            "ref_id":referenc_id,
                    "catrgory":category,
                    "otp":otp,
                    "user_id":user_id,
                    "token":'', 
                    "amount":amount,
                    "from_user_id": user_id,
                    "to_user_id": to_user_id,
                    "charges_amount":allcharges.get("charges_amount",0),
                    "currency_id":from_userwallet.currency_id,
                    "http_request_data":json.dumps(allcharges),
                    "admin_charges": allcharges.get("admin_charges",0),
                    "agent_charges": allcharges.get("agent_charges",0)

                    
                    }
        otpdata["token"] = AuthHandler().encode_token(otpdata,minutes=6)
        if Utility.inactive_previous_tokens(db=db, catrgory=category, user_id=user_id) == False:
                db.rollback()
                return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})
        
        token_data = tokensModel(ref_id=user_id,token=otpdata["token"],catrgory=category,user_id=user_id,otp=otp,active=True)
        db.add(token_data)
        db.commit()
        if token_data.id:
            mail_data = { "source_amount":f"{amount} {from_userwallet.currency_detils.iso_code} ","otp":str(otp),"name":user_obj.first_name +" "+user_obj.last_name,"beneficiary_name":exists_ben.name,"transaction_id":referenc_id,'remmit_id':referenc_id,"track_id":referenc_id}
            background_tasks.add_task(Email.send_mail,recipient_email=[user_obj.email], subject="Fund Tranfer Initiated", template='send_money.html',data=mail_data )
        
            return Utility.json_response(status=SUCCESS, message=all_messages.RESEND_VERIFICATION_OTP, error=[], data={"referenc_id":referenc_id, "allcharges":allcharges},code="")
        else:
            db.rollback()
            return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})
    

    except Exception as E:
        print(E)        
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

@router.post("/activate-transaction", response_description="Activate Transaction ")
async def activate_transaction(request: ActivateTransactionRequest,background_tasks: BackgroundTasks,auth_user=Depends(AuthHandler().auth_wrapper), db: Session = Depends(get_database_session)):
    try:
        
        user_id = auth_user["id"]
        otp = request.otp
        ref_id = request.ref_id
        tenant_id = auth_user.get("tenant_id",None)
        
        user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
        if user_obj is None:            
            return Utility.json_response(status=500, message=all_messages.USER_NOT_EXISTS, error=[], data={},code="LOGOUT_ACCOUNT")            
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
         
        
        
        token_query = db.query(tokensModel).filter(tokensModel.catrgory =="TRANSFER_MONEY", tokensModel.user_id==user_id, tokensModel.otp == otp,tokensModel.active==True,tokensModel.ref_id==user_id).first()
        if token_query is None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.INVALIED_OTP, error=[], data={},code="")
        else:
            """
            from_user_id
            to_user_id
            currency_id
            amount
            charges_amount,
            http_request_data
            """
            token_data = AuthHandler().decode_otp_token(token_query.token)
            if str(token_data["otp"]) == str(otp):
                from_userwallet =  db.query(UserWalletModel).filter(UserWalletModel.user_id==token_data["from_user_id"], UserWalletModel.currency_id == token_data["currency_id"]).first()  
                to_userwallet   =  db.query(UserWalletModel).filter(UserWalletModel.user_id==token_data["to_user_id"], UserWalletModel.currency_id == token_data["currency_id"]).first()  
                if from_userwallet is None:
                    return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Account has no sufficient balance", error=[], data={},code="NO_SUFFICIENT_BALANCE")
                     
                exists_ben = db.query(UserModel).filter(UserModel.id == token_data["to_user_id"]).first()
                if exists_ben is None:
                    return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.BENEFICIARY_NOT_EXISTS, error=[], data={},code="BENEFICIARY_NOT_EXISTS")

                elif exists_ben.kyc_status_id != 3:
                    return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Beneficiary is Not active", error=[], data={},code="BENEFICIARY_NOT_ACTIVE")

                admin_details = db.query(AdminUser).filter(AdminUser.tenant_id==tenant_id, AdminUser.role_id==3).first()
                admin_wallet = None
                if admin_details is not None:
                    admin_wallet = db.query(AdminWalletModel).filter(AdminWalletModel.admin_id==admin_details.id,AdminWalletModel.currency_id==token_data["currency_id"]).first()
                
                if from_userwallet.balance < token_data["amount"]+token_data["charges_amount"]:
                    return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Account has no sufficient balance", error=[], data={},code="NO_SUFFICIENT_BALANCE")
                shared_transaction_id = Utility.generate_random_string()
                debet_amount = decimal.Decimal(token_data["amount"])+decimal.Decimal(token_data["charges_amount"])
                cr_transaction = TransactionModel(
                    shared_transaction_id = shared_transaction_id,
                    transaction_type ="CREDIT",
                    referenc_id = Utility.generatecode("CREDIT"),
                    amount=token_data["amount"],
                    charges_amount = token_data["charges_amount"],
                    user_id = token_data["to_user_id"],
                    credited_from_user_id = token_data["from_user_id"],
                    currency_id = token_data["currency_id"],
                    status_id = 2, #1== Initiated, 2== In-Progress, 3 == Completed, 4== Failed
                    tenant_id = tenant_id,
                    request_data = token_data["http_request_data"],
                     
                    
                )
                
                debet_transaction = TransactionModel(
                    shared_transaction_id = shared_transaction_id,
                    referenc_id = Utility.generatecode("DEBIT"),
                    transaction_type ="DEBIT",
                    amount= debet_amount,
                    charges_amount = token_data["charges_amount"],
                    user_id = token_data["from_user_id"],
                    credited_from_user_id = token_data["from_user_id"],
                    currency_id = token_data["currency_id"],
                    status_id = 2, #1== Initiated, 2== In-Progress, 3 == Completed, 4== Failed
                    tenant_id = tenant_id,
                    request_data = token_data["http_request_data"], 
                    
                )
                if admin_details is not None and token_data.get("admin_charges",None) is not None:
                    if token_data.get("admin_charges",0)>0:
                        admin_transaction = AdminTransactionModel(
                        shared_transaction_id = shared_transaction_id,
                        referenc_id = Utility.generatecode("CREDIT"),
                        transaction_type ="CREDIT",
                        amount=token_data["admin_charges"],
                        charges_amount = token_data["admin_charges"],
                        admin_id = admin_details.id,
                        credited_from_user_id = token_data["from_user_id"],
                        currency_id = token_data["currency_id"],
                        status_id = 3, #1== Initiated, 2== In-Progress, 3 == Completed, 4== Failed
                        tenant_id = tenant_id,
                        request_data = token_data["http_request_data"], 
                        
                        )
                        db.add(admin_transaction)
                #funds transfor from  user to agent         
                if user_obj.role_id==2 and exists_ben.role_id ==5:
                    cr_transaction.amount += decimal.Decimal(token_data["agent_charges"])
                    
                    charges_transaction = TransactionModel(
                        shared_transaction_id = shared_transaction_id,
                        transaction_type ="CREDIT",
                        credit_type="CHARGES",
                        referenc_id = Utility.generatecode("CREDIT"),
                        amount=decimal.Decimal(token_data["agent_charges"]),
                        charges_amount = token_data["charges_amount"],
                        user_id = token_data["to_user_id"],
                        credited_from_user_id = token_data["from_user_id"],
                        currency_id = token_data["currency_id"],
                        status_id = 2, #1== Initiated, 2== In-Progress, 3 == Completed, 4== Failed
                        tenant_id = tenant_id,
                        request_data = token_data["http_request_data"]                    
                        
                    )
                    db.add(charges_transaction)
                    
                msg = f"{debet_amount} is debeted and creditaed to {exists_ben.name}"
                user_notification = NotificationModel(user_id=from_userwallet.user_id,tenant_id=user_obj.tenant_id,description=msg,category="AMOUNT_TRNSFERED",ref_id=auth_user["id"],status_category="AMOUNT_TRNSFERED")
                db.add(user_notification)
                db.add(debet_transaction)
                db.add(cr_transaction)
                db.commit()
                if cr_transaction.id:
                    token_query.active = False
                    cr_transaction.status_id = 3
                    if to_userwallet is None:
                        to_userwallet = UserWalletModel(user_id=cr_transaction.user_id,currency_id=cr_transaction.currency_id,balance = cr_transaction.amount,credited_by=cr_transaction.credited_from_user_id )
                        cr_transaction.ledger_amount = copy.deepcopy(to_userwallet.balance)

                        
                        debet_transaction.ledger_amount = copy.deepcopy(from_userwallet.balance)
                        from_userwallet.balance -= debet_amount
                        db.add(to_userwallet)
                    else:
                        to_userwallet.balance += cr_transaction.amount
                        from_userwallet.balance -= debet_amount

                    #add amount to Admin wallets
                    if admin_details is not None and token_data.get("admin_charges",None) is not None:
                            if admin_wallet is not None :
                                admin_transaction.ledger_amount = copy.deepcopy(admin_wallet.balance)
                                admin_wallet.balance += decimal.Decimal(token_data["admin_charges"])
                            else:
                                admin_new_wallet = AdminWalletModel(admin_id=admin_details.id,currency_id=cr_transaction.currency_id,balance = token_data["admin_charges"],credited_by=cr_transaction.credited_from_user_id )
                                db.add(admin_new_wallet)
                                admin_transaction.ledger_amount = 0


                    db.commit()
                    datetime_obj = cr_transaction.created_on
                    date_part = datetime_obj.strftime("%d-%m-%Y")
                    time_part = datetime_obj.strftime("%I:%M %p")
                    mail_data = {"name":user_obj.first_name +" "+user_obj.last_name,"beneficiary_name":exists_ben.name,"source_amount":f"{cr_transaction.amount} {from_userwallet.currency_detils.iso_code}","transaction_id":cr_transaction.referenc_id,"date_part":date_part,"time_part": time_part}
                    
                    status_msg = "Activated"
                    msg = f"Transaction Processed successfully"
                    # mail_data = {"user_name":user_obj.name,"message":f'''{exists_ben.full_name} payment trancaction has been Activated successfully!'''}
                    background_tasks.add_task(Email.send_mail, recipient_email=[user_obj.email], subject="Transaction is Activated", template='transaction_activate.html',data=mail_data )
            
                    return Utility.json_response(status=SUCCESS, message=msg, error=[], data={"transaction_id":cr_transaction.id},code="")
                else:
                    db.rollback()
                    return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.INVALIED_OTP, error=[], data={},code="")
            
    except Exception as E:
        print(E)
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

#ResendTransactionOtp
@router.post("/resend-transaction-otp", response_description="Resend transaction OTP ")
async def resend_transaction_otp(request: ActivateTransactionRequest,background_tasks: BackgroundTasks,auth_user=Depends(AuthHandler().auth_wrapper), db: Session = Depends(get_database_session)):
    try:
        
        user_id = auth_user["id"]
        otp = request.otp
        token = request.token
        tenant_id = None
        
        user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
        if user_obj is None:            
            return Utility.json_response(status=500, message=all_messages.USER_NOT_EXISTS, error=[], data={},code="LOGOUT_ACCOUNT")            
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
         
        
        
        token_query = db.query(tokensModel).filter(tokensModel.catrgory =="TRANSFER_MONEY", tokensModel.user_id==user_id, tokensModel.otp == otp,tokensModel.active==True,tokensModel.token==token).first()
        if token_query is None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.INVALIED_OTP, error=[], data={},code="")
        else:
            """
            from_user_id
            to_user_id
            currency_id
            amount
            charges_amount,
            http_request_data
            """
            token_data = AuthHandler().decode_otp_token(token_query.token)
            if str(token_data["otp"]) == str(otp):
                from_userwallet =  db.query(UserWalletModel).filter(UserWalletModel.user_id==token_data["from_user_id"], UserWalletModel.currency_id == token_data["currency_id"]).first()  
                to_userwallet   =  db.query(UserWalletModel).filter(UserWalletModel.user_id==token_data["to_user_id"], UserWalletModel.currency_id == token_data["currency_id"]).first()  
                if from_userwallet is None:
                    return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Account has no sufficient balance", error=[], data={},code="NO_SUFFICIENT_BALANCE")

                exists_ben = db.query(UserModel).filter(UserModel.id == token_data["to_user_id"]).first()
                if exists_ben is None:
                    return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.BENEFICIARY_NOT_EXISTS, error=[], data={},code="BENEFICIARY_NOT_EXISTS")

                elif exists_ben.kyc_status_id != 3:
                    return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Beneficiary is Not active", error=[], data={},code="BENEFICIARY_NOT_ACTIVE")

                
                
                
                transaction = TransactionModel(
                    transaction_type ="CREDIT",
                    amount=token_data["amount"],
                    charges_amount = token_data["charges_amount"],
                    user_id = token_data["to_user_id"],
                    credited_from_user_id = token_data["from_user_id"],
                    currency_id = token_data["currency_id"],
                    status_id = 2, #1== Initiated, 2== In-Progress, 3 == Completed, 4== Failed
                    tenant_id = tenant_id,
                    request_data = token_data["http_request_data"], 
                    
                )
                db.add(transaction)
                db.commit()
                if transaction.id:
                    token_query.active = False
                    transaction.status_id = 3
                    if to_userwallet is None:
                        to_userwallet = UserWalletModel(user_id=transaction.user_id,currency_id=transaction.currency_id,balance = transaction.amount,credited_by=transaction.credited_from_user_id )
                        from_userwallet.balance -= transaction.amount
                        db.add(to_userwallet)
                    else:
                        to_userwallet.balance += transaction.amount
                        from_userwallet.balance -= transaction.amount

                    db.commit()
                    datetime_obj = transaction.created_on
                    date_part = datetime_obj.strftime("%d-%m-%Y")
                    time_part = datetime_obj.strftime("%I:%M %p")
                    mail_data = {"name":user_obj.first_name +" "+user_obj.last_name,"beneficiary_name":exists_ben.full_name,"source_amount":transaction.amount,"transaction_id":transaction.referenc_id,"date_part":date_part,"time_part": time_part}
                    
                    status_msg = "Activated"
                    msg = f"Transaction Process {status_msg} successfully"
                    # mail_data = {"user_name":user_obj.name,"message":f'''{exists_ben.full_name} payment trancaction has been Activated successfully!'''}
                    background_tasks.add_task(Email.send_mail, recipient_email=[user_obj.email], subject="Transaction is Activated", template='transaction_activate.html',data=mail_data )
            
                    return Utility.json_response(status=SUCCESS, message=msg, error=[], data={"transaction_id":transaction.id},code="")
                else:
                    return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.INVALIED_OTP, error=[], data={},code="")
            
    except Exception as E:
        print(E)
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

@router.post("/request-funds", response_description="transfer funds")
def request_funds(request:GetSummary,background_tasks: BackgroundTasks,auth_user=Depends(AuthHandler().auth_wrapper), db: Session = Depends(get_database_session)):
    try:
        user_id = auth_user["id"]
        tenant_id = auth_user["tenant_id"]
        currency_id = request.currency_id
        amount = request.transfer_amount
        to_user_id = request.to_user_id
       
        print(to_user_id)
        
        user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
        if user_obj is None:            
            return Utility.json_response(status=500, message=all_messages.USER_NOT_EXISTS, error=[], data={},code="LOGOUT_ACCOUNT")            
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
        
        exists_ben = db.query(UserModel).filter(UserModel.id == to_user_id).first()
        if exists_ben is None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.BENEFICIARY_NOT_EXISTS, error=[], data={},code="BENEFICIARY_NOT_EXISTS")

        elif exists_ben.status_id != 3:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Beneficiary is Not active", error=[], data={},code="BENEFICIARY_NOT_ACTIVE")

        from_userwallet =  db.query(UserWalletModel).filter(UserWalletModel.user_id==to_user_id,UserWalletModel.currency_id == currency_id).first()  
        print(from_userwallet)
        if from_userwallet is None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Account has no sufficient balance", error=[], data={},code="NO_SUFFICIENT_BALANCE")
        if from_userwallet.balance<amount:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Account has no sufficient balance", error=[], data={},code="NO_SUFFICIENT_BALANCE")
        category = "REQUEST_FOR_FUNDS"
        allcharges = get_charges(db,request,auth_user,exists_ben.role_id,user_obj.role_id )
        referenc_id = Utility.generatecode(code_for=category)
        
        
        otp = Utility.generate_otp()
        otpdata = { 
                  "otp":otp,
                  "amount":amount,
                  "charges_amount":allcharges.get("charges_amount",0),
                  "admin_charges": allcharges.get("admin_charges",0),
                  "agent_charges": allcharges.get("agent_charges",0),
                  "referenc_id":referenc_id,
                  "http_request_data":json.dumps(allcharges),
                  "to_user_id": to_user_id,
                  "currency_id":from_userwallet.currency_id,
                  "from_user_id": user_id,
                  "description":request.description

                    }
        otpdata["token"] = AuthHandler().encode_token(otpdata,minutes=6)
        if Utility.inactive_previous_tokens(db=db, catrgory=category, user_id=user_id) == False:
                db.rollback()
                return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})
        
        token_data = tokensModel(ref_id=user_id,token=otpdata["token"],catrgory=category,user_id=user_id,otp=otp,active=True)
        db.add(token_data)
        db.commit()
        if token_data.id:
            mail_data = { "source_amount":amount,"otp":str(otp),"name":user_obj.first_name +" "+user_obj.last_name,"beneficiary_name":exists_ben.name,"transaction_id":referenc_id,'remmit_id':referenc_id,"track_id":referenc_id}
            background_tasks.add_task(Email.send_mail,recipient_email=[user_obj.email], subject="Fund Request Initiated", template='send_money.html',data=mail_data )
        
            return Utility.json_response(status=SUCCESS, message=all_messages.RESEND_VERIFICATION_OTP, error=[], data={"referenc_id":referenc_id},code="")
        else:
            db.rollback()
            return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})
    
    except Exception as E:
        print(E)        
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

@router.post("/activate-request-fund", response_description="Activate Transaction ")
async def activate_transaction(request: ActivateTransactionRequest,background_tasks: BackgroundTasks,auth_user=Depends(AuthHandler().auth_wrapper), db: Session = Depends(get_database_session)):
    try:
        
        user_id = auth_user["id"]
        otp = request.otp
        ref_id = request.ref_id
        tenant_id = None
        
        user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
        if user_obj is None:            
            return Utility.json_response(status=500, message=all_messages.USER_NOT_EXISTS, error=[], data={},code="LOGOUT_ACCOUNT")            
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
         
        
        category = "REQUEST_FOR_FUNDS"
       
        token_query = db.query(tokensModel).filter(tokensModel.catrgory ==category, tokensModel.user_id==user_id, tokensModel.otp == otp,tokensModel.active==True).first()
        if token_query is None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.INVALIED_OTP, error=[], data={},code="")
        else:
            """
            from_user_id
            to_user_id
            currency_id
            amount
            charges_amount,
            http_request_data
            """
            token_data = AuthHandler().decode_otp_token(token_query.token)
            if str(token_data["otp"]) == str(otp):
                from_userwallet =  db.query(UserWalletModel).filter(UserWalletModel.user_id==token_data["from_user_id"], UserWalletModel.currency_id == token_data["currency_id"]).first()  
                to_userwallet   =  db.query(UserWalletModel).filter(UserWalletModel.user_id==token_data["to_user_id"], UserWalletModel.currency_id == token_data["currency_id"]).first()  
                # if from_userwallet is None:
                #     return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Account has no sufficient balance", error=[], data={},code="NO_SUFFICIENT_BALANCE")

                exists_ben = db.query(UserModel).filter(UserModel.id == token_data["to_user_id"]).first()
                if exists_ben is None:
                    return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.BENEFICIARY_NOT_EXISTS, error=[], data={},code="BENEFICIARY_NOT_EXISTS")

                elif exists_ben.kyc_status_id != 3:
                    return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Beneficiary is Not active", error=[], data={},code="BENEFICIARY_NOT_ACTIVE")

                """
                
                amount = Column(Numeric(precision=10, scale=2), default=0.00, comment="This amount is user want to send")
                charges_amount = Column(Numeric(precision=10, scale=2), default=0.00,comment="This amount is all charges amount")
                referenc_id =Column(String(50), default=time.time())
                http_request_data = Column(Text,default='')
                to_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
                to_user_details = relationship("UserModel", back_populates="to_user_transaction_requests", foreign_keys=[to_user_id])
                currency_id = Column(Integer, default=None, nullable=True)
                from_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
                from_user_details = relationship("UserModel", back_populates="from_user_transaction_requests", foreign_keys=[from_user_id])
                transactions = relationship("TransactionModel", back_populates="transaction_request_details", foreign_keys="TransactionModel.transaction_request_id")
                is_active = Column(Boolean, default=True, nullable=False)
                description = Column(Text,default='')

                status_id = Column(Integer, ForeignKey('md_funds_request_status.id'), nullable=False, default=1)
                
                """
                
                
                request_fund = TransactionRequestModel(
                    amount =token_data["amount"],
                    charges_amount = token_data["charges_amount"],
                    referenc_id = token_data["referenc_id"],
                    http_request_data = token_data["http_request_data"],
                    to_user_id = token_data["to_user_id"],
                    currency_id = token_data["currency_id"],
                    from_user_id = user_id,
                    description = token_data["description"]
                    
                )
                
                iso_code = ''
                if to_userwallet.currency_detils:
                    if to_userwallet.currency_detils.iso_code:
                        iso_code = to_userwallet.currency_detils.iso_code
                cr_msg = f"Requested for funds from {user_obj.name} {token_data['amount']} {iso_code}"
                
                req_notification = NotificationModel(user_id=to_userwallet.user_id,tenant_id=user_obj.tenant_id,description=cr_msg,category="REQUESTED_FOR_FUNDS",ref_id=auth_user["id"],status_category="REQUESTED_AMOUNT_TRNSFERED")
                db.add(req_notification)
                db.add(request_fund)
                db.commit()
                
                if request_fund.id:
                    datetime_obj = request_fund.created_on
                    date_part = datetime_obj.strftime("%d-%m-%Y")
                    time_part = datetime_obj.strftime("%I:%M %p")
                    
                    
                
                    msg = f"Request Created successfully"
                    mail_data = {"user_name":user_obj.name,"to_user_name":exists_ben.name,"source_amount":request_fund.amount,"transaction_id":request_fund.referenc_id,"date_part":date_part,"time_part": time_part}
                    background_tasks.add_task(Email.send_mail, recipient_email=[user_obj.email], subject="Funds Requst raised", template='funds_request_raised.html',data=mail_data )
                    
                    maildata = {"user_name":exists_ben.name,"from_user_name":user_obj.name,"transaction_id":request_fund.referenc_id,"date_part":date_part,"time_part": time_part}
                    background_tasks.add_task(Email.send_mail, recipient_email=[exists_ben.email], subject="Requested For Funds", template='funds_request_recevied.html',data=maildata )
            
                    return Utility.json_response(status=SUCCESS, message=msg, error=[], data={"request_id":request_fund.id},code="")
                else:
                    return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.INVALIED_OTP, error=[], data={},code="")
            
    except Exception as E:
        
        print(E)
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

@router.post("/request-list", response_description="list")
def request_list(request: TransactionListReq,auth_user=Depends(AuthHandler().auth_wrapper),db: Session = Depends(get_database_session)):
    try:

        user_id = auth_user["id"]
        tenant_id =auth_user["tenant_id"]
        user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
        if user_obj is None:            
            return Utility.json_response(status=500, message=all_messages.USER_NOT_EXISTS, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 1:
                return Utility.json_response(status=500, message=all_messages.PENDING_PROFILE_COMPLATION, error=[], data={},code="LOGOUT_ACCOUNT")
        
        elif user_obj.status_id == 2:
            return Utility.json_response(status=500, message=all_messages.PENDING_EMAIL_VERIFICATION, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 4:
            return Utility.json_response(status=500, message=all_messages.PROFILE_INACTIVE, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 5:
            return Utility.json_response(status=500, message=all_messages.PROFILE_DELETED, error=[], data={},code="LOGOUT_ACCOUNT")
        
        
        
        query = db.query(TransactionRequestModel).options(
                                                  joinedload(TransactionRequestModel.to_user_details),
                                                   joinedload(TransactionRequestModel.from_user_details),
                                                    joinedload(TransactionRequestModel.transactions))    
        #query = query.filter(TransactionModel.tenant_id==tenant_id)
        #if auth_user["role_id"] ==2:
        if request.category == "INBOX_REQUESTS":
            query = query.filter(TransactionRequestModel.to_user_id==user_id) 
        elif request.category == "SENT_REQUESTS": 
            query = query.filter( TransactionRequestModel.from_user_id==user_id)  
        else:
            query = query.filter( or_(TransactionRequestModel.from_user_id==user_id,  TransactionRequestModel.to_user_id==user_id))

        
        if request.search_string:
            search = f"%{request.search_string}%"
            query = query.filter(or_(TransactionRequestModel.referenc_id.ilike(search),  TransactionRequestModel.charges_amount.ilike(search),TransactionRequestModel.referenc_id.ilike(search)  ))
            
               
        if request.status_ids and len(request.status_ids)>0:
            query = query.filter(TransactionRequestModel.status_id.in_(request.status_ids))
        else:
            query = query.filter(TransactionRequestModel.status_id == 1)

        total_count = query.count()
        sort_column = getattr(TransactionRequestModel, request.sort_by, None)
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
        # Create a paginated response
        
        res_data ={ "total_count": total_count,"list":[],"page":request.page,"per_page":request.per_page}
        for item in paginated_query:
            #print(item.current_exchange_rate)
            acc = Utility.model_to_dict(item)
            acc["amount"] = float(acc["amount"])
            acc["charges_amount"] = float(acc["charges_amount"])
            #acc["ledger_amount"] = float(acc["ledger_amount"])
            #acc["current_exange_rate"] = float(acc["ledger_amount"])
            if "request_data" in acc:
                del acc["request_data"]
            type_transaction ="from_user_details"    
            if item.from_user_id:               

                beneficiary_details = Utility.model_to_dict(item.from_user_details)
                acc[type_transaction] = {}
                acc[type_transaction]["id"] = beneficiary_details["id"]
                acc[type_transaction]["full_name"] = beneficiary_details["name"]
                acc[type_transaction]["first_name"] = beneficiary_details["first_name"]
                acc[type_transaction]["last_name"] = beneficiary_details["last_name"]
                acc[type_transaction]["email"] = beneficiary_details["email"]
                acc[type_transaction]["mobile_no"] = beneficiary_details["mobile_no"]

            if item.to_user_id != auth_user["id"]:
                user_details = Utility.model_to_dict(item.to_user_details)
                acc["to_user_details"] = {}
                acc["to_user_details"]["id"] = user_details["id"]
                acc["to_user_details"]["first_name"] = user_details["first_name"]
                acc["to_user_details"]["last_name"] = user_details["last_name"]
                acc["to_user_details"]["name"] = user_details["name"]
                acc["to_user_details"]["email"] = user_details["email"]
                acc["to_user_details"]["status_id"] = user_details["status_id"]            
            if item.currency_id:
                c_details = db.query(MdCurrency).filter(MdCurrency.id==item.currency_id).first()
                if c_details is not None:
                    acc["currency_details"] = Utility.model_to_dict(c_details)

            
            res_data["list"].append(acc)
            
        return Utility.json_response(status=SUCCESS, message="", error=[], data=res_data,code="")

    except Exception as E:
        print(E)        
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})


@router.post("/request-details", response_description="Transaction Details")
def request_details(request: TransactionDetailsSchema,auth_user=Depends(AuthHandler().auth_wrapper),db: Session = Depends(get_database_session)):
    try:
        transaction_id = request.transaction_id
        user_id = auth_user["id"]
        user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
        if user_obj is None:            
            return Utility.json_response(status=500, message=all_messages.USER_NOT_EXISTS, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 1:
                return Utility.json_response(status=500, message=all_messages.PENDING_PROFILE_COMPLATION, error=[], data={},code="LOGOUT_ACCOUNT")
        
        elif user_obj.status_id == 2:
            return Utility.json_response(status=500, message=all_messages.PENDING_EMAIL_VERIFICATION, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 4:
            return Utility.json_response(status=500, message=all_messages.PROFILE_INACTIVE, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 5:
            return Utility.json_response(status=500, message=all_messages.PROFILE_DELETED, error=[], data={},code="LOGOUT_ACCOUNT")
        
        
        query = db.query(TransactionRequestModel)
        query = query.filter(TransactionRequestModel.id==transaction_id)   
        query = query.filter(or_(TransactionRequestModel.to_user_id==user_id, TransactionRequestModel.from_user_id==user_id) )        
        
        result = query.options(
            
                        joinedload(TransactionRequestModel.to_user_details),                        
                        joinedload(TransactionRequestModel.from_user_details)
            ).first()   
        if result is None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Transaction Request Not Found", error=[], data={})

        
        
        acc = Utility.model_to_dict(result)
        acc["amount"] = float(acc["amount"])
        acc["charges_amount"] = float(acc["charges_amount"])
        acc["transfer_amount"] = float(acc["transfer_amount"])
        
        if "request_data" in acc:
            del acc["request_data"]
        type_transaction ="from_user_details"    
        if result.from_user_details:
            

            beneficiary_details = Utility.model_to_dict(result.from_user_details)
            acc[type_transaction] = {}
            acc[type_transaction]["id"] = beneficiary_details["id"]
            acc[type_transaction]["full_name"] = beneficiary_details["full_name"]
            acc[type_transaction]["nick_name"] = beneficiary_details["nick_name"]
            acc[type_transaction]["email"] = beneficiary_details["email"]
            acc[type_transaction]["mobile_no"] = beneficiary_details["mobile_no"]

        if result.to_user_id:
            user_details = Utility.model_to_dict(result.to_user_details)
            acc["to_user_details"] = {}
            acc["to_user_details"]["id"] = user_details["id"]
            acc["to_user_details"]["first_name"] = user_details["first_name"]
            acc["to_user_details"]["last_name"] = user_details["last_name"]
            acc["to_user_details"]["name"] = user_details["name"]
            acc["to_user_details"]["email"] = user_details["email"]
            acc["to_user_details"]["status_id"] = user_details["status_id"]            
        

        return Utility.json_response(status=SUCCESS, message="Details are retrived successfully", error=[], data=acc)

    except Exception as E:
        print(E)        
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})

@router.post("/update-request-status", response_description="Transaction Details")
def request_details(request: UpdateRequestStatus,auth_user=Depends(AuthHandler().auth_wrapper),db: Session = Depends(get_database_session)):
    try:
        transaction_id = request.transaction_id
        status_id = request.status_id
        user_id = auth_user["id"]
        user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
        if user_obj is None:            
            return Utility.json_response(status=500, message=all_messages.USER_NOT_EXISTS, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 1:
                return Utility.json_response(status=500, message=all_messages.PENDING_PROFILE_COMPLATION, error=[], data={},code="LOGOUT_ACCOUNT")
        
        elif user_obj.status_id == 2:
            return Utility.json_response(status=500, message=all_messages.PENDING_EMAIL_VERIFICATION, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 4:
            return Utility.json_response(status=500, message=all_messages.PROFILE_INACTIVE, error=[], data={},code="LOGOUT_ACCOUNT")            
        elif user_obj.status_id == 5:
            return Utility.json_response(status=500, message=all_messages.PROFILE_DELETED, error=[], data={},code="LOGOUT_ACCOUNT")
        
        
        query = db.query(TransactionRequestModel)
        query = query.filter(TransactionRequestModel.id==transaction_id)   
        query = query.filter(or_(TransactionRequestModel.to_user_id==user_id, TransactionRequestModel.from_user_id==user_id) )        
        
        result = query.options(
            
                        joinedload(TransactionRequestModel.to_user_details),                        
                        joinedload(TransactionRequestModel.from_user_details)
            ).first()   
        if result is None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Transaction Request Not Found", error=[], data={})

        if result.status_id == status_id:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.REQUEST_IS_SAME_STATUS, error=[], data={},code="REQUEST_IS_SAME_STATUS")
        if result.status_id != 1:
            msg = "Request status is already updated"
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=msg, error=[], data={},code="")


        result.status_id = status_id
        return Utility.json_response(status=SUCCESS, message="Updated successfully", error=[], data={})

    except Exception as E:
        print(E)        
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})


@router.post("/get-otp-for-fund-request-approve", response_description="Transaction Details")
def get_otp_for_fund_request_transfer(request: getOtpForFundRequestTransferSchema,background_tasks:BackgroundTasks,auth_user=Depends(AuthHandler().auth_wrapper),db: Session = Depends(get_database_session)):
    try:
        transaction_id = request.transaction_request_id
        user_id = auth_user["id"]
        user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
        if user_obj is None:            
            return Utility.json_response(status=500, message=all_messages.USER_NOT_EXISTS, error=[], data={},code="LOGOUT_ACCOUNT")            
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
        
        
        
        transaction = db.query(TransactionModel).filter(TransactionModel.transaction_request_id==transaction_id).first()
        if transaction is not None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=f"Transaction Request Already settled", error=[], data={})
        query = db.query(TransactionRequestModel)
        query = query.filter(TransactionRequestModel.id==transaction_id,TransactionRequestModel.to_user_id==user_id)        
        
        result = query.options( joinedload(TransactionRequestModel.to_user_details), joinedload(TransactionRequestModel.from_user_details)).first()   
        if result is None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Transaction Request Not Found", error=[], data={})
        category = "APPROVE_REQUEST_FOR_FUNDS_TRANSFER"
        referenc_id = Utility.generatecode(code_for=category)
        exists_ben = db.query(UserModel).filter(UserModel.id == result.to_user_id).first()
        if exists_ben is None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.BENEFICIARY_NOT_EXISTS, error=[], data={},code="BENEFICIARY_NOT_EXISTS")

        elif exists_ben.kyc_status_id != 3:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Beneficiary is Not active", error=[], data={},code="BENEFICIARY_NOT_ACTIVE")
        req = GetSummary(

            currency_id =result.currency_id,
            transfer_amount = result.amount,
            description="",          
            to_user_id=user_id
        )
        allcharges = get_charges(db,req,auth_user,exists_ben.role_id,user_obj.role_id)
        otp = Utility.generate_otp()
        
        otpdata = { 
                  "amount":decimal.Decimal(result.amount),
                  "amount":allcharges["transfer_amount"],
                  "charges_amount":allcharges.get("charges_amount",0),
                  "admin_charges": allcharges.get("admin_charges",0),
                  "agent_charges": allcharges.get("agent_charges",0),
                  "referenc_id":referenc_id,
                  "http_request_data":json.dumps(allcharges),
                  "to_user_id": result.to_user_id,
                  "currency_id":result.currency_id,
                  "from_user_id": user_id,
                  "transaction_request_id":result.id,
                  "otp":otp

                    }
        
        token = AuthHandler().encode_token(otpdata,minutes=6)
        if Utility.inactive_previous_tokens(db=db, catrgory=category, user_id=user_id) == False:
                db.rollback()
                return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})
        
        token_data = tokensModel(ref_id=user_id,token=token,catrgory=category,user_id=user_id,otp=otp,active=True)
        db.add(token_data)
        db.commit()
        if token_data.id:
            mail_data = { "source_amount":result.amount,"otp":str(otp),"name":user_obj.first_name +" "+user_obj.last_name,"beneficiary_name":exists_ben.name,"transaction_id":referenc_id,'remmit_id':referenc_id,"track_id":referenc_id}
            background_tasks.add_task(Email.send_mail,recipient_email=[user_obj.email], subject="Fund Request Initiated", template='send_money.html',data=mail_data )
        
            return Utility.json_response(status=SUCCESS, message=all_messages.RESEND_VERIFICATION_OTP, error=[], data={"referenc_id":referenc_id},code="")
        else:
            db.rollback()
            return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})
        
        
    except Exception as E:
        print(E)        
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})


@router.post("/requested-funds-transfer", response_description="requested funds transfer")
def requestd_funds_transfer(request: ApproveRequestedFundsTransferSchema,background_tasks:BackgroundTasks,auth_user=Depends(AuthHandler().auth_wrapper),db: Session = Depends(get_database_session)):
    try:
        transaction_request_id = request.transaction_request_id
        otp = request.otp
        user_id = auth_user["id"]
        tenant_id = auth_user.get("tenant_id", None)
        
        user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
        if user_obj is None:            
            return Utility.json_response(status=500, message=all_messages.USER_NOT_EXISTS, error=[], data={},code="LOGOUT_ACCOUNT")            
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
        
        

        transaction = db.query(TransactionModel).filter(TransactionModel.transaction_request_id==transaction_request_id).first()
        if transaction is not None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Transaction Request Already settled", error=[], data={})

        query = db.query(TransactionRequestModel)
        query = query.filter(TransactionRequestModel.id==transaction_request_id,TransactionRequestModel.to_user_id==user_id)        
        
        transaction_request = query.options( joinedload(TransactionRequestModel.to_user_details), joinedload(TransactionRequestModel.from_user_details)).first()   
        if transaction_request is None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Transaction Request Not Found", error=[], data={})
        category = "APPROVE_REQUEST_FOR_FUNDS_TRANSFER"
        referenc_id = Utility.generatecode(code_for=category)
        #allcharges = get_charges(db,request,auth_user)
        
        if transaction_request.status_id not in [1]:
            message="Transaction Request Rejeted"
            if transaction_request.status_id ==2:
                message="Fund Request is Already Processed"
            if transaction_request.status_id ==3:
                message="Fund Request Rejected"
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=message, error=[], data={})
        
        
        token_query = db.query(tokensModel).filter(tokensModel.catrgory ==category, tokensModel.user_id==user_id, tokensModel.otp == otp,tokensModel.active==True).first()
        if token_query is None:
            return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.INVALIED_OTP, error=[], data={},code="")
        else:
            """
            from_user_id
            to_user_id
            currency_id
            amount
            charges_amount,
            http_request_data
            """
            token_data = AuthHandler().decode_otp_token(token_query.token)
            if token_data["to_user_id"] != user_id:
                return Utility.json_response(status=500, message=all_messages.NO_PERMISSIONS, error=[], data={},code="NO_PERMISSIONS")      

            if str(token_data["otp"]) != str(otp):
                return Utility.json_response(status=500, message=all_messages.INVALIED_OTP, error=[], data={},code="INVALIED_OTP")
            
            
            exists_ben = db.query(UserModel).filter(UserModel.id == transaction_request.from_user_id).first()
            if exists_ben is None:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.BENEFICIARY_NOT_EXISTS, error=[], data={},code="BENEFICIARY_NOT_EXISTS")

            elif exists_ben.kyc_status_id != 3:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Beneficiary is Not active", error=[], data={},code="BENEFICIARY_NOT_ACTIVE")

            
            from_userwallet =  db.query(UserWalletModel).filter(UserWalletModel.user_id==transaction_request.to_user_id, UserWalletModel.currency_id == token_data["currency_id"]).first()  
            to_userwallet   =  db.query(UserWalletModel).filter(UserWalletModel.user_id==transaction_request.from_user_id, UserWalletModel.currency_id == token_data["currency_id"]).first()  
            if from_userwallet is None:
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Account has no sufficient balance", error=[], data={},code="NO_SUFFICIENT_BALANCE")
            
            if from_userwallet.balance < token_data["amount"]+token_data["charges_amount"]:
                    return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message="Account has no sufficient balance", error=[], data={},code="NO_SUFFICIENT_BALANCE")
                
            admin_details = db.query(AdminUser).filter(AdminUser.tenant_id==tenant_id, AdminUser.role_id==3).first()
            admin_wallet = None
            if admin_details is not None:
                admin_wallet = db.query(AdminWalletModel).filter(AdminWalletModel.admin_id==admin_details.id,AdminWalletModel.currency_id==token_data["currency_id"]).first()
            
            shared_transaction_id = Utility.generate_random_string()
            
            debet_amount = decimal.Decimal(token_data["amount"])+decimal.Decimal(token_data["charges_amount"])
            cr_msg = f"{token_data['amount']} is Credited from {user_obj.name}"
            cr_transaction = TransactionModel(
                    shared_transaction_id = shared_transaction_id,
                    transaction_request_id =transaction_request_id,
                    transaction_type ="CREDIT",
                    referenc_id = Utility.generatecode("CREDIT"),
                    amount=token_data["amount"],
                    charges_amount = token_data["charges_amount"],
                    user_id = token_data["from_user_id"],
                    credited_from_user_id = token_data["to_user_id"],
                    currency_id = token_data["currency_id"],
                    status_id = 3, #1== Initiated, 2== In-Progress, 3 == Completed, 4== Failed
                    tenant_id = tenant_id,
                    request_data = token_data["http_request_data"],
                     
                    
                )
                
            debet_transaction = TransactionModel(
                shared_transaction_id = shared_transaction_id,
                transaction_request_id =transaction_request_id,
                referenc_id = Utility.generatecode("DEBIT"),
                transaction_type ="DEBIT",
                amount= debet_amount,
                charges_amount = token_data["charges_amount"],
                user_id = from_userwallet.user_id,
                credited_from_user_id = token_data["from_user_id"],
                currency_id = token_data["currency_id"],
                status_id = 3, #1== Initiated, 2== In-Progress, 3 == Completed, 4== Failed
                tenant_id = tenant_id,
                request_data = token_data["http_request_data"], 
                
            )
            admin_transaction  =None
            if admin_details is not None and token_data.get("admin_charges",None) is not None:
                if token_data.get("admin_charges",0)>0:                    
                    admin_transaction = AdminTransactionModel(transaction_request_id =transaction_request_id,shared_transaction_id = shared_transaction_id,referenc_id = Utility.generatecode("CREDIT"),transaction_type ="CREDIT",amount=token_data["admin_charges"],
                    charges_amount = token_data["admin_charges"],admin_id = admin_details.id,credited_from_user_id = token_data["from_user_id"],currency_id = token_data["currency_id"],
                    status_id = 3,tenant_id = tenant_id,request_data = token_data["http_request_data"])
                    db.add(admin_transaction)
                    
            #funds transfor from  user to agent         
            if user_obj.role_id==5 and exists_ben.role_id ==2:
                
                charges_transaction = TransactionModel(
                    shared_transaction_id = shared_transaction_id,
                    transaction_request_id =transaction_request_id,
                    transaction_type ="CREDIT",
                    credit_type="CHARGES",
                    referenc_id = Utility.generatecode("CREDIT"),
                    amount=decimal.Decimal(token_data["agent_charges"]),
                    charges_amount = token_data["charges_amount"],
                    user_id = transaction_request.from_user_id,
                    credited_from_user_id = transaction_request.to_user_id,
                    currency_id = token_data["currency_id"],
                    status_id = 3, #1== Initiated, 2== In-Progress, 3 == Completed, 4== Failed
                    tenant_id = tenant_id,
                    request_data = token_data["http_request_data"]
                )
                db.add(charges_transaction)

                
            msg = f"{debet_amount} is debeted and creditaed to {exists_ben.name}"
            msg_recevied ="f{cr_transaction.amount} is recevied from {user_obj.name}"
            from_user_notification = NotificationModel(user_id=from_userwallet.user_id,tenant_id=user_obj.tenant_id,description=msg,category="REQUESTED_AMOUNT_TRNSFERED",ref_id=auth_user["id"],status_category="REQUESTED_AMOUNT_TRNSFERED")
            db.add(from_user_notification)
            
            db.add(debet_transaction)
            db.add(cr_transaction)
            db.commit()
            if cr_transaction.id:
                token_query.active = False
                cr_transaction.status_id = 3
                transaction_request.status_id =2
                
                if to_userwallet is None:
                    to_userwallet = UserWalletModel(user_id=transaction_request.from_user_id,currency_id=cr_transaction.currency_id,balance = cr_transaction.amount,credited_by=cr_transaction.credited_from_user_id )
                    cr_transaction.ledger_amount =0
                    
                    debet_transaction.ledger_amount = copy.deepcopy(from_userwallet.balance)
                    from_userwallet.balance -= debet_amount
                    db.add(to_userwallet)
                    to_user_notification = NotificationModel(user_id=transaction_request.from_user_id,tenant_id=user_obj.tenant_id,description=msg_recevied,category="REQUESTED_AMOUNT_RECEIVED",ref_id=auth_user["id"],status_category="REQUESTED_AMOUNT_RECEIVED")
                    db.add(to_user_notification)
                    db.commit()
                else:
                    print("sgf sfgdsf ")
                    cr_transaction.ledger_amount = copy.deepcopy(to_userwallet.balance)
                    to_userwallet.balance += decimal.Decimal(cr_transaction.amount)
                    from_userwallet.balance -= debet_amount
                    #to_user_notification = NotificationModel(user_id=to_userwallet.user_id,tenant_id=user_obj.tenant_id,description=msg_recevied,category="REQUESTED_AMOUNT_RECEIVED",ref_id=auth_user["id"],status_category="REQUESTED_AMOUNT_RECEIVED")
                    #db.add(to_user_notification)
                    db.commit()


                #add amount to Admin wallets
                if admin_details is not None and token_data.get("admin_charges",None) is not None and admin_transaction is not None:
                        if token_data.get("admin_charges",0)>0 and admin_transaction.id:
                            if admin_wallet is not None :
                                admin_transaction.ledger_amount = copy.deepcopy(admin_wallet.balance)
                                admin_wallet.balance += decimal.Decimal(token_data["admin_charges"])
                            else:
                                admin_new_wallet = AdminWalletModel(admin_id=admin_details.id,currency_id=cr_transaction.currency_id,balance = token_data["admin_charges"],credited_by=cr_transaction.credited_from_user_id )
                                db.add(admin_new_wallet)
                                admin_transaction.ledger_amount = 0


                db.commit()
                datetime_obj = cr_transaction.created_on
                date_part = datetime_obj.strftime("%d-%m-%Y")
                time_part = datetime_obj.strftime("%I:%M %p")
                mail_data = {"name":user_obj.first_name +" "+user_obj.last_name,"beneficiary_name":exists_ben.name,"source_amount":f"{cr_transaction.amount} {from_userwallet.currency_detils.iso_code}","transaction_id":cr_transaction.referenc_id,"date_part":date_part,"time_part": time_part}
                
                status_msg = "Activated"
                msg = f"Amount transferred successfully"
                # mail_data = {"user_name":user_obj.name,"message":f'''{exists_ben.full_name} payment trancaction has been Activated successfully!'''}
                background_tasks.add_task(Email.send_mail, recipient_email=[user_obj.email], subject=msg, template='transaction_activate.html',data=mail_data )
        
                return Utility.json_response(status=SUCCESS, message=msg, error=[], data={"transaction_id":cr_transaction.id},code="")
            else:
                db.rollback()
                return Utility.json_response(status=BUSINESS_LOGIG_ERROR, message=all_messages.INVALIED_OTP, error=[], data={},code="")
        
    except Exception as E:
        print(E)        
        db.rollback()
        return Utility.json_response(status=INTERNAL_ERROR, message=all_messages.SOMTHING_WRONG, error=[], data={})
