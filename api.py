import requests
import time
from config import USER_AGENT
from auth import get_tokens

# Get authentication tokens
tokens = get_tokens()
if tokens:
    ACCESS_TOKEN = tokens["access_token"]
    REFRESH_TOKEN = tokens["refresh_token"]
else:
    print("❌ Failed to authenticate.")
    exit()

def refresh_access_token(refresh_token):
    """Refreshes an expired access token."""
    headers = {
        "Authorization": f"Basic {ACCESS_TOKEN}",
        "User-Agent": USER_AGENT
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    response = requests.post("https://www.reddit.com/api/v1/access_token", headers=headers, data=data)
    return response.json().get("access_token") if response.status_code == 200 else None

def make_request(endpoint):
    """Makes an authenticated API request to Reddit."""
    global ACCESS_TOKEN
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "User-Agent": USER_AGENT
    }
    url = f"https://oauth.reddit.com{endpoint}"

    response = requests.get(url, headers=headers)
    if response.status_code == 401:
        print("🔄 Access token expired, refreshing...")
        ACCESS_TOKEN = refresh_access_token(REFRESH_TOKEN)
        headers["Authorization"] = f"Bearer {ACCESS_TOKEN}"
        response = requests.get(url, headers=headers)

    return response.json() if response.status_code == 200 else None

def fetch_saved_posts():
    """Fetches all saved Reddit posts using pagination."""
    all_posts = []
    after = None
    while True:
        endpoint = "/user/GeekIsTheNewSexy/saved"
        if after:
            endpoint += f"?after={after}&limit=100"
        else:
            endpoint += "?limit=100"

        response = make_request(endpoint)
        if not response or 'data' not in response or 'children' not in response['data']:
            print("❌ Error: Unexpected response format.")
            return []

        posts = response['data']['children']
        if not posts:
            break
        all_posts.extend(posts)

        after = response['data'].get('after')
        if not after:
            break
        time.sleep(1)

    return all_posts
