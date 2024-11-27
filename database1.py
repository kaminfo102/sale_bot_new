# database.py
import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_name="bot.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cur = self.conn.cursor()
        self.create_tables()
        
    def create_tables(self):
        # جدول کاربران
        self.cur.execute('''CREATE TABLE IF NOT EXISTS users
            (user_id INTEGER PRIMARY KEY,
             username TEXT,
             is_admin INTEGER DEFAULT 0,
             is_blocked INTEGER DEFAULT 0,
             created_at TIMESTAMP)''')
        
        # جدول دسته‌بندی‌ها
        self.cur.execute('''CREATE TABLE IF NOT EXISTS categories
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             name TEXT,
             parent_id INTEGER DEFAULT NULL,
             created_at TIMESTAMP)''')
            
        # جدول فایل‌ها
        self.cur.execute('''CREATE TABLE IF NOT EXISTS files
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             category_id INTEGER,
             title TEXT,
             description TEXT,
             file_id TEXT,
             image_id TEXT,
             price REAL DEFAULT 0,
             created_at TIMESTAMP,
             FOREIGN KEY (category_id) REFERENCES categories (id))''')
             
        # جدول پرداخت‌ها
        self.cur.execute('''CREATE TABLE IF NOT EXISTS payments
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             user_id INTEGER,
             file_id INTEGER,
             amount REAL,
             status TEXT,
             created_at TIMESTAMP,
             FOREIGN KEY (user_id) REFERENCES users (user_id),
             FOREIGN KEY (file_id) REFERENCES files (id))''')
             
        # جدول دسترسی‌های فایل
        self.cur.execute('''CREATE TABLE IF NOT EXISTS file_access
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             user_id INTEGER,
             file_id INTEGER,
             created_at TIMESTAMP,
             FOREIGN KEY (user_id) REFERENCES users (user_id),
             FOREIGN KEY (file_id) REFERENCES files (id))''')
        
        # به متد create_tables در database.py اضافه کنید

# جدول فعالیت کاربران
        self.cur.execute('''CREATE TABLE IF NOT EXISTS user_activity
    (id INTEGER PRIMARY KEY AUTOINCREMENT,
     user_id INTEGER,
     activity_type TEXT,
     activity_time TIMESTAMP,
     FOREIGN KEY (user_id) REFERENCES users (user_id))''')

# جدول امتیازها
        self.cur.execute('''CREATE TABLE IF NOT EXISTS ratings
    (id INTEGER PRIMARY KEY AUTOINCREMENT,
     user_id INTEGER,
     file_id INTEGER,
     rating INTEGER,
     created_at TIMESTAMP,
     FOREIGN KEY (user_id) REFERENCES users (user_id),
     FOREIGN KEY (file_id) REFERENCES files (id))''')

