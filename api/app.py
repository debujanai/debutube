from flask import Flask, request, jsonify
import subprocess
import sys
import json
import os
import tempfile
import random
import base64

app = Flask(__name__)

# User agents to rotate for better bot detection avoidance
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

# YouTube cookies for accessing age-restricted and private content
YOUTUBE_COOKIES = """# Netscape HTTP Cookie File
# http://curl.haxx.se/rfc/cookie_spec.html
# This is a generated file!  Do not edit.

.youtube.com	TRUE	/	TRUE	1754964596	GPS	1
.youtube.com	TRUE	/	TRUE	1789522799	PREF	f6=40000000&tz=Asia.Karachi
.youtube.com	TRUE	/	TRUE	1754964596	GPS	1
.youtube.com	TRUE	/	TRUE	0	YSC	G9TKfyk0caU
.youtube.com	TRUE	/	TRUE	1770514799	VISITOR_INFO1_LIVE	Xal1p7296vs
.youtube.com	TRUE	/	TRUE	1770514799	VISITOR_PRIVACY_METADATA	CgJQSxIEGgAgMQ%3D%3D
.youtube.com	TRUE	/	TRUE	1789522799	PREF	f6=40000000&tz=Asia.Karachi
.youtube.com	TRUE	/	TRUE	1770514798	__Secure-ROLLOUT_TOKEN	CNe13Y-LmNCs-AEQx9u78JGEjwMYj9yk8ZGEjwM%3D"""

def save_cookies_to_temp_file(cookies_content):
    """Save cookies content to a temporary file and return the path"""
    try:
        # Create a temporary file for cookies
        temp_fd, temp_path = tempfile.mkstemp(suffix='.txt', prefix='youtube_cookies_')
        
        # Decode if cookies are base64 encoded
        if cookies_content.startswith('data:'):
            # Handle data URL format (data:text/plain;base64,...)
            header, encoded = cookies_content.split(',', 1)
            if 'base64' in header:
                cookies_content = base64.b64decode(encoded).decode('utf-8')
        
        # Write cookies to the temporary file
        with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
            f.write(cookies_content)
        
        return temp_path
    except Exception as e:
        print(f"Error saving cookies: {e}")
        return None

def get_ytdlp_base_options(url, cookies_file=None, use_builtin_cookies=True):
    """Get base yt-dlp options optimized for Vercel serverless environment"""
    temp_cache_dir = tempfile.mkdtemp(prefix='ytdlp_cache_')
    user_agent = random.choice(USER_AGENTS)
    
    base_options = [
        '--no-cache-dir',  # Disable cache completely
        '--cache-dir', temp_cache_dir,  # Use temp directory for any cache needs
        '--user-agent', user_agent,
        '--referer', 'https://www.youtube.com/',
        '--extractor-retries', '3',
        '--fragment-retries', '3',
        '--retry-sleep', '1',
        '--socket-timeout', '30',
        '--no-check-certificate',  # Skip SSL verification issues
    ]
    
    # Add cookies if provided or use built-in cookies
    if cookies_file and os.path.exists(cookies_file):
        base_options.extend(['--cookies', cookies_file])
    elif use_builtin_cookies:
        # Use built-in YouTube cookies
        builtin_cookies_file = save_cookies_to_temp_file(YOUTUBE_COOKIES)
        if builtin_cookies_file:
            base_options.extend(['--cookies', builtin_cookies_file])
    
    return base_options, temp_cache_dir

def cleanup_temp_dir(temp_dir):
    """Clean up temporary directory"""
    try:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    except:
        pass

