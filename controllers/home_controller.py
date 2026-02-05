"""
Home Controller - Xử lý trang chủ
"""
from flask import render_template

class HomeController:
    """Controller cho trang chủ"""
    
    @staticmethod
    def index():
        """Trang chủ"""
        return render_template('index.html')
