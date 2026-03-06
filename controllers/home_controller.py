"""
Home Controller - Xử lý trang chủ
"""
from flask import render_template, session

class HomeController:
    """Controller cho trang chủ"""
    
    @staticmethod
    def index():
        """Trang chủ"""
        premium_info = None
        
        # Kiểm tra nếu user đã đăng nhập
        if session.get('user_id'):
            try:
                from app import db_pool
                
                if db_pool:
                    conn = db_pool.getconn()
                    cursor = conn.cursor()
                    
                    # Lấy thông tin premium
                    cursor.execute("""
                        SELECT is_premium, premium_expires 
                        FROM users 
                        WHERE id = %s
                    """, (session['user_id'],))
                    
                    result = cursor.fetchone()
                    if result:
                        premium_info = {
                            'is_premium': result[0],
                            'premium_expires': result[1]
                        }
                    
                    cursor.close()
                    db_pool.putconn(conn)
            except Exception as e:
                print(f"Error getting premium info: {e}")
        
        return render_template('index.html', premium_info=premium_info)
