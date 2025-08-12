#!/usr/bin/env python3
"""
Test script for YouTube cookie integration with DebuTube API

This script tests the cookie functionality and demonstrates how to use
the enhanced API with YouTube authentication cookies.
"""

import requests
import json
import sys
import os
from datetime import datetime

class CookieIntegrationTest:
    def __init__(self, api_base_url='http://localhost:5000'):
        self.api_base_url = api_base_url
        self.test_results = []
    
    def log_test(self, test_name, success, message):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
    
    def test_api_health(self):
        """Test if the API is running"""
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=10)
            if response.status_code == 200:
                self.log_test("API Health Check", True, "API is running")
                return True
            else:
                self.log_test("API Health Check", False, f"API returned {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.log_test("API Health Check", False, f"Cannot connect to API: {str(e)}")
            return False
    
    def test_formats_without_cookies(self):
        """Test formats endpoint without cookies (baseline)"""
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Public video
        
        try:
            response = requests.post(
                f"{self.api_base_url}/api/formats",
                json={"url": test_url},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                formats_count = len(data.get('formats', []))
                self.log_test("Formats Without Cookies", True, f"Retrieved {formats_count} formats")
                return True
            else:
                self.log_test("Formats Without Cookies", False, f"API error: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test("Formats Without Cookies", False, f"Request failed: {str(e)}")
            return False
    
    def test_cookie_validation_endpoint(self, cookie_content=None):
        """Test the cookie validation endpoint"""
        if not cookie_content:
            # Use a dummy cookie for testing the endpoint
            cookie_content = "# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tFALSE\t0\ttest\tvalue"
        
        try:
            response = requests.post(
                f"{self.api_base_url}/api/validate-cookies",
                json={"cookies": cookie_content},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                is_valid = data.get('valid', False)
                message = data.get('message', 'Unknown')
                self.log_test("Cookie Validation Endpoint", True, f"Endpoint works: {message}")
                return is_valid
            else:
                self.log_test("Cookie Validation Endpoint", False, f"API error: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test("Cookie Validation Endpoint", False, f"Request failed: {str(e)}")
            return False
    
    def test_formats_with_cookies(self, cookie_content):
        """Test formats endpoint with cookies"""
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Public video
        
        try:
            response = requests.post(
                f"{self.api_base_url}/api/formats",
                json={
                    "url": test_url,
                    "cookies": cookie_content
                },
                timeout=45
            )
            
            if response.status_code == 200:
                data = response.json()
                formats_count = len(data.get('formats', []))
                video_info = data.get('videoInfo', {})
                self.log_test("Formats With Cookies", True, 
                            f"Retrieved {formats_count} formats for '{video_info.get('title', 'Unknown')}'")
                return True
            else:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('error', f"HTTP {response.status_code}")
                self.log_test("Formats With Cookies", False, f"API error: {error_msg}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test("Formats With Cookies", False, f"Request failed: {str(e)}")
            return False
    
    def test_direct_url_with_cookies(self, cookie_content):
        """Test direct URL endpoint with cookies"""
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        try:
            # First get formats
            formats_response = requests.post(
                f"{self.api_base_url}/api/formats",
                json={
                    "url": test_url,
                    "cookies": cookie_content
                },
                timeout=45
            )
            
            if formats_response.status_code != 200:
                self.log_test("Direct URL With Cookies", False, "Could not get formats first")
                return False
            
            formats_data = formats_response.json()
            formats = formats_data.get('formats', [])
            
            if not formats:
                self.log_test("Direct URL With Cookies", False, "No formats available")
                return False
            
            # Test with the first available format
            format_id = formats[0]['format_id']
            
            response = requests.post(
                f"{self.api_base_url}/api/direct-url",
                json={
                    "url": test_url,
                    "formatId": format_id,
                    "cookies": cookie_content
                },
                timeout=45
            )
            
            if response.status_code == 200:
                data = response.json()
                direct_url = data.get('directUrl', '')
                if direct_url:
                    self.log_test("Direct URL With Cookies", True, f"Got direct URL for format {format_id}")
                    return True
                else:
                    self.log_test("Direct URL With Cookies", False, "Empty direct URL")
                    return False
            else:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('error', f"HTTP {response.status_code}")
                self.log_test("Direct URL With Cookies", False, f"API error: {error_msg}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test("Direct URL With Cookies", False, f"Request failed: {str(e)}")
            return False
    
    def test_error_handling(self):
        """Test error handling for various scenarios"""
        # Test invalid URL
        try:
            response = requests.post(
                f"{self.api_base_url}/api/formats",
                json={"url": "not-a-youtube-url"},
                timeout=10
            )
            
            if response.status_code == 400:
                self.log_test("Error Handling - Invalid URL", True, "Correctly rejected invalid URL")
            else:
                self.log_test("Error Handling - Invalid URL", False, f"Expected 400, got {response.status_code}")
        except Exception as e:
            self.log_test("Error Handling - Invalid URL", False, f"Request failed: {str(e)}")
        
        # Test missing URL
        try:
            response = requests.post(
                f"{self.api_base_url}/api/formats",
                json={},
                timeout=10
            )
            
            if response.status_code == 400:
                self.log_test("Error Handling - Missing URL", True, "Correctly rejected missing URL")
            else:
                self.log_test("Error Handling - Missing URL", False, f"Expected 400, got {response.status_code}")
        except Exception as e:
            self.log_test("Error Handling - Missing URL", False, f"Request failed: {str(e)}")
    
    def run_comprehensive_test(self, cookie_file=None):
        """Run all tests"""
        print("🧪 Starting DebuTube Cookie Integration Tests")
        print("=" * 60)
        
        # Basic API tests
        if not self.test_api_health():
            print("❌ API is not running. Please start the Flask API first.")
            return False
        
        self.test_formats_without_cookies()
        self.test_error_handling()
        
        # Cookie-specific tests
        cookie_content = None
        if cookie_file and os.path.exists(cookie_file):
            print(f"\n🍪 Testing with cookie file: {cookie_file}")
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookie_content = f.read()
        else:
            print("\n🍪 Testing cookie endpoints with dummy data")
        
        self.test_cookie_validation_endpoint(cookie_content)
        
        if cookie_content:
            self.test_formats_with_cookies(cookie_content)
            self.test_direct_url_with_cookies(cookie_content)
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        
        if failed_tests > 0:
            print("\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        print(f"\n📈 Success Rate: {success_rate:.1f}%")
        
        return failed_tests == 0

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == '--help':
            print("Usage: python test_cookie_integration.py [cookie_file] [api_url]")
            print("\nArguments:")
            print("  cookie_file  - Path to YouTube cookie file (optional)")
            print("  api_url      - API base URL (default: http://localhost:5000)")
            print("\nExamples:")
            print("  python test_cookie_integration.py")
            print("  python test_cookie_integration.py youtube_cookies.txt")
            print("  python test_cookie_integration.py youtube_cookies.txt http://localhost:8000")
            return
        
        cookie_file = sys.argv[1] if len(sys.argv) > 1 else None
        api_url = sys.argv[2] if len(sys.argv) > 2 else 'http://localhost:5000'
    else:
        cookie_file = None
        api_url = 'http://localhost:5000'
    
    tester = CookieIntegrationTest(api_url)
    success = tester.run_comprehensive_test(cookie_file)
    
    if success:
        print("\n🎉 All tests passed! Cookie integration is working correctly.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Please check the API implementation.")
        sys.exit(1)

if __name__ == '__main__':
    main() 