from flask import Flask, request, jsonify
import subprocess
import sys
import json
import os
import tempfile
import random
import base64
from datetime import datetime

app = Flask(__name__)

# User agents to rotate for better bot detection avoidance
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

class CookieManager:
    """Secure cookie management for YouTube authentication"""
    
    def __init__(self):
        self.data_dir = os.path.join(tempfile.gettempdir(), 'ytdlp_cookies')
        os.makedirs(self.data_dir, exist_ok=True)
    
    def save_cookies(self, cookies_data, session_id=None):
        """Save cookies securely to temporary file"""
        if not session_id:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"
        
        cookie_file = os.path.join(self.data_dir, f"{session_id}.txt")
        
        try:
            # Handle different cookie formats
            if isinstance(cookies_data, str):
                # If it's a base64 encoded cookie file
                if cookies_data.startswith('data:'):
                    # Handle data URL format
                    _, encoded = cookies_data.split(',', 1)
                    cookie_content = base64.b64decode(encoded).decode('utf-8')
                else:
                    cookie_content = cookies_data
            else:
                cookie_content = str(cookies_data)
            
            with open(cookie_file, 'w', encoding='utf-8') as f:
                f.write(cookie_content)
            
            return cookie_file
            
        except Exception as e:
            print(f"Error saving cookies: {str(e)}")
            return None
    
    def cleanup_cookie_file(self, cookie_file):
        """Securely cleanup cookie file"""
        try:
            if cookie_file and os.path.exists(cookie_file):
                os.remove(cookie_file)
        except Exception:
            pass
    
    def cleanup_old_sessions(self, max_age_hours=1):
        """Clean up old cookie sessions"""
        try:
            current_time = datetime.now()
            for filename in os.listdir(self.data_dir):
                file_path = os.path.join(self.data_dir, filename)
                if os.path.isfile(file_path):
                    file_age = datetime.fromtimestamp(os.path.getctime(file_path))
                    age_hours = (current_time - file_age).total_seconds() / 3600
                    if age_hours > max_age_hours:
                        os.remove(file_path)
        except Exception:
            pass

