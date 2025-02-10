import requests
import base64
import json
import os
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, USER_AGENT, TOKEN_FILE

# Global variable to store the authorization code
auth_code = None

def load_tokens():
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError:
            print("❌ Token file is corrupted. Resetting...")
            os.remove(TOKEN_FILE)
    return None

class AuthHandler(BaseHTTPRequestHandler):
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
    global auth_code
    server = HTTPServer(("localhost", 8080), AuthHandler)
    print("🌍 Waiting for authorization...")
    server.handle_request()

def get_new_tokens():
    print("🌍 Opening Reddit authorization page in your browser...")
    webbrowser.open(f"https://www.reddit.com/api/v1/authorize?client_id={CLIENT_ID}&response_type=code&state=RANDOM_STRING&redirect_uri={REDIRECT_URI}&duration=permanent&scope=identity history read save")
    start_auth_server()
    
    if not auth_code:
        print("❌ No authorization code received. Exiting...")
        return None
    
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
    
    print("🔍 Response Status Code:", response.status_code)
   # print("🔍 Response Content:", response.text)
    
    if response.status_code == 200:
        tokens = response.json()
        with open(TOKEN_FILE, "w", encoding="utf-8") as file:
            json.dump(tokens, file)
        print("✅ Authentication successful. Tokens saved.")
        return tokens
    
    print("❌ Authentication failed. Exiting...")
    return None
def refresh_access_token():
    tokens = load_tokens()
    if not tokens or "refresh_token" not in tokens:
        print("❌ No refresh token found. Re-authenticating...")
        return get_new_tokens()
    
    refresh_token = tokens["refresh_token"]
    auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
    b64_auth = base64.b64encode(auth_string.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {b64_auth}",
        "User-Agent": USER_AGENT,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    
    response = requests.post("https://www.reddit.com/api/v1/access_token", headers=headers, data=data)
    if response.status_code == 200:
        tokens["access_token"] = response.json().get("access_token")
        with open(TOKEN_FILE, "w", encoding="utf-8") as file:
            json.dump(tokens, file)
        print("🔄 Access token refreshed successfully.")
        return tokens["access_token"]
    
    print(f"❌ Failed to refresh access token: {response.status_code} - {response.text}")
    return get_new_tokens()
