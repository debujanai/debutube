import subprocess
import sys

if len(sys.argv) < 2:
    print("Usage: python get_formats.py <YouTube_URL>")
    sys.exit(1)

youtube_url = sys.argv[1]

# Step 1: Get all available formats
print("\nFetching available formats...\n")
subprocess.run(
    [sys.executable, "-m", "yt_dlp", "-F", youtube_url]
)

# Step 2: Ask user which format ID they want
format_id = input("\nEnter the format ID you want to download: ").strip()

# Step 3: Get direct link for that format
print("\nFetching direct link...\n")
result = subprocess.run(
    [sys.executable, "-m", "yt_dlp", "-g", "-f", format_id, youtube_url],
    capture_output=True,
    text=True
)

direct_url = result.stdout.strip()
print(f"\nDirect URL for format {format_id}:\n{direct_url}\n")
print("⚠️ Remember: This link will expire in a few hours.")

# Optional: auto-open in browser
open_browser = input("Open in browser? (y/n): ").strip().lower()
if open_browser == "y":
    import webbrowser
    webbrowser.open(direct_url) 