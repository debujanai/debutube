#!/usr/bin/env python3
"""
Test script for advanced TLS client YouTube session
"""
import sys
import os
import json

# Add the api directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

try:
    from youtube_session import YouTubeSession
except ImportError as e:
    print(f"❌ Failed to import YouTubeSession: {e}")
    print("Make sure you're running this from the project root directory")
    print("And that tls-client and fake-useragent are installed:")
    print("  pip install tls-client fake-useragent")
    sys.exit(1)

def test_tls_connection():
    """Test TLS connection to YouTube"""
    print("🧪 Testing TLS Connection")
    print("-" * 40)
    
    try:
        session = YouTubeSession()
        result = session.test_connection()
        
        if result.get('success'):
            print("✅ TLS Connection: SUCCESS")
            print(f"   TLS Fingerprint: {result.get('tls_fingerprint')}")
            print(f"   User Agent: {result.get('user_agent')[:60]}...")
            print(f"   Status Code: {result.get('status_code')}")
            print(f"   Response Size: {result.get('response_size')} bytes")
            return True
        else:
            print("❌ TLS Connection: FAILED")
            print(f"   Error: {result.get('error')}")
            print(f"   TLS Fingerprint: {result.get('tls_fingerprint')}")
            return False
            
    except Exception as e:
        print(f"❌ TLS Connection: EXCEPTION - {e}")
        return False

def test_video_extraction(url, use_stealth=False):
    """Test video information extraction"""
    mode = "STEALTH" if use_stealth else "ENHANCED"
    print(f"\n🎥 Testing Video Extraction ({mode} MODE)")
    print("-" * 50)
    print(f"URL: {url}")
    
    try:
        session = YouTubeSession()
        result = session.extract_video_info(url, use_stealth=use_stealth)
        
        if result.get('success'):
            video_info = result['data']
            print("✅ Video Extraction: SUCCESS")
            print(f"   Title: {video_info.get('title', 'Unknown')}")
            print(f"   Duration: {video_info.get('duration', 0)} seconds")
            print(f"   Uploader: {video_info.get('uploader', 'Unknown')}")
            print(f"   View Count: {video_info.get('view_count', 0):,}")
            print(f"   Formats Available: {len(video_info.get('formats', []))}")
            
            # Show some format examples
            formats = video_info.get('formats', [])[:5]  # First 5 formats
            if formats:
                print("   Sample Formats:")
                for fmt in formats:
                    quality = fmt.get('format_note', 'Unknown')
                    ext = fmt.get('ext', 'Unknown')
                    format_id = fmt.get('format_id', 'Unknown')
                    print(f"     - {format_id}: {quality} ({ext})")
            
            return True, video_info
        else:
            print("❌ Video Extraction: FAILED")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            print(f"   TLS Fingerprint: {result.get('tls_fingerprint', 'Unknown')}")
            return False, None
            
    except Exception as e:
        print(f"❌ Video Extraction: EXCEPTION - {e}")
        return False, None

def test_direct_url(url, format_id, use_stealth=False):
    """Test direct URL extraction"""
    mode = "STEALTH" if use_stealth else "ENHANCED"
    print(f"\n🔗 Testing Direct URL Extraction ({mode} MODE)")
    print("-" * 55)
    print(f"URL: {url}")
    print(f"Format ID: {format_id}")
    
    try:
        session = YouTubeSession()
        result = session.get_direct_url(url, format_id, use_stealth=use_stealth)
        
        if result.get('success'):
            direct_url = result['direct_url']
            print("✅ Direct URL Extraction: SUCCESS")
            print(f"   Direct URL: {direct_url[:80]}...")
            print(f"   URL Length: {len(direct_url)} characters")
            return True, direct_url
        else:
            print("❌ Direct URL Extraction: FAILED")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            print(f"   TLS Fingerprint: {result.get('tls_fingerprint', 'Unknown')}")
            return False, None
            
    except Exception as e:
        print(f"❌ Direct URL Extraction: EXCEPTION - {e}")
        return False, None

def main():
    """Main test function"""
    print("🚀 Advanced TLS Client YouTube Session Test")
    print("=" * 60)
    
    # Test URLs
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll - reliable test
        "https://www.youtube.com/watch?v=7YBO1SfxJ4A",  # The problematic URL from your error
    ]
    
    # Step 1: Test TLS connection
    if not test_tls_connection():
        print("\n❌ TLS connection failed. Check your internet connection and dependencies.")
        return
    
    # Step 2: Test video extraction
    success_count = 0
    total_tests = len(test_urls) * 2  # Each URL tested in both modes
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n" + "=" * 60)
        print(f"📹 Test Video {i}/{len(test_urls)}")
        print("=" * 60)
        
        # Test enhanced mode first
        success, video_info = test_video_extraction(url, use_stealth=False)
        if success:
            success_count += 1
            
            # If enhanced mode works, test direct URL extraction
            formats = video_info.get('formats', [])
            if formats:
                # Try to get direct URL for the first available format
                format_id = formats[0].get('format_id')
                if format_id:
                    direct_success, _ = test_direct_url(url, format_id, use_stealth=False)
                    if direct_success:
                        print("   ✅ Direct URL also working!")
                    else:
                        print("   ⚠️ Direct URL failed, but video info worked")
        else:
            # If enhanced mode fails, try stealth mode
            print("\n🔄 Enhanced mode failed, trying stealth mode...")
            success, video_info = test_video_extraction(url, use_stealth=True)
            if success:
                success_count += 1
                print("   ✅ Stealth mode successful!")
            else:
                print("   ❌ Both enhanced and stealth modes failed")
        
        success_count += 1 if success else 0
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 Test Summary")
    print("=" * 60)
    print(f"Success Rate: {success_count}/{len(test_urls)} videos")
    
    if success_count == len(test_urls):
        print("🎉 All tests passed! The TLS client implementation is working perfectly.")
    elif success_count > 0:
        print("⚠️ Some tests passed. The implementation is working but may need fine-tuning.")
    else:
        print("❌ All tests failed. Check the troubleshooting section.")
    
    print("\n📋 Troubleshooting:")
    print("1. Ensure dependencies are installed: pip install tls-client fake-useragent")
    print("2. Check your internet connection")
    print("3. Try running the Flask app and test via API endpoints")
    print("4. Verify Chrome is installed for cookie extraction")
    print("5. Wait a few minutes if you see rate limiting")

if __name__ == "__main__":
    main() 