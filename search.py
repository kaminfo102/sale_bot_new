# search.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Database

db = Database()

async def search_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query_text = update.message.text[8:].strip()  # حذف /search از ابتدای متن
    
    if len(query_text) < 3:
        await update.message.reply_text(
            "لطفا حداقل 3 حرف برای جستجو وارد کنید."
        )
        return
    
    results = db.search_files(query_text)
    
    if not results:
        await update.message.reply_text(
            "موردی یافت نشد."
        )
        return
    
    for file in results:
        keyboard = []
        if file['price'] > 0:
            if db.check_file_access(update.effective_user.id, file['id']):
                keyboard.append([InlineKeyboardButton(
                    "دانلود فایل",
                    callback_data=f"download_{file['id']}"
                )])
            else:
                keyboard.append([InlineKeyboardButton(
                    "خرید",
                    callback_data=f"buy_{file['id']}"
                )])
        else:
            keyboard.append([InlineKeyboardButton(
                "دانلود رایگان",
                callback_data=f"download_{file['id']}"
            )])
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        caption = f"🔍 نتیجه جستجو:\n\n"
        caption += f"📝 عنوان: {file['title']}\n"
        caption += f"📁 دسته‌بندی: {file['category_name']}\n"
        caption += f"💰 قیمت: {'رایگان' if file['price'] == 0 else f'{file['price']:,} تومان'}\n"
        caption += f"📝 توضیحات: {file['description']}"
        
        if file['image_id']:
            await update.message.reply_photo(
                photo=file['image_id'],
                caption=caption,
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                caption,
                reply_markup=reply_markup
            )
