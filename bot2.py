import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    CallbackContext,
    MessageHandler,
    # Filters
)

from database import Database
from config import BOT_TOKEN, ADMIN_IDS
from user_handlers import manage_users, user_actions, toggle_admin, toggle_block
from admin_handlers import (
    add_category_start, 
    category_name, 
    category_parent,
    add_file_start,
    cancel
)
from support import show_support_menu, handle_support_message, show_faq

# تنظیم logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

db = Database()

def get_main_keyboard(user_id: int):
    keyboard = []
    keyboard.append([InlineKeyboardButton("👤 پنل کاربری", callback_data="user_panel")])
    
    if db.is_admin(user_id):
        keyboard.append([InlineKeyboardButton("👨‍💼 پنل مدیریت", callback_data="admin_panel")])
    
    return InlineKeyboardMarkup(keyboard)

def start(update: Update, context: CallbackContext):
    try:
        user = update.effective_user
        user_id = user.id
        
        if not db.get_user(user_id):
            db.add_user(user_id, user.full_name)
            logger.info(f"New user registered: {user_id}")
        
        welcome_text = (
            f"👋 سلام {user.full_name}!\n"
            "به ربات فروشگاهی خوش آمدید."
        )
        
        update.message.reply_text(
            welcome_text,
            reply_markup=get_main_keyboard(user_id)
        )
        
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        update.message.reply_text("متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید.")

def user_panel(update: Update, context: CallbackContext):
    try:
        query = update.callback_query
        keyboard = [
            [
                InlineKeyboardButton("📁 دسته‌بندی‌ها", callback_data="show_categories"),
                InlineKeyboardButton("📂 فایل‌های من", callback_data="my_files")
            ],
            [InlineKeyboardButton("📞 پشتیبانی", callback_data="support")],
            [InlineKeyboardButton("🏠 بازگشت", callback_data="back_to_main")]
        ]
        
        query.edit_message_text(
            "🎯 پنل کاربری\nلطفا یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        logger.error(f"Error in user panel: {e}")
        query.answer("خطایی رخ داد!", show_alert=True)

def admin_panel(update: Update, context: CallbackContext):
    try:
        query = update.callback_query
        user_id = query.from_user.id
        
        if not db.is_admin(user_id):
            query.answer("شما دسترسی ادمین ندارید!", show_alert=True)
            return
        
        keyboard = [
            [
                InlineKeyboardButton("➕ افزودن دسته‌بندی", callback_data="add_category"),
                InlineKeyboardButton("➕ افزودن فایل", callback_data="add_file")
            ],
            [
                InlineKeyboardButton("👥 مدیریت کاربران", callback_data="manage_users"),
                InlineKeyboardButton("📞 پشتیبانی", callback_data="admin_support")
            ],
            [InlineKeyboardButton("🏠 بازگشت", callback_data="back_to_main")]
        ]
        
        query.edit_message_text(
            "👨‍💼 پنل مدیریت\nلطفا یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        logger.error(f"Error in admin panel: {e}")
        query.answer("خطایی رخ داد!", show_alert=True)

def button_handler(update: Update, context: CallbackContext):
    try:
        query = update.callback_query
        data = query.data
        user_id = query.from_user.id
        
        logger.info(f"Callback received: {data} from user {user_id}")
        
        if data == "back_to_main":
            query.edit_message_text(
                "منوی اصلی:",
                reply_markup=get_main_keyboard(user_id)
            )
            return
            
        handlers = {
            "user_panel": user_panel,
            "admin_panel": admin_panel,
            "show_categories": show_categories,
            "my_files": show_my_files,
            "support": show_support_menu,
            "manage_users": manage_users,
            "add_category": add_category_start,
            "add_file": add_file_start
        }
        
        if data in handlers:
            handlers[data](update, context)
        else:
            logger.warning(f"Unknown callback data: {data}")
            query.answer("دستور نامعتبر!", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error processing callback: {e}")
        query.answer("خطایی رخ داد. لطفاً دوباره تلاش کنید.", show_alert=True)

def error_handler(update: Update, context: CallbackContext):
    logger.error(f"Update {update} caused error {context.error}")

def main():
    try:
        updater = Updater(BOT_TOKEN)
        dp = updater.dispatcher

        # Command handlers
        dp.add_handler(CommandHandler("start", start))
        
        # Conversation handlers for admin actions
        conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(add_category_start, pattern="^add_category$"),
                CallbackQueryHandler(add_file_start, pattern="^add_file$")
            ],
            states={
                'CATEGORY_NAME': [MessageHandler(Filters.text & ~Filters.command, category_name)],
                'CATEGORY_PARENT': [CallbackQueryHandler(category_parent)],
                # اضافه کردن state های دیگر برای add_file
            },
            fallbacks=[CommandHandler("cancel", cancel)]
        )
        dp.add_handler(conv_handler)
        
        # Callback Query Handler
        dp.add_handler(CallbackQueryHandler(button_handler))
        
        # Error Handler
        dp.add_error_handler(error_handler)
        
        logger.info("Bot started!")
        updater.start_polling()
        updater.idle()
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")

if __name__ == '__main__':
    main()
