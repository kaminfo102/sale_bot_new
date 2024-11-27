# user_handlers.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Database

db = Database()

async def manage_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not db.is_admin(update.effective_user.id):
        await query.edit_message_text("شما دسترسی ادمین ندارید.")
        return
    
    users = db.get_all_users()
    keyboard = []
    
    for user in users:
        user_id, username, is_admin, is_blocked = user[:4]
        status = "🔴" if is_blocked else "🟢"
        admin_status = "👑" if is_admin else ""
        
        keyboard.append([
            InlineKeyboardButton(
                f"{status} {username or user_id} {admin_status}",
                callback_data=f"user_{user_id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 برگشت", callback_data="admin_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "لیست کاربران:\n"
        "🟢 = فعال | 🔴 = مسدود | 👑 = ادمین",
        reply_markup=reply_markup
    )

async def user_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not db.is_admin(update.effective_user.id):
        await query.edit_message_text("شما دسترسی ادمین ندارید.")
        return
    
    user_id = int(query.data.split("_")[1])
    user = db.get_user(user_id)
    
    if not user:
        await query.edit_message_text("کاربر یافت نشد.")
        return
    
    keyboard = [
        [InlineKeyboardButton(
            "❌ لغو ادمین" if user[2] else "✅ ادمین کردن",
            callback_data=f"toggle_admin_{user_id}"
        )],
        [InlineKeyboardButton(
            "🔓 رفع مسدودی" if user[3] else "🔒 مسدود کردن",
            callback_data=f"toggle_block_{user_id}"
        )],
        [InlineKeyboardButton("🔙 برگشت", callback_data="manage_users")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    status = "مسدود" if user[3] else "فعال"
    admin_status = "ادمین" if user[2] else "کاربر عادی"
    
    await query.edit_message_text(
        f"مدیریت کاربر {user[1] or user[0]}\n"
        f"وضعیت: {status}\n"
        f"سطح دسترسی: {admin_status}",
        reply_markup=reply_markup
    )

async def toggle_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not db.is_admin(update.effective_user.id):
        await query.edit_message_text("شما دسترسی ادمین ندارید.")
        return
    
    user_id = int(query.data.split("_")[2])
    user = db.get_user(user_id)
    
    if not user:
        await query.edit_message_text("کاربر یافت نشد.")
        return
    
    new_status = not user[2]
    db.set_admin(user_id, new_status)
    
    await query.edit_message_text(
        f"وضعیت ادمین کاربر {user[1] or user_id} به "
        f"{'ادمین' if new_status else 'کاربر عادی'} تغییر کرد."
    )

async def toggle_block(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not db.is_admin(update.effective_user.id):
        await query.edit_message_text("شما دسترسی ادمین ندارید.")
        return
    
    user_id = int(query.data.split("_")[2])
    user = db.get_user(user_id)
    
    if not user:
        await query.edit_message_text("کاربر یافت نشد.")
        return
    
    new_status = not user[3]
    db.block_user(user_id, new_status)
    
    await query.edit_message_text(
        f"وضعیت کاربر {user[1] or user_id} به "
        f"{'مسدود' if new_status else 'فعال'} تغییر کرد."
    )
