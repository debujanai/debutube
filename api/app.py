from flask import Flask, request, jsonify
import subprocess
import sys
import json
import os
import tempfile
import random
import time
from datetime import datetime
from youtube_session import get_youtube_session

app = Flask(__name__)

# Legacy user agents kept for fallback compatibility
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

def cleanup_temp_dir(temp_dir):
    """Clean up temporary directory"""
    try:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    except:
        pass

def format_error_message(error_msg, technical_details=None):
    """Format user-friendly error messages"""
    error_msg = error_msg.lower() if error_msg else ""
    
    if "sign in to confirm you're not a bot" in error_msg:
        return {
            'error': 'YouTube is detecting automated access. This video may require authentication or may be age-restricted.',
            'suggestions': [
                'Try a different video',
                'Wait 5-10 minutes before retrying',
                'Ensure you have Chrome installed and are logged into YouTube',
                'Check if the video is age-restricted or private'
            ],
            'technical_error': technical_details
        }
    elif "video unavailable" in error_msg:
        return {
            'error': 'This video is not available. It may be private, deleted, or restricted in your region.',
            'suggestions': [
                'Check if the video URL is correct',
                'Verify the video is still available on YouTube',
                'Try accessing the video in a web browser'
            ],
            'technical_error': technical_details
        }
    elif "age-restricted" in error_msg or "age restricted" in error_msg:
        return {
            'error': 'This video is age-restricted and cannot be accessed without authentication.',
            'suggestions': [
                'Log into YouTube in your Chrome browser',
                'Try a different, non-age-restricted video',
                'Contact administrator for cookie setup assistance'
            ],
            'technical_error': technical_details
        }
    elif "private video" in error_msg or "private" in error_msg:
        return {
            'error': 'This video is private and cannot be accessed.',
            'suggestions': [
                'Ensure you have permission to view this video',
                'Try a public video instead'
            ],
            'technical_error': technical_details
        }
    else:
        return {
            'error': f'Failed to process video: {technical_details or error_msg}',
            'suggestions': [
                'Try again in a few minutes',
                'Check your internet connection',
                'Try a different video'
            ],
            'technical_error': technical_details
        }

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
        
        # Use advanced TLS client session for extraction
        try:
            print(f"🚀 Processing video with advanced TLS fingerprinting: {url}")
            youtube_session = get_youtube_session()
            
            # First attempt with enhanced TLS fingerprinting
            result = youtube_session.extract_video_info(url, use_stealth=False)
            
            if not result.get('success') and result.get('error'):
                print(f"⚠️ Enhanced method failed, trying stealth mode: {result.get('error')}")
                # Try stealth mode if enhanced fails
                result = youtube_session.extract_video_info(url, use_stealth=True)
            
            if result.get('success'):
                video_info = result['data']
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
                
                print(f"✅ Successfully extracted {len(filtered_formats)} formats for: {video_metadata['title']}")
                
                response = jsonify({
                    'videoInfo': video_metadata,
                    'formats': filtered_formats,
                    'extraction_method': 'advanced_tls_fingerprinting',
                    'tls_fingerprint': result.get('tls_fingerprint', 'unknown')
                })
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response
            else:
                # Format error message for user
                error_details = format_error_message(
                    result.get('error', ''),
                    technical_details=result
                )
                
                response = jsonify(error_details)
                response.status_code = 500
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response
                
        except Exception as e:
            print(f"❌ TLS extraction failed with exception: {str(e)}")
            error_details = format_error_message(
                str(e),
                technical_details=f"TLS extraction exception: {str(e)}"
            )
            response = jsonify(error_details)
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
        
        # Use advanced TLS client session for direct URL extraction
        try:
            print(f"🔗 Getting direct URL with advanced TLS fingerprinting: {url} (format: {format_id})")
            youtube_session = get_youtube_session()
            
            # First attempt with enhanced TLS fingerprinting
            result = youtube_session.get_direct_url(url, format_id, use_stealth=False)
            
            if not result.get('success') and result.get('error'):
                print(f"⚠️ Enhanced direct URL method failed, trying stealth mode: {result.get('error')}")
                # Try stealth mode if enhanced fails
                result = youtube_session.get_direct_url(url, format_id, use_stealth=True)
            
            if result.get('success'):
                print(f"✅ Successfully obtained direct URL for format {format_id}")
                response = jsonify({
                    'directUrl': result['direct_url'],
                    'extraction_method': 'advanced_tls_fingerprinting',
                    'tls_fingerprint': result.get('tls_fingerprint', 'unknown')
                })
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response
            else:
                # Format error message for direct URL failures
                error_msg = result.get('error', '').lower()
                
                if "no video formats found" in error_msg or "format not available" in error_msg:
                    error_details = {
                        'error': f'The requested format ({format_id}) is not available for this video.',
                        'suggestions': [
                            'Try a different format from the formats list',
                            'Check if the video is still available',
                            'Refresh the formats list and try again'
                        ],
                        'technical_error': result
                    }
                elif "sign in to confirm you're not a bot" in error_msg:
                    error_details = {
                        'error': 'YouTube is blocking direct URL access. Authentication may be required.',
                        'suggestions': [
                            'Try a different format',
                            'Wait a few minutes before retrying',
                            'Ensure Chrome is logged into YouTube'
                        ],
                        'technical_error': result
                    }
                else:
                    error_details = format_error_message(
                        result.get('error', ''),
                        technical_details=result
                    )
                
                response = jsonify(error_details)
                response.status_code = 500
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response
                
        except Exception as e:
            print(f"❌ TLS direct URL extraction failed with exception: {str(e)}")
            error_details = format_error_message(
                str(e),
                technical_details=f"TLS direct URL exception: {str(e)}"
            )
            response = jsonify(error_details)
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
        'message': 'Advanced TLS Fingerprinting & Cookie Authentication',
        'description': 'This API uses advanced TLS client fingerprinting to bypass bot detection, with automatic cookie support.',
        'features': {
            'tls_fingerprinting': {
                'description': 'Uses real browser TLS fingerprints (Chrome, Firefox, Safari, Opera)',
                'benefits': ['Better bot detection avoidance', 'Randomized TLS extensions', 'Authentic browser behavior simulation']
            },
            'automatic_cookies': {
                'description': 'Automatically extracts cookies from your Chrome browser',
                'note': 'Works if you have Chrome installed and are logged into YouTube'
            },
            'stealth_mode': {
                'description': 'Ultra-stealth mode with additional geo-bypass and randomization',
                'triggers': ['When standard method fails', 'For problematic videos', 'Age-restricted content']
            }
        },
        'manual_cookies': {
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
        },
        'privacy_note': 'Cookies contain your authentication information. Only use trusted extensions and never share cookie files.',
        'troubleshooting': {
            'bot_detection': 'The TLS fingerprinting significantly reduces bot detection. If you still see errors, try waiting or using a different video.',
            'age_restricted': 'Age-restricted videos work better with proper Chrome login and cookie extraction',
            'private_videos': 'Private videos require authentication from the video owner\'s account',
            'connection_test': 'Use /api/test-connection to verify TLS fingerprinting is working'
        }
    }
    
    response = jsonify(cookie_info)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

