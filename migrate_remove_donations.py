"""Migration: Remove donations table and merge into premium_subscriptions"""
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
    
    # Step 1: Add payment columns to premium_subscriptions
    print("[INFO] Adding payment columns to premium_subscriptions...")
    
    columns_to_add = [
        ("payment_status", "VARCHAR(20) DEFAULT 'success'"),
        ("payment_method", "VARCHAR(50)"),
        ("transaction_id", "VARCHAR(100)"),
        ("donor_email", "VARCHAR(100)"),
        ("ip_address", "VARCHAR(45)"),
        ("user_agent", "TEXT"),
        ("paid_at", "TIMESTAMP")
    ]
    
    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE premium_subscriptions ADD COLUMN IF NOT EXISTS {col_name} {col_type}")
            print(f"  ✓ Added column: {col_name}")
        except Exception as e:
            print(f"  ⚠ Column {col_name}: {e}")
            conn.rollback()
    
    conn.commit()
    
    # Step 2: Migrate data from donations to premium_subscriptions (only if table exists)
    print("[INFO] Migrating payment data from donations to premium_subscriptions...")
    
    cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'donations')")
    donations_exists = cursor.fetchone()[0]
    
    if donations_exists:
        cursor.execute("""
            UPDATE premium_subscriptions ps
            SET 
                payment_status = d.payment_status,
                payment_method = d.payment_method,
                transaction_id = d.transaction_id,
                donor_email = d.donor_email,
                ip_address = d.ip_address,
                user_agent = d.user_agent,
                paid_at = d.paid_at
            FROM donations d
            WHERE ps.order_code = d.order_code
            AND d.payment_status = 'success'
        """)
        updated_count = cursor.rowcount
        print(f"  ✓ Updated {updated_count} premium subscriptions with payment data")
        conn.commit()
        
        # Step 3: Drop donations table
        print("[INFO] Dropping donations table...")
        cursor.execute("DROP TABLE IF EXISTS donations CASCADE")
        conn.commit()
        print("  ✓ Donations table dropped")
    else:
        updated_count = 0
        print("  ℹ donations table not found - already migrated or never existed, skipping")
    
    cursor.close()
    conn.close()
    
    print("[SUCCESS] Migration completed successfully!")
    print("Summary:")
    print(f"  - Added 7 payment columns to premium_subscriptions")
    print(f"  - Migrated {updated_count} payment records")
    print(f"  - Dropped donations table")
    
except Exception as e:
    print(f"[ERROR] Migration failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
