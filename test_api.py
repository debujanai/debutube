#!/usr/bin/env python3
"""
Test script to verify the API endpoints work with the three-tier bot detection fix
"""

import requests
import json

def test_api_formats():
    """Test the /api/formats endpoint"""
    url = "http://localhost:5000/api/formats"
    test_video_url = "https://www.youtube.com/watch?v=7YBO1SfxJ4A"
    
    payload = {"url": test_video_url}
    headers = {"Content-Type": "application/json"}
    
    try:
        print(f"Testing API endpoint: {url}")
        print(f"With video URL: {test_video_url}")
        print("-" * 50)
        
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API Test SUCCESS!")
            print(f"Video Title: {data.get('videoInfo', {}).get('title', 'Unknown')}")
            print(f"Formats Available: {len(data.get('formats', []))}")
            print(f"Duration: {data.get('videoInfo', {}).get('duration', 0)} seconds")
            return True
        else:
            print(f"❌ API Test FAILED!")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Flask app is not running on localhost:5000")
        print("Please start the Flask app first: python api/app.py")
        return False
    except Exception as e:
        print(f"❌ API Test ERROR: {e}")
        return False

def test_api_direct_url():
    """Test the /api/direct-url endpoint"""
    url = "http://localhost:5000/api/direct-url"
    test_video_url = "https://www.youtube.com/watch?v=7YBO1SfxJ4A"
    format_id = "18"  # Common format ID
    
    payload = {"url": test_video_url, "formatId": format_id}
    headers = {"Content-Type": "application/json"}
    
    try:
        print(f"\nTesting API endpoint: {url}")
        print(f"With video URL: {test_video_url}")
        print(f"Format ID: {format_id}")
        print("-" * 50)
        
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Direct URL API Test SUCCESS!")
            print(f"Direct URL obtained: {data.get('directUrl', 'Not found')[:100]}...")
            return True
        else:
            print(f"❌ Direct URL API Test FAILED!")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Flask app is not running on localhost:5000")
        return False
    except Exception as e:
        print(f"❌ Direct URL API Test ERROR: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing DebuTube API with Three-Tier Bot Detection Fix")
    print("=" * 60)
    
    # Test formats endpoint
    formats_success = test_api_formats()
    
    # Test direct-url endpoint
    direct_url_success = test_api_direct_url()
    
    print("\n" + "=" * 60)
    if formats_success and direct_url_success:
        print("🎉 ALL API TESTS PASSED!")
        print("✅ Three-tier bot detection fix is working in the API")
        print("✅ Ready for deployment to Vercel")
    elif formats_success:
        print("🎯 FORMATS API PASSED, DIRECT URL API FAILED")
        print("⚠️ Partial success - formats endpoint works")
    else:
        print("💥 API TESTS FAILED!")
        print("❌ Do not deploy yet")
    print("=" * 60) 