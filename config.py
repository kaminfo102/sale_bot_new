# config.py
import os
from dotenv import load_dotenv

# بارگذاری تنظیمات از فایل .env
load_dotenv()

# تنظیمات اصلی
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = list(map(int, os.getenv('ADMIN_IDS', '').split(',')))
MERCHANT_ID = os.getenv('MERCHANT_ID')
CALLBACK_URL = os.getenv('CALLBACK_URL')

# تنظیمات دیتابیس
DATABASE_PATH = os.getenv('DATABASE_PATH', 'bot.db')

# تنظیمات فایل‌ها
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'files/')
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 50 * 1024 * 1024))  # 50MB
ALLOWED_EXTENSIONS = set(os.getenv('ALLOWED_EXTENSIONS', 'pdf,zip,rar,doc,docx,xls,xlsx').split(','))

# تنظیمات کش
CACHE_TTL = int(os.getenv('CACHE_TTL', 3600))
CACHE_SIZE = int(os.getenv('CACHE_SIZE', 128))

# تنظیمات امنیتی
RATE_LIMIT = int(os.getenv('RATE_LIMIT', 30))  # تعداد درخواست در دقیقه
BAN_DURATION = int(os.getenv('BAN_DURATION', 24 * 60 * 60))  # مدت زمان مسدودیت به ثانیه

# پیام‌های پیش‌فرض
DEFAULT_MESSAGES = {
    'welcome': os.getenv('WELCOME_MESSAGE', 'به ربات خوش آمدید!'),
    'help': os.getenv('HELP_MESSAGE', 'راهنمای استفاده از ربات'),
    'not_found': os.getenv('NOT_FOUND_MESSAGE', 'موردی یافت نشد.'),
    'access_denied': os.getenv('ACCESS_DENIED_MESSAGE', 'شما دسترسی به این بخش را ندارید.')
}

# تنظیمات پرداخت
PAYMENT = {
    'merchant_id': MERCHANT_ID,
    'callback_url': CALLBACK_URL,
    'description': os.getenv('PAYMENT_DESCRIPTION', 'پرداخت از طریق ربات'),
    'sandbox': os.getenv('PAYMENT_SANDBOX', 'false').lower() == 'true'
}

# تنظیمات پشتیبانی
SUPPORT = {
    'admin_ids': list(map(int, os.getenv('SUPPORT_ADMIN_IDS', '').split(','))),
    'working_hours': os.getenv('SUPPORT_HOURS', '9-21'),
    'auto_reply': os.getenv('AUTO_REPLY', 'true').lower() == 'true'
}
