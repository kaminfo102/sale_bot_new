import sqlite3
from typing import Dict, List, Optional, Union
from datetime import datetime
import json
from contextlib import contextmanager

class Database:
    def __init__(self, db_path: str = 'bot.db'):
        self.db_path = db_path
        self.init_db()
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def init_db(self):
        """ایجاد جداول مورد نیاز دیتابیس"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # جدول کاربران
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    telegram_id INTEGER UNIQUE,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    phone TEXT,
                    is_admin BOOLEAN DEFAULT 0,
                    is_blocked BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP,
                    settings TEXT
                )
            ''')
            
            # جدول دسته‌بندی‌ها
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    parent_id INTEGER,
                    order_num INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_id) REFERENCES categories (id)
                )
            ''')
            
            # جدول فایل‌ها
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY,
                    category_id INTEGER,
                    title TEXT NOT NULL,
                    description TEXT,
                    price INTEGER DEFAULT 0,
                    file_path TEXT,
                    file_name TEXT,
                    file_size INTEGER,
                    telegram_file_id TEXT,
                    image_id TEXT,
                    download_count INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES categories (id)
                )
            ''')
            
            # جدول پرداخت‌ها
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    file_id INTEGER,
                    amount INTEGER,
                    transaction_id TEXT,
                    status TEXT,
                    payment_date TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (file_id) REFERENCES files (id)
                )
            ''')
            
            # جدول تیکت‌های پشتیبانی
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    subject TEXT,
                    status TEXT DEFAULT 'open',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # جدول پیام‌های تیکت
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ticket_messages (
                    id INTEGER PRIMARY KEY,
                    ticket_id INTEGER,
                    user_id INTEGER,
                    message TEXT,
                    file_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ticket_id) REFERENCES tickets (id),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            conn.commit()
    
    # توابع مربوط به کاربران
    def add_user(self, telegram_id: int, username: str = None, 
                 first_name: str = None, last_name: str = None) -> int:
        """افزودن کاربر جدید"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO users (telegram_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            ''', (telegram_id, username, first_name, last_name))
            conn.commit()
            return cursor.lastrowid
    
    def get_user(self, telegram_id: int) -> Optional[Dict]:
        """دریافت اطلاعات کاربر"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_user_activity(self, telegram_id: int):
        """بروزرسانی آخرین فعالیت کاربر"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET last_active = CURRENT_TIMESTAMP 
                WHERE telegram_id = ?
            ''', (telegram_id,))
            conn.commit()
    
    def block_user(self, telegram_id: int, block: bool = True):
        """مسدود/آزاد کردن کاربر"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET is_blocked = ? 
                WHERE telegram_id = ?
            ''', (block, telegram_id))
            conn.commit()
    
    # توابع مربوط به دسته‌بندی‌ها
    def add_category(self, name: str, description: str = None, 
                    parent_id: int = None) -> int:
        """افزودن دسته‌بندی جدید"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO categories (name, description, parent_id)
                VALUES (?, ?, ?)
            ''', (name, description, parent_id))
            conn.commit()
            return cursor.lastrowid
    
    def get_categories(self, parent_id: int = None) -> List[Dict]:
        """دریافت لیست دسته‌بندی‌ها"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if parent_id is None:
                cursor.execute('''
                    SELECT c.*, COUNT(f.id) as file_count 
                    FROM categories c 
                    LEFT JOIN files f ON f.category_id = c.id 
                    WHERE c.is_active = 1 
                    GROUP BY c.id 
                    ORDER BY c.order_num
                ''')
            else:
                cursor.execute('''
                    SELECT c.*, COUNT(f.id) as file_count 
                    FROM categories c 
                    LEFT JOIN files f ON f.category_id = c.id 
                    WHERE c.parent_id = ? AND c.is_active = 1 
                    GROUP BY c.id 
                    ORDER BY c.order_num
                ''', (parent_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_category(self, category_id: int) -> Optional[Dict]:
        """دریافت اطلاعات یک دسته‌بندی"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.*, COUNT(f.id) as file_count 
                FROM categories c 
                LEFT JOIN files f ON f.category_id = c.id 
                WHERE c.id = ? 
                GROUP BY c.id
            ''', (category_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # توابع مربوط به فایل‌ها
    def add_file(self, category_id: int, title: str, description: str,
                 price: int, file_path: str, file_name: str, 
                 file_size: int, telegram_file_id: str,
                 image_id: str = None) -> int:
        """افزودن فایل جدید"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO files (
                    category_id, title, description, price, 
                    file_path, file_name, file_size, 
                    telegram_file_id, image_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                category_id, title, description, price,
                file_path, file_name, file_size,
                telegram_file_id, image_id
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_file_info(self, file_id: int) -> Optional[Dict]:
        """دریافت اطلاعات یک فایل"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT f.*, c.name as category_name 
                FROM files f 
                JOIN categories c ON f.category_id = c.id 
                WHERE f.id = ? AND f.is_active = 1
            ''', (file_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_category_files(self, category_id: int) -> List[Dict]:
        """دریافت لیست فایل‌های یک دسته‌بندی"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM files 
                WHERE category_id = ? AND is_active = 1 
                ORDER BY created_at DESC
            ''', (category_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def increment_download_count(self, file_id: int):
        """افزایش تعداد دانلود فایل"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE files 
                SET download_count = download_count + 1 
                WHERE id = ?
            ''', (file_id,))
            conn.commit()
    
    # توابع مربوط به پرداخت‌ها
    def add_payment(self, user_id: int, file_id: int, 
                   amount: int, transaction_id: str) -> int:
        """ثبت پرداخت جدید"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO payments (
                    user_id, file_id, amount, 
                    transaction_id, status
                )
                VALUES (?, ?, ?, ?, 'pending')
            ''', (user_id, file_id, amount, transaction_id))
            conn.commit()
            return cursor.lastrowid
    
    def update_payment_status(self, transaction_id: str, 
                            status: str, payment_date: datetime = None):
        """بروزرسانی وضعیت پرداخت"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE payments 
                SET status = ?, payment_date = ? 
                WHERE transaction_id = ?
            ''', (status, payment_date, transaction_id))
            conn.commit()
    
    def check_purchase(self, user_id: int, file_id: int) -> bool:
        """بررسی خرید فایل توسط کاربر"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) as count 
                FROM payments 
                WHERE user_id = ? AND file_id = ? 
                AND status = 'completed'
            ''', (user_id, file_id))
            return cursor.fetchone()['count'] > 0
    
    # توابع مربوط به تیکت‌های پشتیبانی
    def create_ticket(self, user_id: int, subject: str) -> int:
        """ایجاد تیکت جدید"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO tickets (user_id, subject)
                VALUES (?, ?)
            ''', (user_id, subject))
            conn.commit()
            return cursor.lastrowid
    
    def add_ticket_message(self, ticket_id: int, user_id: int,
                          message: str, file_id: str = None) -> int:
        """افزودن پیام به تیکت"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO ticket_messages (
                    ticket_id, user_id, message, file_id
                )
                VALUES (?, ?, ?, ?)
            ''', (ticket_id, user_id, message, file_id))
            conn.commit()
            return cursor.lastrowid
    
    def get_user_tickets(self, user_id: int) -> List[Dict]:
        """دریافت لیست تیکت‌های کاربر"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM tickets 
                WHERE user_id = ? 
                ORDER BY created_at DESC
            ''', (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_ticket_messages(self, ticket_id: int) -> List[Dict]:
        """دریافت پیام‌های یک تیکت"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT tm.*, u.first_name, u.is_admin 
                FROM ticket_messages tm 
                JOIN users u ON tm.user_id = u.id 
                WHERE tm.ticket_id = ? 
                ORDER BY tm.created_at
            ''', (ticket_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def close_ticket(self, ticket_id: int):
        """بستن تیکت"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE tickets 
                SET status = 'closed', closed_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (ticket_id,))
            conn.commit()
