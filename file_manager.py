# file_manager.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Database
import os
from typing import Optional, Tuple, Dict
from datetime import datetime
import shutil

db = Database()
UPLOAD_FOLDER = "files/"

async def add_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db.is_admin(update.effective_user.id):
        await update.message.reply_text("شما دسترسی ادمین ندارید.")
        return
    
    context.user_data['adding_file'] = True
    
    categories = db.get_categories()
    keyboard = []
    for cat in categories:
        keyboard.append([InlineKeyboardButton(
            cat['name'], 
            callback_data=f"addfile_cat_{cat['id']}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "لطفا دسته‌بندی فایل را انتخاب کنید:",
        reply_markup=reply_markup
    )
    return "WAITING_FILE_CATEGORY"

async def file_set_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    category_id = int(query.data.split("_")[2])
    context.user_data['file_category'] = category_id
    
    await query.edit_message_text(
        "لطفا عنوان فایل را وارد کنید:"
    )
    return "WAITING_FILE_TITLE"

async def file_set_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['file_title'] = update.message.text
    
    await update.message.reply_text(
        "لطفا توضیحات فایل را وارد کنید:"
    )
    return "WAITING_FILE_DESCRIPTION"

async def file_set_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['file_description'] = update.message.text
    
    await update.message.reply_text(
        "لطفا قیمت فایل را به تومان وارد کنید:\n"
        "(برای فایل رایگان عدد 0 را وارد کنید)"
    )
    return "WAITING_FILE_PRICE"

async def file_set_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = int(update.message.text)
        context.user_data['file_price'] = price
        
        await update.message.reply_text(
            "لطفا تصویر پیش‌نمایش فایل را ارسال کنید:\n"
            "(یا /skip را بزنید تا این مرحله را رد کنید)"
        )
        return "WAITING_FILE_IMAGE"
    except ValueError:
        await update.message.reply_text(
            "لطفا یک عدد صحیح وارد کنید."
        )
        return "WAITING_FILE_PRICE"

async def file_set_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "/skip":
        context.user_data['file_image'] = None
    else:
        photo = update.message.photo[-1]
        context.user_data['file_image'] = photo.file_id
    
    await update.message.reply_text(
        "لطفا فایل اصلی را ارسال کنید:"
    )
    return "WAITING_FILE_UPLOAD"
async def file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.document
    if not file:
        await update.message.reply_text(
            "لطفا یک فایل ارسال کنید."
        )
        return "WAITING_FILE_UPLOAD"
    
    # دانلود فایل
    file_info = await context.bot.get_file(file.file_id)
    file_path = os.path.join(UPLOAD_FOLDER, file.file_name)
    await file_info.download_to_drive(file_path)
    
    # ذخیره اطلاعات در دیتابیس
    file_id = db.add_file(
        category_id=context.user_data['file_category'],
        title=context.user_data['file_title'],
        description=context.user_data['file_description'],
        price=context.user_data['file_price'],
        image_id=context.user_data.get('file_image'),
        file_path=file_path,
        file_name=file.file_name,
        file_size=file.file_size,
        telegram_file_id=file.file_id
    )
    
    await update.message.reply_text(
        "✅ فایل با موفقیت آپلود و ثبت شد!\n\n"
        f"🆔 شناسه فایل: {file_id}\n"
        f"📝 عنوان: {context.user_data['file_title']}\n"
        f"💰 قیمت: {context.user_data['file_price']:,} تومان"
    )
    
    # پاک کردن اطلاعات موقت
    context.user_data.clear()
    return ConversationHandler.END

async def edit_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    file_id = int(query.data.split("_")[1])
    file_info = db.get_file_info(file_id)
    
    if not file_info:
        await query.edit_message_text("فایل مورد نظر یافت نشد.")
        return
    
    keyboard = [
        [InlineKeyboardButton("ویرایش عنوان", callback_data=f"edit_title_{file_id}")],
        [InlineKeyboardButton("ویرایش توضیحات", callback_data=f"edit_desc_{file_id}")],
        [InlineKeyboardButton("ویرایش قیمت", callback_data=f"edit_price_{file_id}")],
        [InlineKeyboardButton("ویرایش تصویر", callback_data=f"edit_image_{file_id}")],
        [InlineKeyboardButton("تغییر دسته‌بندی", callback_data=f"edit_cat_{file_id}")],
        [InlineKeyboardButton("❌ حذف فایل", callback_data=f"delete_file_{file_id}")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="admin_files")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = f"🗂 ویرایش فایل #{file_id}\n\n"
    message += f"📝 عنوان: {file_info['title']}\n"
    message += f"📁 دسته‌بندی: {file_info['category_name']}\n"
    message += f"💰 قیمت: {file_info['price']:,} تومان\n"
    message += f"📅 تاریخ ثبت: {file_info['created_at']}\n"
    
    await query.edit_message_text(message, reply_markup=reply_markup)

async def delete_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    file_id = int(query.data.split("_")[2])
    
    keyboard = [
        [
            InlineKeyboardButton("✅ بله، حذف شود", callback_data=f"confirm_delete_{file_id}"),
            InlineKeyboardButton("❌ خیر", callback_data=f"edit_file_{file_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "آیا از حذف این فایل اطمینان دارید؟\n"
        "این عمل قابل بازگشت نیست!",
        reply_markup=reply_markup
    )

async def confirm_delete_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    file_id = int(query.data.split("_")[2])
    file_info = db.get_file_info(file_id)
    
    if file_info:
        # حذف فایل فیزیکی
        try:
            os.remove(file_info['file_path'])
        except:
            pass
        
        # حذف از دیتابیس
        db.delete_file(file_id)
        
        await query.edit_message_text("✅ فایل با موفقیت حذف شد.")
    else:
        await query.edit_message_text("❌ فایل مورد نظر یافت نشد.")
# *************************************************************************************************

class FileManager:
    def __init__(self, base_path: str = "files"):
        """
        مدیریت فایل‌ها
        
        Args:
            base_path: مسیر پایه برای ذخیره فایل‌ها
        """
        self.base_path = base_path
        self._ensure_directories()
    
    def _ensure_directories(self):
        """اطمینان از وجود دایرکتوری‌های مورد نیاز"""
        directories = [
            self.base_path,
            os.path.join(self.base_path, "products"),
            os.path.join(self.base_path, "images"),
            os.path.join(self.base_path, "tickets")
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
    
    def save_product_file(self, file_path: str, category_id: int) -> Tuple[str, str, int]:
        """
        ذخیره فایل محصول
        
        Args:
            file_path: مسیر فایل اصلی
            category_id: شناسه دسته‌بندی
            
        Returns:
            tuple: (مسیر ذخیره شده, نام فایل, حجم فایل)
        """
        # ساخت نام یکتا برای فایل
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = os.path.basename(file_path)
        base_name, ext = os.path.splitext(file_name)
        unique_name = f"{base_name}_{timestamp}{ext}"
        
        # مسیر ذخیره‌سازی
        save_dir = os.path.join(self.base_path, "products", str(category_id))
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        save_path = os.path.join(save_dir, unique_name)
        
        # کپی فایل
        shutil.copy2(file_path, save_path)
        
        # دریافت حجم فایل
        file_size = os.path.getsize(save_path)
        
        return save_path, unique_name, file_size
    
    def save_image(self, image_path: str) -> str:
        """
        ذخیره تصویر
        
        Args:
            image_path: مسیر تصویر
            
        Returns:
            str: مسیر ذخیره شده
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_name = os.path.basename(image_path)
        base_name, ext = os.path.splitext(image_name)
        unique_name = f"{base_name}_{timestamp}{ext}"
        
        save_path = os.path.join(self.base_path, "images", unique_name)
        shutil.copy2(image_path, save_path)
        
        return save_path
    
    def save_ticket_file(self, file_path: str, ticket_id: int) -> str:
        """
        ذخیره فایل ضمیمه تیکت
        
        Args:
            file_path: مسیر فایل
            ticket_id: شناسه تیکت
            
        Returns:
            str: مسیر ذخیره شده
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = os.path.basename(file_path)
        base_name, ext = os.path.splitext(file_name)
        unique_name = f"{base_name}_{timestamp}{ext}"
        
        save_dir = os.path.join(self.base_path, "tickets", str(ticket_id))
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        save_path = os.path.join(save_dir, unique_name)
        shutil.copy2(file_path, save_path)
        
        return save_path
    
    def get_file_path(self, file_path: str) -> Optional[str]:
        """
        دریافت مسیر کامل فایل
        
        Args:
            file_path: مسیر نسبی فایل
            
        Returns:
            Optional[str]: مسیر کامل فایل یا None
        """
        full_path = os.path.join(self.base_path, file_path)
        return full_path if os.path.exists(full_path) else None
    
    def delete_file(self, file_path: str) -> bool:
        """
        حذف فایل
        
        Args:
            file_path: مسیر فایل
            
        Returns:
            bool: موفقیت عملیات
        """
        try:
            full_path = os.path.join(self.base_path, file_path)
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
        except Exception:
            pass
        return False
    
    def get_file_info(self, file_path: str) -> Optional[Dict]:
        """
        دریافت اطلاعات فایل
        
        Args:
            file_path: مسیر فایل
            
        Returns:
            Optional[Dict]: اطلاعات فایل یا None
        """
        try:
            full_path = os.path.join(self.base_path, file_path)
            if os.path.exists(full_path):
                return {
                    'size': os.path.getsize(full_path),
                    'created': datetime.fromtimestamp(os.path.getctime(full_path)),
                    'modified': datetime.fromtimestamp(os.path.getmtime(full_path)),
                    'name': os.path.basename(full_path)
                }
        except Exception:
            pass
        return None
    
    def move_file(self, source_path: str, dest_path: str) -> bool:
        """
        جابجایی فایل
        
        Args:
            source_path: مسیر مبدا
            dest_path: مسیر مقصد
            
        Returns:
            bool: موفقیت عملیات
        """
        try:
            full_source = os.path.join(self.base_path, source_path)
            full_dest = os.path.join(self.base_path, dest_path)
            
            # اطمینان از وجود دایرکتوری مقصد
            os.makedirs(os.path.dirname(full_dest), exist_ok=True)
            
            if os.path.exists(full_source):
                shutil.move(full_source, full_dest)
                return True
        except Exception:
            pass
        return False
    
    def cleanup_temp_files(self, max_age_days: int = 1):
        """
        پاکسازی فایل‌های موقت
        
        Args:
            max_age_days: حداکثر عمر فایل‌ها به روز
        """
        now = datetime.now()
        for root, dirs, files in os.walk(self.base_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    # بررسی تاریخ ایجاد فایل
                    creation_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    age_days = (now - creation_time).days
                    
                    # حذف فایل‌های قدیمی
                    if age_days > max_age_days:
                        os.remove(file_path)
                except Exception:
                    continue
