# admin_handlers.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from database import Database
import config

db = Database()

# وضعیت‌های مختلف برای کانورسیشن هندلر
CATEGORY_NAME, CATEGORY_PARENT = range(2)
FILE_CATEGORY, FILE_TITLE, FILE_DESCRIPTION, FILE_UPLOAD, FILE_IMAGE, FILE_PRICE = range(6)

async def add_category_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not db.is_admin(user_id):
        await update.message.reply_text("شما دسترسی ادمین ندارید.")
        return ConversationHandler.END

    await update.message.reply_text("لطفا نام دسته‌بندی را وارد کنید:")
    return CATEGORY_NAME

async def category_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['category_name'] = update.message.text
    
    categories = db.get_categories()
    keyboard = []
    for cat in categories:
        keyboard.append([InlineKeyboardButton(cat[1], callback_data=f"parent_{cat[0]}")])
    keyboard.append([InlineKeyboardButton("بدون والد", callback_data="parent_none")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "آیا این دسته‌بندی زیرمجموعه دسته‌بندی دیگری است؟",
        reply_markup=reply_markup
    )
    return CATEGORY_PARENT

async def category_parent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    parent_id = None
    if not query.data == "parent_none":
        parent_id = int(query.data.split("_")[1])
    
    db.add_category(context.user_data['category_name'], parent_id)
    
    await query.edit_message_text("دسته‌بندی با موفقیت اضافه شد.")
    return ConversationHandler.END

async def add_file_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not db.is_admin(user_id):
        await update.message.reply_text("شما دسترسی ادمین ندارید.")
        return ConversationHandler.END

    categories = db.get_categories()
    keyboard = []
    for cat in categories:
        keyboard.append([InlineKeyboardButton(cat[1], callback_data=f"cat_{cat[0]}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "لطفا دسته‌بندی فایل را انتخاب کنید:",
        reply_markup=reply_markup
    )
    return FILE_CATEGORY

async def file_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    context.user_data['category_id'] = int(query.data.split("_")[1])
    await query.edit_message_text("لطفا عنوان فایل را وارد کنید:")
    return FILE_TITLE

async def file_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['title'] = update.message.text
    await update.message.reply_text("لطفا توضیحات فایل را وارد کنید:")
    return FILE_DESCRIPTION

async def file_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['description'] = update.message.text
    await update.message.reply_text("لطفا فایل را آپلود کنید:")
    return FILE_UPLOAD

async def file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.document
    if not file:
        await update.message.reply_text("لطفا یک فایل آپلود کنید.")
        return FILE_UPLOAD
    
    context.user_data['file_id'] = file.file_id
    await update.message.reply_text("لطفا تصویر پیش‌نمایش فایل را آپلود کنید:")
    return FILE_IMAGE

async def file_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo
    if not photo:
        await update.message.reply_text("لطفا یک تصویر آپلود کنید.")
        return FILE_IMAGE
    
    context.user_data['image_id'] = photo[-1].file_id
    await update.message.reply_text("لطفا قیمت فایل را به تومان وارد کنید (برای رایگان عدد 0 را وارد کنید):")
    return FILE_PRICE

async def file_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = float(update.message.text)
        if price < 0:
            raise ValueError
            
        db.add_file(
            context.user_data['category_id'],
            context.user_data['title'],
            context.user_data['description'],
            context.user_data['file_id'],
            context.user_data['image_id'],
            price
        )
        
        await update.message.reply_text("فایل با موفقیت اضافه شد.")
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text("لطفا یک عدد معتبر وارد کنید:")
        return FILE_PRICE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("عملیات لغو شد.")
    return ConversationHandler.END

# تعریف کانورسیشن هندلرها
add_category_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(add_category_start, pattern="^add_category$")],
    states={
        CATEGORY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, category_name)],
        CATEGORY_PARENT: [CallbackQueryHandler(category_parent, pattern="^parent_")],
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)

add_file_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(add_file_start, pattern="^add_file$")],
    states={
        FILE_CATEGORY: [CallbackQueryHandler(file_category, pattern="^cat_")],
        FILE_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, file_title)],
        FILE_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, file_description)],
        FILE_UPLOAD: [MessageHandler(filters.Document.ALL, file_upload)],
        FILE_IMAGE: [MessageHandler(filters.PHOTO, file_image)],
        FILE_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, file_price)],
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)
