#!/usr/bin/env python3
"""
Test script to verify yt-dlp cookie fixes for bot detection
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

def test_ytdlp_with_cookies(test_url):
    """Test yt-dlp with the new three-tier approach"""
    print(f"Testing yt-dlp with three-tier approach for URL: {test_url}")
    
    # Create temporary cache directory
    temp_cache_dir = tempfile.mkdtemp(prefix='ytdlp_basic_test_')
    user_agent = random.choice(USER_AGENTS)
    
    print(f"Using User-Agent: {user_agent}")
    print(f"Using temp cache dir: {temp_cache_dir}")
    
    # Tier 1: Basic method (no cookies)
    cmd_basic = [
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
        '--sleep-interval', '1',
        '--max-sleep-interval', '3',
        '--sleep-requests', '1',
        '--extractor-args', 'youtube:player_client=web,mweb',
        '--extractor-args', 'youtube:skip=hls,dash',
        '--no-warnings',
        test_url
    ]
    
    print("\n=== Testing Tier 1: Basic Method (no cookies) ===")
    try:
        result = subprocess.run(
            cmd_basic,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✅ Basic method SUCCESS!")
            video_info = json.loads(result.stdout.strip())
            print(f"Title: {video_info.get('title', 'Unknown')}")
            print(f"Duration: {video_info.get('duration', 0)} seconds")
            print(f"Formats available: {len(video_info.get('formats', []))}")
            return True
        else:
            print(f"❌ Basic method FAILED: {result.stderr}")
            
            # Check if it's a bot detection error
            if 'Sign in to confirm' in result.stderr or 'bot' in result.stderr.lower():
                print("\n=== Bot detection triggered, testing Tier 2: Cookie method ===")
                return test_ytdlp_cookies_tier(test_url)
            else:
                print("\n=== Non-bot error, testing Tier 3: Fallback method ===")
                return test_ytdlp_fallback(test_url)
                
    except subprocess.TimeoutExpired:
        print("❌ Basic method TIMEOUT")
        return test_ytdlp_fallback(test_url)
    except Exception as e:
        print(f"❌ Basic method ERROR: {e}")
        return test_ytdlp_fallback(test_url)
    finally:
        # Cleanup
        try:
            import shutil
            shutil.rmtree(temp_cache_dir, ignore_errors=True)
        except:
            pass

def test_ytdlp_cookies_tier(test_url):
    """Test yt-dlp with cookie-based configuration (Tier 2)"""
    print(f"\n=== Testing Tier 2: Cookie Method ===")
    
    temp_cache_dir = tempfile.mkdtemp(prefix='ytdlp_cookie_test_')
    user_agent = random.choice(USER_AGENTS)
    
    cmd_cookies = [
        sys.executable, '-m', 'yt_dlp',
        '--dump-json',
        '--no-download',
        '--no-cache-dir',
        '--cache-dir', temp_cache_dir,
        '--user-agent', user_agent,
        '--referer', 'https://www.youtube.com/',
        '--extractor-retries', '2',
        '--fragment-retries', '2',
        '--retry-sleep', '1',
        '--socket-timeout', '30',
        '--no-check-certificate',
        '--cookies-from-browser', 'chrome',
        '--sleep-interval', '1',
        '--max-sleep-interval', '3',
        '--sleep-requests', '1',
        '--extractor-args', 'youtube:player_client=web',
        '--no-warnings',
        test_url
    ]
    
    try:
        result = subprocess.run(
            cmd_cookies,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✅ Cookie method SUCCESS!")
            video_info = json.loads(result.stdout.strip())
            print(f"Title: {video_info.get('title', 'Unknown')}")
            print(f"Duration: {video_info.get('duration', 0)} seconds")
            print(f"Formats available: {len(video_info.get('formats', []))}")
            return True
        else:
            print(f"❌ Cookie method FAILED: {result.stderr}")
            print("\n=== Cookie method failed, testing Tier 3: Fallback method ===")
            return test_ytdlp_fallback(test_url)
            
    except subprocess.TimeoutExpired:
        print("❌ Cookie method TIMEOUT")
        return test_ytdlp_fallback(test_url)
    except Exception as e:
        print(f"❌ Cookie method ERROR: {e}")
        return test_ytdlp_fallback(test_url)
    finally:
        # Cleanup
        try:
            import shutil
            shutil.rmtree(temp_cache_dir, ignore_errors=True)
        except:
            pass

def test_ytdlp_fallback(test_url):
    """Test yt-dlp with fallback configuration (Tier 3 - no cookies)"""
    print(f"\n=== Testing Tier 3: Fallback Method (no cookies) ===")
    
    temp_cache_dir = tempfile.mkdtemp(prefix='ytdlp_fallback_test_')
    user_agent = random.choice(USER_AGENTS)
    
    cmd_fallback = [
        sys.executable, '-m', 'yt_dlp',
        '--dump-json',
        '--no-download',
        '--no-cache-dir',
        '--cache-dir', temp_cache_dir,
        '--user-agent', user_agent,
        '--referer', 'https://www.youtube.com/',
        '--extractor-retries', '5',
        '--fragment-retries', '5',
        '--retry-sleep', '2',
        '--socket-timeout', '45',
        '--no-check-certificate',
        '--sleep-interval', '2',
        '--max-sleep-interval', '5',
        '--sleep-requests', '1',
        '--extractor-args', 'youtube:player_client=web',
        '--extractor-args', 'youtube:skip=dash',
        '--no-warnings',
        test_url
    ]
    
    try:
        result = subprocess.run(
            cmd_fallback,
            capture_output=True,
            text=True,
            timeout=45
        )
        
        if result.returncode == 0:
            print("✅ Fallback method SUCCESS!")
            video_info = json.loads(result.stdout.strip())
            print(f"Title: {video_info.get('title', 'Unknown')}")
            print(f"Duration: {video_info.get('duration', 0)} seconds")
            print(f"Formats available: {len(video_info.get('formats', []))}")
            return True
        else:
            print(f"❌ Fallback method FAILED: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Fallback method TIMEOUT")
        return False
    except Exception as e:
        print(f"❌ Fallback method ERROR: {e}")
        return False
    finally:
        # Cleanup
        try:
            import shutil
            shutil.rmtree(temp_cache_dir, ignore_errors=True)
        except:
            pass

if __name__ == "__main__":
    # Test with the problematic video
    test_url = "https://www.youtube.com/watch?v=7YBO1SfxJ4A"
    
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    
    print("🚀 Testing yt-dlp Three-Tier Bot Detection Fix")
    print(f"Test URL: {test_url}")
    print("-" * 50)
    
    success = test_ytdlp_with_cookies(test_url)
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Test PASSED! Three-tier fix is working.")
        print("✅ Ready for deployment to Vercel")
    else:
        print("💥 Test FAILED! Three-tier fix needs more work.")
        print("❌ Do not deploy yet")
    print("=" * 50) 