# جدول نظرات
        self.cur.execute('''CREATE TABLE IF NOT EXISTS reviews
    (id INTEGER PRIMARY KEY AUTOINCREMENT,
     user_id INTEGER,
     file_id INTEGER,
     rating INTEGER,
     review_text TEXT,
     created_at TIMESTAMP,
     FOREIGN KEY (user_id) REFERENCES users (user_id),
     FOREIGN KEY (file_id) REFERENCES files (id))''')

        
        self.conn.commit()

    # متدهای مربوط به کاربران
    def add_user(self, user_id, username):
        self.cur.execute("INSERT OR IGNORE INTO users (user_id, username, created_at) VALUES (?, ?, ?)",
                        (user_id, username, datetime.now()))
        self.conn.commit()

    def get_user(self, user_id):
        self.cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return self.cur.fetchone()

    def is_admin(self, user_id):
        self.cur.execute("SELECT is_admin FROM users WHERE user_id = ?", (user_id,))
        result = self.cur.fetchone()
        return result[0] if result else False

    def set_admin(self, user_id, status):
        self.cur.execute("UPDATE users SET is_admin = ? WHERE user_id = ?", (status, user_id))
        self.conn.commit()

    def block_user(self, user_id, status):
        self.cur.execute("UPDATE users SET is_blocked = ? WHERE user_id = ?", (status, user_id))
        self.conn.commit()

    # متدهای مربوط به دسته‌بندی‌ها
    def add_category(self, name, parent_id=None):
        self.cur.execute("INSERT INTO categories (name, parent_id, created_at) VALUES (?, ?, ?)",
                        (name, parent_id, datetime.now()))
        self.conn.commit()
        return self.cur.lastrowid

    def get_categories(self, parent_id=None):
        if parent_id is None:
            self.cur.execute("SELECT * FROM categories WHERE parent_id IS NULL")
        else:
            self.cur.execute("SELECT * FROM categories WHERE parent_id = ?", (parent_id,))
        return self.cur.fetchall()

    # متدهای مربوط به فایل‌ها
    def add_file(self, category_id, title, description, file_id, image_id, price=0):
        self.cur.execute("""
            INSERT INTO files (category_id, title, description, file_id, image_id, price, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (category_id, title, description, file_id, image_id, price, datetime.now()))
        self.conn.commit()
        return self.cur.lastrowid

    def get_files_by_category(self, category_id):
        self.cur.execute("SELECT * FROM files WHERE category_id = ?", (category_id,))
        return self.cur.fetchall()

    def get_file(self, file_id):
        self.cur.execute("SELECT * FROM files WHERE id = ?", (file_id,))
        return self.cur.fetchone()

    # متدهای مربوط به پرداخت‌ها
    def add_payment(self, user_id, file_id, amount):
        self.cur.execute("""
            INSERT INTO payments (user_id, file_id, amount, status, created_at)
            VALUES (?, ?, ?, ?, ?)""",
            (user_id, file_id, amount, 'pending', datetime.now()))
        self.conn.commit()
        return self.cur.lastrowid

    def update_payment_status(self, payment_id, status):
        self.cur.execute("UPDATE payments SET status = ? WHERE id = ?", (status, payment_id))
        self.conn.commit()

    # متدهای مربوط به دسترسی فایل
    def add_file_access(self, user_id, file_id):
        self.cur.execute("""
            INSERT INTO file_access (user_id, file_id, created_at)
            VALUES (?, ?, ?)""",
            (user_id, file_id, datetime.now()))
        self.conn.commit()

    def check_file_access(self, user_id, file_id):
        self.cur.execute("""
            SELECT * FROM file_access 
            WHERE user_id = ? AND file_id = ?""",
            (user_id, file_id))
        return bool(self.cur.fetchone())
    
    
# به فایل database.py اضافه کنید

def get_sales_report(self, start_date, end_date):
    self.cur.execute("""
        SELECT DATE(created_at) as date, SUM(amount) as total
        FROM payments
        WHERE status = 'completed'
        AND created_at BETWEEN ? AND ?
        GROUP BY DATE(created_at)
        ORDER BY date
    """, (start_date, end_date))
    return self.cur.fetchall()

def get_statistics(self):
    stats = {}
    
    # تعداد کل کاربران
    self.cur.execute("SELECT COUNT(*) FROM users")
    stats['total_users'] = self.cur.fetchone()[0]
    
    # کاربران فعال امروز
    today = datetime.now().date()
    self.cur.execute("""
        SELECT COUNT(DISTINCT user_id)
        FROM user_activity
        WHERE DATE(activity_time) = ?
    """, (today,))
    stats['active_users_today'] = self.cur.fetchone()[0]
    
    # تعداد کل فایل‌ها
    self.cur.execute("SELECT COUNT(*) FROM files")
    stats['total_files'] = self.cur.fetchone()[0]
    
    # مجموع فروش
    self.cur.execute("""
        SELECT SUM(amount)
        FROM payments
        WHERE status = 'completed'
    """)
    stats['total_sales'] = self.cur.fetchone()[0] or 0
    
    # تعداد تراکنش‌های موفق
    self.cur.execute("""
        SELECT COUNT(*)
        FROM payments
        WHERE status = 'completed'
    """)
    stats['successful_payments'] = self.cur.fetchone()[0]
    
    return stats

def search_files(self, query):
    self.cur.execute("""
        SELECT f.*, c.name as category_name
        FROM files f
        JOIN categories c ON f.category_id = c.id
        WHERE f.title LIKE ? OR f.description LIKE ?
    """, (f"%{query}%", f"%{query}%"))
    return self.cur.fetchall()

def add_rating(self, user_id, file_id, rating):
    self.cur.execute("""
        INSERT OR REPLACE INTO ratings (user_id, file_id, rating, created_at)
        VALUES (?, ?, ?, ?)
    """, (user_id, file_id, rating, datetime.now()))
    self.conn.commit()

def add_review(self, user_id, file_id, rating, review_text):
    self.cur.execute("""
        INSERT OR REPLACE INTO reviews 
        (user_id, file_id, rating, review_text, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, file_id, rating, review_text, datetime.now()))
    self.conn.commit()
