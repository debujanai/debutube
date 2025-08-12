# YouTube Cookie Integration for DebuTube API

## Overview

DebuTube API now supports YouTube cookies to access age-restricted content, private videos, and members-only content while avoiding bot detection. This implementation follows yt-dlp best practices for secure cookie handling.

## ⚠️ Important Security Notice

**CAUTION**: Using your YouTube account with yt-dlp may risk temporary or permanent account suspension. Please:
- Use responsibly and limit request frequency
- Consider using a throwaway/secondary account
- Only use when necessary for accessing restricted content

## 🚀 Quick Start

### 1. Export YouTube Cookies

Use the cookie helper utility to get step-by-step instructions:

```bash
python cookie_helper.py export-guide
```

### 2. Validate Your Cookies

```bash
python cookie_helper.py validate youtube_cookies.txt
```

### 3. Test with API

```bash
python test_cookie_integration.py youtube_cookies.txt
```

## 📋 Cookie Export Process

### Method 1: Browser Extension (Recommended)

1. **Open Private/Incognito Window**
   - Chrome: `Ctrl+Shift+N` (Windows) / `Cmd+Shift+N` (Mac)
   - Firefox: `Ctrl+Shift+P` (Windows) / `Cmd+Shift+P` (Mac)

2. **Login to YouTube**
   - Navigate to https://www.youtube.com
   - Sign in with your account
   - Ensure you're fully authenticated

3. **Navigate to robots.txt** (Critical!)
   - In the SAME private tab, go to: https://www.youtube.com/robots.txt
   - This prevents cookie rotation
   - DO NOT open any other tabs in this session

4. **Export Cookies**
   - Install a cookie export extension:
     - Chrome: "Get cookies.txt LOCALLY" or "cookies.txt"
     - Firefox: "cookies.txt" or "Export Cookies"
   - Export all youtube.com cookies
   - Save as .txt file in Netscape format

5. **Close Private Window**
   - Immediately close the private browsing session
   - Never reuse this session to keep cookies valid

### Method 2: Developer Tools

1. Follow steps 1-3 above
2. Press `F12` to open Developer Tools
3. Go to `Application` (Chrome) or `Storage` (Firefox)
4. Navigate to `Cookies` > `https://www.youtube.com`
5. Copy all cookie values manually
6. Format using: `python cookie_helper.py format "cookie_string"`

## 🔧 API Usage

### Basic Request with Cookies

```javascript
// JavaScript/Frontend
const response = await fetch('/api/formats', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    url: 'https://www.youtube.com/watch?v=VIDEO_ID',
    cookies: '# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\t...'
  })
});
```

```python
# Python
import requests

response = requests.post('http://localhost:5000/api/formats', json={
    'url': 'https://www.youtube.com/watch?v=VIDEO_ID',
    'cookies': cookie_content
})
```

### Supported Cookie Formats

The API accepts cookies in multiple formats:

1. **Netscape Format** (Preferred)
```
# Netscape HTTP Cookie File
.youtube.com	TRUE	/	TRUE	1234567890	SAPISID	value_here
```

2. **JSON Format**
```json
[
  {
    "domain": ".youtube.com",
    "name": "SAPISID",
    "value": "value_here",
    "path": "/",
    "secure": true,
    "expirationDate": 1234567890
  }
]
```

3. **Base64 Encoded**
```
data:text/plain;base64,IyBOZXRzY2FwZSBIVFRQIENvb2tpZSBGaWxl...
```

## 🛠️ API Endpoints

### POST `/api/formats`
Get video formats with cookie support.

**Request:**
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "cookies": "cookie_content_here"  // Optional
}
```

**Response:**
```json
{
  "videoInfo": {
    "title": "Video Title",
    "duration": 240,
    "age_limit": 18,
    "availability": "needs_auth"
  },
  "formats": [...]
}
```

### POST `/api/direct-url`
Get direct download URL with cookie support.

**Request:**
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "formatId": "22",
  "cookies": "cookie_content_here"  // Optional
}
```

### POST `/api/validate-cookies`
Validate cookie functionality.

