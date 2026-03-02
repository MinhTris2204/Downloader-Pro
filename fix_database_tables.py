#!/usr/bin/env python3
"""
Script để fix database tables:
- Xóa bảng premium_users (thừa)
- Tạo bảng page_visits (thiếu)
"""

import os
import psycopg2
from psycopg2 import pool

def fix_database():
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found!")
        return False
    
    try:
        # Fix Railway URL format if needed
        db_url = DATABASE_URL
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        
        # Connect to database
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        print("🔗 Connected to database successfully!")
        
        # 1. Xóa bảng premium_users (thừa)
        print("\n🗑️ Removing unnecessary table...")
        try:
            cursor.execute("DROP TABLE IF EXISTS premium_users CASCADE")
            print("✅ Dropped premium_users table")
        except Exception as e:
            print(f"⚠️ Error dropping premium_users: {e}")
        
        # 2. Tạo bảng page_visits (thiếu)
        print("\n📊 Creating page_visits table...")
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS page_visits (
                    id SERIAL PRIMARY KEY,
                    ip_address VARCHAR(45) NOT NULL,
                    user_agent TEXT,
                    page_url VARCHAR(500),
                    referrer VARCHAR(500),
                    visit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    session_id VARCHAR(64),
                    country VARCHAR(100),
                    city VARCHAR(100),
                    device_type VARCHAR(50),
                    browser VARCHAR(100),
                    is_mobile BOOLEAN DEFAULT FALSE
                )
            """)
            print("✅ Created page_visits table")
            
            # Tạo indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_page_visits_time 
                ON page_visits(visit_time)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_page_visits_ip_time 
                ON page_visits(ip_address, visit_time)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_page_visits_session 
                ON page_visits(session_id, visit_time)
            """)
            print("✅ Created indexes for page_visits")
            
        except Exception as e:
            print(f"⚠️ Error creating page_visits: {e}")
        
        # Commit changes
        conn.commit()
        
        # 3. Kiểm tra kết quả
        print("\n📋 Final database tables:")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        for i, (table_name,) in enumerate(tables, 1):
            print(f"  {i}. {table_name}")
        
        cursor.close()
        conn.close()
        
        print(f"\n🎉 Database fixed successfully! Total tables: {len(tables)}")
        return True
        
    except Exception as e:
        print(f"❌ Database fix failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Starting database fix...")
    success = fix_database()
    
    if success:
        print("\n✅ All done! Database is now clean and optimized.")
    else:
        print("\n❌ Fix failed. Please check the errors above.")