# # support.py
# from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
# from telegram.ext import ContextTypes, ConversationHandler
# from database import Database


# db = Database()

# SUPPORT_ADMINS = [12345678]  # آیدی عددی ادمین‌های پشتیبانی

# # async def Support(update: Update, context: ContextTypes.DEFAULT_TYPE):
# #     keyboard = [
# #         [InlineKeyboardButton("گزارش مشکل", callback_data="report_issue")],
# #         [InlineKeyboardButton("سوال متداول", callback_data="faq")],
# #         [InlineKeyboardButton("تماس با پشتیبانی", callback_data="contact_support")]
# #     ]
# #     reply_markup = InlineKeyboardMarkup(keyboard)
    
# #     await update.message.reply_text(
# #         "👋 به بخش پشتیبانی خوش آمدید\n"
# #         "لطفا یکی از گزینه‌های زیر را انتخاب کنید:",
# #         reply_markup=reply_markup
# #     )

# async def show_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()
    
#     faq_text = """❓ سوالات متداول:

# 1️⃣ چگونه می‌توانم فایل خریداری کنم؟
# - از منوی دسته‌بندی‌ها فایل مورد نظر را انتخاب کنید
# - روی دکمه خرید کلیک کنید
# - مراحل پرداخت را تکمیل کنید

# 2️⃣ فایل‌های خریداری شده کجا ذخیره می‌شوند؟
# - در بخش "فایل‌های من" می‌توانید تمام خریدهای خود را مشاهده کنید

# 3️⃣ اگر لینک دانلود کار نکرد چه کنم؟
# - با پشتیبانی تماس بگیرید
# - مجددا از بخش "فایل‌های من" اقدام به دانلود کنید

# 4️⃣ چگونه می‌توانم درخواست بازپرداخت بدهم؟
# - حداکثر تا 24 ساعت پس از خرید
# - از طریق بخش پشتیبانی اقدام کنید"""
    
#     keyboard = [[InlineKeyboardButton("🔙 برگشت", callback_data="support_menu")]]
#     reply_markup = InlineKeyboardMarkup(keyboard)
    
#     await query.edit_message_text(faq_text, reply_markup=reply_markup)

# async def report_issue(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()
    
#     await query.edit_message_text(
#         "لطفا مشکل خود را به صورت کامل شرح دهید:\n"
#         "(شامل جزئیات مشکل، زمان وقوع و اطلاعات مرتبط)"
#     )
#     return "WAITING_ISSUE_DESCRIPTION"

# async def save_issue(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     issue_text = update.message.text
#     user_id = update.effective_user.id
    
#     ticket_id = db.create_support_ticket(user_id, issue_text)
    
#     # ارسال نوتیفیکیشن به ادمین‌ها
#     for admin_id in SUPPORT_ADMINS:
#         try:
#             keyboard = [[InlineKeyboardButton(
#                 "پاسخ", 
#                 callback_data=f"reply_ticket_{ticket_id}"
#             )]]
#             reply_markup = InlineKeyboardMarkup(keyboard)
            
#             await context.bot.send_message(
#                 chat_id=admin_id,
#                 text=f"🎫 تیکت جدید #{ticket_id}\n"
#                      f"👤 کاربر: {user_id}\n\n"
#                      f"📝 متن پیام:\n{issue_text}",
#                 reply_markup=reply_markup
#             )
#         except Exception as e:
#             print(f"Error notifying admin {admin_id}: {str(e)}")
    
#     await update.message.reply_text(
#         f"✅ گزارش شما با شماره پیگیری #{ticket_id} ثبت شد\n"
#         "کارشناسان ما در اسرع وقت پاسخگو خواهند بود."
#     )
#     return ConversationHandler.END

# async def reply_to_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()
    
#     ticket_id = int(query.data.split("_")[2])
#     context.user_data['replying_to_ticket'] = ticket_id
    
#     await query.edit_message_text(
#         f"در حال پاسخ به تیکت #{ticket_id}\n"
#         "لطفا پاسخ خود را بنویسید:"
#     )
#     return "WAITING_ADMIN_REPLY"

# async def send_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     reply_text = update.message.text
#     ticket_id = context.user_data.get('replying_to_ticket')
    
#     if not ticket_id:
#         return ConversationHandler.END
    
#     ticket_info = db.get_ticket_info(ticket_id)
#     if not ticket_info:
#         await update.message.reply_text("تیکت مورد نظر یافت نشد.")
#         return ConversationHandler.END
    
