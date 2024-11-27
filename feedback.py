# feedback.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Database

db = Database()

async def add_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    file_id = int(query.data.split("_")[1])
    
    if not db.check_file_access(update.effective_user.id, file_id):
        await query.edit_message_text(
            "شما فقط می‌توانید به فایل‌هایی که دسترسی دارید نظر دهید."
        )
        return
    
    keyboard = [
        [
            InlineKeyboardButton("⭐", callback_data=f"rate_{file_id}_1"),
            InlineKeyboardButton("⭐⭐", callback_data=f"rate_{file_id}_2"),
            InlineKeyboardButton("⭐⭐⭐", callback_data=f"rate_{file_id}_3"),
            InlineKeyboardButton("⭐⭐⭐⭐", callback_data=f"rate_{file_id}_4"),
            InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data=f"rate_{file_id}_5")
        ],
        [InlineKeyboardButton("🔙 انصراف", callback_data=f"file_{file_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "لطفا به این فایل امتیاز دهید:",
        reply_markup=reply_markup
    )

async def save_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    _, file_id, rating = query.data.split("_")
    file_id = int(file_id)
    rating = int(rating)
    
    db.add_rating(update.effective_user.id, file_id, rating)
    
    context.user_data['rating'] = rating
    
    await query.edit_message_text(
        "لطفا نظر خود را درباره این فایل بنویسید:\n"
        "یا روی /skip بزنید تا فقط امتیاز ثبت شود."
    )
    return "WAITING_REVIEW"

async def save_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "/skip":
        await update.message.reply_text("امتیاز شما ثبت شد.")
        return ConversationHandler.END
    
    rating = context.user_data.get('rating', 0)
    review_text = update.message.text
    
    db.add_review(update.effective_user.id, file_id, rating, review_text)
    
    await update.message.reply_text("نظر و امتیاز شما با موفقیت ثبت شد.")
    return ConversationHandler.END
