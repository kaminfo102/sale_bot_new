# reporting.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Database
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import io

db = Database()

async def generate_sales_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not db.is_admin(update.effective_user.id):
        await query.edit_message_text("شما دسترسی ادمین ندارید.")
        return

    # گزارش فروش 7 روز اخیر
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    sales_data = db.get_sales_report(start_date, end_date)
    
    # رسم نمودار
    plt.figure(figsize=(10, 6))
    dates = [s[0] for s in sales_data]
    amounts = [s[1] for s in sales_data]
    plt.plot(dates, amounts, marker='o')
    plt.title('گزارش فروش 7 روز اخیر')
    plt.xlabel('تاریخ')
    plt.ylabel('مبلغ (تومان)')
    plt.xticks(rotation=45)
    plt.grid(True)
    
    # تبدیل نمودار به عکس
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    
    # ارسال گزارش
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=buf,
        caption="گزارش فروش 7 روز اخیر"
    )
    plt.close()

async def show_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not db.is_admin(update.effective_user.id):
        await query.edit_message_text("شما دسترسی ادمین ندارید.")
        return
    
    stats = db.get_statistics()
    
    message = "📊 آمار کلی ربات:\n\n"
    message += f"👥 تعداد کل کاربران: {stats['total_users']}\n"
    message += f"👤 کاربران فعال امروز: {stats['active_users_today']}\n"
    message += f"📁 تعداد کل فایل‌ها: {stats['total_files']}\n"
    message += f"💰 مجموع فروش: {stats['total_sales']:,} تومان\n"
    message += f"💳 تعداد تراکنش‌های موفق: {stats['successful_payments']}\n"
    
    keyboard = [
        [InlineKeyboardButton("نمودار فروش", callback_data="sales_chart")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="admin_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup)
