#!/usr/bin/env python3
"""
YouTube Cookie Helper for DebuTube API

This utility helps users format and validate their YouTube cookies
for use with the DebuTube API to access age-restricted and private content.

Usage:
    python cookie_helper.py validate <cookie_file>
    python cookie_helper.py format <cookie_string>
    python cookie_helper.py export-guide

Based on the yt-dlp cookie requirements:
- Use private/incognito browser session
- Navigate to https://www.youtube.com/robots.txt
- Export cookies using browser extension
- Never open the private session again after exporting
"""

import json
import sys
import os
import base64
import tempfile
from datetime import datetime
import requests

class YouTubeCookieHelper:
    def __init__(self):
        self.required_domains = ['youtube.com', '.youtube.com', 'www.youtube.com']
        self.important_cookies = ['SAPISID', 'HSID', 'SSID', 'APISID', 'SID']
    
    def validate_cookie_format(self, cookie_content):
        """Validate if the cookie content is in proper Netscape format"""
        lines = cookie_content.strip().split('\n')
        
        # Check for Netscape header
        if not lines[0].startswith('# Netscape HTTP Cookie File'):
            print("⚠️  Warning: Missing Netscape header. This might still work.")
        
        valid_entries = 0
        youtube_entries = 0
        
        for line in lines:
            if line.startswith('#') or not line.strip():
                continue
                
            parts = line.split('\t')
            if len(parts) >= 7:
                domain = parts[0]
                valid_entries += 1
                
                if any(yt_domain in domain for yt_domain in self.required_domains):
                    youtube_entries += 1
        
        return {
            'valid': valid_entries > 0,
            'total_entries': valid_entries,
            'youtube_entries': youtube_entries,
            'has_important_cookies': self.check_important_cookies(cookie_content)
        }
    
    def check_important_cookies(self, cookie_content):
        """Check if important YouTube authentication cookies are present"""
        found_cookies = []
        for cookie_name in self.important_cookies:
            if cookie_name in cookie_content:
                found_cookies.append(cookie_name)
        return found_cookies
    
    def format_cookie_string(self, cookie_string):
        """Format various cookie string formats to Netscape format"""
        # If it's already in Netscape format, return as-is
        if '# Netscape HTTP Cookie File' in cookie_string:
            return cookie_string
        
        # Handle JSON format cookies (from browser extensions)
        try:
            cookies = json.loads(cookie_string)
            return self.json_to_netscape(cookies)
        except json.JSONDecodeError:
            pass
        
        # Handle semicolon-separated format
        if ';' in cookie_string and '=' in cookie_string:
            return self.semicolon_to_netscape(cookie_string)
        
        return cookie_string
    
    def json_to_netscape(self, cookies):
        """Convert JSON cookies to Netscape format"""
        netscape_lines = ['# Netscape HTTP Cookie File']
        
        for cookie in cookies:
            if isinstance(cookie, dict):
                domain = cookie.get('domain', '.youtube.com')
                flag = 'TRUE' if domain.startswith('.') else 'FALSE'
                path = cookie.get('path', '/')
                secure = 'TRUE' if cookie.get('secure', False) else 'FALSE'
                expiry = str(int(cookie.get('expirationDate', 0)))
                name = cookie.get('name', '')
                value = cookie.get('value', '')
                
                line = f"{domain}\t{flag}\t{path}\t{secure}\t{expiry}\t{name}\t{value}"
                netscape_lines.append(line)
        
        return '\n'.join(netscape_lines)
    
    def semicolon_to_netscape(self, cookie_string):
        """Convert semicolon-separated cookies to Netscape format"""
        netscape_lines = ['# Netscape HTTP Cookie File']
        
        cookies = cookie_string.split(';')
        for cookie in cookies:
            if '=' in cookie:
                name, value = cookie.strip().split('=', 1)
                line = f".youtube.com\tTRUE\t/\tFALSE\t0\t{name}\t{value}"
                netscape_lines.append(line)
        
        return '\n'.join(netscape_lines)
    
    def test_cookies_with_api(self, cookie_content, api_url='http://localhost:5000'):
        """Test cookies with the DebuTube API"""
        try:
            response = requests.post(
                f"{api_url}/api/validate-cookies",
                json={'cookies': cookie_content},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('valid', False), result.get('message', 'Unknown')
            else:
                return False, f"API error: {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {str(e)}"
    
    def export_guide(self):
        """Print detailed cookie export guide"""
        guide = """
🍪 YouTube Cookie Export Guide for DebuTube API

⚠️  CAUTION: Using your account with yt-dlp may risk temporary or permanent bans.
   Use responsibly and consider using a throwaway account.

📋 STEP-BY-STEP INSTRUCTIONS:

1. 🔒 Open a NEW private/incognito browser window
   - Chrome: Ctrl+Shift+N
   - Firefox: Ctrl+Shift+P
   - Safari: Cmd+Shift+N

2. 🔑 Log into YouTube in the private window
   - Go to https://www.youtube.com
   - Sign in with your account
   - Make sure you're fully logged in

3. 🤖 Navigate to the robots.txt page (IMPORTANT!)
   - In the SAME private tab, go to: https://www.youtube.com/robots.txt
   - This prevents cookie rotation
   - DO NOT open any other tabs in this private session

4. 🍪 Export cookies using a browser extension:
   
   Recommended Extensions:
   - Chrome: "Get cookies.txt LOCALLY" or "cookies.txt"
   - Firefox: "cookies.txt" or "Export Cookies"
   
   Alternative Methods:
   - Use browser developer tools (F12 > Application/Storage > Cookies)
   - Copy all youtube.com cookies manually

5. 💾 Save the cookie file
   - Save as .txt file (e.g., youtube_cookies.txt)
   - Make sure it's in Netscape format

6. 🚫 CLOSE the private browser window immediately
   - Never use this private session again
   - This keeps the cookies from rotating

7. ✅ Test your cookies:
   python cookie_helper.py validate youtube_cookies.txt

📝 COOKIE FORMAT EXAMPLE:
# Netscape HTTP Cookie File
.youtube.com	TRUE	/	TRUE	1234567890	SAPISID	your_value_here
.youtube.com	TRUE	/	TRUE	1234567890	HSID	your_value_here

🔧 USAGE WITH API:
Send cookies in your API request:
{
  "url": "https://youtube.com/watch?v=...",
  "cookies": "# Netscape HTTP Cookie File\\n.youtube.com\\tTRUE..."
}

🛡️  SECURITY NOTES:
- Cookies contain sensitive authentication data
- Never share your cookies publicly
- Use environment variables for production
- Cookies expire and may need refreshing
"""
        print(guide)

def main():
    helper = YouTubeCookieHelper()
    
    if len(sys.argv) < 2:
        print("Usage: python cookie_helper.py <command> [args]")
        print("Commands:")
        print("  validate <cookie_file>    - Validate cookie file format")
        print("  format <cookie_string>    - Format cookie string to Netscape")
        print("  export-guide             - Show detailed export instructions")
        print("  test <cookie_file>       - Test cookies with API (requires running API)")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'export-guide':
        helper.export_guide()
        
    elif command == 'validate':
        if len(sys.argv) < 3:
            print("Usage: python cookie_helper.py validate <cookie_file>")
            return
            
        cookie_file = sys.argv[2]
        if not os.path.exists(cookie_file):
            print(f"❌ Cookie file not found: {cookie_file}")
            return
        
        with open(cookie_file, 'r', encoding='utf-8') as f:
            cookie_content = f.read()
        
        validation = helper.validate_cookie_format(cookie_content)
        
        print(f"🍪 Cookie Validation Results for: {cookie_file}")
        print(f"✅ Valid format: {'Yes' if validation['valid'] else 'No'}")
        print(f"📊 Total entries: {validation['total_entries']}")
        print(f"🎥 YouTube entries: {validation['youtube_entries']}")
        print(f"🔑 Important cookies found: {', '.join(validation['has_important_cookies']) if validation['has_important_cookies'] else 'None'}")
        
        if validation['youtube_entries'] == 0:
            print("⚠️  Warning: No YouTube cookies found!")
        
        if not validation['has_important_cookies']:
            print("⚠️  Warning: No important authentication cookies found!")
            print("   Make sure you're logged in when exporting cookies.")
    
    elif command == 'format':
        if len(sys.argv) < 3:
            print("Usage: python cookie_helper.py format <cookie_string>")
            return
        
        cookie_string = sys.argv[2]
        formatted = helper.format_cookie_string(cookie_string)
        print("🔄 Formatted cookies:")
        print(formatted)
    
    elif command == 'test':
        if len(sys.argv) < 3:
            print("Usage: python cookie_helper.py test <cookie_file>")
            return
        
        cookie_file = sys.argv[2]
        if not os.path.exists(cookie_file):
            print(f"❌ Cookie file not found: {cookie_file}")
            return
        
        with open(cookie_file, 'r', encoding='utf-8') as f:
            cookie_content = f.read()
        
        print("🧪 Testing cookies with API...")
        is_valid, message = helper.test_cookies_with_api(cookie_content)
        
        if is_valid:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: validate, format, export-guide, test")

if __name__ == '__main__':
    main() 