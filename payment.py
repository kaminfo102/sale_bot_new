# payment.py
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Database
import json
import datetime

db = Database()

MERCHANT_ID = "YOUR_ZARINPAL_MERCHANT_ID"
CALLBACK_URL = "YOUR_CALLBACK_URL"
ZARINPAL_REQUEST_URL = "https://api.zarinpal.com/pg/v4/payment/request.json"
ZARINPAL_VERIFY_URL = "https://api.zarinpal.com/pg/v4/payment/verify.json"
ZARINPAL_START_URL = "https://www.zarinpal.com/pg/StartPay/"

async def start_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()
    
    file_id = int(query.data.split("_")[1])
    file_info = db.get_file_info(file_id)
    
    if not file_info:
        await query.edit_message_text("فایل مورد نظر یافت نشد.")
        return
        
    amount = file_info['price']  # مبلغ به تومان
    description = f"خرید فایل {file_info['title']}"
    
    payment_data = {
        "merchant_id": MERCHANT_ID,
        "amount": amount,
        "description": description,
        "callback_url": f"{CALLBACK_URL}?user_id={update.effective_user.id}&file_id={file_id}",
    }
    
    try:
        response = requests.post(ZARINPAL_REQUEST_URL, json=payment_data)
        response_data = response.json()
        
        if response_data['data']['code'] == 100:
            authority = response_data['data']['authority']
            
            # ذخیره اطلاعات پرداخت در دیتابیس
            db.create_payment(
                user_id=update.effective_user.id,
                file_id=file_id,
                amount=amount,
                authority=authority,
                status='pending'
            )
            
            payment_url = f"{ZARINPAL_START_URL}{authority}"
            
            keyboard = [
                [InlineKeyboardButton("پرداخت", url=payment_url)],
                [InlineKeyboardButton("انصراف", callback_data=f"cancel_payment_{authority}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"لطفا برای پرداخت مبلغ {amount:,} تومان روی دکمه پرداخت کلیک کنید.",
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_text("خطا در ایجاد تراکنش. لطفا بعدا تلاش کنید.")
            
    except Exception as e:
        print(f"Payment error: {str(e)}")
        await query.edit_message_text("خطا در برقراری ارتباط با درگاه پرداخت.")

async def verify_payment(authority: str, amount: int):
    verify_data = {
        "merchant_id": MERCHANT_ID,
        "authority": authority,
        "amount": amount
    }
    
    try:
        response = requests.post(ZARINPAL_VERIFY_URL, json=verify_data)
        response_data = response.json()
        
        if response_data['data']['code'] == 100:
            ref_id = response_data['data']['ref_id']
            db.update_payment_status(authority, 'completed', ref_id)
            return True
        else:
            db.update_payment_status(authority, 'failed')
            return False
            
    except Exception as e:
        print(f"Verify error: {str(e)}")
        db.update_payment_status(authority, 'failed')
        return False

class Payment:
    def __init__(self):
        self.MERCHANT_ID = "YOUR_ZARINPAL_MERCHANT_ID"
        self.CALLBACK_URL = "YOUR_CALLBACK_URL"
        self.ZARINPAL_REQUEST_URL = "https://api.zarinpal.com/pg/v4/payment/request.json"
        self.ZARINPAL_VERIFY_URL = "https://api.zarinpal.com/pg/v4/payment/verify.json"
        self.ZARINPAL_START_URL = "https://www.zarinpal.com/pg/StartPay/"
        self.db = Database()

    def create_payment(self, amount: int, user_id: int, file_id: int) -> str:
        payment_data = {
            "merchant_id": self.MERCHANT_ID,
            "amount": amount,
            "description": f"خرید فایل {file_id}",
            "callback_url": f"{self.CALLBACK_URL}?user_id={user_id}&file_id={file_id}",
        }
        
        try:
            response = requests.post(self.ZARINPAL_REQUEST_URL, json=payment_data)
            response_data = response.json()
            
            if response_data['data']['code'] == 100:
                authority = response_data['data']['authority']
                
                # ذخیره اطلاعات پرداخت در دیتابیس
                self.db.create_payment(
                    user_id=user_id,
                    file_id=file_id,
                    amount=amount,
                    authority=authority,
                    status='pending'
                )
                
                return f"{self.ZARINPAL_START_URL}{authority}"
                
        except Exception as e:
            print(f"Payment error: {str(e)}")
            return None

    async def verify_payment(self, authority: str, amount: int):
        verify_data = {
            "merchant_id": self.MERCHANT_ID,
            "authority": authority,
            "amount": amount
        }
        
        try:
            response = requests.post(self.ZARINPAL_VERIFY_URL, json=verify_data)
            response_data = response.json()
            
            if response_data['data']['code'] == 100:
                ref_id = response_data['data']['ref_id']
                self.db.update_payment_status(authority, 'completed', ref_id)
                return True
            else:
                self.db.update_payment_status(authority, 'failed')
                return False
                
        except Exception as e:
            print(f"Verify error: {str(e)}")
            self.db.update_payment_status(authority, 'failed')
            return False
