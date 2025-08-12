from flask import Flask, request, jsonify
import subprocess
import sys
import json
import os
import tempfile
import random
import time
from datetime import datetime

app = Flask(__name__)

# Enhanced user agents with more realistic browser fingerprints
USER_AGENTS = [
    # Chrome on Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    
    # Chrome on macOS
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    
    # Firefox on Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    
    # Safari on macOS
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    
    # Edge on Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0',
]

# Additional headers to make requests look more legitimate
BROWSER_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
}

def get_ytdlp_base_options(url):
    """Get enhanced yt-dlp options with better bot detection avoidance"""
    temp_cache_dir = tempfile.mkdtemp(prefix='ytdlp_cache_')
    user_agent = random.choice(USER_AGENTS)
    
    # Add random delay to avoid rate limiting
    time.sleep(random.uniform(0.5, 2.0))
    
    base_options = [
        '--no-cache-dir',  # Disable cache completely
        '--cache-dir', temp_cache_dir,  # Use temp directory for any cache needs
        '--user-agent', user_agent,
        '--referer', 'https://www.youtube.com/',
        
        # Enhanced anti-bot detection
        '--add-header', f'Accept:{BROWSER_HEADERS["Accept"]}',
        '--add-header', f'Accept-Language:{BROWSER_HEADERS["Accept-Language"]}',
        '--add-header', f'Accept-Encoding:{BROWSER_HEADERS["Accept-Encoding"]}',
        '--add-header', f'DNT:{BROWSER_HEADERS["DNT"]}',
        '--add-header', f'Upgrade-Insecure-Requests:{BROWSER_HEADERS["Upgrade-Insecure-Requests"]}',
        '--add-header', f'Sec-Fetch-Dest:{BROWSER_HEADERS["Sec-Fetch-Dest"]}',
        '--add-header', f'Sec-Fetch-Mode:{BROWSER_HEADERS["Sec-Fetch-Mode"]}',
        '--add-header', f'Sec-Fetch-Site:{BROWSER_HEADERS["Sec-Fetch-Site"]}',
        '--add-header', f'Cache-Control:{BROWSER_HEADERS["Cache-Control"]}',
        
        # Network and retry settings
        '--extractor-retries', '5',  # Increased retries
        '--fragment-retries', '5',
        '--retry-sleep', 'linear=2:10:1',  # Progressive backoff
        '--socket-timeout', '60',  # Increased timeout
        '--no-check-certificate',
        
        # Additional YouTube-specific options
        '--force-ipv4',  # Force IPv4 to avoid potential IPv6 issues
        '--sleep-interval', '1',  # Sleep between requests
        '--max-sleep-interval', '5',
        
        # Cookie handling - try to extract from browser if available
        '--cookies-from-browser', 'chrome',  # Try Chrome first
        '--ignore-errors',  # Continue on cookie extraction errors
    ]
    
    return base_options, temp_cache_dir

