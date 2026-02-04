import sys
import requests
import json
import traceback

def log_debug(msg):
    with open("debug_fetch.log", "a", encoding="utf-8") as f:
        f.write(str(msg) + "\n")

def get_images_data(url):
    log_debug(f"Starting fetch for: {url}")
    try:
        # Resolve short link first
        if 'vm.tiktok.com' in url or 'vt.tiktok.com' in url or '/t/' in url:
            try:
                h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
                r = requests.head(url, allow_redirects=True, headers=h, timeout=10)
                url = r.url
                if 'tiktok.com' not in url:
                    r = requests.get(url, allow_redirects=True, headers=h, timeout=10)
                    url = r.url
                log_debug(f"Resolved URL: {url}")
            except Exception as e:
                log_debug(f"Resolve Error: {e}")
            
        # Clean URL
        if '?' in url: url = url.split('?')[0]

        image_urls = []
        
        # 1. TikWM
        try:
            log_debug("Trying TikWM...")
            resp = requests.post("https://www.tikwm.com/api/", data={'url': url}, timeout=10)
            data = resp.json()
            log_debug(f"TikWM Code: {data.get('code')}")
            if 'data' in data and 'images' in data['data']:
                image_urls = data['data']['images']
                log_debug(f"TikWM Success: {len(image_urls)} images")
        except Exception as e:
            log_debug(f"TikWM Error: {e}")
            pass
        
        # 2. LoveTik
        if not image_urls:
            try:
                log_debug("Trying LoveTik...")
                payload = {'query': url}
                headers = {'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
                resp = requests.post("https://lovetik.com/api/ajax/search", data=payload, headers=headers, timeout=10)
                data = resp.json()
                if data.get('status') == 'ok' and 'images' in data:
                    image_urls = [img['url'] for img in data['images']]
                    log_debug(f"LoveTik Success: {len(image_urls)} images")
            except Exception as e:
                log_debug(f"LoveTik Error: {e}")
                pass
                
        # 3. yt-dlp
        if not image_urls:
            try:
                import yt_dlp
                ydl_opts = {'quiet': True, 'no_warnings': True, 'extract_flat': True}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if 'entries' in info:
                        for entry in info['entries']:
                            if 'url' in entry: image_urls.append(entry['url'])
                    elif 'images' in info:
                         for img in info['images']:
                              if 'url' in img: image_urls.append(img['url'])
                    elif 'thumbnails' in info:
                        for thumb in info['thumbnails']:
                             u = thumb.get('url', '')
                             if u and ('1080' in u or '720' in u or 'obj' in u):
                                 image_urls.append(u)
            except Exception as e: pass

        return list(dict.fromkeys(image_urls))
        
    except Exception as e:
        log_debug(f"Global Error: {traceback.format_exc()}")
        return []

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else "output.json"
        
        imgs = get_images_data(url)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(imgs, f)
            
        print(f"DONE: {len(imgs)}")
    else:
        print("Usage: python fetch_tiktok.py <url> <output_file>")

