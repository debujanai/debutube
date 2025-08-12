#!/usr/bin/env python3
"""
Simple test to verify hardcoded cookies work with the API
"""

import requests
import json

def test_hardcoded_cookies():
    """Test the API with hardcoded cookies"""
    print("🧪 Testing API with hardcoded cookies...")
    
    # Test a simple YouTube video
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    try:
        response = requests.post(
            'http://localhost:5000/api/formats',
            json={'url': test_url},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            video_info = data.get('videoInfo', {})
            formats = data.get('formats', [])
            using_hardcoded = data.get('using_hardcoded_cookies', False)
            
            print(f"✅ Success!")
            print(f"📹 Video: {video_info.get('title', 'Unknown')}")
            print(f"📊 Formats: {len(formats)}")
            print(f"🍪 Using hardcoded cookies: {using_hardcoded}")
            print(f"👤 Channel: {video_info.get('channel', 'Unknown')}")
            print(f"⏱️  Duration: {video_info.get('duration', 0)} seconds")
            
            if formats:
                best_format = max(formats, key=lambda x: x.get('quality', 0) or 0)
                print(f"🎯 Best quality: {best_format.get('format_id')} ({best_format.get('resolution', 'unknown')})")
            
            return True
            
        else:
            print(f"❌ Failed: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data.get('error', 'Unknown error')}")
                if 'help' in error_data:
                    print(f"Help: {error_data['help']}")
            except:
                print(f"Raw response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False

if __name__ == '__main__':
    print("🚀 Testing Hardcoded YouTube Cookies")
    print("=" * 50)
    
    # Check if API is running
    try:
        health = requests.get('http://localhost:5000/health', timeout=5)
        if health.status_code != 200:
            print("❌ API not running. Start it with: python api/app.py")
            exit(1)
    except:
        print("❌ Cannot connect to API. Start it with: python api/app.py")
        exit(1)
    
    success = test_hardcoded_cookies()
    
    if success:
        print("\n🎉 Hardcoded cookies are working! Ready for Vercel deployment.")
    else:
        print("\n⚠️  Hardcoded cookies may need refreshing or there's an API issue.") 