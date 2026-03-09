#!/usr/bin/env python3
"""
Script tự động xóa lịch sử tải xuống cũ hơn 3 ngày
Chạy định kỳ để giảm dung lượng database
"""

import os
import sys
from datetime import datetime, timedelta
import psycopg2
from psycopg2 import pool

def cleanup_old_download_history():
    """Xóa lịch sử tải xuống cũ hơn 3 ngày"""
    
    # Lấy database URL từ environment
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("[ERROR] DATABASE_URL not found in environment variables")
        return False
    
    try:
        # Kết nối database
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Tính ngày 3 ngày trước
        three_days_ago = datetime.now() - timedelta(days=3)
        
        print(f"[INFO] Cleaning up download history older than {three_days_ago.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Đếm số bản ghi sẽ xóa
        cursor.execute("""
            SELECT COUNT(*) FROM user_downloads 
            WHERE download_time < %s
        """, (three_days_ago,))
        
        count_before = cursor.fetchone()[0]
        print(f"[INFO] Found {count_before} records to delete")
        
        if count_before == 0:
            print("[INFO] No old records to delete")
            cursor.close()
            conn.close()
            return True
        
        # Xóa các bản ghi cũ
        cursor.execute("""
            DELETE FROM user_downloads 
            WHERE download_time < %s
        """, (three_days_ago,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        
        print(f"[SUCCESS] Deleted {deleted_count} old download history records")
        
        # Kiểm tra số bản ghi còn lại
        cursor.execute("SELECT COUNT(*) FROM user_downloads")
        remaining = cursor.fetchone()[0]
        print(f"[INFO] Remaining records: {remaining}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Cleanup failed: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("DOWNLOAD HISTORY CLEANUP - Auto delete records older than 3 days")
    print("=" * 60)
    
    success = cleanup_old_download_history()
    
    if success:
        print("\n[✓] Cleanup completed successfully")
        sys.exit(0)
    else:
        print("\n[✗] Cleanup failed")
        sys.exit(1)
