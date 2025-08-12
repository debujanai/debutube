from flask import Flask, request, jsonify
import subprocess
import sys
import json
import os
import tempfile
import random
import shutil
from pathlib import Path

app = Flask(__name__)

# User agents to rotate for better bot detection avoidance
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

def get_ytdlp_base_options(url, use_cookies=True):
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
    
    # Add cookie support to bypass bot detection
    if use_cookies:
        # Try to use cookies from browser (Chrome first, then Firefox, then Edge)
        cookie_options = [
            '--cookies-from-browser', 'chrome',
        ]
        base_options.extend(cookie_options)
    
    return base_options, temp_cache_dir

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
    
    try:
        data = request.get_json()
        url = data.get('url') if data else None
        use_cookies = data.get('useCookies', True) if data else True  # Default to True
        
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
        
        # Run yt-dlp to get video information with Vercel-compatible options
        try:
            base_options, temp_cache_dir = get_ytdlp_base_options(url, use_cookies)
            
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
                timeout=45,  # Increased timeout for cookie processing
                env={**os.environ, 'HOME': '/tmp'}  # Set HOME to /tmp for any home directory writes
            )
            
            # Clean up temp directory
            cleanup_temp_dir(temp_cache_dir)
            
            if result.returncode != 0:
                # If cookies failed, try without cookies as fallback
                if use_cookies and 'Sign in to confirm' in result.stderr:
                    return retry_without_cookies(url, 'formats')
                
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

def retry_without_cookies(url, endpoint_type):
    """Retry the request without cookies as a fallback"""
    try:
        base_options, temp_cache_dir = get_ytdlp_base_options(url, use_cookies=False)
        
        if endpoint_type == 'formats':
            cmd = [
                sys.executable, '-m', 'yt_dlp',
                '--dump-json',
                '--no-download',
                *base_options,
                url
            ]
        else:  # direct-url
            format_id = request.get_json().get('formatId')
            cmd = [
                sys.executable, '-m', 'yt_dlp',
                '-g',
                '-f', format_id,
                *base_options,
                url
            ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            env={**os.environ, 'HOME': '/tmp'}
        )
        
        cleanup_temp_dir(temp_cache_dir)
        
        if result.returncode != 0:
            response = jsonify({
                'error': f'yt-dlp failed even without cookies: {result.stderr}',
                'suggestion': 'This video may require manual cookie authentication. Please try using a different video or check if the video is publicly accessible.'
            })
            response.status_code = 500
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        
        if endpoint_type == 'formats':
            video_info = json.loads(result.stdout.strip())
            formats = video_info.get('formats', [])
            
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
            
            filtered_formats.sort(key=lambda x: x.get('quality', 0) or 0, reverse=True)
            
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
                'formats': filtered_formats,
                'warning': 'Retrieved without cookies - some content may be limited'
            })
        else:  # direct-url
            direct_url = result.stdout.strip()
            response = jsonify({
                'directUrl': direct_url,
                'warning': 'Retrieved without cookies - some content may be limited'
            })
        
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        response = jsonify({'error': f'Fallback processing error: {str(e)}'})
        response.status_code = 500
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

@app.route('/api/direct-url', methods=['POST', 'OPTIONS'])
def get_direct_url():
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    
    try:
        data = request.get_json()
        url = data.get('url') if data else None
        format_id = data.get('formatId') if data else None
        use_cookies = data.get('useCookies', True) if data else True  # Default to True
        
        if not url or not format_id:
            response = jsonify({'error': 'URL and formatId are required'})
            response.status_code = 400
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        
        # Run yt-dlp to get direct URL with Vercel-compatible options
        try:
            base_options, temp_cache_dir = get_ytdlp_base_options(url, use_cookies)
            
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
                timeout=45,  # Increased timeout for cookie processing
                env={**os.environ, 'HOME': '/tmp'}  # Set HOME to /tmp for any home directory writes
            )
            
            # Clean up temp directory
            cleanup_temp_dir(temp_cache_dir)
            
            if result.returncode != 0:
                # If cookies failed, try without cookies as fallback
                if use_cookies and 'Sign in to confirm' in result.stderr:
                    return retry_without_cookies(url, 'direct-url')
                
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

# New endpoint to check available browsers for cookie extraction
@app.route('/api/cookie-browsers', methods=['GET', 'OPTIONS'])
def get_cookie_browsers():
    """Get list of available browsers for cookie extraction"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        return response
    
    try:
        # Test which browsers are available for cookie extraction
        available_browsers = []
        browsers_to_test = ['chrome', 'firefox', 'edge', 'safari', 'opera']
        
        for browser in browsers_to_test:
            try:
                # Test if browser cookies can be accessed
                cmd = [
                    sys.executable, '-m', 'yt_dlp',
                    '--cookies-from-browser', browser,
                    '--simulate',
                    '--quiet',
                    'https://www.youtube.com/watch?v=dQw4w9WgXcQ'  # Test video
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    env={**os.environ, 'HOME': '/tmp'}
                )
                
                if result.returncode == 0:
                    available_browsers.append(browser)
            except:
                continue
        
        response = jsonify({
            'availableBrowsers': available_browsers,
            'recommendation': 'chrome' if 'chrome' in available_browsers else available_browsers[0] if available_browsers else None
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        response = jsonify({'error': f'Error checking browsers: {str(e)}'})
        response.status_code = 500
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

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