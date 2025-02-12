from auth import load_tokens, get_new_tokens, refresh_access_token
from api import make_request
from config import REDDIT_USERNAME
import time
import json
import os
import argparse

LAST_FETCH_FILE = "last_fetch.json"
SAVED_POSTS_FILE = "saved_posts.txt"
BOOKMARKS_FILE = "bookmarks.html"

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Fetch Reddit saved posts and output in desired format.")
parser.add_argument("--format", choices=["text", "html"], required=True, help="Output format: text or html")
parser.add_argument("--force-fetch", action="store_true", help="Ignore last fetch timestamp and fetch all saved posts")
args = parser.parse_args()

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

def token_expired(tokens):
    return "timestamp" not in tokens or (time.time() - tokens["timestamp"]) >= 3600

# Refresh token if needed
if token_expired(tokens):
    print("🔄 Access token expired. Refreshing...")
    tokens["access_token"] = refresh_access_token()
    if not tokens["access_token"]:
        print("❌ Unable to refresh token. Exiting...")
        exit()

# Load last fetch timestamp
def load_last_fetch():
    if os.path.exists(LAST_FETCH_FILE) and not args.force_fetch:
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

# Fetch saved posts once and store in memory
print("📡 Fetching new saved posts...")
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
    
    new_posts = [post for post in posts if args.force_fetch or post.get("data", {}).get("created_utc", 0) > (last_fetch or 0)]
    
    all_posts.extend(new_posts)
    after = saved_posts["data"].get("after")
    if not after:
        break
    
    time.sleep(1)  # Avoid hitting rate limits

print(f"✅ Retrieved {len(all_posts)} new saved posts.")

# Output data in the chosen format
if all_posts:
    if args.format == "text":
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
    else:
        with open(BOOKMARKS_FILE, "w", encoding="utf-8") as file:
            file.write("<!DOCTYPE NETSCAPE-Bookmark-file-1>\n")
            file.write("<META HTTP-EQUIV=\"Content-Type\" CONTENT=\"text/html; charset=UTF-8\">\n")
            file.write("<TITLE>Bookmarks</TITLE>\n")
            file.write("<H1>Bookmarks</H1>\n")
            file.write("<DL><p>\n")
            for post in all_posts:
                data = post.get("data", {})
                kind = post.get("kind", "")
                if kind == "t3":  # Post
                    title = data.get("title", "No Title")
                    url = data.get("url", "No URL")
                    file.write(f"    <DT><A HREF=\"{url}\">{title}</A>\n")
                elif kind == "t1":  # Comment
                    body = data.get("body", "No Content").replace("\n", " ")
                    link_title = data.get("link_title", "No Title")
                    link_url = data.get("link_url", "No URL")
                    file.write(f"    <DT><A HREF=\"{link_url}\">Comment on: {link_title}</A> - {body[:100]}...\n")
            file.write("</DL><p>\n")
    
    # Save last fetch timestamp
    latest_timestamp = max(post.get("data", {}).get("created_utc", 0) for post in all_posts)
    save_last_fetch(latest_timestamp)

if all_posts:
    print("✅ Saved posts successfully exported in chosen format.")
else:
    print("⚠️ No new posts fetched. No changes were made.")