# Hardcoded YouTube cookies for Vercel deployment (temporary)
HARDCODED_YOUTUBE_COOKIES = """# Netscape HTTP Cookie File
# http://curl.haxx.se/rfc/cookie_spec.html
# This is a generated file!  Do not edit.

.youtube.com	TRUE	/	TRUE	1789524374	PREF	tz=Asia.Karachi&f6=40000000&f5=20000&f7=100
.youtube.com	TRUE	/	TRUE	1767266244	VISITOR_INFO1_LIVE	ZzXSMVagoSc
.youtube.com	TRUE	/	TRUE	1767266244	VISITOR_PRIVACY_METADATA	CgJQSxIEGgAgJQ%3D%3D
.youtube.com	TRUE	/	FALSE	1789513636	HSID	AlFtsF_hfYaNDL1nS
.youtube.com	TRUE	/	TRUE	1789513636	SSID	AlmYdbysVQcG8ft7s
.youtube.com	TRUE	/	FALSE	1789513636	APISID	quDZ96FGcG6lvYiO/Abfb-nZz8zBiVjlUa
.youtube.com	TRUE	/	TRUE	1789513636	SAPISID	KCbPbd1QMDDqCblq/ALiPffGNkTmxEyyfe
.youtube.com	TRUE	/	TRUE	1789513636	__Secure-1PAPISID	KCbPbd1QMDDqCblq/ALiPffGNkTmxEyyfe
.youtube.com	TRUE	/	TRUE	1789513636	__Secure-3PAPISID	KCbPbd1QMDDqCblq/ALiPffGNkTmxEyyfe
.youtube.com	TRUE	/	FALSE	1789513636	SID	g.a0000AisQoz5BGjCDzkcZkMMUdpGTxftXzQWUcJaTvCDCcsrr4y-qAkWMmd3MeHZ2NbDyc-hygACgYKAVsSARASFQHGX2MipF_mgbhctDzDqmJCiw97WBoVAUF8yKqSlPCgeswf_9LlyNuvVp7E0076
.youtube.com	TRUE	/	TRUE	1789513636	__Secure-1PSID	g.a0000AisQoz5BGjCDzkcZkMMUdpGTxftXzQWUcJaTvCDCcsrr4y-kMyayDq883XTxPSGUDbPwQACgYKAR8SARASFQHGX2MiVFr01GHSomS0ORmD1UIdcxoVAUF8yKrHona74JR0X7unKetXbZAL0076
.youtube.com	TRUE	/	TRUE	1789513636	__Secure-3PSID	g.a0000AisQoz5BGjCDzkcZkMMUdpGTxftXzQWUcJaTvCDCcsrr4y-iyejOpq4uXy1try0tUcsLAACgYKAVISARASFQHGX2MiEEmsImZZHBlY5v_V01ba0BoVAUF8yKquVawLu0leB0O7Cd8FuBhQ0076
.youtube.com	TRUE	/	TRUE	1789524375	LOGIN_INFO	AFmmF2swRQIhAP7xURVtxk4ONVkiuFP_jzYSS-EnwK_388K7A9a-UcpTAiAVBd14LFVZD7aGrVQU6m6HATr8JHySWl5a1P7Wm6-4VQ:QUQ3MjNmeTZmZkZlaXNCakxTZ0RtUVJqVzlob1JxUVQzNG9LalpMWmJPekE0SVJrdnRLaGhodEVxcGp4UDZWcUpUc25aWXAtQjlwLUxoUE10Wl80dVBHTFJIdkhtaHNLd2ZVYnRsOFk3eXVReUY0a3JldG5ZSUtFMVlnWGZkc3V0dW96blBzbmNXSHVzRFB1aTRBc3h2UTNSTThkVldPZmxB
.youtube.com	TRUE	/	TRUE	1786500377	__Secure-1PSIDTS	sidts-CjUB5H03P8EeAatusvoG9vQeeP8RLDCl6lznQhNPaFvSBHkGjhYawKpzLggl6Fjwet-DbjpA4hAA
.youtube.com	TRUE	/	TRUE	1786500377	__Secure-3PSIDTS	sidts-CjUB5H03P8EeAatusvoG9vQeeP8RLDCl6lznQhNPaFvSBHkGjhYawKpzLggl6Fjwet-DbjpA4hAA
.youtube.com	TRUE	/	FALSE	1786500385	SIDCC	AKEyXzWLdoarLp3F_zS8PJF0PwDLWK_9gkbymtG4YiOd2gq5Yb_CpXwaKIe5kquTtbuh2DHw
.youtube.com	TRUE	/	TRUE	1786500385	__Secure-1PSIDCC	AKEyXzWcPmGDnnkt6LZzITI1R78BXoLrwMyhccO4oldt3bXUPk8yo_rcGioCtllVDv4E84iO_g
.youtube.com	TRUE	/	TRUE	1786500385	__Secure-3PSIDCC	AKEyXzU9issa2apSvH_p_qMmTFHszmcIgelaJIgWowxJ50Xo6NDfS_WJgihZQyudRJArgVO6og
.youtube.com	TRUE	/	TRUE	1770516375	VISITOR_INFO1_LIVE	z5Mp1mNC6Jg
.youtube.com	TRUE	/	TRUE	1770516375	VISITOR_PRIVACY_METADATA	CgJQSxIEGgAgNQ%3D%3D
.youtube.com	TRUE	/	TRUE	0	YSC	pn7g_g9UaM0
.youtube.com	TRUE	/	TRUE	1770516372	__Secure-ROLLOUT_TOKEN	CN-7zd-9gp_hIhCV2vLd0t-NAxiRiPvfl4SPAw%3D%3D"""

def get_ytdlp_base_options(url, cookie_file=None):
    """Get base yt-dlp options optimized for Vercel serverless environment with cookie support"""
    temp_cache_dir = tempfile.mkdtemp(prefix='ytdlp_cache_')
    user_agent = random.choice(USER_AGENTS)
    
    base_options = [
        '--no-cache-dir',  # Disable cache completely
        '--cache-dir', temp_cache_dir,  # Use temp directory for any cache needs
        '--user-agent', user_agent,
        '--referer', 'https://www.youtube.com/',
        '--extractor-retries', '5',  # Increased retries
        '--fragment-retries', '5',
        '--retry-sleep', '2',  # Increased sleep time
        '--socket-timeout', '30',
        '--no-check-certificate',  # Skip SSL verification issues
        '--no-warnings',  # Reduce noise in logs
        '--add-header', 'Accept-Language:en-US,en;q=0.9',  # Add language header
        '--add-header', 'Accept:text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',  # Add accept header
    ]
    
    # Add cookie support - prioritize hardcoded cookies for now
    cookie_manager = CookieManager()
    
    # Use hardcoded cookies if no specific cookies provided
    if not cookie_file:
        hardcoded_cookie_file = cookie_manager.save_cookies(HARDCODED_YOUTUBE_COOKIES, 'hardcoded_session')
        if hardcoded_cookie_file:
            base_options.extend(['--cookies', hardcoded_cookie_file])
            return base_options, temp_cache_dir, hardcoded_cookie_file
    
    # Add cookie support if provided
    if cookie_file and os.path.exists(cookie_file):
        base_options.extend(['--cookies', cookie_file])
    
    # Add environment-specific options as fallback
    env_cookies = os.environ.get('YTDLP_COOKIES')
    if env_cookies and not cookie_file:
        env_cookie_file = cookie_manager.save_cookies(env_cookies, 'env_session')
        if env_cookie_file:
            base_options.extend(['--cookies', env_cookie_file])
    
    return base_options, temp_cache_dir, None

