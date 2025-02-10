# services/razorpay_service.py

import razorpay
from fastapi import HTTPException
from ..aploger import AppLogger
import hmac
import hashlib
import os

key_id = os.getenv("RAZORPAY_KEY_ID", "rzp_test_rAye2CW0Kqx4If")
key_secret = os.getenv("RAZORPAY_KEY_SECRET","DuqBIo8eYeZ7QaGuHadEo4GS")


class RazorpayClient:
    def __init__(self, key_id: str, key_secret: str):
        self.client = razorpay.Client(auth=(key_id, key_secret))

    def create_order(self, amount: int, currency: str = "INR") -> dict:
        try:
            # Convert amount to paise
            amount_in_paise = amount * 100
            order = self.client.order.create({
                'amount': amount_in_paise,
                'currency': currency,
                'payment_capture': '1'
            })
            razorpay_order_id = order.get("id")
            response = {
                "status": True,
                "razorpay_order_id": razorpay_order_id,
                "amount": amount_in_paise,
                "currency": currency,
                "order_details": order
            }
            return response
        except Exception as e:
            AppLogger.error(f"Error creating order: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Error creating order: {str(e)}")

    def fetch_order(self, order_id: str) -> dict:
        try:
            order = self.client.order.fetch(order_id)
            return order
        except Exception as e:
            AppLogger.error(f"Error fetching order: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Error fetching order: {str(e)}")

    def _generate_payment_id(self, order_id: str) -> str:
        return f"dummy_payment_id_{order_id}"

    def _generate_signature(self, order_id: str, payment_id: str) -> str:
        string = f"razorpay_order_id={order_id}|razorpay_payment_id={payment_id}"
        return hashlib.sha256(f"{string}|{key_secret}".encode('utf-8')).hexdigest()

    def _validate_signature(self, razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> bool:
        try:
            data = f"{razorpay_order_id}|{razorpay_payment_id}"
            generated_signature = hmac.new(
                key_secret.encode('utf-8'),
                data.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            if razorpay_signature == generated_signature:
                return True
            else:
                raise HTTPException(status_code=400, detail="Signature mismatch")
        except Exception as e:
            AppLogger.error(f"Error validating signature: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Error validating signature: {str(e)}")

    def check_payment_status_by_payment_id(self, payment_id: str) -> dict:
        
        try:
            payment = self.client.payment.fetch(payment_id)  # Fetch payment details
            payment_status = payment.get("status", "unknown")  # Get the status of the payment
            print(payment)
            response = {
                "status": True,
                "payment_status": payment_status,
                "payment_details": payment
            }
            return response
        except Exception as e:
            AppLogger.error(f"Error fetching payment status: {str(e)}")
            return None

    
def get_razorpay_client() -> RazorpayClient:
    razorpay_client = RazorpayClient(key_id=key_id, key_secret=key_secret)
    return razorpay_client
