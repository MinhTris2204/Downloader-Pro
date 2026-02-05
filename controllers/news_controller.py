"""
News Controller - Lấy tin tức từ các nguồn RSS
"""
from flask import render_template, jsonify
import feedparser
import requests
from datetime import datetime
import re

class NewsController:
    """Controller cho tin tức"""
    
    # Các nguồn RSS về TikTok, YouTube, công nghệ
    RSS_FEEDS = [
        {
            'name': 'VnExpress Công nghệ',
            'url': 'https://vnexpress.net/rss/so-hoa.rss',
            'category': 'tech'
        },
        {
            'name': 'Báo Mới Công nghệ',
            'url': 'https://baomoi.com/cong-nghe.rss',
            'category': 'tech'
        },
        {
            'name': 'Zing News Công nghệ',
            'url': 'https://zingnews.vn/cong-nghe.rss',
            'category': 'tech'
        }
    ]
    
    @staticmethod
    def index():
        """Trang danh sách tin tức"""
        return render_template('news/index.html')
    
    @staticmethod
    def get_news():
        """API lấy tin tức từ RSS feeds"""
        all_articles = []
        
        for feed_info in NewsController.RSS_FEEDS:
            try:
                # Parse RSS feed
                feed = feedparser.parse(feed_info['url'])
                
                for entry in feed.entries[:10]:  # Lấy 10 bài mới nhất
                    # Lọc chỉ lấy bài liên quan TikTok, YouTube
                    title = entry.get('title', '').lower()
                    description = entry.get('description', '').lower()
                    content = title + ' ' + description
                    
                    # Kiểm tra keywords
                    keywords = ['tiktok', 'youtube', 'video', 'mạng xã hội', 'social media', 
                               'streaming', 'content creator', 'youtuber', 'tiktoker']
                    
                    if any(keyword in content for keyword in keywords):
                        # Lấy ảnh thumbnail
                        thumbnail = ''
                        if hasattr(entry, 'media_content'):
                            thumbnail = entry.media_content[0]['url']
                        elif hasattr(entry, 'media_thumbnail'):
                            thumbnail = entry.media_thumbnail[0]['url']
                        elif 'description' in entry:
                            # Tìm ảnh trong description
                            img_match = re.search(r'<img[^>]+src="([^"]+)"', entry.description)
                            if img_match:
                                thumbnail = img_match.group(1)
                        
                        # Parse thời gian
                        published = entry.get('published', '')
                        try:
                            pub_date = datetime(*entry.published_parsed[:6])
                            published = pub_date.strftime('%d/%m/%Y %H:%M')
                        except:
                            pass
                        
                        # Clean description (remove HTML tags)
                        description_clean = re.sub(r'<[^>]+>', '', entry.get('description', ''))
                        description_clean = description_clean[:200] + '...' if len(description_clean) > 200 else description_clean
                        
                        article = {
                            'title': entry.get('title', ''),
                            'link': entry.get('link', ''),
                            'description': description_clean,
                            'thumbnail': thumbnail,
                            'published': published,
                            'source': feed_info['name']
                        }
                        
                        all_articles.append(article)
                        
            except Exception as e:
                print(f"Error fetching {feed_info['name']}: {e}")
                continue
        
        # Sắp xếp theo thời gian mới nhất
        all_articles.sort(key=lambda x: x.get('published', ''), reverse=True)
        
        return jsonify({
            'success': True,
            'articles': all_articles[:20]  # Trả về 20 bài mới nhất
        })
    
    @staticmethod
    def proxy_article(url):
        """Proxy để lấy nội dung bài viết (tránh CORS)"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            return response.text
        except Exception as e:
            return jsonify({'error': str(e)}), 500
