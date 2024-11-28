from database import Database


def test_database():
    db = Database()
    
    # تست اضافه کردن FAQ
    print("Adding FAQs...")
    db.add_faq("سوال تست 1", "پاسخ تست 1")
    db.add_faq("سوال تست 2", "پاسخ تست 2")
    
    # تست دریافت FAQs
    print("Getting FAQs...")
    faqs = db.get_faqs()
    for faq in faqs:
        print(f"Q: {faq['question']}")
        print(f"A: {faq['answer']}\n")
    
    # تست ذخیره پیام پشتیبانی
    print("Saving support message...")
    db.save_support_message(123456, "این یک پیام تست است")
    
    # تست دریافت پیام‌های پشتیبانی
    print("Getting support messages...")
    messages = db.get_support_messages()
    for msg in messages:
        print(f"Message ID: {msg[0]}")
        print(f"User ID: {msg[1]}")
        print(f"Message: {msg[2]}\n")

if __name__ == "__main__":
    test_database()
