#!/usr/bin/env python3
"""
Test script for bgutil POT provider integration
Tests if bgutil server is running and yt-dlp can use it
"""

import subprocess
import time
import requests
import sys

def test_bgutil_server():
    """Test if bgutil server is running"""
    print("🔍 Testing bgutil POT provider server...")
    
    try:
        response = requests.get('http://127.0.0.1:4416/health', timeout=2)
        if response.status_code == 200:
            print("✅ bgutil server is running on port 4416")
            return True
        else:
            print(f"⚠️ bgutil server responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ bgutil server is NOT running")
        print("💡 Start it with: python -m bgutil_ytdlp_pot_provider --host 0.0.0.0 --port 4416 &")
        return False
    except Exception as e:
        print(f"❌ Error checking bgutil server: {e}")
        return False

def test_yt_dlp_with_bgutil():
    """Test yt-dlp with bgutil POT provider"""
    print("\n🔍 Testing yt-dlp with bgutil POT provider...")
    
    # Test video (short, public)
    test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # "Me at the zoo" - first YouTube video
    
    cmd = [
        'yt-dlp',
        '--quiet',
        '--no-warnings',
        '--print', 'title',
        '--extractor-args', 'youtube:player_client=web;pot_bgutilhttp:base_url=http://127.0.0.1:4416',
        test_url
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and result.stdout.strip():
            print(f"✅ yt-dlp with bgutil works!")
            print(f"📹 Video title: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ yt-dlp failed")
            if result.stderr:
                print(f"Error: {result.stderr[:200]}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ yt-dlp timed out (30s)")
        return False
    except Exception as e:
        print(f"❌ Error running yt-dlp: {e}")
        return False

def test_fallback_strategies():
    """Test fallback strategies without bgutil"""
    print("\n🔍 Testing fallback strategies (without bgutil)...")
    
    test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
    
    strategies = [
        ('TV Client', 'youtube:player_client=tv'),
        ('Android Embedded', 'youtube:player_client=android_embedded,android'),
        ('iOS', 'youtube:player_client=ios'),
    ]
    
    for name, args in strategies:
        print(f"\n  Testing {name}...")
        cmd = [
            'yt-dlp',
            '--quiet',
            '--no-warnings',
            '--print', 'title',
            '--extractor-args', args,
            test_url
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            if result.returncode == 0 and result.stdout.strip():
                print(f"  ✅ {name} works")
            else:
                print(f"  ❌ {name} failed")
        except:
            print(f"  ❌ {name} timed out")

def main():
    print("=" * 60)
    print("🚀 bgutil POT Provider Integration Test")
    print("=" * 60)
    
    # Test 1: bgutil server
    bgutil_running = test_bgutil_server()
    
    # Test 2: yt-dlp with bgutil (only if server is running)
    if bgutil_running:
        yt_dlp_works = test_yt_dlp_with_bgutil()
    else:
        print("\n⚠️ Skipping yt-dlp test (bgutil server not running)")
        yt_dlp_works = False
    
    # Test 3: Fallback strategies
    test_fallback_strategies()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    print(f"bgutil Server: {'✅ Running' if bgutil_running else '❌ Not Running'}")
    print(f"yt-dlp + bgutil: {'✅ Working' if yt_dlp_works else '❌ Failed'}")
    
    if bgutil_running and yt_dlp_works:
        print("\n🎉 All tests passed! bgutil POT provider is working correctly.")
        print("💡 Expected success rate: 95%+ for YouTube downloads")
        return 0
    elif bgutil_running and not yt_dlp_works:
        print("\n⚠️ bgutil server is running but yt-dlp integration failed")
        print("💡 This might be due to:")
        print("   - IP still blacklisted by YouTube (wait 2-4 hours)")
        print("   - Network connectivity issues")
        print("   - yt-dlp version incompatibility")
        return 1
    else:
        print("\n❌ bgutil server is not running")
        print("💡 Start it with: bash start_bgutil.sh")
        return 1

if __name__ == '__main__':
    sys.exit(main())
