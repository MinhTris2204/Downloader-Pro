"""
Migration script to create donations table
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
    
    print("Creating donations table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS donations (
            id SERIAL PRIMARY KEY,
            order_code VARCHAR(50) UNIQUE NOT NULL,
            amount INTEGER NOT NULL,
            donor_name VARCHAR(100) DEFAULT 'Anonymous',
            donor_email VARCHAR(100),
            message TEXT,
            payment_status VARCHAR(20) DEFAULT 'pending',
            payment_method VARCHAR(50),
            transaction_id VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            paid_at TIMESTAMP,
            ip_address VARCHAR(45),
            user_agent TEXT
        )
    """)
    
    print("Creating donation_messages table with foreign key...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS donation_messages (
            id SERIAL PRIMARY KEY,
            order_code VARCHAR(50) UNIQUE NOT NULL,
            donor_name VARCHAR(100) DEFAULT 'Anonymous',
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_approved BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (order_code) REFERENCES donations(order_code) ON DELETE CASCADE
        )
    """)
    
    # Create indexes for better performance
    print("Creating indexes...")
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_donations_status 
        ON donations(payment_status)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_donations_created 
        ON donations(created_at DESC)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_donations_paid 
        ON donations(paid_at DESC)
    """)
    
    conn.commit()
    print("✅ Tables and indexes created successfully!")
    
    # Verify tables exist
    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_name IN ('donations', 'donation_messages')
        ORDER BY table_name
    """)
    
    tables = cursor.fetchall()
    print(f"\n✅ Verified tables: {[t[0] for t in tables]}")
    
    # Show table structure
    print("\n📋 Donations table structure:")
    cursor.execute("""
        SELECT column_name, data_type, character_maximum_length, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'donations'
        ORDER BY ordinal_position
    """)
    
    for row in cursor.fetchall():
        print(f"  - {row[0]}: {row[1]}" + (f"({row[2]})" if row[2] else "") + f" {'NULL' if row[3] == 'YES' else 'NOT NULL'}")
    
    cursor.close()
    conn.close()
    
    print("\n🎉 Migration completed successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