def get_ytdlp_fallback_options(url):
    """Fallback options when cookie extraction fails"""
    temp_cache_dir = tempfile.mkdtemp(prefix='ytdlp_cache_fallback_')
    user_agent = random.choice(USER_AGENTS)
    
    time.sleep(random.uniform(1.0, 3.0))  # Longer delay for fallback
    
    fallback_options = [
        '--no-cache-dir',
        '--cache-dir', temp_cache_dir,
        '--user-agent', user_agent,
        '--referer', 'https://www.youtube.com/',
        
        # More aggressive headers
        '--add-header', f'Accept:{BROWSER_HEADERS["Accept"]}',
        '--add-header', f'Accept-Language:{BROWSER_HEADERS["Accept-Language"]}',
        '--add-header', 'X-Forwarded-For:8.8.8.8',  # Use Google DNS IP
        
        # Bypass some restrictions
        '--geo-bypass',
        '--geo-bypass-country', 'US',
        
        # Alternative extraction method
        '--youtube-skip-dash-manifest',
        '--no-warnings',
        
        # Network settings
        '--extractor-retries', '3',
        '--fragment-retries', '3',
        '--retry-sleep', '5',
        '--socket-timeout', '30',
        '--no-check-certificate',
        '--force-ipv4',
    ]
    
    return fallback_options, temp_cache_dir

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
        
        # Run yt-dlp to get video information with enhanced bot detection avoidance
        try:
            # First attempt with enhanced options (including cookies)
            base_options, temp_cache_dir = get_ytdlp_base_options(url)
            
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
                timeout=60,  # Increased timeout
                env={**os.environ, 'HOME': '/tmp'}
            )
            
            # Clean up temp directory
            cleanup_temp_dir(temp_cache_dir)
            
            # If first attempt fails, try fallback method
            if result.returncode != 0:
                print(f"Primary method failed, trying fallback: {result.stderr}")
                
                fallback_options, fallback_temp_dir = get_ytdlp_fallback_options(url)
                
                fallback_cmd = [
                    sys.executable, '-m', 'yt_dlp',
                    '--dump-json',
                    '--no-download',
                    *fallback_options,
                    url
                ]
                
                result = subprocess.run(
                    fallback_cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    env={**os.environ, 'HOME': '/tmp'}
                )
                
                cleanup_temp_dir(fallback_temp_dir)
            
            if result.returncode != 0:
                error_msg = result.stderr.strip()
                
                # Provide more helpful error messages
                if "Sign in to confirm you're not a bot" in error_msg:
                    response = jsonify({
                        'error': 'YouTube is blocking automated access. This video may require authentication or may be age-restricted. Please try a different video or try again later.',
                        'technical_error': error_msg
                    })
                elif "Video unavailable" in error_msg:
                    response = jsonify({
                        'error': 'This video is not available. It may be private, deleted, or restricted in your region.',
                        'technical_error': error_msg
                    })
                elif "age-restricted" in error_msg.lower():
                    response = jsonify({
                        'error': 'This video is age-restricted and cannot be accessed without authentication.',
                        'technical_error': error_msg
                    })
                else:
                    response = jsonify({
                        'error': f'Failed to fetch video information: {error_msg}',
                        'technical_error': error_msg
                    })
                
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
        
        if not url or not format_id:
            response = jsonify({'error': 'URL and formatId are required'})
            response.status_code = 400
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        
        # Run yt-dlp to get direct URL with enhanced bot detection avoidance
        try:
            # First attempt with enhanced options (including cookies)
            base_options, temp_cache_dir = get_ytdlp_base_options(url)
            
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
                timeout=60,  # Increased timeout
                env={**os.environ, 'HOME': '/tmp'}
            )
            
            # Clean up temp directory
            cleanup_temp_dir(temp_cache_dir)
            
            # If first attempt fails, try fallback method
            if result.returncode != 0:
                print(f"Primary method failed for direct URL, trying fallback: {result.stderr}")
                
                fallback_options, fallback_temp_dir = get_ytdlp_fallback_options(url)
                
                fallback_cmd = [
                    sys.executable, '-m', 'yt_dlp',
                    '-g',  # Get URL only
                    '-f', format_id,
                    *fallback_options,
                    url
                ]
                
                result = subprocess.run(
                    fallback_cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    env={**os.environ, 'HOME': '/tmp'}
                )
                
                cleanup_temp_dir(fallback_temp_dir)
            
            if result.returncode != 0:
                error_msg = result.stderr.strip()
                
                # Provide more helpful error messages
                if "Sign in to confirm you're not a bot" in error_msg:
                    response = jsonify({
                        'error': 'YouTube is blocking automated access. Please try a different video or try again later.',
                        'technical_error': error_msg
                    })
                elif "No video formats found" in error_msg or "format not available" in error_msg.lower():
                    response = jsonify({
                        'error': f'The requested format ({format_id}) is not available for this video. Please try a different format.',
                        'technical_error': error_msg
                    })
                else:
                    response = jsonify({
                        'error': f'Failed to get direct URL: {error_msg}',
                        'technical_error': error_msg
                    })
                
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

# Health check endpoint for Vercel
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'message': 'DebuTube API is running perfectly!'})

# Cookie information endpoint
@app.route('/api/cookie-info', methods=['GET', 'OPTIONS'])
def cookie_info():
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        return response
    
    cookie_info = {
        'message': 'Cookie Authentication Information',
        'description': 'If you encounter bot detection errors, you may need to provide cookies from your browser.',
        'methods': {
            'automatic': {
                'description': 'The API automatically tries to extract cookies from Chrome browser if available',
                'note': 'This works if you have Chrome installed and are logged into YouTube'
            },
            'manual': {
                'description': 'You can manually export cookies using browser extensions',
                'extensions': {
                    'chrome': 'Get cookies.txt LOCALLY - Available in Chrome Web Store',
                    'firefox': 'cookies.txt - Available in Firefox Add-ons'
                },
                'steps': [
                    '1. Install a cookie export extension',
                    '2. Visit YouTube and log in',
                    '3. Export cookies for youtube.com',
                    '4. Save the cookies.txt file',
                    '5. Contact the API administrator to configure cookie support'
                ]
            }
        },
        'privacy_note': 'Cookies contain your authentication information. Only use trusted extensions and never share cookie files.',
        'troubleshooting': {
            'bot_detection': 'If you see "Sign in to confirm you\'re not a bot", try using a different video or wait before retrying',
            'age_restricted': 'Age-restricted videos require authentication and may not work without proper cookies',
            'private_videos': 'Private or unlisted videos require authentication from the video owner\'s account'
        }
    }
    
    response = jsonify(cookie_info)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

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