**Request:**
```json
{
  "cookies": "cookie_content_here"
}
```

**Response:**
```json
{
  "valid": true,
  "message": "Cookies are valid and working"
}
```

## 🔍 Troubleshooting

### Common Issues

1. **"Sign in to confirm you're not a bot"**
   - Your cookies may be invalid or expired
   - Try re-exporting cookies following the exact process
   - Ensure you used private/incognito window

2. **"This video requires authentication"**
   - Video needs valid YouTube account cookies
   - Check if your account has access to the content
   - Verify cookies contain authentication tokens (SAPISID, HSID, etc.)

3. **"Age-restricted video"**
   - Your account must be verified for age-restricted content
   - Ensure cookies are from an authenticated session
   - Some content may require additional verification

4. **"Private video" or "Members-only content"**
   - Your account must have access to the specific content
   - Check if you're subscribed to the channel (for members-only)
   - Verify you're using cookies from the correct account

### Debug Steps

1. **Validate Cookie Format**
   ```bash
   python cookie_helper.py validate your_cookies.txt
   ```

2. **Test Cookie Functionality**
   ```bash
   python cookie_helper.py test your_cookies.txt
   ```

3. **Run Integration Tests**
   ```bash
   python test_cookie_integration.py your_cookies.txt
   ```

4. **Check API Logs**
   - Look for yt-dlp error messages in console output
   - Check for network connectivity issues
   - Verify cookie file permissions

## 🔒 Security Best Practices

### Cookie Storage
- **Never commit cookies to version control**
- Use environment variables for production:
  ```bash
  export YTDLP_COOKIES="cookie_content_here"
  ```
- Store cookies securely and rotate regularly

### Production Deployment
```python
# Use environment variables
import os
cookies = os.environ.get('YTDLP_COOKIES')

# Or secure file storage
cookie_file = '/secure/path/youtube_cookies.txt'
```

### Rate Limiting
- Implement request throttling to avoid detection
- Add random delays between requests
- Monitor for 429 (Too Many Requests) responses

## 📊 Monitoring and Maintenance

### Cookie Expiration
- YouTube cookies typically expire after 1-2 weeks
- Monitor for authentication failures
- Implement automatic cookie refresh if needed

### Health Checks
```bash
# Regular validation
python cookie_helper.py test your_cookies.txt

# API health check
curl http://localhost:5000/health
```

### Logging
The API provides detailed error messages for troubleshooting:
- Bot detection warnings
- Authentication requirements
- Age restriction notices
- Cookie validation failures

## 🔧 Utility Scripts

### `cookie_helper.py`
- `export-guide`: Step-by-step cookie export instructions
- `validate <file>`: Validate cookie file format
- `format <string>`: Convert cookie formats
- `test <file>`: Test cookies with API

### `test_cookie_integration.py`
- Comprehensive API testing
- Cookie functionality validation
- Error handling verification
- Performance benchmarking

## 📈 Performance Considerations

### Serverless Deployment (Vercel)
- Cookies are stored in temporary directories
- Automatic cleanup after requests
- Increased timeout for authentication requests
- Memory-efficient cookie handling

### Local Development
- Persistent cookie validation
- Debug logging enabled
- Development-friendly error messages
- Hot reload support

## 🤝 Contributing

When contributing to cookie functionality:

1. **Test thoroughly** with various cookie formats
2. **Follow security practices** - never log sensitive data
3. **Update documentation** for any API changes
4. **Add tests** for new cookie features
5. **Consider edge cases** - expired cookies, malformed data, etc.

## 📚 Additional Resources

- [yt-dlp Cookie Documentation](https://github.com/yt-dlp/yt-dlp#how-do-i-pass-cookies-to-yt-dlp)
- [YouTube API Terms of Service](https://developers.google.com/youtube/terms/api-services-terms-of-service)
- [Browser Cookie Export Extensions](https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp)

---

**Remember**: This feature should be used responsibly and in compliance with YouTube's Terms of Service. The primary purpose is to access content you have legitimate rights to view, not to circumvent YouTube's restrictions. 