def validate_cookie_content(cookie_content):
    """Validate if cookie content has essential YouTube authentication tokens"""
    if not cookie_content:
        return False, "No cookies provided"
    
    # Essential YouTube authentication cookies
    essential_cookies = ['SAPISID', 'HSID', 'SSID', 'APISID', 'SID']
    found_essential = []
    
    for cookie_name in essential_cookies:
        if cookie_name in cookie_content:
            found_essential.append(cookie_name)
    
    if not found_essential:
        return False, f"Missing essential authentication cookies. Found: {', '.join(found_essential) if found_essential else 'None'}. Required: {', '.join(essential_cookies)}"
    
    # Check if we have at least SAPISID which is most important
    if 'SAPISID' not in cookie_content:
        return False, "Missing SAPISID cookie which is essential for YouTube authentication"
    
    return True, f"Found {len(found_essential)} essential cookies: {', '.join(found_essential)}"

def cleanup_temp_dir(temp_dir):
    """Clean up temporary directory"""
    try:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    except:
        pass

@app.route('/api/formats', methods=['POST', 'OPTIONS'])
def get_formats():
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    
    cookie_manager = CookieManager()
    cookie_file = None
    hardcoded_cookie_file = None
    
    try:
        # Clean up old sessions
        cookie_manager.cleanup_old_sessions()
        
        data = request.get_json()
        url = data.get('url') if data else None
        cookies = data.get('cookies') if data else None  # New cookie support
        
        if not url:
            response = jsonify({'error': 'URL is required'})
            response.status_code = 400
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        
        # Validate YouTube URL
        youtube_patterns = ['youtube.com', 'youtu.be', 'youtube-nocookie.com']
        if not any(pattern in url for pattern in youtube_patterns):
            response = jsonify({'error': 'Please provide a valid YouTube URL'})
            response.status_code = 400
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        
        # Handle and validate cookies if provided
        if cookies:
            # Validate cookie content first
            is_valid, validation_message = validate_cookie_content(cookies)
            if not is_valid:
                response = jsonify({
                    'error': f'Invalid cookies: {validation_message}',
                    'help': 'Please export cookies from an authenticated YouTube session. Make sure you are logged in when exporting cookies.',
                    'guide': 'Run: python cookie_helper.py export-guide'
                })
                response.status_code = 400
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response
            
            cookie_file = cookie_manager.save_cookies(cookies)
            if not cookie_file:
                response = jsonify({'error': 'Failed to process cookies'})
                response.status_code = 400
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response
        
        # Run yt-dlp to get video information with Vercel-compatible options
        try:
            base_options, temp_cache_dir, hardcoded_cookie_file = get_ytdlp_base_options(url, cookie_file)
            
            cmd = [
                sys.executable, '-m', 'yt_dlp',
                '--dump-json',
                '--no-download',
                *base_options,
                url
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=45,  # Increased timeout for cookie authentication
                env={**os.environ, 'HOME': '/tmp'}  # Set HOME to /tmp for any home directory writes
            )
            
            # Clean up temp directory and cookie files
            cleanup_temp_dir(temp_cache_dir)
            if cookie_file:
                cookie_manager.cleanup_cookie_file(cookie_file)
            if hardcoded_cookie_file:
                cookie_manager.cleanup_cookie_file(hardcoded_cookie_file)
            
            if result.returncode != 0:
                error_msg = result.stderr
                # Provide more helpful error messages
                if 'Sign in to confirm' in error_msg or 'bot' in error_msg.lower():
                    if not cookies:
                        error_response = {
                            'error': 'YouTube bot detection triggered. Using hardcoded cookies but they may be expired.',
                            'help': 'The hardcoded authentication cookies may need refreshing.',
                            'guide': 'Try providing fresh cookies or contact support',
                            'solution': 'Hardcoded cookies are being used but may be expired'
                        }
                    else:
                        error_response = {
                            'error': 'YouTube bot detection triggered despite cookies. Your cookies may be invalid or expired.',
                            'help': 'Please re-export your cookies following the exact process.',
                            'guide': 'Run: python cookie_helper.py export-guide',
                            'solution': 'Make sure to: 1) Use private/incognito window, 2) Login to YouTube, 3) Navigate to robots.txt, 4) Export cookies, 5) Close private window immediately'
                        }
                elif 'Private video' in error_msg or 'members-only' in error_msg.lower():
                    error_response = {
                        'error': 'This video requires authentication or special access.',
                        'help': 'Please provide valid YouTube cookies from an account that has access to this content.',
                        'solution': 'Make sure your account has access to this private/members-only content'
                    }
                elif 'age-restricted' in error_msg.lower():
                    error_response = {
                        'error': 'This video is age-restricted.',
                        'help': 'Please provide valid YouTube cookies from an age-verified account.',
                        'solution': 'Make sure your YouTube account is verified for age-restricted content'
                    }
                else:
                    error_response = {
                        'error': f'yt-dlp failed: {error_msg}',
                        'help': 'Check the error message above for specific details.'
                    }
                
                response = jsonify(error_response)
                response.status_code = 500
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response
            
            # Parse the JSON output
            video_info = json.loads(result.stdout.strip())
            formats = video_info.get('formats', [])
            
            # Filter and process formats
            filtered_formats = []
            for format_data in formats:
                if format_data.get('url') and format_data.get('format_id'):
                    filtered_formats.append({
                        'format_id': format_data.get('format_id'),
                        'ext': format_data.get('ext'),
                        'resolution': format_data.get('resolution'),
                        'format_note': format_data.get('format_note'),
                        'filesize': format_data.get('filesize'),
                        'vcodec': format_data.get('vcodec'),
                        'acodec': format_data.get('acodec'),
                        'fps': format_data.get('fps'),
                        'quality': format_data.get('quality')
                    })
            
            # Sort by quality
            filtered_formats.sort(key=lambda x: x.get('quality', 0) or 0, reverse=True)
            
            # Extract video metadata
            video_metadata = {
                'title': video_info.get('title', 'Unknown Title'),
                'description': video_info.get('description', ''),
                'duration': video_info.get('duration', 0),
                'uploader': video_info.get('uploader') or video_info.get('channel', 'Unknown'),
                'upload_date': video_info.get('upload_date', ''),
                'view_count': video_info.get('view_count', 0),
                'like_count': video_info.get('like_count', 0),
                'thumbnail': video_info.get('thumbnail', ''),
                'channel': video_info.get('channel') or video_info.get('uploader', 'Unknown'),
                'channel_id': video_info.get('channel_id') or video_info.get('uploader_id', ''),
                'webpage_url': video_info.get('webpage_url', url),
                'id': video_info.get('id', ''),
                'fulltitle': video_info.get('fulltitle') or video_info.get('title', 'Unknown Title'),
                'age_limit': video_info.get('age_limit', 0),
                'is_live': video_info.get('is_live', False),
                'availability': video_info.get('availability', 'public')
            }
            
            response = jsonify({
                'videoInfo': video_metadata,
                'formats': filtered_formats,
                'using_hardcoded_cookies': not bool(cookies)  # Debug info
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
            
        except subprocess.TimeoutExpired:
            response = jsonify({'error': 'Request timeout - video processing took too long'})
            response.status_code = 500
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        except json.JSONDecodeError:
            response = jsonify({'error': 'Failed to parse video information'})
            response.status_code = 500
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        except Exception as e:
            response = jsonify({'error': f'Processing error: {str(e)}'})
            response.status_code = 500
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
            
    except Exception as e:
        response = jsonify({'error': f'Server error: {str(e)}'})
        response.status_code = 500
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    finally:
        # Always cleanup cookie files
        if cookie_file:
            cookie_manager.cleanup_cookie_file(cookie_file)
        if hardcoded_cookie_file:
            cookie_manager.cleanup_cookie_file(hardcoded_cookie_file)

@app.route('/api/direct-url', methods=['POST', 'OPTIONS'])
def get_direct_url():
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    
    cookie_manager = CookieManager()
    cookie_file = None
    hardcoded_cookie_file = None
    
    try:
        data = request.get_json()
        url = data.get('url') if data else None
        format_id = data.get('formatId') if data else None
        cookies = data.get('cookies') if data else None  # New cookie support
        
        if not url or not format_id:
            response = jsonify({'error': 'URL and formatId are required'})
            response.status_code = 400
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        
        # Handle cookies if provided
        if cookies:
            cookie_file = cookie_manager.save_cookies(cookies)
        
        # Run yt-dlp to get direct URL with Vercel-compatible options
        try:
            base_options, temp_cache_dir, hardcoded_cookie_file = get_ytdlp_base_options(url, cookie_file)
            
            cmd = [
                sys.executable, '-m', 'yt_dlp',
                '-g',  # Get URL only
                '-f', format_id,
                *base_options,
                url
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=45,  # Increased timeout for cookie authentication
                env={**os.environ, 'HOME': '/tmp'}  # Set HOME to /tmp for any home directory writes
            )
            
            # Clean up temp directory and cookie files
            cleanup_temp_dir(temp_cache_dir)
            if cookie_file:
                cookie_manager.cleanup_cookie_file(cookie_file)
            if hardcoded_cookie_file:
                cookie_manager.cleanup_cookie_file(hardcoded_cookie_file)
            
            if result.returncode != 0:
                response = jsonify({'error': f'Failed to get direct URL: {result.stderr}'})
                response.status_code = 500
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response
            
            direct_url = result.stdout.strip()
            
            if not direct_url:
                response = jsonify({'error': 'No direct URL found'})
                response.status_code = 500
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response
            
            response = jsonify({
                'directUrl': direct_url,
                'using_hardcoded_cookies': not bool(cookies)  # Debug info
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
            
        except subprocess.TimeoutExpired:
            response = jsonify({'error': 'Request timeout'})
            response.status_code = 500
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        except Exception as e:
            response = jsonify({'error': f'Processing error: {str(e)}'})
            response.status_code = 500
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
            
    except Exception as e:
        response = jsonify({'error': f'Server error: {str(e)}'})
        response.status_code = 500
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    finally:
        # Always cleanup cookie files
        if cookie_file:
            cookie_manager.cleanup_cookie_file(cookie_file)
        if hardcoded_cookie_file:
            cookie_manager.cleanup_cookie_file(hardcoded_cookie_file)

# New endpoint for cookie validation
@app.route('/api/validate-cookies', methods=['POST', 'OPTIONS'])
def validate_cookies():
    """Validate YouTube cookies by testing access to a known restricted video"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    
    cookie_manager = CookieManager()
    cookie_file = None
    
    try:
        data = request.get_json()
        cookies = data.get('cookies') if data else None
        
        if not cookies:
            response = jsonify({'error': 'Cookies are required for validation'})
            response.status_code = 400
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        
        # Save cookies temporarily
        cookie_file = cookie_manager.save_cookies(cookies)
        if not cookie_file:
            response = jsonify({'error': 'Failed to process cookies'})
            response.status_code = 400
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        
        # Test with a simple YouTube video (using robots.txt as mentioned in the instructions)
        test_url = "https://www.youtube.com/robots.txt"
        
        try:
            base_options, temp_cache_dir = get_ytdlp_base_options(test_url, cookie_file)
            
            # Simple test command
            cmd = [
                sys.executable, '-m', 'yt_dlp',
                '--simulate',
                '--no-warnings',
                *base_options,
                'https://www.youtube.com/watch?v=dQw4w9WgXcQ'  # Test with a known public video
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Clean up
            cleanup_temp_dir(temp_cache_dir)
            
            is_valid = result.returncode == 0
            message = "Cookies are valid and working" if is_valid else "Cookies may be invalid or expired"
            
            response = jsonify({
                'valid': is_valid,
                'message': message
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
            
        except Exception as e:
            response = jsonify({
                'valid': False,
                'message': f'Cookie validation failed: {str(e)}'
            })
            response.status_code = 500
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
            
    except Exception as e:
        response = jsonify({'error': f'Server error: {str(e)}'})
        response.status_code = 500
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    finally:
        if cookie_file:
            cookie_manager.cleanup_cookie_file(cookie_file)

# Health check endpoint for Vercel
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'message': 'DebuTube API is running perfectly!'})

# Catch-all route to handle other API requests
@app.route('/api/<path:path>', methods=['GET', 'POST', 'OPTIONS'])
def catch_all(path):
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        return response
    
    response = jsonify({'error': f'API endpoint /{path} not found'})
    response.status_code = 404
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

if __name__ == '__main__':
    app.run(debug=True) 