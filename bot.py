from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes
)
import logging
from datetime import datetime
import os

from config import (
    BOT_TOKEN, 
    ADMIN_IDS, 
    UPLOAD_FOLDER, 
    MAX_FILE_SIZE, 
    ALLOWED_EXTENSIONS,
    DEFAULT_MESSAGES
)
from database import Database
from cache import Cache, cached
from file_manager import FileManager
from payment import Payment
from support import Support

# تنظیم لاگینگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ایجاد نمونه‌های مورد نیاز
db = Database()
cache = Cache()
file_manager = FileManager()
payment = Payment()
support = Support()

# حالت‌های مکالمه
(
    MAIN_MENU,
    CATEGORY_SELECT,
    FILE_SELECT,
    PAYMENT_PROCESS,
    SUPPORT_CHAT,
    ADMIN_MENU,
    WAITING_CATEGORY_NAME,
    WAITING_FILE_TITLE,
    WAITING_FILE_DESCRIPTION,
    WAITING_FILE_PRICE,
    WAITING_FILE_IMAGE,
    WAITING_FILE_UPLOAD,
) = range(12)

# توابع کمکی
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    context.user_data.clear()
    
    if is_admin(user.id):
        keyboard = [
            [InlineKeyboardButton("👤 پنل کاربری", callback_data="user_panel")],
            [InlineKeyboardButton("👨‍💻 پنل مدیریت", callback_data="admin_panel")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("📁 دسته‌بندی‌ها", callback_data="categories")],
            [InlineKeyboardButton("🔍 جستجو", callback_data="search")],
            [InlineKeyboardButton("👤 پروفایل من", callback_data="profile")],
            [InlineKeyboardButton("📞 پشتیبانی", callback_data="support")]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"سلام {user.first_name} عزیز! 👋\n" + DEFAULT_MESSAGES['welcome'],
        reply_markup=reply_markup
    )
    return MAIN_MENU

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.edit_message_text(DEFAULT_MESSAGES['access_denied'])
        return MAIN_MENU
    
    keyboard = [
        [InlineKeyboardButton("📁 مدیریت دسته‌بندی‌ها", callback_data="admin_categories")],
        [InlineKeyboardButton("🗂 مدیریت فایل‌ها", callback_data="admin_files")],
        [InlineKeyboardButton("💰 مدیریت پرداخت‌ها", callback_data="admin_payments")],
        [InlineKeyboardButton("👥 مدیریت کاربران", callback_data="admin_users")],
        [InlineKeyboardButton("📊 گزارش‌ها", callback_data="admin_reports")],
        [InlineKeyboardButton("⚙️ تنظیمات", callback_data="admin_settings")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "👨‍💻 پنل مدیریت\n"
        "لطفا یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=reply_markup
    )
    return ADMIN_MENU

@cached(ttl=300)  # کش برای 5 دقیقه
async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    categories = db.get_categories()
    keyboard = []
    
    for cat in categories:
        keyboard.append([
            InlineKeyboardButton(
                f"📁 {cat['name']} ({cat['file_count']})",
                callback_data=f"cat_{cat['id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 برگشت", callback_data="main_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📁 دسته‌بندی‌های موجود:\n"
        "لطفا یک دسته‌بندی را انتخاب کنید:",
        reply_markup=reply_markup
    )
    return CATEGORY_SELECT

async def show_category_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    category_id = int(query.data.split("_")[1])
    files = db.get_category_files(category_id)
    category = db.get_category(category_id)
    
    keyboard = []
    for file in files:
        keyboard.append([
            InlineKeyboardButton(
                f"📄 {file['title']} - {file['price']:,} تومان",
                callback_data=f"file_{file['id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 برگشت", callback_data="categories")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"📁 دسته‌بندی: {category['name']}\n"
        f"تعداد فایل‌ها: {len(files)}\n\n"
        "لطفا فایل مورد نظر خود را انتخاب کنید:",
        reply_markup=reply_markup
    )
    return FILE_SELECT

async def show_file_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    file_id = int(query.data.split("_")[1])
    file_info = db.get_file_info(file_id)
    
    if not file_info:
        await query.edit_message_text("❌ فایل مورد نظر یافت نشد.")
        return MAIN_MENU
    
    keyboard = [
        [InlineKeyboardButton("💰 خرید و دانلود", callback_data=f"buy_{file_id}")],
        [InlineKeyboardButton("🔙 برگشت", callback_data=f"cat_{file_info['category_id']}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = f"📄 {file_info['title']}\n\n"
    message += f"توضیحات: {file_info['description']}\n"
    message += f"قیمت: {file_info['price']:,} تومان\n"
    message += f"حجم فایل: {file_info['file_size'] // 1024:,} KB\n"
    message += f"تعداد دانلود: {file_info['download_count']}\n"
    
    if file_info['image_id']:
        await query.message.reply_photo(
            file_info['image_id'],
            caption=message,
            reply_markup=reply_markup
        )
        await query.message.delete()
    else:
        await query.edit_message_text(
            message,
            reply_markup=reply_markup
        )
    
    return FILE_SELECT

async def process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    file_id = int(query.data.split("_")[1])
    file_info = db.get_file_info(file_id)
    
    if not file_info:
        await query.edit_message_text("❌ فایل مورد نظر یافت نشد.")
        return MAIN_MENU
    
    # بررسی خرید قبلی
    if db.check_purchase(query.from_user.id, file_id):
        keyboard = [
            [InlineKeyboardButton("📥 دانلود فایل", callback_data=f"download_{file_id}")],
            [InlineKeyboardButton("🔙 برگشت", callback_data=f"file_{file_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "✅ شما قبلاً این فایل را خریداری کرده‌اید.\n"
            "می‌توانید آن را دانلود کنید:",
            reply_markup=reply_markup
        )
        return FILE_SELECT
    
    # ایجاد لینک پرداخت
    payment_link = payment.create_payment(
        amount=file_info['price'],
        user_id=query.from_user.id,
        file_id=file_id
    )
    
    keyboard = [
        [InlineKeyboardButton("💳 پرداخت", url=payment_link)],
        [InlineKeyboardButton("🔙 برگشت", callback_data=f"file_{file_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"💰 مبلغ قابل پرداخت: {file_info['price']:,} تومان\n"
        "برای پرداخت روی دکمه زیر کلیک کنید:",
        reply_markup=reply_markup
    )
    return PAYMENT_PROCESS

async def download_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    file_id = int(query.data.split("_")[1])
    
    if not db.check_purchase(query.from_user.id, file_id):
        keyboard = [
            [InlineKeyboardButton("💰 خرید فایل", callback_data=f"buy_{file_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "❌ شما هنوز این فایل را خریداری نکرده‌اید!",
            reply_markup=reply_markup
        )
        return FILE_SELECT
    
    file_info = db.get_file_info(file_id)
    
    if not file_info:
        await query.edit_message_text("❌ فایل مورد نظر یافت نشد.")
        return MAIN_MENU
    
    try:
        await context.bot.send_document(
            chat_id=query.message.chat_id,
            document=file_info['telegram_file_id'],
            filename=file_info['file_name'],
            caption=f"📥 دانلود فایل: {file_info['title']}"
        )
        
        # بروزرسانی تعداد دانلود
        db.increment_download_count(file_id)
        
    except Exception as e:
        logger.error(f"Error sending file: {e}")
        await query.edit_message_text(
            "❌ خطا در دانلود فایل. لطفا با پشتیبانی تماس بگیرید."
        )
    
    return FILE_SELECT

async def support_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📝 ارسال پیام", callback_data="new_ticket")],
        [InlineKeyboardButton("📜 تیکت‌های من", callback_data="my_tickets")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📞 پشتیبانی\n"
        "چگونه می‌توانیم به شما کمک کنیم؟",
        reply_markup=reply_markup
    )
    return SUPPORT_CHAT

def main():
    # ایجاد پوشه‌های مورد نیاز
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    # ایجاد و راه‌اندازی ربات
    application = Application.builder().token(BOT_TOKEN).build()
    
    # تعریف هندلرها
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(admin_panel, pattern='^admin_panel$'),
                CallbackQueryHandler(show_categories, pattern='^categories$'),
                CallbackQueryHandler(support_chat, pattern='^support$'),
            ],
            ADMIN_MENU: [
                # هندلرهای پنل ادمین
            ],
            CATEGORY_SELECT: [
                CallbackQueryHandler(show_category_files, pattern='^cat_'),
                CallbackQueryHandler(start, pattern='^main_menu$'),
            ],
            FILE_SELECT: [
                CallbackQueryHandler(show_file_details, pattern='^file_'),
                CallbackQueryHandler(process_payment, pattern='^buy_'),
                CallbackQueryHandler(download_file, pattern='^download_'),
                CallbackQueryHandler(show_categories, pattern='^categories$'),
            ],
            PAYMENT_PROCESS: [
                # هندلرهای پرداخت
            ],
            SUPPORT_CHAT: [
                # هندلرهای چت پشتیبانی
            ],
        },
        fallbacks=[CommandHandler('start', start)],
    )
    
    application.add_handler(conv_handler)
    
    # شروع ربات
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