def cleanup_temp_file(temp_file):
    """Clean up temporary file"""
    try:
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)
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
    
    cookies_file = None
    try:
        data = request.get_json()
        url = data.get('url') if data else None
        cookies_content = data.get('cookies') if data else None
        
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
        
        # Handle cookies if provided (otherwise built-in cookies will be used automatically)
        if cookies_content:
            cookies_file = save_cookies_to_temp_file(cookies_content)
            if not cookies_file:
                response = jsonify({'error': 'Failed to process cookies'})
                response.status_code = 400
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response
        
        # Run yt-dlp to get video information (will use built-in cookies if no custom cookies provided)
        try:
            base_options, temp_cache_dir = get_ytdlp_base_options(url, cookies_file, use_builtin_cookies=True)
            
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
                timeout=30,
                env={**os.environ, 'HOME': '/tmp'}  # Set HOME to /tmp for any home directory writes
            )
            
            # Clean up temp directory and cookies file
            cleanup_temp_dir(temp_cache_dir)
            if cookies_file:
                cleanup_temp_file(cookies_file)
            
            if result.returncode != 0:
                response = jsonify({'error': f'yt-dlp failed: {result.stderr}'})
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
                'fulltitle': video_info.get('fulltitle') or video_info.get('title', 'Unknown Title')
            }
            
            response = jsonify({
                'videoInfo': video_metadata,
                'formats': filtered_formats
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
        # Cleanup cookies file if it exists
        if cookies_file:
            cleanup_temp_file(cookies_file)

@app.route('/api/direct-url', methods=['POST', 'OPTIONS'])
def get_direct_url():
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    
    cookies_file = None
    try:
        data = request.get_json()
        url = data.get('url') if data else None
        format_id = data.get('formatId') if data else None
        cookies_content = data.get('cookies') if data else None
        
        if not url or not format_id:
            response = jsonify({'error': 'URL and formatId are required'})
            response.status_code = 400
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        
        # Handle cookies if provided (otherwise built-in cookies will be used automatically)
        if cookies_content:
            cookies_file = save_cookies_to_temp_file(cookies_content)
            if not cookies_file:
                response = jsonify({'error': 'Failed to process cookies'})
                response.status_code = 400
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response
        
        # Run yt-dlp to get direct URL (will use built-in cookies if no custom cookies provided)
        try:
            base_options, temp_cache_dir = get_ytdlp_base_options(url, cookies_file, use_builtin_cookies=True)
            
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
                timeout=30,
                env={**os.environ, 'HOME': '/tmp'}  # Set HOME to /tmp for any home directory writes
            )
            
            # Clean up temp directory and cookies file
            cleanup_temp_dir(temp_cache_dir)
            if cookies_file:
                cleanup_temp_file(cookies_file)
            
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
            
            response = jsonify({'directUrl': direct_url})
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
        # Cleanup cookies file if it exists
        if cookies_file:
            cleanup_temp_file(cookies_file)

# Endpoint to test cookies validity (tests built-in cookies if none provided)
@app.route('/api/test-cookies', methods=['POST', 'OPTIONS'])
def test_cookies():
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    
    cookies_file = None
    try:
        data = request.get_json() if request.get_json() else {}
        cookies_content = data.get('cookies') if data else None
        
        # If no cookies provided, test built-in cookies
        if not cookies_content:
            cookies_content = YOUTUBE_COOKIES
            test_type = "built-in"
        else:
            test_type = "provided"
        
        # Handle cookies
        cookies_file = save_cookies_to_temp_file(cookies_content)
        if not cookies_file:
            response = jsonify({'error': 'Failed to process cookies'})
            response.status_code = 400
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        
        # Test cookies with a simple YouTube request
        try:
            base_options, temp_cache_dir = get_ytdlp_base_options('https://www.youtube.com/', cookies_file, use_builtin_cookies=False)
            
            cmd = [
                sys.executable, '-m', 'yt_dlp',
                '--dump-json',
                '--no-download',
                '--playlist-end', '1',  # Only get first video from homepage
                *base_options,
                'https://www.youtube.com/'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15,
                env={**os.environ, 'HOME': '/tmp'}
            )
            
            # Clean up
            cleanup_temp_dir(temp_cache_dir)
            cleanup_temp_file(cookies_file)
            
            if result.returncode == 0:
                response = jsonify({
                    'valid': True,
                    'message': f'Cookies are valid and working ({test_type} cookies tested)',
                    'type': test_type
                })
            else:
                response = jsonify({
                    'valid': False,
                    'message': f'Cookies may be invalid or expired ({test_type} cookies tested)',
                    'error': result.stderr,
                    'type': test_type
                })
            
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
            
        except subprocess.TimeoutExpired:
            response = jsonify({
                'valid': False,
                'message': f'Cookie test timeout ({test_type} cookies tested)',
                'type': test_type
            })
            response.status_code = 500
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        except Exception as e:
            response = jsonify({
                'valid': False,
                'message': f'Cookie test error: {str(e)} ({test_type} cookies tested)',
                'type': test_type
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
        # Cleanup cookies file if it exists
        if cookies_file:
            cleanup_temp_file(cookies_file)

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