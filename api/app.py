from flask import Flask, request, jsonify
import subprocess
import sys
import json
import os
import tempfile
import random

app = Flask(__name__)

# User agents to rotate for better bot detection avoidance
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

def get_ytdlp_base_options(url):
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
        # Bot detection avoidance options (without cookies first)
        '--sleep-interval', '1',  # Sleep between requests
        '--max-sleep-interval', '3',  # Max sleep interval
        '--sleep-requests', '1',  # Sleep every N requests
        # Additional anti-bot measures
        '--extractor-args', 'youtube:player_client=web,mweb',  # Use web client
        '--extractor-args', 'youtube:skip=hls,dash',  # Skip some formats that might trigger detection
        '--no-warnings',  # Suppress warnings
    ]
    
    return base_options, temp_cache_dir

def get_ytdlp_with_cookies_options(url):
    """Get yt-dlp options with cookie extraction (fallback method)"""
    temp_cache_dir = tempfile.mkdtemp(prefix='ytdlp_cookies_cache_')
    user_agent = random.choice(USER_AGENTS)
    
    cookie_options = [
        '--no-cache-dir',
        '--cache-dir', temp_cache_dir,
        '--user-agent', user_agent,
        '--referer', 'https://www.youtube.com/',
        '--extractor-retries', '2',  # Fewer retries for cookie method
        '--fragment-retries', '2',
        '--retry-sleep', '1',
        '--socket-timeout', '30',
        '--no-check-certificate',
        # Try to use browser cookies
        '--cookies-from-browser', 'chrome',
        '--sleep-interval', '1',
        '--max-sleep-interval', '3',
        '--sleep-requests', '1',
        '--extractor-args', 'youtube:player_client=web',
        '--no-warnings',
    ]
    
    return cookie_options, temp_cache_dir

def get_ytdlp_fallback_options(url):
    """Get fallback yt-dlp options when cookies fail"""
    temp_cache_dir = tempfile.mkdtemp(prefix='ytdlp_fallback_cache_')
    user_agent = random.choice(USER_AGENTS)
    
    fallback_options = [
        '--no-cache-dir',
        '--cache-dir', temp_cache_dir,
        '--user-agent', user_agent,
        '--referer', 'https://www.youtube.com/',
        '--extractor-retries', '5',  # More retries for fallback
        '--fragment-retries', '5',
        '--retry-sleep', '2',  # Longer sleep
        '--socket-timeout', '45',  # Longer timeout
        '--no-check-certificate',
        # More aggressive anti-detection
        '--sleep-interval', '2',
        '--max-sleep-interval', '5',
        '--sleep-requests', '1',
        '--extractor-args', 'youtube:player_client=web',
        '--extractor-args', 'youtube:skip=dash',  # Skip DASH formats
        # Try different approach without cookies
        '--no-warnings',  # Suppress warnings
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
        
        # Run yt-dlp to get video information with Vercel-compatible options
        try:
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
                timeout=30,
                env={**os.environ, 'HOME': '/tmp'}  # Set HOME to /tmp for any home directory writes
            )
            
            # Clean up temp directory
            cleanup_temp_dir(temp_cache_dir)
            
            # If primary method fails with bot detection, try cookies first, then fallback
            if result.returncode != 0 and ('Sign in to confirm' in result.stderr or 'bot' in result.stderr.lower()):
                print("Primary method failed with bot detection, trying cookies...")
                
                # Try with cookies first
                try:
                    cookie_options, cookie_temp_dir = get_ytdlp_with_cookies_options(url)
                    
                    cookie_cmd = [
                        sys.executable, '-m', 'yt_dlp',
                        '--dump-json',
                        '--no-download',
                        *cookie_options,
                        url
                    ]
                    
                    result = subprocess.run(
                        cookie_cmd,
                        capture_output=True,
                        text=True,
                        timeout=30,
                        env={**os.environ, 'HOME': '/tmp'}
                    )
                    
                    cleanup_temp_dir(cookie_temp_dir)
                    
                    # If cookies also fail, try final fallback
                    if result.returncode != 0:
                        print("Cookie method also failed, trying final fallback...")
                        
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
                            timeout=45,  # Longer timeout for fallback
                            env={**os.environ, 'HOME': '/tmp'}
                        )
                        
                        cleanup_temp_dir(fallback_temp_dir)
                        
                except Exception as e:
                    print(f"Cookie method error: {e}, trying final fallback...")
                    
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
                        timeout=45,
                        env={**os.environ, 'HOME': '/tmp'}
                    )
                    
                    cleanup_temp_dir(fallback_temp_dir)
            
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
        
        # Run yt-dlp to get direct URL with Vercel-compatible options
        try:
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
                timeout=30,
                env={**os.environ, 'HOME': '/tmp'}  # Set HOME to /tmp for any home directory writes
            )
            
            # Clean up temp directory
            cleanup_temp_dir(temp_cache_dir)
            
            # If primary method fails with bot detection, try cookies first, then fallback
            if result.returncode != 0 and ('Sign in to confirm' in result.stderr or 'bot' in result.stderr.lower()):
                print("Primary method failed with bot detection, trying cookies...")
                
                # Try with cookies first
                try:
                    cookie_options, cookie_temp_dir = get_ytdlp_with_cookies_options(url)
                    
                    cookie_cmd = [
                        sys.executable, '-m', 'yt_dlp',
                        '-g',  # Get URL only
                        '-f', format_id,
                        *cookie_options,
                        url
                    ]
                    
                    result = subprocess.run(
                        cookie_cmd,
                        capture_output=True,
                        text=True,
                        timeout=30,
                        env={**os.environ, 'HOME': '/tmp'}
                    )
                    
                    cleanup_temp_dir(cookie_temp_dir)
                    
                    # If cookies also fail, try final fallback
                    if result.returncode != 0:
                        print("Cookie method also failed, trying final fallback...")
                        
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
                            timeout=45,  # Longer timeout for fallback
                            env={**os.environ, 'HOME': '/tmp'}
                        )
                        
                        cleanup_temp_dir(fallback_temp_dir)
                        
                except Exception as e:
                    print(f"Cookie method error: {e}, trying final fallback...")
                    
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
                        timeout=45,
                        env={**os.environ, 'HOME': '/tmp'}
                    )
                    
                    cleanup_temp_dir(fallback_temp_dir)
            
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