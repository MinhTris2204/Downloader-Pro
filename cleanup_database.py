#!/usr/bin/env python3
"""
Database Cleanup Script
Xóa các bảng không cần thiết và chỉ giữ lại:
- donations (thanh toán)
- stats (thống kê tổng)
- downloads (lịch sử tải - có tracking info)
"""

import os
import psycopg2

DATABASE_URL = os.environ.get('DATABASE_URL')

def cleanup_database():
    """Xóa các bảng không cần thiết"""
    if not DATABASE_URL:
        print("[ERROR] DATABASE_URL not found")
        return False
    
    try:
        # Fix Railway URL format
        db_url = DATABASE_URL
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        print("[INFO] Starting database cleanup...")
        
        # Xóa các bảng không cần thiết
        tables_to_drop = [
            'donation_messages',  # Không dùng
            'email_verifications',  # Từ premium system đã xóa
            'page_visits',  # Không cần thiết
            'user_downloads',  # Từ premium system đã xóa
            'users',  # Từ premium system đã xóa
            'download_history',  # Trùng với downloads
            'premium_users'  # Cũ, không dùng
        ]
        
        for table in tables_to_drop:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                print(f"[SUCCESS] Dropped table: {table}")
            except Exception as e:
                print(f"[WARNING] Could not drop {table}: {e}")
                conn.rollback()
        
        # Commit changes
        conn.commit()
        
        # Verify remaining tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        remaining_tables = [row[0] for row in cursor.fetchall()]
        print(f"\n[INFO] Remaining tables: {', '.join(remaining_tables)}")
        
        cursor.close()
        conn.close()
        
        print("[SUCCESS] Database cleanup completed!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Database cleanup failed: {e}")
        return False

if __name__ == '__main__':
    cleanup_database()
