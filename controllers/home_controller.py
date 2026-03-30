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
        
        if session.get('user_id'):
            try:
                from controllers.auth_controller import get_user_premium_info
                premium_info = get_user_premium_info(session['user_id'])
            except Exception as e:
                print(f"Error getting premium info: {e}")
        
        return render_template('index.html', premium_info=premium_info)
