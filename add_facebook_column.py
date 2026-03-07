"""
Migration script to add facebook_id column to users table
Run this once: python add_facebook_column.py
"""
import os
import psycopg2

def add_facebook_column():
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("[ERROR] DATABASE_URL not found in environment variables")
        return
    
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='facebook_id'
        """)
        
        if cursor.fetchone():
            print("[INFO] facebook_id column already exists")
        else:
            # Add facebook_id column
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN facebook_id VARCHAR(100) UNIQUE
            """)
            conn.commit()
            print("[SUCCESS] Added facebook_id column to users table")
        
        # Create index for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_facebook_id 
            ON users(facebook_id)
        """)
        conn.commit()
        print("[SUCCESS] Created index on facebook_id")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    add_facebook_column()
