"""
Spotify OAuth token getter - generates tokens with required scopes.
"""
import sys
import os
import requests
import base64
import webbrowser
from urllib.parse import urlparse, parse_qs, quote
from app import WavvyAPIWrapper


# Add parent directory to path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

APP = WavvyAPIWrapper(__name__).create_dev_app()
settings = APP.settings

# Get credentials from config or env
CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID") or settings.SPOTIFY_CLIENT_ID_C or settings.SPOTIFY_CLIENT_ID_P
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET") or settings.SPOTIFY_CLIENT_SECRET_C or settings.SPOTIFY_CLIENT_SECRET_P

if not CLIENT_ID:
    CLIENT_ID = input("Enter your Spotify Client ID: ").strip()
if not CLIENT_SECRET:
    CLIENT_SECRET = input("Enter your Spotify Client Secret: ").strip()

REDIRECT_URI =  settings.BACKEND_URL
SCOPE = "playlist-read-private playlist-read-collaborative user-read-recently-played"

print("Spotify OAuth Token Getter")
print(f"Redirect URI: {REDIRECT_URI}")
print("(Make sure this is added to your Spotify app's redirect URIs)\n")

# Step 1: Open browser for authorization
auth_url = (
    f"https://accounts.spotify.com/authorize?"
    f"client_id={CLIENT_ID}&"
    f"response_type=code&"
    f"redirect_uri={quote(REDIRECT_URI, safe='')}&"
    f"scope={quote(SCOPE, safe='')}"
)

print("Opening browser for authorization...")
webbrowser.open(auth_url)

# Step 2: Get code from redirect URL
if "httpbin.org" in REDIRECT_URI:
    print("\nAfter authorizing, copy the 'code' value from the httpbin.org JSON response")
    code = input("Authorization code: ").strip()
    redirect_url = None
else:
    print(f"\nAfter authorizing, copy the full redirect URL")
    redirect_url = input("Redirect URL: ").strip()
    code = None

# Extract code from URL or use directly if from httpbin
if code is None:
    redirect_url = redirect_url.strip('"').strip("'").strip()
    
    try:
        parsed = urlparse(redirect_url)
        params = parse_qs(parsed.query)
        code = params.get('code', [None])[0]
        
        if not code:
            if 'code=' in redirect_url:
                code = redirect_url.split('code=')[1].split('&')[0]
            
        if not code:
            print("❌ Error: No authorization code found in URL!")
            exit(1)
        
    except Exception as e:
        print(f"❌ Error parsing URL: {e}")
        exit(1)

if not code:
    print("❌ Error: No authorization code provided!")
    exit(1)

# Step 3: Exchange code for token
print("Exchanging code for access token...")

auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
auth_bytes = auth_string.encode('utf-8')
auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')

url = "https://accounts.spotify.com/api/token"
headers = {
    "Authorization": f"Basic {auth_base64}",
    "Content-Type": "application/x-www-form-urlencoded"
}
data = {
    "grant_type": "authorization_code",
    "code": code,
    "redirect_uri": REDIRECT_URI
}

try:
    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code == 200:
        token_data = response.json()
        token = token_data.get('access_token')
        expires_in = token_data.get('expires_in', 3600)
        
        print(f"\n✓ Success! Token expires in {expires_in} seconds")
        print(f"\nAccess Token:")
        print(token)
        print(f"\nAdd to .env: SPOTIFY_USER_TOKEN={token}")
        
    else:
        error_data = response.json() if response.text else {}
        error_msg = error_data.get('error', 'Unknown error')
        error_description = error_data.get('error_description', response.text)
        
        print(f"\n❌ Error: {error_msg}")
        print(f"Details: {error_description}")
        print("\nCommon fixes:")
        print("- Check CLIENT_ID and CLIENT_SECRET")
        print("- Verify redirect_uri matches in Spotify dashboard")
        print("- Authorization code can only be used once")
        
except Exception as e:
    print(f"❌ Network error: {e}")

