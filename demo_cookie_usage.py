#!/usr/bin/env python3
"""
Demo script showing how to use YouTube cookies with DebuTube API

This demonstrates the cookie functionality for accessing age-restricted
and private YouTube content.
"""

import requests
import json
import sys

def demo_without_cookies():
    """Demo accessing a public video without cookies"""
    print("🎬 Demo 1: Accessing public video WITHOUT cookies")
    print("-" * 50)
    
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll - public video
    
    try:
        response = requests.post('http://localhost:5000/api/formats', 
                               json={'url': url}, 
                               timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            video_info = data['videoInfo']
            formats = data['formats']
            
            print(f"✅ Success! Retrieved video: {video_info['title']}")
            print(f"📊 Available formats: {len(formats)}")
            print(f"👤 Channel: {video_info['channel']}")
            print(f"⏱️  Duration: {video_info['duration']} seconds")
            print(f"🔒 Age limit: {video_info.get('age_limit', 0)}")
            print(f"📺 Availability: {video_info.get('availability', 'unknown')}")
            
        else:
            print(f"❌ Failed: {response.status_code}")
            if response.content:
                error = response.json().get('error', 'Unknown error')
                print(f"Error: {error}")
                
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    print()

def demo_with_cookies(cookie_content):
    """Demo accessing content WITH cookies"""
    print("🍪 Demo 2: Accessing video WITH cookies")
    print("-" * 50)
    
    # Test with the same video but with authentication
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    try:
        # First validate cookies
        print("🔍 Validating cookies...")
        validate_response = requests.post('http://localhost:5000/api/validate-cookies',
                                        json={'cookies': cookie_content},
                                        timeout=30)
        
        if validate_response.status_code == 200:
            validation = validate_response.json()
            print(f"✅ Cookie validation: {validation['message']}")
        else:
            print("⚠️  Cookie validation failed")
        
        # Now try with cookies
        print("📹 Fetching video with cookies...")
        response = requests.post('http://localhost:5000/api/formats',
                               json={
                                   'url': url,
                                   'cookies': cookie_content
                               },
                               timeout=45)
        
        if response.status_code == 200:
            data = response.json()
            video_info = data['videoInfo']
            formats = data['formats']
            
            print(f"✅ Success with cookies! Video: {video_info['title']}")
            print(f"📊 Available formats: {len(formats)}")
            print(f"👤 Channel: {video_info['channel']}")
            print(f"🔒 Age limit: {video_info.get('age_limit', 0)}")
            print(f"📺 Availability: {video_info.get('availability', 'unknown')}")
            
            # Show format quality differences
            if formats:
                best_quality = max(formats, key=lambda x: x.get('quality', 0) or 0)
                print(f"🎯 Best quality format: {best_quality['format_id']} "
                      f"({best_quality.get('resolution', 'unknown')})")
        else:
            print(f"❌ Failed with cookies: {response.status_code}")
            if response.content:
                error = response.json().get('error', 'Unknown error')
                print(f"Error: {error}")
                
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    print()

def demo_age_restricted_example():
    """Show how to handle age-restricted content"""
    print("🔞 Demo 3: Age-restricted content example")
    print("-" * 50)
    
    print("📝 For age-restricted videos, you would:")
    print("1. Export cookies from an authenticated YouTube session")
    print("2. Ensure your account is verified for age-restricted content")
    print("3. Use the same API calls but with cookies included")
    print()
    print("Example age-restricted video URL:")
    print("https://www.youtube.com/watch?v=SOME_AGE_RESTRICTED_VIDEO")
    print()
    print("The API will return helpful error messages like:")
    print("- 'This video is age-restricted. Please provide valid YouTube cookies.'")
    print("- 'YouTube bot detection triggered. Please provide valid cookies.'")
    print()

def demo_cookie_formats():
    """Show different cookie format examples"""
    print("📋 Demo 4: Supported cookie formats")
    print("-" * 50)
    
    print("1. Netscape Format (Recommended):")
    print("# Netscape HTTP Cookie File")
    print(".youtube.com\tTRUE\t/\tTRUE\t1234567890\tSAPISID\tyour_value_here")
    print()
    
    print("2. JSON Format:")
    json_example = [{
        "domain": ".youtube.com",
        "name": "SAPISID",
        "value": "your_value_here",
        "path": "/",
        "secure": True,
        "expirationDate": 1234567890
    }]
    print(json.dumps(json_example, indent=2))
    print()
    
    print("3. Base64 Encoded:")
    print("data:text/plain;base64,IyBOZXRzY2FwZSBIVFRQIENvb2tpZSBGaWxl...")
    print()

def main():
    print("🚀 DebuTube Cookie Integration Demo")
    print("=" * 60)
    print()
    
    # Check if API is running
    try:
        health_check = requests.get('http://localhost:5000/health', timeout=5)
        if health_check.status_code != 200:
            print("❌ API is not running. Please start it first:")
            print("   python api/app.py")
            return
    except:
        print("❌ Cannot connect to API. Please start it first:")
        print("   python api/app.py")
        return
    
    # Demo 1: Without cookies
    demo_without_cookies()
    
    # Demo 2: With cookies (if provided)
    if len(sys.argv) > 1:
        cookie_file = sys.argv[1]
        try:
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookie_content = f.read()
            demo_with_cookies(cookie_content)
        except FileNotFoundError:
            print(f"❌ Cookie file not found: {cookie_file}")
        except Exception as e:
            print(f"❌ Error reading cookie file: {str(e)}")
    else:
        print("🍪 To test with cookies, run:")
        print(f"   python {sys.argv[0]} your_cookies.txt")
        print()
    
    # Demo 3: Age-restricted info
    demo_age_restricted_example()
    
    # Demo 4: Cookie formats
    demo_cookie_formats()
    
    print("🎯 Next Steps:")
    print("1. Export your YouTube cookies following the guide:")
    print("   python cookie_helper.py export-guide")
    print()
    print("2. Validate your cookies:")
    print("   python cookie_helper.py validate your_cookies.txt")
    print()
    print("3. Test with your cookies:")
    print(f"   python {sys.argv[0]} your_cookies.txt")
    print()
    print("4. Use in your application:")
    print("   Send cookies in the 'cookies' field of your API requests")

if __name__ == '__main__':
    main() 