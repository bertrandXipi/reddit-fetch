import requests
import base64
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import time
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, USER_AGENT

auth_code = None  # Stores auth code after successful login

class AuthHandler(BaseHTTPRequestHandler):
    """Handles OAuth2 authentication by capturing the authorization code."""
    
    def do_GET(self):
        global auth_code
        query_components = parse_qs(urlparse(self.path).query)
        if "code" in query_components:
            auth_code = query_components["code"][0].strip()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Authorization successful! You can close this tab.")
            print(f"✅ Authorization Code Captured: {auth_code}")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Error: Authorization code not found.")

def start_auth_server():
    """Starts a local server to capture the Reddit authorization code."""
    server = HTTPServer(("localhost", 8080), AuthHandler)
    print("🌍 Waiting for authorization...")
    server.handle_request()

def get_tokens():
    """Handles the OAuth2 flow and retrieves access & refresh tokens."""
    
    threading.Thread(target=start_auth_server, daemon=True).start()

    # Open Reddit OAuth login page
    authorization_url = (
        f"https://www.reddit.com/api/v1/authorize?client_id={CLIENT_ID}&response_type=code"
        f"&state=RANDOM_STRING&redirect_uri={REDIRECT_URI}&duration=permanent&scope=identity history read save"
    )
    print("🌍 Opening Reddit authorization page in your browser...")
    webbrowser.open(authorization_url)

    # Wait for auth code to be captured
    while auth_code is None:
        time.sleep(0.1)

    # Exchange auth code for access token
    auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
    b64_auth = base64.b64encode(auth_string.encode()).decode()

    headers = {
        "Authorization": f"Basic {b64_auth}",
        "User-Agent": USER_AGENT,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI
    }

    response = requests.post("https://www.reddit.com/api/v1/access_token", headers=headers, data=data)

    if response.status_code == 200:
        tokens = response.json()
        print("✅ Successfully authenticated!")
        return tokens
    else:
        print("❌ Error:", response.text)
        return None
