# Cookie Troubleshooting Guide - Missing Authentication Tokens

## 🚨 Your Current Issue

Your cookies are **missing essential authentication tokens**. Here's what you have vs. what you need:

### ❌ What You Currently Have:
```
GPS, PREF, YSC, VISITOR_INFO1_LIVE, VISITOR_PRIVACY_METADATA, __Secure-ROLLOUT_TOKEN
```
These are tracking and preference cookies, but **not authentication cookies**.

### ✅ What You Need:
```
SAPISID, HSID, SSID, APISID, SID
```
These are the **essential authentication cookies** that prove you're logged in.

## 🔍 Why This Happens

1. **You exported cookies while NOT logged in** to YouTube
2. **You exported cookies from the wrong browser tab/session**
3. **You used a browser extension that only exports non-authentication cookies**
4. **Your login session expired before exporting**

## 🛠️ How to Fix This

### Step 1: Verify You're Logged In

1. Open a **NEW private/incognito window**
2. Go to https://www.youtube.com
3. **Sign in with your account**
4. Make sure you see your profile picture in the top-right corner
5. Try watching a video to confirm you're fully logged in

### Step 2: Navigate to robots.txt (CRITICAL!)

**In the SAME private tab**, go to:
```
https://www.youtube.com/robots.txt
```

This prevents cookie rotation. **DO NOT** open any other tabs!

### Step 3: Export Cookies Correctly

#### Method A: Browser Extension (Recommended)
1. Install a proper cookie extension:
   - **Chrome**: "Get cookies.txt LOCALLY" or "Export cookies.txt"
   - **Firefox**: "cookies.txt" or "Export Cookies"

2. **Export ALL youtube.com cookies** (not just some)
3. Make sure the extension exports authentication cookies

#### Method B: Manual Export via Developer Tools
1. Press `F12` to open Developer Tools
2. Go to **Application** (Chrome) or **Storage** (Firefox)
3. Navigate to **Cookies** > **https://www.youtube.com**
4. Look for and copy these specific cookies:
   - `SAPISID`
   - `HSID`
   - `SSID`
   - `APISID`
   - `SID`

### Step 4: Verify Your New Cookies

Save your new cookies and test them:
```bash
python cookie_helper.py validate your_new_cookies.txt
```

You should see output like:
```
🔑 Important cookies found: SAPISID, HSID, SSID, APISID, SID
```

## 🎯 Quick Test

Create a test file with this format (replace with your actual values):

```
# Netscape HTTP Cookie File
.youtube.com	TRUE	/	FALSE	1234567890	SAPISID	your_actual_sapisid_value_here
.youtube.com	TRUE	/	FALSE	1234567890	HSID	your_actual_hsid_value_here
.youtube.com	TRUE	/	FALSE	1234567890	SSID	your_actual_ssid_value_here
.youtube.com	TRUE	/	FALSE	1234567890	APISID	your_actual_apisid_value_here
.youtube.com	TRUE	/	FALSE	1234567890	SID	your_actual_sid_value_here
```

## 🔧 Browser-Specific Instructions

### Chrome
1. Open incognito: `Ctrl+Shift+N`
2. Login to YouTube
3. Go to robots.txt
4. Install "Get cookies.txt LOCALLY" extension
5. Export cookies for youtube.com
6. Close incognito window immediately

### Firefox
1. Open private window: `Ctrl+Shift+P`
2. Login to YouTube
3. Go to robots.txt
4. Install "cookies.txt" extension
5. Export cookies for youtube.com
6. Close private window immediately

### Manual Method (Any Browser)
1. Open incognito/private window
2. Login to YouTube
3. Go to robots.txt
4. Press F12 → Application/Storage → Cookies → https://www.youtube.com
5. Find SAPISID, HSID, SSID, APISID, SID cookies
6. Copy their values manually
7. Format them in Netscape format

## ⚠️ Common Mistakes to Avoid

1. **DON'T** export cookies from a regular browser window
2. **DON'T** open multiple tabs in the private session
3. **DON'T** skip the robots.txt step
4. **DON'T** reuse the private session after exporting
5. **DON'T** export cookies when not logged in

## 🧪 Test Your Fixed Cookies

Once you have proper cookies:
```bash
# Validate format and authentication tokens
python cookie_helper.py validate your_cookies.txt

# Test with the API
python test_cookie_integration.py your_cookies.txt

# Try the demo
python demo_cookie_usage.py your_cookies.txt
```

## 🎉 Success Indicators

You'll know it's working when:
- Cookie validation shows: `🔑 Important cookies found: SAPISID, HSID, SSID, APISID, SID`
- API calls succeed without bot detection errors
- You can access age-restricted content (if your account allows it)

## 🆘 Still Having Issues?

If you're still getting bot detection after following these steps:

1. **Wait 15-30 minutes** before trying again (YouTube rate limiting)
2. **Try a different YouTube account** (preferably a throwaway account)
3. **Clear your browser completely** and start fresh
4. **Use a different browser** for the cookie export process
5. **Check if your IP is temporarily blocked** by YouTube

Remember: The key is having those **5 essential authentication cookies**: `SAPISID`, `HSID`, `SSID`, `APISID`, and `SID`. Without them, YouTube will always detect you as a bot! 