#     # ارسال پاسخ به کاربر
#     try:
#         await context.bot.send_message(
#             chat_id=ticket_info['user_id'],
#             text=f"📩 پاسخ به تیکت #{ticket_id}:\n\n{reply_text}"
#         )
        
#         db.update_ticket_status(ticket_id, 'answered', reply_text)
        
#         await update.message.reply_text("✅ پاسخ شما با موفقیت ارسال شد.")
#     except Exception as e:
#         print(f"Error sending reply: {str(e)}")
#         await update.message.reply_text("❌ خطا در ارسال پاسخ.")
    
#     return ConversationHandler.END


# # ***********************************************************************************************
# class Support:
#     def __init__(self):
#         self.db = Database()
        
#     async def show_support_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
#         keyboard = [
#             [InlineKeyboardButton("📝 ارسال پیام به پشتیبانی", callback_data="contact_support")],
#             [InlineKeyboardButton("❓ سوالات متداول", callback_data="faq")],
#             [InlineKeyboardButton("🔙 برگشت به منوی اصلی", callback_data="main_menu")]
#         ]
#         reply_markup = InlineKeyboardMarkup(keyboard)
        
#         await update.callback_query.edit_message_text(
#             "🛎 به بخش پشتیبانی خوش آمدید\n"
#             "چطور می‌توانیم به شما کمک کنیم؟",
#             reply_markup=reply_markup
#         )

#     async def handle_support_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
#         user_id = update.effective_user.id
#         message = update.message.text
        
#         # ذخیره پیام در دیتابیس
#         self.db.save_support_message(user_id, message)
        
#         await update.message.reply_text(
#             "✅ پیام شما با موفقیت ثبت شد.\n"
#             "کارشناسان ما در اسرع وقت با شما تماس خواهند گرفت."
#         )

#     async def show_faq(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
#         faqs = self.db.get_faqs()  # دریافت سوالات متداول از دیتابیس
        
#         faq_text = "❓ سوالات متداول:\n\n"
#         for faq in faqs:
#             faq_text += f"س: {faq['question']}\n"
#             faq_text += f"ج: {faq['answer']}\n\n"
            
#         keyboard = [[InlineKeyboardButton("🔙 برگشت", callback_data="support_menu")]]
#         reply_markup = InlineKeyboardMarkup(keyboard)
        
#         await update.callback_query.edit_message_text(
#             faq_text,
#             reply_markup=reply_markup
#         )


#  ################################################################################
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Database

class Support:
    def __init__(self):
        self.db = Database()
        
    async def show_support_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("📝 ارسال پیام به پشتیبانی", callback_data="contact_support")],
            [InlineKeyboardButton("❓ سوالات متداول", callback_data="faq")],
            [InlineKeyboardButton("🔙 برگشت به منوی اصلی", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "🛎 به بخش پشتیبانی خوش آمدید\n"
                "چطور می‌توانیم به شما کمک کنیم؟",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                "🛎 به بخش پشتیبانی خوش آمدید\n"
                "چطور می‌توانیم به شما کمک کنیم؟",
                reply_markup=reply_markup
            )

    async def handle_support_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        message = update.message.text
        
        # ذخیره پیام در دیتابیس
        self.db.save_support_message(user_id, message)
        
        keyboard = [[InlineKeyboardButton("🔙 برگشت به منوی پشتیبانی", callback_data="support_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "✅ پیام شما با موفقیت ثبت شد.\n"
            "کارشناسان ما در اسرع وقت با شما تماس خواهند گرفت.",
            reply_markup=reply_markup
        )

    async def show_faq(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # برای تست، چند سوال متداول ثابت را نمایش می‌دهیم
        faq_text = "❓ سوالات متداول:\n\n"
        faq_text += "س: چگونه می‌توانم خرید کنم؟\n"
        faq_text += "ج: شما می‌توانید از طریق منوی خرید، محصول مورد نظر را انتخاب کنید.\n\n"
        faq_text += "س: زمان پاسخگویی پشتیبانی چقدر است؟\n"
        faq_text += "ج: معمولاً در کمتر از 24 ساعت به پیام‌های شما پاسخ می‌دهیم.\n\n"
        
        keyboard = [[InlineKeyboardButton("🔙 برگشت", callback_data="support_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            faq_text,
            reply_markup=reply_markup
        )
