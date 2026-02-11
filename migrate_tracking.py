"""
Migration script to add tracking columns to existing downloads table
Run this once if you already have a database
"""
import os
import psycopg2

DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found")
    exit(1)

# Fix Railway URL format
db_url = DATABASE_URL
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)

try:
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    print("Adding tracking columns to downloads table...")
    
    # Add columns one by one (ignore errors if already exists)
    columns = [
        ("ip_address", "VARCHAR(45)"),
        ("country", "VARCHAR(100)"),
        ("country_code", "VARCHAR(5)"),
        ("region", "VARCHAR(100)"),
        ("city", "VARCHAR(100)"),
        ("timezone", "VARCHAR(50)"),
        ("latitude", "DECIMAL(10, 8)"),
        ("longitude", "DECIMAL(11, 8)"),
        ("device_type", "VARCHAR(50)"),
        ("os", "VARCHAR(100)"),
        ("browser", "VARCHAR(100)"),
        ("is_mobile", "BOOLEAN"),
        ("is_tablet", "BOOLEAN"),
        ("is_pc", "BOOLEAN"),
        ("user_agent", "TEXT")
    ]
    
    for col_name, col_type in columns:
        try:
            cursor.execute(f"ALTER TABLE downloads ADD COLUMN {col_name} {col_type}")
            print(f"✓ Added column: {col_name}")
        except psycopg2.errors.DuplicateColumn:
            print(f"- Column already exists: {col_name}")
            conn.rollback()
        except Exception as e:
            print(f"✗ Error adding {col_name}: {e}")
            conn.rollback()
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("\n✓ Migration completed successfully!")
    
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)
