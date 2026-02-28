#!/usr/bin/env python3
"""
Script để xóa các bảng liên quan đến hệ thống premium cũ
"""

import sqlite3
import os

def drop_premium_tables():
    """Xóa các bảng premium không còn sử dụng"""
    
    # Tìm file database
    db_path = None
    possible_paths = [
        'database.db',
        'app.db', 
        'downloader.db',
        'data.db'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ Không tìm thấy file database")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Danh sách các bảng cần xóa
        tables_to_drop = [
            'user_downloads',
            'premium_users'
        ]
        
        print(f"🗄️ Đang kết nối database: {db_path}")
        
        # Kiểm tra các bảng tồn tại
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📋 Các bảng hiện có: {existing_tables}")
        
        # Xóa từng bảng
        for table in tables_to_drop:
            if table in existing_tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                print(f"✅ Đã xóa bảng: {table}")
            else:
                print(f"⚠️ Bảng không tồn tại: {table}")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print("🎉 Hoàn thành xóa các bảng premium cũ!")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi khi xóa bảng: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Bắt đầu xóa các bảng premium cũ...")
    drop_premium_tables()