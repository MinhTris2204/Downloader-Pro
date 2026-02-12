#!/usr/bin/env python3
"""
Test YouTube download strategies to identify which ones work
"""
import yt_dlp
import sys

def test_strategy(url, strategy_name, strategy_config):
    """Test a single strategy"""
    try:
        opts = {
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 15,
            'extractor_args': {
                'youtube': strategy_config
            }
        }
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            return True, f"{title} ({duration}s)"
    except Exception as e:
        error = str(e)
        # Truncate long errors
        if len(error) > 100:
            error = error[:100] + "..."
        return False, error

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_youtube_strategies.py <youtube_url>")
        print("Example: python test_youtube_strategies.py https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        sys.exit(1)
    
    url = sys.argv[1]
    
    print(f"\n{'='*70}")
    print(f"Testing YouTube URL: {url}")
    print(f"{'='*70}\n")
    
    # Define strategies to test
    strategies = [
        ('android_embedded', {
            'player_client': ['android_embedded'],
        }),
        ('android_music', {
            'player_client': ['android_music'],
        }),
        ('android', {
            'player_client': ['android'],
        }),
        ('tv_embedded', {
            'player_client': ['tv_embedded'],
        }),
        ('tv', {
            'player_client': ['tv'],
        }),
        ('ios', {
            'player_client': ['ios'],
        }),
        ('mweb', {
            'player_client': ['mweb'],
        }),
        ('web', {
            'player_client': ['web'],
        }),
    ]
    
    results = []
    
    for strategy_name, strategy_config in strategies:
        print(f"Testing: {strategy_name:20s} ... ", end='', flush=True)
        success, message = test_strategy(url, strategy_name, strategy_config)
        
        if success:
            print(f"✓ SUCCESS - {message}")
            results.append((strategy_name, True, message))
        else:
            print(f"✗ FAILED - {message}")
            results.append((strategy_name, False, message))
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}\n")
    
    successful = [r for r in results if r[1]]
    failed = [r for r in results if not r[1]]
    
    print(f"✓ Successful strategies: {len(successful)}/{len(results)}")
    for name, _, msg in successful:
        print(f"  - {name}")
    
    print(f"\n✗ Failed strategies: {len(failed)}/{len(results)}")
    for name, _, msg in failed:
        print(f"  - {name}: {msg[:60]}")
    
    # Recommendations
    print(f"\n{'='*70}")
    print("RECOMMENDATIONS")
    print(f"{'='*70}\n")
    
    if successful:
        print(f"✓ Use these strategies in your app (in order):")
        for i, (name, _, _) in enumerate(successful, 1):
            print(f"  {i}. {name}")
    else:
        print("✗ No strategies worked. Possible issues:")
        print("  1. Video is geo-restricted - try with VPN")
        print("  2. Video requires authentication - add cookies")
        print("  3. yt-dlp needs update: pip install -U yt-dlp")
        print("  4. Network/firewall issues")
    
    print()

if __name__ == '__main__':
    main()
