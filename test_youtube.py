#!/usr/bin/env python3
"""Test YouTube download with minimal config"""

import yt_dlp

# Test video ID
video_url = "https://www.youtube.com/watch?v=NcYIj0T2vsQ"

print("Testing YouTube download with minimal config...")
print(f"Video URL: {video_url}\n")

# Strategy 1: Absolute minimal
print("=" * 60)
print("Strategy 1: Absolute minimal config")
print("=" * 60)
try:
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'best',
        'skip_download': True,  # Just test extraction
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        print(f"✅ SUCCESS!")
        print(f"Title: {info.get('title', 'N/A')}")
        print(f"Duration: {info.get('duration', 'N/A')}s")
        print(f"Available formats: {len(info.get('formats', []))}")
except Exception as e:
    print(f"❌ FAILED: {str(e)[:200]}")

# Strategy 2: With legacy options
print("\n" + "=" * 60)
print("Strategy 2: Legacy format")
print("=" * 60)
try:
    ydl_opts = {
        'quiet': True,
        'format': 'bestvideo+bestaudio/best',
        'skip_download': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        print(f"✅ SUCCESS!")
        print(f"Title: {info.get('title', 'N/A')}")
except Exception as e:
    print(f"❌ FAILED: {str(e)[:200]}")

# Strategy 3: No format specified
print("\n" + "=" * 60)
print("Strategy 3: No format specified")
print("=" * 60)
try:
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        print(f"✅ SUCCESS!")
        print(f"Title: {info.get('title', 'N/A')}")
except Exception as e:
    print(f"❌ FAILED: {str(e)[:200]}")

print("\n" + "=" * 60)
print("yt-dlp version:")
print("=" * 60)
import subprocess
result = subprocess.run(['yt-dlp', '--version'], capture_output=True, text=True)
print(result.stdout)
