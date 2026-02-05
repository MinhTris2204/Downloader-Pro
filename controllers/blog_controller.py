"""
Blog Controller - Xử lý các trang blog và bài viết
"""
from flask import render_template

class BlogController:
    """Controller cho các trang blog"""
    
    @staticmethod
    def index():
        """Trang danh sách blog"""
        articles = [
            {
                'slug': 'tai-video-youtube',
                'title': 'Hướng Dẫn Tải Video YouTube Miễn Phí 2026',
                'description': 'Hướng dẫn chi tiết cách tải video YouTube về máy tính, điện thoại với chất lượng HD, Full HD, 4K. Chuyển đổi YouTube sang MP3 dễ dàng.',
                'image': '/static/favicon.svg',
                'date': '2026-02-05',
                'category': 'YouTube'
            },
            {
                'slug': 'tai-video-tiktok',
                'title': 'Cách Tải Video TikTok Không Logo Watermark 2026',
                'description': 'Hướng dẫn tải video TikTok không logo, tải album ảnh TikTok slideshow. Công nghệ loại bỏ watermark hiệu quả nhất.',
                'image': '/static/favicon.svg',
                'date': '2026-02-05',
                'category': 'TikTok'
            },
            {
                'slug': 'chuyen-youtube-sang-mp3',
                'title': 'Chuyển Đổi YouTube Sang MP3 Chất Lượng Cao',
                'description': 'Hướng dẫn chuyển đổi video YouTube sang file MP3 với chất lượng 128kbps, 192kbps, 320kbps. Tải nhạc YouTube miễn phí.',
                'image': '/static/favicon.svg',
                'date': '2026-02-05',
                'category': 'YouTube'
            }
        ]
        return render_template('blog/index.html', articles=articles)
    
    @staticmethod
    def youtube_guide():
        """Trang hướng dẫn tải YouTube"""
        return render_template('blog/tai-video-youtube.html')
    
    @staticmethod
    def tiktok_guide():
        """Trang hướng dẫn tải TikTok"""
        return render_template('blog/tai-video-tiktok.html')
    
    @staticmethod
    def youtube_to_mp3():
        """Trang hướng dẫn chuyển YouTube sang MP3"""
        return render_template('blog/chuyen-youtube-sang-mp3.html')
