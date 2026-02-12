"""
Migration script to create donation_messages table
Run this if you already have a deployed app and need to add the table
"""
import os
import psycopg2

DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found in environment variables")
    exit(1)

# Fix Railway URL format if needed
db_url = DATABASE_URL
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)

try:
    print("Connecting to database...")
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    print("Creating donation_messages table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS donation_messages (
            id SERIAL PRIMARY KEY,
            order_code VARCHAR(50) UNIQUE NOT NULL,
            donor_name VARCHAR(100) DEFAULT 'Anonymous',
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_approved BOOLEAN DEFAULT TRUE
        )
    """)
    
    conn.commit()
    print("✅ Table created successfully!")
    
    # Check if table exists
    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.tables 
        WHERE table_name = 'donation_messages'
    """)
    
    if cursor.fetchone()[0] > 0:
        print("✅ Verified: donation_messages table exists")
    else:
        print("❌ Error: Table was not created")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
