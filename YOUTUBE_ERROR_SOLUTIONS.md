# YouTube Download Error Solutions

## Common Errors and Fixes

### 1. Geo-Restriction Error
**Error**: "The uploader has not made this video available in your country"

**Causes**:
- Video is region-locked by the uploader
- Content licensing restrictions
- Government censorship

**Solutions**:

#### Option A: Use VPN/Proxy (Recommended)
```bash
# Install a VPN or use proxy with yt-dlp
# Add to your yt-dlp command:
--proxy socks5://127.0.0.1:1080
```

#### Option B: Update yt-dlp Configuration
Add proxy support to the download function:
```python
common_opts['proxy'] = os.environ.get('YOUTUBE_PROXY', None)
```

Set environment variable:
```bash
export YOUTUBE_PROXY="socks5://your-proxy:port"
```

#### Option C: Use Invidious Instances
The code already has Invidious fallback, but you can add more instances:
```python
INVIDIOUS_INSTANCES = [
    'https://invidious.fdn.fr',
    'https://invidious.snopyta.org',
    'https://yewtu.be',
    # Add more instances
]
```

### 2. Bot Detection Error
**Error**: "Sign in to confirm you're not a bot"

**Causes**:
- Too many requests from same IP
- YouTube's anti-bot protection
- Missing or expired cookies
- Invalid PO tokens

**Solutions**:

#### Option A: Update Cookies (Most Effective)
1. Export fresh cookies from your browser:
```bash
# Using browser extension "Get cookies.txt LOCALLY"
# Or use yt-dlp:
yt-dlp --cookies-from-browser chrome --cookies cookies.txt https://youtube.com
```

2. Convert to base64 and set environment variable:
```bash
base64 -w 0 cookies.txt > cookies_base64.txt
export YOUTUBE_COOKIES=$(cat cookies_base64.txt)
```

#### Option B: Increase Delays Between Requests
```python
# In app.py, increase the cooldown:
YOUTUBE_COOLDOWN = 30  # Increase from 20 to 30 seconds
```

#### Option C: Rotate User Agents More Aggressively
Already implemented, but you can add more:
```python
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
    # Add more diverse user agents
]
```

#### Option D: Use bgutil POT Provider
Start the bgutil server for professional token generation:
```bash
# Install bgutil
pip install bgutil-ytdlp-pot-provider

# Start server
python -m bgutil_ytdlp_pot_provider --host 0.0.0.0 --port 4416 &
```

### 3. Failed to Extract Player Response
**Error**: "Failed to extract any player response"

**Solutions**:

#### Update yt-dlp
```bash
pip install -U yt-dlp
```

#### Clear Cache
```bash
rm -rf ~/.cache/yt-dlp/
```

### 4. HTTP Error 429 (Too Many Requests)
**Solutions**:

#### Implement Rate Limiting Per Video
```python
# Add to app.py
video_download_tracker = {}  # video_id -> last_download_time

def check_video_cooldown(video_id):
    if video_id in video_download_tracker:
        elapsed = time.time() - video_download_tracker[video_id]
        if elapsed < 60:  # 1 minute cooldown per video
            return False
    return True
```

#### Use Multiple IP Addresses
If running on cloud, consider using rotating proxies or multiple servers.

## Strategy Improvements

### Current Strategy Order (Updated)
1. `android_embed` - No cookies needed, bypasses most restrictions
2. `android_music` - Alternative Android client
3. `tv_embed` - TV embedded client
4. `ios_classic` - iOS client with cookies
5. `bgutil_pot` - Professional token generation
6. `po_token_web` - Web client with PO token
7. `mweb_clean` - Mobile web fallback

### Why Android Clients Work Better
- Don't require cookies
- Lower bot detection
- Better geo-restriction bypass
- More stable API

## Testing Your Fixes

### Test Script
```python
# test_youtube_strategies.py
import yt_dlp

test_urls = [
    'https://www.youtube.com/watch?v=dQw4w9WgXcQ',  # Normal video
    'https://www.youtube.com/watch?v=JFbmna9zNv0',  # Geo-restricted
]

strategies = ['android_embedded', 'android_music', 'tv_embedded', 'ios']

for url in test_urls:
    print(f"\nTesting: {url}")
    for strategy in strategies:
        try:
            opts = {
                'quiet': True,
                'extractor_args': {
                    'youtube': {
                        'player_client': [strategy],
                    }
                }
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                print(f"  ✓ {strategy}: SUCCESS - {info.get('title')}")
        except Exception as e:
            print(f"  ✗ {strategy}: FAILED - {str(e)[:50]}")
```

## Monitoring and Logging

### Add Better Error Tracking
```python
# Add to app.py
error_stats = {
    'geo_restriction': 0,
    'bot_detection': 0,
    'player_response': 0,
    'other': 0
}

def track_error(error_msg):
    if 'not available in your country' in error_msg:
        error_stats['geo_restriction'] += 1
    elif 'bot' in error_msg.lower():
        error_stats['bot_detection'] += 1
    elif 'player response' in error_msg:
        error_stats['player_response'] += 1
    else:
        error_stats['other'] += 1
```

## Production Recommendations

1. **Use VPN/Proxy**: Essential for geo-restricted content
2. **Keep yt-dlp Updated**: Run `pip install -U yt-dlp` weekly
3. **Monitor Error Rates**: Track which errors occur most
4. **Implement Caching**: Cache successful video info to reduce requests
5. **Use bgutil**: For professional deployments
6. **Rotate IPs**: If possible, use multiple servers or proxies

## Environment Variables

```bash
# Required for bot detection bypass
YOUTUBE_COOKIES=<base64_encoded_cookies>

# Optional for geo-restriction bypass
YOUTUBE_PROXY=socks5://proxy-server:port

# Optional for professional token generation
YOUTUBE_PO_TOKEN=<your_po_token>
YOUTUBE_VISITOR_DATA=<your_visitor_data>
```

## Quick Fix Checklist

- [ ] Update yt-dlp: `pip install -U yt-dlp`
- [ ] Add fresh cookies from browser
- [ ] Increase cooldown delays
- [ ] Add more Android-based strategies
- [ ] Test with VPN/proxy
- [ ] Monitor error logs
- [ ] Consider bgutil POT provider
- [ ] Add better error messages for users