# TLS connection test endpoint
@app.route('/api/test-connection', methods=['GET', 'OPTIONS'])
def test_connection():
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        return response
    
    try:
        print("🧪 Testing TLS connection to YouTube...")
        youtube_session = get_youtube_session()
        
        # Test the TLS connection
        connection_result = youtube_session.test_connection()
        
        if connection_result.get('success'):
            test_result = {
                'status': 'success',
                'message': 'TLS fingerprinting is working correctly',
                'connection_details': {
                    'tls_fingerprint': connection_result.get('tls_fingerprint'),
                    'user_agent': connection_result.get('user_agent'),
                    'status_code': connection_result.get('status_code'),
                    'response_size': connection_result.get('response_size')
                },
                'capabilities': {
                    'tls_client': 'Available',
                    'fake_useragent': 'Available',
                    'cookie_extraction': 'Automatic (Chrome)',
                    'stealth_mode': 'Available'
                }
            }
            print(f"✅ TLS test successful with fingerprint: {connection_result.get('tls_fingerprint')}")
        else:
            test_result = {
                'status': 'error',
                'message': 'TLS connection test failed',
                'error': connection_result.get('error'),
                'tls_fingerprint': connection_result.get('tls_fingerprint'),
                'troubleshooting': [
                    'Check internet connection',
                    'Verify tls-client package is installed',
                    'Try again in a few minutes'
                ]
            }
            print(f"❌ TLS test failed: {connection_result.get('error')}")
        
        response = jsonify(test_result)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        print(f"❌ TLS test exception: {str(e)}")
        error_result = {
            'status': 'error',
            'message': 'TLS test failed with exception',
            'error': str(e),
            'troubleshooting': [
                'Install required packages: pip install tls-client fake-useragent',
                'Check if dependencies are properly installed',
                'Verify Python environment'
            ]
        }
        
        response = jsonify(error_result)
        response.status_code = 500
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