"""
Download Limit & Premium Management
Quản lý giới hạn tải xuống và người dùng premium
"""
import time
from datetime import datetime, timedelta
from flask import request
import hashlib

# Constants
FREE_DOWNLOADS_PER_WEEK = 2
PREMIUM_DURATION_DAYS = 30

def get_user_identifier():
    """Get unique user identifier from IP + User-Agent"""
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ip:
        ip = ip.split(',')[0].strip()
    user_agent = request.headers.get('User-Agent', '')
    
    # Create hash from IP + User-Agent
    identifier = f"{ip}:{user_agent}"
    return hashlib.sha256(identifier.encode()).hexdigest()

def check_download_limit(db_pool):
    """
    Check if user can download
    Returns: (can_download: bool, remaining: int, is_premium: bool, premium_expires: datetime)
    """
    if not db_pool:
        return True, FREE_DOWNLOADS_PER_WEEK, False, None
    
    user_id = get_user_identifier()
    
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        # Check if user is premium
        cursor.execute("""
            SELECT expires_at, downloads_used
            FROM premium_users
            WHERE user_id = %s AND expires_at > NOW()
            ORDER BY expires_at DESC
            LIMIT 1
        """, (user_id,))
        
        premium = cursor.fetchone()
        if premium:
            # User is premium - unlimited downloads
            cursor.close()
            db_pool.putconn(conn)
            return True, -1, True, premium[0]
        
        # Check free downloads this week
        week_start = datetime.now() - timedelta(days=7)
        cursor.execute("""
            SELECT COUNT(*) 
            FROM user_downloads
            WHERE user_id = %s AND download_time > %s
        """, (user_id, week_start))
        
        downloads_count = cursor.fetchone()[0]
        remaining = FREE_DOWNLOADS_PER_WEEK - downloads_count
        
        cursor.close()
        db_pool.putconn(conn)
        
        can_download = remaining > 0
        return can_download, remaining, False, None
        
    except Exception as e:
        print(f"[ERROR] Check download limit failed: {e}")
        # On error, allow download
        return True, FREE_DOWNLOADS_PER_WEEK, False, None

def record_download(db_pool, platform='unknown'):
    """Record a download for the user"""
    if not db_pool:
        return
    
    user_id = get_user_identifier()
    
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO user_downloads (user_id, platform, download_time)
            VALUES (%s, %s, NOW())
        """, (user_id, platform))
        
        conn.commit()
        cursor.close()
        db_pool.putconn(conn)
        
    except Exception as e:
        print(f"[ERROR] Record download failed: {e}")

def activate_premium(db_pool, user_id, order_code, amount, duration_days=PREMIUM_DURATION_DAYS):
    """Activate premium for user after successful payment"""
    if not db_pool:
        return False
    
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        expires_at = datetime.now() + timedelta(days=duration_days)
        
        cursor.execute("""
            INSERT INTO premium_users (user_id, order_code, amount, activated_at, expires_at)
            VALUES (%s, %s, %s, NOW(), %s)
            ON CONFLICT (user_id, order_code) 
            DO UPDATE SET expires_at = EXCLUDED.expires_at
        """, (user_id, order_code, amount, expires_at))
        
        conn.commit()
        cursor.close()
        db_pool.putconn(conn)
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Activate premium failed: {e}")
        return False

def get_premium_status(db_pool, user_id):
    """Get premium status for user"""
    if not db_pool:
        return None
    
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT activated_at, expires_at, amount
            FROM premium_users
            WHERE user_id = %s AND expires_at > NOW()
            ORDER BY expires_at DESC
            LIMIT 1
        """, (user_id,))
        
        result = cursor.fetchone()
        cursor.close()
        db_pool.putconn(conn)
        
        if result:
            return {
                'is_premium': True,
                'activated_at': result[0],
                'expires_at': result[1],
                'amount': result[2],
                'days_remaining': (result[1] - datetime.now()).days
            }
        
        return {'is_premium': False}
        
    except Exception as e:
        print(f"[ERROR] Get premium status failed: {e}")
        return None
