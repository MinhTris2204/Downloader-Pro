#!/usr/bin/env python3
"""
Script để xóa bảng premium_users trên Railway PostgreSQL
"""

import os
import psycopg2
from urllib.parse import urlparse

def drop_premium_tables():
    """Xóa bảng premium_users"""
    
    # Lấy DATABASE_URL từ environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ Không tìm thấy DATABASE_URL")
        return False
    
    try:
        # Parse URL
        url = urlparse(database_url)
        
        # Kết nối database
        conn = psycopg2.connect(
            host=url.hostname,
            port=url.port,
            database=url.path[1:],  # Remove leading slash
            user=url.username,
            password=url.password
        )
        
        cursor = conn.cursor()
        
        print("🗄️ Đã kết nối PostgreSQL database")
        
        # Kiểm tra bảng tồn tại
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📋 Các bảng hiện có: {existing_tables}")
        
        # Xóa bảng premium_users
        if 'premium_users' in existing_tables:
            cursor.execute("DROP TABLE IF EXISTS premium_users CASCADE")
            print("✅ Đã xóa bảng: premium_users")
        else:
            print("⚠️ Bảng premium_users không tồn tại")
        
        # Xóa bảng user_downloads nếu có
        if 'user_downloads' in existing_tables:
            cursor.execute("DROP TABLE IF EXISTS user_downloads CASCADE")
            print("✅ Đã xóa bảng: user_downloads")
        else:
            print("⚠️ Bảng user_downloads không tồn tại")
        
        # Commit changes
        conn.commit()
        cursor.close()
        conn.close()
        
        print("🎉 Hoàn thành xóa các bảng premium!")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi khi xóa bảng: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Bắt đầu xóa bảng premium...")
    drop_premium_tables()