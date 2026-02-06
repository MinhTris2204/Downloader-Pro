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
    
    # Cache cho tin tức
    _news_cache = {
        'articles': [],
        'last_updated': None
    }
    _CACHE_TIMEOUT = 600  # 10 phút (giây)
    
    @staticmethod
    def _fetch_all_news():
        """Hàm helper để fetch tin tức từ tất cả RSS feeds"""
        all_articles = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/rss+xml, application/xml, text/xml, */*',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        
        for feed_info in NewsController.RSS_FEEDS:
            try:
                # Fetch RSS feed
                response = requests.get(feed_info['url'], headers=headers, timeout=10)
                if response.status_code == 200:
                    articles = NewsController.parse_rss_simple(response.content)
                    for article in articles[:15]:
                        title = article['title'].lower()
                        description = article['description'].lower()
                        content = title + ' ' + description
                        
                        tech_keywords = [
                            'tiktok', 'youtube', 'facebook', 'instagram', 'twitter', 'x.com',
                            'mạng xã hội', 'social media', 'video', 'streaming', 'livestream',
                            'youtuber', 'tiktoker', 'content creator', 'influencer',
                            'meta', 'google', 'apple', 'microsoft', 'amazon',
                            'smartphone', 'iphone', 'android', 'app', 'ứng dụng',
                            'ai', 'trí tuệ nhân tạo', 'chatgpt', 'openai',
                            'game', 'gaming', 'esports', 'steam',
                            'netflix', 'spotify', 'zalo', 'telegram', 'whatsapp',
                            'công nghệ', 'technology', 'tech', 'digital',
                            'internet', 'web', 'online', 'cloud',
                            'software', 'phần mềm', 'hardware', 'phần cứng',
                            'laptop', 'pc', 'máy tính', 'tablet', 'ipad'
                        ]
                        
                        exclude_keywords = [
                            'chính trị', 'bầu cử', 'quốc hội', 'chính phủ',
                            'kinh tế vĩ mô', 'chứng khoán', 'bất động sản',
                            'thể thao', 'bóng đá', 'world cup',
                            'giải trí', 'ca sĩ', 'diễn viên', 'phim ảnh',
                            'thời tiết', 'giao thông', 'tai nạn'
                        ]
                        
                        has_tech = any(keyword in content for keyword in tech_keywords)
                        has_exclude = any(keyword in content for keyword in exclude_keywords)
                        
                        if has_tech and not has_exclude:
                            published = article['published']
                            try:
                                from email.utils import parsedate_to_datetime
                                dt = parsedate_to_datetime(published)
                                published = dt.strftime('%d/%m/%Y %H:%M')
                            except:
                                published = datetime.now().strftime('%d/%m/%Y %H:%M')
                            
                            article['published'] = published
                            article['source'] = feed_info['name']
                            all_articles.append(article)
            except Exception as e:
                print(f"Error fetching {feed_info['name']}: {e}")
                continue
        
        return all_articles[:40]

    @staticmethod
    def index():
        """Trang danh sách tin tức - Load từ cache hoặc fetch mới"""
        now = datetime.now()
        
        # Kiểm tra cache
        if (not NewsController._news_cache['articles'] or 
            not NewsController._news_cache['last_updated'] or 
            (now - NewsController._news_cache['last_updated']).total_seconds() > NewsController._CACHE_TIMEOUT):
            
            # Update cache
            NewsController._news_cache['articles'] = NewsController._fetch_all_news()
            NewsController._news_cache['last_updated'] = now
                
        return render_template('news/index.html', initial_news=NewsController._news_cache['articles'])
    
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
    def proxy_article():
        """Proxy để lấy nội dung bài viết (tránh CSP)"""
        from flask import request
        
        url = request.args.get('url')
        if not url:
            return jsonify({'error': 'Missing URL'}), 400
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Parse HTML và lấy nội dung chính
            html = response.text
            
            # Inject base tag để fix relative URLs
            base_tag = f'<base href="{url}">'
            html = html.replace('<head>', f'<head>{base_tag}')
            
            # Thêm CSS để ẩn header/footer/ads
            custom_css = '''
            <style>
                header, .header, #header,
                footer, .footer, #footer,
                .advertisement, .ads, .banner,
                .sidebar, .side-bar,
                .navigation, .nav, .menu,
                .social-share, .share-buttons,
                .comment, .comments,
                .related-news, .related-articles,
                iframe[src*="ads"], iframe[src*="doubleclick"],
                .box-tinkhac, .box-tinlienquan, .recommendation, .popup {
                    display: none !important;
                }
                
                body {
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    line-height: 1.6;
                    overflow-x: hidden;
                    width: 100%;
                    box-sizing: border-box;
                    background: #fff;
                    color: #333;
                }
                
                img, video, iframe {
                    max-width: 100% !important;
                    height: auto !important;
                    display: block;
                    margin: 10px auto;
                }

                @media (max-width: 768px) {
                    body {
                        padding: 15px;
                        font-size: 16px;
                    }
                }
            </style>
            '''
            html = html.replace('</head>', f'{custom_css}</head>')
            
            return html, 200, {'Content-Type': 'text/html; charset=utf-8'}
            
        except Exception as e:
            print(f"Error proxying article: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    def get_news():
        """API lấy tin tức - Sử dụng cache"""
        now = datetime.now()
        
        if (not NewsController._news_cache['articles'] or 
            not NewsController._news_cache['last_updated'] or 
            (now - NewsController._news_cache['last_updated']).total_seconds() > NewsController._CACHE_TIMEOUT):
            
            NewsController._news_cache['articles'] = NewsController._fetch_all_news()
            NewsController._news_cache['last_updated'] = now
            
        return jsonify({
            'success': True,
            'articles': NewsController._news_cache['articles']
        })

