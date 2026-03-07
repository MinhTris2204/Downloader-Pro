"""Migration script to drop donation_messages table"""
import os
import psycopg2

DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("[ERROR] DATABASE_URL not found in environment variables")
    exit(1)

# Fix Railway URL format if needed
db_url = DATABASE_URL
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)

try:
    print("[INFO] Connecting to database...")
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    # Drop donation_messages table
    print("[INFO] Dropping donation_messages table...")
    cursor.execute("DROP TABLE IF EXISTS donation_messages CASCADE")
    
    conn.commit()
    print("[SUCCESS] donation_messages table dropped successfully!")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"[ERROR] Migration failed: {e}")
    exit(1)
