# Vercel yt-dlp Deployment Fixes

## Problem
When deploying to Vercel, yt-dlp was failing with two main issues:

1. **Read-only file system error**: `OSError: [Errno 30] Read-only file system: '/home/sbx_user1051'`
2. **YouTube bot detection**: `Sign in to confirm you're not a bot`

## Root Causes
- Vercel serverless functions have a read-only file system except for `/tmp`
- yt-dlp tries to write cache files to the user's home directory
- YouTube detects serverless environments as bots and blocks requests

## Solutions Implemented

### 1. File System Fixes
- **Set HOME environment variable** to `/tmp` (writable directory)
- **Use temporary cache directories** in `/tmp` with automatic cleanup
- **Disable caching** with `--no-cache-dir` flag
- **Specify temp cache directory** as fallback with `--cache-dir`

### 2. Bot Detection Avoidance
- **Rotate User-Agents**: Use realistic browser user agents
- **Add referer header**: Set `https://www.youtube.com/` as referer
- **Retry logic**: Configure retries and timeouts for reliability
- **SSL handling**: Skip certificate verification issues

### 3. Configuration Options Added
```bash
--no-cache-dir                    # Disable cache completely
--cache-dir /tmp/ytdlp_cache_*   # Use temp directory for any cache needs
--user-agent "Chrome/120.0..."   # Realistic browser user agent (rotated)
--referer "https://www.youtube.com/" # Set YouTube as referer
--extractor-retries 3            # Retry failed extractions
--fragment-retries 3             # Retry failed fragments
--retry-sleep 1                  # Wait between retries
--socket-timeout 30              # Socket timeout
--no-check-certificate           # Skip SSL verification issues
```

## Testing

### Local Testing
Run the test script to verify fixes work:
```bash
python test_ytdlp_fix.py
```

### Manual Testing
Test individual URLs:
```bash
python -m yt_dlp --dump-json --no-download --no-cache-dir \
  --user-agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  --referer "https://www.youtube.com/" \
  "https://www.youtube.com/watch?v=VIDEO_ID"
```

## Deployment Steps

1. **Update dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Test locally**:
   ```bash
   python test_ytdlp_fix.py
   ```

3. **Deploy to Vercel**:
   ```bash
   vercel --prod
   ```

## Additional Recommendations

### If Issues Persist

1. **Add cookies** (for persistent bot detection):
   ```python
   # Add to yt-dlp command:
   '--cookies-from-browser', 'chrome'
   ```

2. **Use proxy rotation** (if available):
   ```python
   '--proxy', 'http://your-proxy:port'
   ```

3. **Implement rate limiting**:
   ```python
   import time
   time.sleep(random.uniform(1, 3))  # Random delay between requests
   ```

4. **Monitor Vercel function logs**:
   ```bash
   vercel logs
   ```

### Environment Variables (Optional)
You can set these in Vercel dashboard:
- `YTDLP_USER_AGENT`: Custom user agent
- `YTDLP_PROXY`: Proxy server if needed
- `YTDLP_COOKIES`: Cookie string for authentication

## Files Modified
- `api/app.py` - Main Flask API with yt-dlp integration
- `requirements.txt` - Updated dependencies
- `test_ytdlp_fix.py` - Test script for verification

## Success Indicators
✅ No cache directory errors  
✅ No bot detection messages  
✅ Successful video metadata extraction  
✅ Working direct URL generation  

## Troubleshooting

### Still getting bot detection?
- Try different user agents
- Add delays between requests
- Consider using cookies

### Still getting file system errors?
- Verify `/tmp` directory usage
- Check environment variable settings
- Ensure proper cleanup of temp directories

### Timeout issues?
- Increase timeout values
- Check network connectivity
- Verify Vercel function limits

## Support
If issues persist, check:
- Vercel function logs: `vercel logs`
- yt-dlp version: `python -m yt_dlp --version`
- Test with simple videos first 