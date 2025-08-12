# Vercel Deployment Guide with YouTube Cookies

## 🚀 Ready for Deployment!

Your API now has **hardcoded YouTube cookies** that are working perfectly. Here's how to deploy to Vercel:

## 📋 Pre-Deployment Checklist

✅ **Hardcoded cookies are working** - Verified locally  
✅ **All essential auth tokens present** - SAPISID, HSID, SSID, APISID, SID  
✅ **Bot detection bypassed** - Successfully tested  
✅ **Enhanced error handling** - Better user feedback  

## 🔧 Deployment Steps

### 1. Deploy to Vercel

```bash
# Install Vercel CLI (if not already installed)
npm i -g vercel

# Deploy from your project directory
vercel --prod
```

### 2. Verify Deployment

After deployment, test these endpoints:

```bash
# Health check
curl https://your-vercel-url.vercel.app/health

# Test formats with hardcoded cookies
curl -X POST https://your-vercel-url.vercel.app/api/formats \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

## 📊 What's Working Now

### ✅ Automatic Cookie Usage
- **Hardcoded cookies are used by default** for all requests
- No need to send cookies from frontend initially
- All essential authentication tokens included

### ✅ Enhanced Features
- **Better error messages** for debugging
- **Debug info** showing when hardcoded cookies are used
- **Fallback system** - can still accept custom cookies if needed

### ✅ Response Format
```json
{
  "videoInfo": {
    "title": "Video Title",
    "duration": 213,
    "channel": "Channel Name"
  },
  "formats": [...],
  "using_hardcoded_cookies": true
}
```

## 🔍 Testing Your Deployment

### Test Script for Production
```javascript
// Test your deployed API
const testUrl = 'https://your-vercel-url.vercel.app/api/formats';

fetch(testUrl, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
  })
})
.then(res => res.json())
.then(data => {
  console.log('✅ Success:', data.videoInfo.title);
  console.log('📊 Formats:', data.formats.length);
  console.log('🍪 Using hardcoded cookies:', data.using_hardcoded_cookies);
})
.catch(err => console.error('❌ Error:', err));
```

## 🛠️ Frontend Integration

Your frontend can now make requests without worrying about cookies:

```javascript
// Simple request - cookies handled automatically
const response = await fetch('/api/formats', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ url: youtubeUrl })
});

const data = await response.json();
// data.using_hardcoded_cookies will be true
```

## ⚠️ Important Notes

### Cookie Expiration
- **YouTube cookies expire** after 1-2 weeks typically
- **Monitor your deployment** for authentication failures
- **Update cookies** when they expire by updating the hardcoded values

### Signs Cookies Need Refreshing
- Getting "bot detection" errors again
- "Sign in to confirm" messages
- Sudden increase in failed requests

### When to Update Cookies
1. Export new cookies following the same process
2. Update the `HARDCODED_YOUTUBE_COOKIES` variable in `api/app.py`
3. Redeploy to Vercel

## 🔮 Future Improvements

### Environment Variables (Recommended)
Later, you can move cookies to environment variables:

1. **Set in Vercel Dashboard:**
   - Go to your project settings
   - Add environment variable: `YTDLP_COOKIES`
   - Paste your cookie content

2. **Remove hardcoded cookies** from code

3. **Redeploy**

### Automatic Cookie Refresh
- Set up a system to automatically refresh cookies
- Use a separate service to monitor cookie validity
- Implement webhook-based updates

## 🚨 Security Reminders

- **Never commit cookies to public repos** (these are already in your code for testing)
- **Use environment variables** for production
- **Monitor cookie usage** and rotate regularly
- **Consider using throwaway accounts** for this purpose

## 🎯 Success Metrics

You'll know it's working when:
- ✅ No bot detection errors
- ✅ Age-restricted videos accessible (if account allows)
- ✅ Consistent format retrieval
- ✅ Fast response times
- ✅ `using_hardcoded_cookies: true` in responses

## 📞 Troubleshooting

### If deployment fails:
1. Check Vercel build logs
2. Verify all dependencies in `requirements.txt`
3. Test locally first with `python test_hardcoded_cookies.py`

### If cookies stop working:
1. Check cookie expiration dates
2. Export fresh cookies using the same process
3. Update the hardcoded values
4. Redeploy

---

**You're ready to deploy! Your cookies are working perfectly and will handle YouTube's bot detection. 🚀** 