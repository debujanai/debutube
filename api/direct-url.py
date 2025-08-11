import json
import subprocess
import sys

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
        format_id = body.get('formatId')
        
        if not url or not format_id:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'URL and formatId are required'})
            }
        
        # Run yt-dlp to get direct URL
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'yt_dlp', '-g', '-f', format_id, url],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    'statusCode': 500,
                    'headers': headers,
                    'body': json.dumps({'error': f'Failed to get direct URL: {result.stderr}'})
                }
            
            direct_url = result.stdout.strip()
            
            if not direct_url:
                return {
                    'statusCode': 500,
                    'headers': headers,
                    'body': json.dumps({'error': 'No direct URL found'})
                }
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'directUrl': direct_url})
            }
            
        except subprocess.TimeoutExpired:
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps({'error': 'Request timeout'})
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