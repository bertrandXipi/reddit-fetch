import requests
from reddit_fetch.auth import refresh_access_token, load_tokens, get_new_tokens
from reddit_fetch.config import USER_AGENT, REDDIT_USERNAME, exponential_backoff

def make_request(endpoint):
    tokens = load_tokens()
    if not tokens:
        print("❌ No stored tokens found. Re-authenticating...")
        tokens = get_new_tokens()
        if not tokens:
            print("❌ Re-authentication failed. Exiting...")
            return None
    
    access_token = tokens.get("access_token")
    headers = {"Authorization": f"Bearer {access_token}", "User-Agent": USER_AGENT}
    url = f"https://oauth.reddit.com{endpoint}"
    
    attempt = 0
    while attempt < 5:
        response = requests.get(url, headers=headers)
        if response.status_code == 401:
            print("🔄 Access token expired, refreshing...")
            new_access_token = refresh_access_token()
            if not new_access_token:
                print("❌ Refresh token failed, re-authenticating...")
                tokens = get_new_tokens()
                if not tokens:
                    print("❌ Re-authentication failed. Exiting...")
                    return None
                access_token = tokens.get("access_token")
            else:
                access_token = new_access_token
            headers["Authorization"] = f"Bearer {access_token}"
            response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            print("⚠️ Rate limited. Retrying with backoff...")
            attempt += 1
            exponential_backoff(attempt)
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return None
    return None
