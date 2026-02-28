#!/usr/bin/env python3
"""
Migration script để xóa các bảng premium trên Railway
Chạy script này sau khi deploy để dọn dẹp database
"""

import sqlite3
import os
import sys

def remove_premium_tables():
    """Xóa các bảng premium không còn sử dụng"""
    
    # Tìm file database
    db_path = None
    possible_paths = [
        'database.db',
        'app.db', 
        'downloader.db',
        'data.db',
        '/app/database.db',
        '/app/data.db'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ Không tìm thấy file database")
        print("📋 Các file hiện có:")
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.db'):
                    print(f"  - {os.path.join(root, file)}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"🗄️ Đang kết nối database: {db_path}")
        
        # Kiểm tra các bảng tồn tại
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📋 Các bảng hiện có: {existing_tables}")
        
        # Danh sách các bảng cần xóa
        tables_to_drop = [
            'user_downloads',
            'premium_users'
        ]
        
        # Xóa từng bảng
        dropped_count = 0
        for table in tables_to_drop:
            if table in existing_tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                print(f"✅ Đã xóa bảng: {table}")
                dropped_count += 1
            else:
                print(f"⚠️ Bảng không tồn tại: {table}")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        if dropped_count > 0:
            print(f"🎉 Hoàn thành! Đã xóa {dropped_count} bảng premium cũ")
        else:
            print("ℹ️ Không có bảng nào cần xóa")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi khi xóa bảng: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Bắt đầu migration xóa bảng premium...")
    success = remove_premium_tables()
    sys.exit(0 if success else 1)