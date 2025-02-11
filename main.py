from auth import load_tokens, get_new_tokens, refresh_access_token
from api import make_request
from config import REDDIT_USERNAME
import time
import json
import os

LAST_FETCH_FILE = "last_fetch.json"
SAVED_POSTS_FILE = "saved_posts.txt"

# Ensure we have valid tokens
def authenticate():
    try:
        tokens = load_tokens()
        if not tokens:
            raise ValueError("Token file is empty or missing.")
    except (json.JSONDecodeError, ValueError):
        print("❌ Token file is empty or corrupted. Re-authenticating...")
        if os.path.exists("tokens.json"):
            os.remove("tokens.json")
        tokens = get_new_tokens()
        if not tokens:
            print("❌ Authentication failed. Exiting...")
            exit()
    return tokens

tokens = authenticate()

access_token = tokens.get("access_token")
refresh_token = tokens.get("refresh_token")

def token_expired(tokens):
    return "timestamp" not in tokens or (time.time() - tokens["timestamp"]) >= 3600

# Refresh token if needed
if not access_token or token_expired(tokens):
    print("🔄 No valid access token found or token expired. Refreshing...")
    access_token = refresh_access_token()
    if not access_token:
        print("❌ Unable to refresh token. Exiting...")
        exit()

# Load last fetch timestamp
def load_last_fetch():
    if os.path.exists(LAST_FETCH_FILE):
        try:
            with open(LAST_FETCH_FILE, "r", encoding="utf-8") as file:
                return json.load(file).get("last_fetch")
        except json.JSONDecodeError:
            print("❌ Last fetch file is corrupted. Resetting...")
            return None
    return None

def save_last_fetch(timestamp):
    with open(LAST_FETCH_FILE, "w", encoding="utf-8") as file:
        json.dump({"last_fetch": timestamp}, file)

# Fetch delta saved posts
print("📡 Fetching new saved posts since last run...")
last_fetch = load_last_fetch()
all_posts = []
after = None
while True:
    endpoint = f"/user/{REDDIT_USERNAME}/saved?limit=100"
    if after:
        endpoint += f"&after={after}"
    
    saved_posts = make_request(endpoint)
    
    if not saved_posts or "data" not in saved_posts:
        print("❌ No more saved posts retrieved.")
        break
    
    posts = saved_posts["data"].get("children", [])
    if not posts:
        break
    
    new_posts = []
    for post in posts:
        created_utc = post.get("data", {}).get("created_utc", 0)
        if last_fetch and created_utc <= last_fetch:
            continue  # Skip already fetched posts
        new_posts.append(post)
    
    all_posts.extend(new_posts)
    after = saved_posts["data"].get("after")
    if not after:
        break
    
    time.sleep(1)  # Avoid hitting rate limits

print(f"✅ Retrieved {len(all_posts)} new saved posts.")

# Append new posts to file
if all_posts:
    with open(SAVED_POSTS_FILE, "a", encoding="utf-8") as file:
        for post in all_posts:
            data = post.get("data", {})
            kind = post.get("kind", "")
            if kind == "t3":  # Post
                title = data.get("title", "No Title")
                url = data.get("url", "No URL")
                file.write(f"Post: {title}\n{url}\n\n")
            elif kind == "t1":  # Comment
                body = data.get("body", "No Content")
                link_title = data.get("link_title", "No Title")
                link_url = data.get("link_url", "No URL")
                file.write(f"Comment on: {link_title}\n{link_url}\nContent: {body}\n\n")
    
    # Save last fetch timestamp
    if all_posts:
        latest_timestamp = max(post.get("data", {}).get("created_utc", 0) for post in all_posts)
        save_last_fetch(latest_timestamp)

print("✅ New saved posts appended to saved_posts.txt")
