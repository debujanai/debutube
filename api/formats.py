import json
import subprocess
import sys
from urllib.parse import parse_qs

def handler(request):
    # CORS headers
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Content-Type': 'application/json'
    }
    
    # Handle preflight request
    if request['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    if request['httpMethod'] != 'POST':
        return {
            'statusCode': 405,
            'headers': headers,
            'body': json.dumps({'error': 'Method not allowed'})
        }
    
    try:
        # Parse the request body
        body = json.loads(request['body'])
        url = body.get('url')
        
        if not url:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'URL is required'})
            }
        
        # Validate YouTube URL
        youtube_patterns = ['youtube.com', 'youtu.be', 'youtube-nocookie.com']
        if not any(pattern in url for pattern in youtube_patterns):
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Please provide a valid YouTube URL'})
            }
        
        # Run yt-dlp to get video information
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'yt_dlp', '--dump-json', '--no-download', url],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    'statusCode': 500,
                    'headers': headers,
                    'body': json.dumps({'error': f'yt-dlp failed: {result.stderr}'})
                }
            
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
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'videoInfo': video_metadata,
                    'formats': filtered_formats
                })
            }
            
        except subprocess.TimeoutExpired:
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps({'error': 'Request timeout - video processing took too long'})
            }
        except json.JSONDecodeError:
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps({'error': 'Failed to parse video information'})
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps({'error': f'Processing error: {str(e)}'})
            }
            
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({'error': 'Invalid JSON in request body'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': f'Server error: {str(e)}'})
        } 