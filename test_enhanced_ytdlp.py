#!/usr/bin/env python3
"""
Test script for enhanced yt-dlp bot detection avoidance
"""
import subprocess
import sys
import json
import tempfile
import random
import time
import os

# Same enhanced configuration as in the Flask app
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
]

BROWSER_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
}

def test_ytdlp_enhanced(test_url):
    """Test enhanced yt-dlp configuration"""
    temp_cache_dir = tempfile.mkdtemp(prefix='ytdlp_test_')
    user_agent = random.choice(USER_AGENTS)
    
    print(f"Testing with URL: {test_url}")
    print(f"Using User-Agent: {user_agent}")
    
    # Add random delay
    time.sleep(random.uniform(0.5, 2.0))
    
    options = [
        '--no-cache-dir',
        '--cache-dir', temp_cache_dir,
        '--user-agent', user_agent,
        '--referer', 'https://www.youtube.com/',
        
        # Enhanced headers
        '--add-header', f'Accept:{BROWSER_HEADERS["Accept"]}',
        '--add-header', f'Accept-Language:{BROWSER_HEADERS["Accept-Language"]}',
        '--add-header', f'DNT:{BROWSER_HEADERS["DNT"]}',
        
        # Network settings
        '--extractor-retries', '5',
        '--fragment-retries', '5',
        '--retry-sleep', 'linear=2:10:1',
        '--socket-timeout', '60',
        '--no-check-certificate',
        '--force-ipv4',
        '--sleep-interval', '1',
        '--max-sleep-interval', '5',
        
        # Cookie handling
        '--cookies-from-browser', 'chrome',
        '--ignore-errors',
        
        # Test options
        '--dump-json',
        '--no-download',
    ]
    
    cmd = [sys.executable, '-m', 'yt_dlp', *options, test_url]
    
    print("Running enhanced yt-dlp test...")
    print("Command:", ' '.join(cmd[:10]) + "... (truncated)")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            env={**os.environ, 'HOME': '/tmp'}
        )
        
        # Clean up
        import shutil
        shutil.rmtree(temp_cache_dir, ignore_errors=True)
        
        if result.returncode == 0:
            try:
                video_info = json.loads(result.stdout.strip())
                print("✅ SUCCESS! Video information extracted:")
                print(f"   Title: {video_info.get('title', 'Unknown')}")
                print(f"   Duration: {video_info.get('duration', 0)} seconds")
                print(f"   Uploader: {video_info.get('uploader', 'Unknown')}")
                print(f"   Formats available: {len(video_info.get('formats', []))}")
                return True
            except json.JSONDecodeError:
                print("✅ SUCCESS! yt-dlp ran successfully but JSON parsing failed")
                print("Output:", result.stdout[:200] + "..." if len(result.stdout) > 200 else result.stdout)
                return True
        else:
            print("❌ FAILED!")
            print("Error:", result.stderr)
            print("Return code:", result.returncode)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ TIMEOUT! Request took too long")
        return False
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        return False

def test_fallback_method(test_url):
    """Test fallback method"""
    temp_cache_dir = tempfile.mkdtemp(prefix='ytdlp_fallback_test_')
    user_agent = random.choice(USER_AGENTS)
    
    print(f"\nTesting fallback method with URL: {test_url}")
    
    time.sleep(random.uniform(1.0, 3.0))
    
    fallback_options = [
        '--no-cache-dir',
        '--cache-dir', temp_cache_dir,
        '--user-agent', user_agent,
        '--referer', 'https://www.youtube.com/',
        '--add-header', f'Accept:{BROWSER_HEADERS["Accept"]}',
        '--add-header', f'Accept-Language:{BROWSER_HEADERS["Accept-Language"]}',
        '--add-header', 'X-Forwarded-For:8.8.8.8',
        '--geo-bypass',
        '--geo-bypass-country', 'US',
        '--youtube-skip-dash-manifest',
        '--no-warnings',
        '--extractor-retries', '3',
        '--fragment-retries', '3',
        '--retry-sleep', '5',
        '--socket-timeout', '30',
        '--no-check-certificate',
        '--force-ipv4',
        '--dump-json',
        '--no-download',
    ]
    
    cmd = [sys.executable, '-m', 'yt_dlp', *fallback_options, test_url]
    
    print("Running fallback yt-dlp test...")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            env={**os.environ, 'HOME': '/tmp'}
        )
        
        # Clean up
        import shutil
        shutil.rmtree(temp_cache_dir, ignore_errors=True)
        
        if result.returncode == 0:
            print("✅ FALLBACK SUCCESS!")
            return True
        else:
            print("❌ FALLBACK FAILED!")
            print("Error:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ FALLBACK EXCEPTION: {e}")
        return False

if __name__ == "__main__":
    # Test with a popular YouTube video
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll - should always work
        "https://www.youtube.com/watch?v=7YBO1SfxJ4A",  # The URL from the error
    ]
    
    print("🚀 Testing Enhanced yt-dlp Bot Detection Avoidance")
    print("=" * 60)
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n📹 Test {i}/{len(test_urls)}")
        print("-" * 30)
        
        # Try enhanced method first
        success = test_ytdlp_enhanced(url)
        
        # If enhanced method fails, try fallback
        if not success:
            print("\n🔄 Trying fallback method...")
            success = test_fallback_method(url)
        
        if success:
            print(f"✅ Test {i} PASSED")
        else:
            print(f"❌ Test {i} FAILED")
    
    print("\n" + "=" * 60)
    print("🏁 Testing complete!")
    print("\nIf tests are failing, you may need to:")
    print("1. Install/update yt-dlp: pip install --upgrade yt-dlp")
    print("2. Check your internet connection")
    print("3. Try with cookies from your browser")
    print("4. Wait a few minutes and try again (rate limiting)") 