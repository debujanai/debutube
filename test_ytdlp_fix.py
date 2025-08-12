#!/usr/bin/env python3
"""
Test script to verify yt-dlp fixes for Vercel deployment
Run this locally to test the new configuration before deploying
"""

import subprocess
import sys
import json
import os
import tempfile
import random

# Same user agents as in the main app
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

def test_ytdlp_with_fixes(test_url):
    """Test yt-dlp with the same configuration used in production"""
    print(f"Testing yt-dlp with URL: {test_url}")
    
    # Create temporary cache directory
    temp_cache_dir = tempfile.mkdtemp(prefix='ytdlp_test_cache_')
    user_agent = random.choice(USER_AGENTS)
    
    print(f"Using User-Agent: {user_agent}")
    print(f"Using temp cache dir: {temp_cache_dir}")
    
    # Build command with same options as production
    cmd = [
        sys.executable, '-m', 'yt_dlp',
        '--dump-json',
        '--no-download',
        '--no-cache-dir',
        '--cache-dir', temp_cache_dir,
        '--user-agent', user_agent,
        '--referer', 'https://www.youtube.com/',
        '--extractor-retries', '3',
        '--fragment-retries', '3',
        '--retry-sleep', '1',
        '--socket-timeout', '30',
        '--no-check-certificate',
        test_url
    ]
    
    try:
        print("Running yt-dlp command...")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            env={**os.environ, 'HOME': temp_cache_dir}  # Simulate Vercel environment
        )
        
        # Clean up
        import shutil
        shutil.rmtree(temp_cache_dir, ignore_errors=True)
        
        if result.returncode == 0:
            print("✅ SUCCESS: yt-dlp executed successfully!")
            
            # Parse and display basic info
            try:
                video_info = json.loads(result.stdout.strip())
                print(f"📺 Title: {video_info.get('title', 'N/A')}")
                print(f"👤 Uploader: {video_info.get('uploader', 'N/A')}")
                print(f"⏱️  Duration: {video_info.get('duration', 'N/A')} seconds")
                print(f"🎬 Format count: {len(video_info.get('formats', []))}")
                return True
            except json.JSONDecodeError:
                print("⚠️  Warning: Could not parse JSON output, but command succeeded")
                return True
                
        else:
            print("❌ FAILED: yt-dlp command failed")
            print(f"Error output: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ FAILED: Command timed out")
        return False
    except Exception as e:
        print(f"❌ FAILED: Exception occurred: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing yt-dlp fixes for Vercel deployment\n")
    
    # Test with a popular YouTube video
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll (classic test video)
        "https://youtu.be/dQw4w9WgXcQ"  # Short URL format
    ]
    
    success_count = 0
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n--- Test {i}/{len(test_urls)} ---")
        if test_ytdlp_with_fixes(url):
            success_count += 1
        print("-" * 50)
    
    print(f"\n📊 Results: {success_count}/{len(test_urls)} tests passed")
    
    if success_count == len(test_urls):
        print("🎉 All tests passed! The fixes should work on Vercel.")
    else:
        print("⚠️  Some tests failed. You may need additional troubleshooting.")
        print("💡 Try running with different URLs or check your internet connection.")

if __name__ == "__main__":
    main() 