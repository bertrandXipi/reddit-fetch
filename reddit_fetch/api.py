import os
import json
import requests
from reddit_fetch.auth import load_tokens_safe, refresh_access_token_safe
from reddit_fetch.config import USER_AGENT, REDDIT_USERNAME, exponential_backoff
from rich.console import Console

console = Console()

DATA_DIR = "/data/" if os.getenv("DOCKER", "0") == "1" else "./"
LAST_FETCH_FILE = f"{DATA_DIR}last_fetch.json"
OUTPUT_JSON = f"{DATA_DIR}saved_posts.json"
OUTPUT_HTML = f"{DATA_DIR}saved_posts.html"

def make_request(endpoint):
    """Makes an API request to Reddit, handling authentication and errors."""
    
    tokens = load_tokens_safe()
    if not tokens:
        console.print("❌ [bold red]No stored tokens found. Re-authenticating...[/bold red]")
        tokens = refresh_access_token_safe()
        if not tokens:
            console.print("❌ [bold red]Re-authentication failed. Exiting...[/bold red]")
            return None
    
    access_token = tokens.get("access_token")
    headers = {"Authorization": f"Bearer {access_token}", "User-Agent": USER_AGENT}
    url = f"https://oauth.reddit.com{endpoint}"

    attempt = 0
    while attempt < 5:
        response = requests.get(url, headers=headers)

        if response.status_code == 401:
            console.print("🔄 [yellow]Access token expired, refreshing...[/yellow]")
            new_access_token = refresh_access_token_safe()
            if not new_access_token:
                console.print("❌ [bold red]Refresh token failed, manual re-authentication needed.[/bold red]")
                return None
            headers["Authorization"] = f"Bearer {new_access_token}"
            response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return response.json()

        elif response.status_code == 429:
            console.print("⚠️ [bold yellow]Rate limited. Retrying with backoff...[/bold yellow]")
            attempt += 1
            exponential_backoff(attempt)

        else:
            console.print(f"❌ [bold red]Error {response.status_code}: {response.reason}[/bold red]")
            return None

    return None

def fetch_saved_posts(format="json", force_fetch=False):
    """Fetch saved Reddit posts, using `after` for full fetch and `before` for incremental fetch."""
    
    last_fetch_timestamp = None
    fetch_mode = "before"  # Default fetch mode for incremental updates
    cursor_param = None  # Holds `after` or `before` value

    # Read last_fetch.json if it exists
    if os.path.exists(LAST_FETCH_FILE) and not force_fetch:
        with open(LAST_FETCH_FILE, "r", encoding="utf-8") as file:
            try:
                last_fetch_data = json.load(file)
                last_fetch_timestamp = last_fetch_data.get("last_fetch")
                cursor_param = last_fetch_data.get("before")  # Default to `before`
            except json.JSONDecodeError:
                console.print("⚠️ [bold yellow]last_fetch.json is corrupted. Ignoring...[/bold yellow]")

    # Use `after` for force fetch (fetch ALL saved posts)
    if force_fetch or not os.path.exists(LAST_FETCH_FILE):
        fetch_mode = "after"
        cursor_param = None  # Reset to fetch all data from the start
        console.print("🚀 [bold cyan]Force Fetch Activated: Fetching ALL saved posts using pagination.[/bold cyan]")

    new_posts = []
    while True:
        endpoint = f"/user/{REDDIT_USERNAME}/saved?limit=100"
        if cursor_param:
            endpoint += f"&{fetch_mode}={cursor_param}"  # Dynamically switch between `after` and `before`

        saved_posts = make_request(endpoint)
        if not saved_posts or "data" not in saved_posts:
            break

        posts = saved_posts["data"].get("children", [])
        if not posts:
            break  # No more posts available

        for post in posts:
            data = post["data"]
            new_posts.append({
                "title": data.get("title", "No Title"),
                "url": data.get("url", f"https://reddit.com{data.get('permalink', '#')}"),
                "subreddit": data.get("subreddit"),
                "created_utc": data.get("created_utc"),
                "fullname": data["name"]  # Store Reddit's unique identifier
            })

        # Move pagination cursor
        if fetch_mode == "after":
            cursor_param = posts[-1]["data"]["name"]  # Take LAST post for force fetch
        else:
            cursor_param = posts[0]["data"]["name"]  # Take FIRST post for incremental

    # **Store last fetched post details**
    if new_posts:
        last_fetched_value = new_posts[-1]["created_utc"] if fetch_mode == "after" else new_posts[0]["created_utc"]
        last_fetched_after = new_posts[-1]["fullname"] if fetch_mode == "after" else None
        last_fetched_before = new_posts[0]["fullname"] if fetch_mode == "before" else None

        with open(LAST_FETCH_FILE, "w", encoding="utf-8") as file:
            json.dump({"last_fetch": last_fetched_value, "after": last_fetched_after, "before": last_fetched_before}, file)

        console.print(f"📌 Last fetch timestamp updated: {last_fetched_value}", style="bold cyan")
        console.print(f"📌 Last fetch `after` updated: {last_fetched_after if last_fetched_after else 'N/A'}", style="bold cyan")
        console.print(f"📌 Last fetch `before` updated: {last_fetched_before if last_fetched_before else 'N/A'}", style="bold cyan")

        #Converting into JSON first
        existing_posts = []
        if os.path.exists(OUTPUT_JSON) and not force_fetch:
            with open(OUTPUT_JSON, "r", encoding="utf-8") as file:
                existing_posts = json.load(file)
        combined_posts = new_posts + existing_posts  # Prepend new posts instead of appending
        unique_posts = {post["fullname"]: post for post in combined_posts}.values()  # Remove duplicates
        if format =="html":
           html_output = "<html><head><title>Saved Reddit Posts</title></head><body><ul>\n"
           for index,post in enumerate(unique_posts, start=1):
                html_output += f'<li>{index}. <a href="{post["url"]}">{post["title"]}</a> (r/{post["subreddit"]})</li>\n'
           html_output += "</ul></body></html>\n"
           return html_output
        elif format =="json":
           return list(unique_posts) if unique_posts else []
   
