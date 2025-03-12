import threading
import requests
import base64
import json
import os
import time
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from reddit_fetch.config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, USER_AGENT, TOKEN_FILE
from rich.console import Console

console = Console()

# Global variable to store the authorization code
auth_code = None

def is_headless():
    """Detects if the system is running in headless mode."""
    return (
        not os.environ.get("DISPLAY")  # No GUI session (Linux/macOS)
        or os.environ.get("XDG_SESSION_TYPE") == "tty"  # Terminal-only mode
        or os.environ.get("SSH_CONNECTION")  # Running over SSH
        or os.environ.get("SSH_CLIENT")  # Running over SSH
    )

def load_tokens_safe():
    """Handles token loading safely, ensuring better error handling in headless mode."""
    if not os.path.exists(TOKEN_FILE):
        console.print("❌ [bold red]No authentication tokens found.[/bold red]")
        if is_headless():
            console.print("🔹 [bold yellow]Headless mode detected.[/bold yellow] Please authenticate on a machine with a browser using 'generate_tokens.py'.")
            console.print("🔹 Copy 'tokens.json' back to this system after authentication.")
            sys.exit(1)
        return get_new_tokens()
    
    with open(TOKEN_FILE, "r", encoding="utf-8") as file:
        return json.load(file)

class AuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        query_components = parse_qs(urlparse(self.path).query)
        if "code" in query_components:
            auth_code = query_components["code"][0].strip()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Authorization successful! You can close this tab.")
            console.print(f"✅ Authorization Code Captured: {auth_code}")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Error: Authorization code not found.")

def start_auth_server():
    global auth_code
    server = HTTPServer(("localhost", 8080), AuthHandler)
    console.print("🌍 Waiting for authorization...", style="bold blue")
    server.handle_request()

def get_new_tokens():
    """Requests new authentication tokens via OAuth."""
    global auth_code
    threading.Thread(target=start_auth_server, daemon=True).start()
    authorization_url = (
        f"https://www.reddit.com/api/v1/authorize?client_id={CLIENT_ID}&response_type=code"
        f"&state=RANDOM_STRING&redirect_uri={REDIRECT_URI}&duration=permanent&scope=identity history read save"
    )
    console.print("🌍 Opening Reddit authorization page in your browser...", style="bold yellow")
    webbrowser.open(authorization_url)

    while auth_code is None:
        time.sleep(0.1)

    auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
    b64_auth = base64.b64encode(auth_string.encode()).decode()
    url = "https://www.reddit.com/api/v1/access_token"
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
    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code == 200:
        tokens = response.json()
        tokens["timestamp"] = time.time()
        with open(TOKEN_FILE, "w", encoding="utf-8") as file:
            json.dump(tokens, file)
        return tokens
    else:
        console.print(f"❌ [bold red]Error: {response.status_code} - {response.text}[/bold red]")
        return None

def refresh_access_token_safe():
    """Refreshes the access token and handles headless system failures."""
    tokens = load_tokens_safe()
    if not tokens or "refresh_token" not in tokens:
        console.print("❌ [bold red]No refresh token found.[/bold red]")
        if is_headless():
            console.print("🔹 [bold yellow]Reauthenticate on a system with a browser.[/bold yellow]")
            console.print("🔹 Copy the new 'tokens.json' back to this system.")
            sys.exit(1)
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
        tokens["timestamp"] = time.time()
        with open(TOKEN_FILE, "w", encoding="utf-8") as file:
            json.dump(tokens, file)
        console.print("🔄 [bold green]Access token refreshed successfully.[/bold green]")
        return tokens["access_token"]

    console.print(f"❌ [bold red]Failed to refresh access token: {response.status_code} - {response.text}[/bold red]")
    if is_headless():
        console.print("🔹 [bold yellow]Reauthenticate on a system with a browser.[/bold yellow]")
        console.print("🔹 Copy the new 'tokens.json' back to this system.")
        sys.exit(1)

    return get_new_tokens()
