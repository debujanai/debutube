import tls_client
from fake_useragent import UserAgent
import random
import json
import os
import tempfile
import time
from datetime import datetime
import subprocess
import sys

class YouTubeSession:
    def __init__(self):
        self.BASE_URL = "https://www.youtube.com"
        self.randomiseRequest()
        # Create a directory for storing session data
        self.data_dir = "youtube_session_data"
        os.makedirs(self.data_dir, exist_ok=True)

    def randomiseRequest(self):
        """Initialize request settings with random browser fingerprint and headers"""
        # Select a random browser identifier for TLS fingerprinting
        self.identifier = random.choice([
            browser for browser in tls_client.settings.ClientIdentifiers.__args__
            if browser.startswith(("chrome", "safari", "firefox", "opera"))
        ])
        
        # Create TLS client session with randomized extensions
        self.sendRequest = tls_client.Session(
            random_tls_extension_order=True,
            client_identifier=self.identifier
        )
        self.sendRequest.timeout_seconds = 60

        # Generate realistic user agent
        try:
            self.user_agent = UserAgent(os=["Windows", "macOS", "Linux"]).random
        except Exception:
            # Fallback user agents if fake_useragent fails
            fallback_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
            ]
            self.user_agent = random.choice(fallback_agents)

        # Comprehensive browser headers that match real browser behavior
        self.headers = {
            "Host": "www.youtube.com",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-US,en;q=0.9",
            "accept-encoding": "gzip, deflate, br",
            "dnt": "1",
            "upgrade-insecure-requests": "1",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "cache-control": "max-age=0",
            "user-agent": self.user_agent,
        }

    def get_ytdlp_enhanced_options(self, url):
        """Get yt-dlp options with advanced TLS fingerprinting simulation"""
        temp_cache_dir = tempfile.mkdtemp(prefix='ytdlp_tls_')
        
        # Add random delay to mimic human behavior
        time.sleep(random.uniform(1.0, 3.0))
        
        # Advanced options that simulate the TLS client behavior
        options = [
            '--no-cache-dir',
            '--cache-dir', temp_cache_dir,
            '--user-agent', self.user_agent,
            '--referer', 'https://www.youtube.com/',
            
            # Comprehensive browser headers matching our TLS session
            '--add-header', f'Accept:{self.headers["accept"]}',
            '--add-header', f'Accept-Language:{self.headers["accept-language"]}',
            '--add-header', f'Accept-Encoding:{self.headers["accept-encoding"]}',
            '--add-header', f'DNT:{self.headers["dnt"]}',
            '--add-header', f'Upgrade-Insecure-Requests:{self.headers["upgrade-insecure-requests"]}',
            '--add-header', f'Sec-Fetch-Dest:{self.headers["sec-fetch-dest"]}',
            '--add-header', f'Sec-Fetch-Mode:{self.headers["sec-fetch-mode"]}',
            '--add-header', f'Sec-Fetch-Site:{self.headers["sec-fetch-site"]}',
            '--add-header', f'Sec-Fetch-User:{self.headers["sec-fetch-user"]}',
            '--add-header', f'Cache-Control:{self.headers["cache-control"]}',
            
            # Advanced network configuration
            '--extractor-retries', '7',  # More retries
            '--fragment-retries', '7',
            '--retry-sleep', 'exp=1:120',  # Exponential backoff
            '--socket-timeout', '90',  # Longer timeout
            '--no-check-certificate',
            '--force-ipv4',
            
            # YouTube-specific optimizations
            '--sleep-interval', '2',  # Longer sleep between requests
            '--max-sleep-interval', '10',
            '--sleep-subtitles', '2',
            
            # Cookie handling with multiple fallbacks
            '--cookies-from-browser', 'chrome',
            '--ignore-errors',
            
            # Additional anti-detection measures
            '--no-warnings',
            '--quiet',  # Reduce output noise
        ]
        
        return options, temp_cache_dir

    def get_ytdlp_stealth_options(self, url):
        """Ultra-stealth options for problematic videos"""
        temp_cache_dir = tempfile.mkdtemp(prefix='ytdlp_stealth_')
        
        # Longer delay for stealth mode
        time.sleep(random.uniform(3.0, 7.0))
        
        # Re-randomize session for stealth attempt
        self.randomiseRequest()
        
        stealth_options = [
            '--no-cache-dir',
            '--cache-dir', temp_cache_dir,
            '--user-agent', self.user_agent,
            '--referer', 'https://www.youtube.com/',
            
            # Stealth headers
            '--add-header', f'Accept:{self.headers["accept"]}',
            '--add-header', f'Accept-Language:{self.headers["accept-language"]}',
            '--add-header', 'X-Forwarded-For:8.8.8.8',
            '--add-header', 'X-Real-IP:8.8.8.8',
            
            # Geo-bypass with multiple countries
            '--geo-bypass',
            '--geo-bypass-country', random.choice(['US', 'CA', 'GB', 'AU']),
            
            # Alternative extraction methods
            '--youtube-skip-dash-manifest',
            '--youtube-skip-hls-manifest',
            '--prefer-free-formats',
            
            # Aggressive retry strategy
            '--extractor-retries', '10',
            '--fragment-retries', '10',
            '--retry-sleep', 'exp=2:300',  # Up to 5 minutes
            '--socket-timeout', '120',
            
            # Network tweaks
            '--no-check-certificate',
            '--force-ipv4',
            '--no-warnings',
            '--quiet',
            
            # Try different cookie sources
            '--cookies-from-browser', random.choice(['chrome', 'firefox', 'edge', 'safari']),
            '--ignore-errors',
        ]
        
        return stealth_options, temp_cache_dir

    def extract_video_info(self, url, use_stealth=False):
        """
        Extract video information using advanced TLS fingerprinting
        
        Args:
            url (str): YouTube video URL
            use_stealth (bool): Whether to use ultra-stealth mode
            
        Returns:
            dict: Video information or error details
        """
        if not url:
            return {"error": "URL is required"}
        
        # Choose options based on stealth mode
        if use_stealth:
            options, temp_cache_dir = self.get_ytdlp_stealth_options(url)
            print(f"Using stealth mode with TLS fingerprint: {self.identifier}")
        else:
            options, temp_cache_dir = self.get_ytdlp_enhanced_options(url)
            print(f"Using enhanced mode with TLS fingerprint: {self.identifier}")
        
        cmd = [
            sys.executable, '-m', 'yt_dlp',
            '--dump-json',
            '--no-download',
            *options,
            url
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,  # Longer timeout for TLS handshakes
                env={**os.environ, 'HOME': '/tmp'}
            )
            
            # Clean up temp directory
            self.cleanup_temp_dir(temp_cache_dir)
            
            if result.returncode == 0:
                try:
                    return {"success": True, "data": json.loads(result.stdout.strip())}
                except json.JSONDecodeError:
                    return {"error": "Failed to parse video information", "raw_output": result.stdout}
            else:
                return {
                    "error": result.stderr.strip(),
                    "returncode": result.returncode,
                    "tls_fingerprint": self.identifier,
                    "user_agent": self.user_agent
                }
                
        except subprocess.TimeoutExpired:
            self.cleanup_temp_dir(temp_cache_dir)
            return {"error": "Request timeout - TLS handshake or video processing took too long"}
        except Exception as e:
            self.cleanup_temp_dir(temp_cache_dir)
            return {"error": f"Extraction error: {str(e)}"}

    def get_direct_url(self, url, format_id, use_stealth=False):
        """
        Get direct download URL using advanced TLS fingerprinting
        
        Args:
            url (str): YouTube video URL
            format_id (str): Format ID to download
            use_stealth (bool): Whether to use ultra-stealth mode
            
        Returns:
            dict: Direct URL or error details
        """
        if not url or not format_id:
            return {"error": "URL and format_id are required"}
        
        # Choose options based on stealth mode
        if use_stealth:
            options, temp_cache_dir = self.get_ytdlp_stealth_options(url)
        else:
            options, temp_cache_dir = self.get_ytdlp_enhanced_options(url)
        
        cmd = [
            sys.executable, '-m', 'yt_dlp',
            '-g',  # Get URL only
            '-f', format_id,
            *options,
            url
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                env={**os.environ, 'HOME': '/tmp'}
            )
            
            # Clean up temp directory
            self.cleanup_temp_dir(temp_cache_dir)
            
            if result.returncode == 0:
                direct_url = result.stdout.strip()
                if direct_url:
                    return {"success": True, "direct_url": direct_url}
                else:
                    return {"error": "No direct URL found"}
            else:
                return {
                    "error": result.stderr.strip(),
                    "returncode": result.returncode,
                    "tls_fingerprint": self.identifier
                }
                
        except subprocess.TimeoutExpired:
            self.cleanup_temp_dir(temp_cache_dir)
            return {"error": "Request timeout"}
        except Exception as e:
            self.cleanup_temp_dir(temp_cache_dir)
            return {"error": f"Direct URL extraction error: {str(e)}"}

    def cleanup_temp_dir(self, temp_dir):
        """Clean up temporary directory"""
        try:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass

    def test_connection(self):
        """Test the TLS connection to YouTube"""
        try:
            response = self.sendRequest.get(
                "https://www.youtube.com/robots.txt",
                headers=self.headers
            )
            return {
                "success": True,
                "status_code": response.status_code,
                "tls_fingerprint": self.identifier,
                "user_agent": self.user_agent,
                "response_size": len(response.text)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tls_fingerprint": self.identifier
            }

# Singleton instance for reuse
_youtube_session = None

def get_youtube_session():
    """Get or create YouTube session instance"""
    global _youtube_session
    if _youtube_session is None:
        _youtube_session = YouTubeSession()
    return _youtube_session 