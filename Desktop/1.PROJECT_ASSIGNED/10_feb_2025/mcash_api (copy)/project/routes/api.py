from fastapi import APIRouter
from project.endpoints.user_auth import user_authentication
from project.endpoints.admin_auth import admin_authentication
from ..endpoints.master_data import master_data
from ..endpoints.tickets_request import tickets_request
from ..endpoints.user import user
from ..endpoints.notifications import notifications,admin_notifications
from ..endpoints.admin import coupon
from ..endpoints.transactions import transactions
from ..endpoints.currency import currency
from ..endpoints.merchant import merchant
from ..endpoints.agent import agent

router = APIRouter()
# --------------------Admin Routing--------------------
router.include_router(admin_authentication.router)

# --------------------merchant Routing--------------------
#router.include_router(merchant.router)

# --------------------agent Routing--------------------
#router.include_router(agent.router)


# --------------------Authenticatio Routing---------------------
router.include_router(user_authentication.router)


# --------------------User Routing---------------------
router.include_router(user.router)

#--------------------User Routing---------------------
router.include_router(tickets_request.router)

#--------------------transactions---------------------
router.include_router(transactions.router)



#----------------------Coupon Routing--------------------
router.include_router(coupon.router)

#---------------------notifications---------------------
router.include_router(notifications.router)
router.include_router(admin_notifications.router)


router.include_router(currency.router)


# --------------------master data Routing--------------------
router.include_router(master_data.router)
