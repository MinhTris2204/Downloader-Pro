"""
News Controller - Lấy tin tức từ các nguồn RSS
"""
from flask import render_template, jsonify
import requests
from datetime import datetime
import re
import xml.etree.ElementTree as ET

class NewsController:
    """Controller cho tin tức"""
    
    # Các nguồn RSS về TikTok, YouTube, công nghệ
    RSS_FEEDS = [
        {
            'name': 'VnExpress Số hoá',
            'url': 'https://vnexpress.net/rss/so-hoa.rss',
            'category': 'tech'
        },
        {
            'name': 'Zing News Công nghệ',
            'url': 'https://zingnews.vn/cong-nghe.rss',
            'category': 'tech'
        },
        {
            'name': 'Genk',
            'url': 'https://genk.vn/rss/tin-tuc-cong-nghe.rss',
            'category': 'tech'
        }
    ]
    
    @staticmethod
    def index():
        """Trang danh sách tin tức"""
        return render_template('news/index.html')
    
    @staticmethod
    def parse_rss_simple(xml_content):
        """Parse RSS feed đơn giản không dùng feedparser"""
        articles = []
        try:
            root = ET.fromstring(xml_content)
            
            # Tìm tất cả items
            for item in root.findall('.//item'):
                title_elem = item.find('title')
                link_elem = item.find('link')
                desc_elem = item.find('description')
                pub_elem = item.find('pubDate')
                
                if title_elem is not None and link_elem is not None:
                    title = title_elem.text or ''
                    link = link_elem.text or ''
                    description = desc_elem.text if desc_elem is not None else ''
                    pub_date = pub_elem.text if pub_elem is not None else ''
                    
                    # Tìm ảnh trong description
                    thumbnail = ''
                    if description:
                        img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', description)
                        if img_match:
                            thumbnail = img_match.group(1)
                    
                    # Clean description
                    description_clean = re.sub(r'<[^>]+>', '', description)
                    description_clean = description_clean.strip()[:200]
                    
                    articles.append({
                        'title': title,
                        'link': link,
                        'description': description_clean,
                        'thumbnail': thumbnail,
                        'published': pub_date
                    })
        except Exception as e:
            print(f"Error parsing RSS: {e}")
        
        return articles
    
    @staticmethod
    def get_news():
        """API lấy tin tức từ RSS feeds"""
        all_articles = []
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/rss+xml, application/xml, text/xml, */*',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        
        for feed_info in NewsController.RSS_FEEDS:
            try:
                print(f"Fetching {feed_info['name']} from {feed_info['url']}")
                
                # Fetch RSS feed
                response = requests.get(feed_info['url'], headers=headers, timeout=15)
                response.raise_for_status()
                
                print(f"Got response: {response.status_code}, length: {len(response.content)}")
                
                # Parse RSS
                articles = NewsController.parse_rss_simple(response.content)
                print(f"Parsed {len(articles)} articles from {feed_info['name']}")
                
                for article in articles[:15]:  # Lấy 15 bài mới nhất
                    # Lọc chỉ lấy bài liên quan TikTok, YouTube
                    title = article['title'].lower()
                    description = article['description'].lower()
                    content = title + ' ' + description
                    
                    # Kiểm tra keywords - mở rộng để lấy nhiều bài hơn
                    keywords = ['tiktok', 'youtube', 'video', 'mạng xã hội', 'social', 
                               'streaming', 'content', 'youtuber', 'tiktoker', 'facebook',
                               'instagram', 'twitter', 'meta', 'google', 'apple', 'smartphone',
                               'app', 'ứng dụng', 'công nghệ', 'tech', 'ai', 'trí tuệ nhân tạo']
                    
                    # Lấy tất cả bài công nghệ, không lọc quá chặt
                    if any(keyword in content for keyword in keywords) or len(all_articles) < 5:
                        # Format thời gian
                        published = article['published']
                        try:
                            # Parse RFC 2822 date format
                            from email.utils import parsedate_to_datetime
                            dt = parsedate_to_datetime(published)
                            published = dt.strftime('%d/%m/%Y %H:%M')
                        except:
                            # Nếu không parse được, lấy ngày hiện tại
                            published = datetime.now().strftime('%d/%m/%Y %H:%M')
                        
                        article['published'] = published
                        article['source'] = feed_info['name']
                        all_articles.append(article)
                        
            except Exception as e:
                print(f"Error fetching {feed_info['name']}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"Total articles collected: {len(all_articles)}")
        
        # Nếu vẫn không có bài nào, trả về lỗi
        if not all_articles:
            return jsonify({
                'success': False,
                'error': 'Không thể lấy tin tức từ các nguồn RSS. Vui lòng thử lại sau.',
                'articles': []
            })
        
        return jsonify({
            'success': True,
            'articles': all_articles[:30]  # Trả về 30 bài mới nhất
        })

