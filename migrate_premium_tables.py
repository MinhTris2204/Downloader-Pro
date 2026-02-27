"""
Migration script to create premium and download limit tables
"""
import os
import psycopg2

DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("[ERROR] DATABASE_URL not found in environment variables")
    exit(1)

# Fix Railway URL format if needed
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

try:
    print("[INFO] Connecting to database...")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    print("[INFO] Creating user_downloads table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_downloads (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(64) NOT NULL,
            platform VARCHAR(20) NOT NULL,
            download_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    print("[INFO] Creating index on user_downloads...")
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_user_downloads_user_time 
        ON user_downloads(user_id, download_time)
    """)
    
    print("[INFO] Creating premium_users table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS premium_users (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(64) NOT NULL,
            order_code VARCHAR(50) NOT NULL,
            amount INTEGER NOT NULL,
            activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            UNIQUE(user_id, order_code)
        )
    """)
    
    print("[INFO] Creating index on premium_users...")
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_premium_users_user_expires 
        ON premium_users(user_id, expires_at)
    """)
    
    conn.commit()
    print("[SUCCESS] Migration completed successfully!")
    
    # Show table info
    cursor.execute("""
        SELECT COUNT(*) FROM user_downloads
    """)
    user_downloads_count = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) FROM premium_users
    """)
    premium_users_count = cursor.fetchone()[0]
    
    print(f"\n[INFO] Table statistics:")
    print(f"  - user_downloads: {user_downloads_count} records")
    print(f"  - premium_users: {premium_users_count} records")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"[ERROR] Migration failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
