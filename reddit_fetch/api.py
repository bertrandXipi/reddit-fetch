import os
import json
import requests
import time
from reddit_fetch.auth import load_tokens_safe, refresh_access_token_safe
from reddit_fetch.config import USER_AGENT, REDDIT_USERNAME, exponential_backoff
from rich.console import Console

console = Console()

DATA_DIR = "/data/" if os.getenv("DOCKER", "0") == "1" else "./"
LAST_FETCH_FILE = f"{DATA_DIR}last_fetch.json"
OUTPUT_JSON = f"{DATA_DIR}saved_posts.json"
OUTPUT_HTML = f"{DATA_DIR}saved_posts.html"

def get_valid_access_token():
    """Gets a valid access token, refreshing if necessary."""
    tokens = load_tokens_safe()
    if not tokens:
        console.print("❌ [bold red]No stored tokens found. Re-authenticating...[/bold red]")
        access_token = refresh_access_token_safe()
        if not access_token:
            console.print("❌ [bold red]Re-authentication failed. Exiting...[/bold red]")
            return None
        return access_token
    
    # Check if access token exists
    access_token = tokens.get("access_token")
    if not access_token:
        console.print("🔄 [yellow]No access token found, attempting to refresh...[/yellow]")
        access_token = refresh_access_token_safe()
        if not access_token:
            console.print("❌ [bold red]Failed to get access token. Manual re-authentication needed.[/bold red]")
            return None
        return access_token
    
    # Check if access token is expired (if timestamp exists)
    if "timestamp" in tokens:
        time_elapsed = time.time() - tokens["timestamp"]
        # Reddit access tokens typically expire after 3600 seconds (1 hour)
        if time_elapsed > 3300:  # 55 minutes buffer
            console.print("⏰ [yellow]Access token appears expired, refreshing...[/yellow]")
            access_token = refresh_access_token_safe()
            if not access_token:
                console.print("❌ [bold red]Failed to refresh expired token.[/bold red]")
                return None
            return access_token
    
    return access_token

def make_request(endpoint):
    """Makes an API request to Reddit, handling authentication and errors."""
    
    access_token = get_valid_access_token()
    if not access_token:
        return None
    
    headers = {"Authorization": f"Bearer {access_token}", "User-Agent": USER_AGENT}
    url = f"https://oauth.reddit.com{endpoint}"

    attempt = 0
    while attempt < 5:
        try:
            response = requests.get(url, headers=headers, timeout=30)
        except requests.exceptions.RequestException as e:
            console.print(f"❌ [bold red]Network error: {e}[/bold red]")
            attempt += 1
            if attempt < 5:
                exponential_backoff(attempt)
                continue
            return None

        if response.status_code == 401:
            console.print("🔄 [yellow]Access token expired, refreshing...[/yellow]")
            new_access_token = refresh_access_token_safe()
            if not new_access_token:
                console.print("❌ [bold red]Refresh token failed, manual re-authentication needed.[/bold red]")
                return None
            headers["Authorization"] = f"Bearer {new_access_token}"
            
            # Retry the request with new token
            try:
                response = requests.get(url, headers=headers, timeout=30)
            except requests.exceptions.RequestException as e:
                console.print(f"❌ [bold red]Network error on retry: {e}[/bold red]")
                return None

        if response.status_code == 200:
            try:
                return response.json()
            except json.JSONDecodeError:
                console.print(f"❌ [bold red]Invalid JSON response from Reddit API[/bold red]")
                return None

        elif response.status_code == 429:
            console.print("⚠️ [bold yellow]Rate limited. Retrying with backoff...[/bold yellow]")
            attempt += 1
            exponential_backoff(attempt)

        elif response.status_code == 403:
            console.print("❌ [bold red]Access forbidden. Check your Reddit app permissions and scopes.[/bold red]")
            return None

        elif response.status_code == 404:
            console.print("❌ [bold red]Reddit API endpoint not found. Check username and endpoint.[/bold red]")
            return None

        else:
            console.print(f"❌ [bold red]Error {response.status_code}: {response.reason}[/bold red]")
            console.print(f"❌ [bold red]Response: {response.text}[/bold red]")
            attempt += 1
            if attempt < 5:
                exponential_backoff(attempt)

    console.print("❌ [bold red]Max retry attempts reached.[/bold red]")
    return None

def fetch_saved_posts(format="json", force_fetch=False):
    """Fetch saved Reddit posts, using `after` for full fetch and `before` for incremental fetch.
    
    Args:
        format (str): Output format - "json" or "html"
        force_fetch (bool): If True, fetch all posts from scratch
    
    Returns:
        dict: A dictionary containing:
            - content: The actual posts (list for JSON, string for HTML)
            - count: Number of posts fetched
            - format: The format used ("json" or "html")
    """
    
    last_fetch_timestamp = None
    last_fetch_before = None
    fetch_mode = "before"  # Default fetch mode for incremental updates
    cursor_param = None  # Holds `after` or `before` value

    # Read last_fetch.json if it exists
    if os.path.exists(LAST_FETCH_FILE) and not force_fetch:
        try:
            with open(LAST_FETCH_FILE, "r", encoding="utf-8") as file:
                last_fetch_data = json.load(file)
                last_fetch_timestamp = last_fetch_data.get("last_fetch")
                last_fetch_before = last_fetch_data.get("before")
                cursor_param = last_fetch_before  # Start from the last known post
                console.print(f"📋 [bold blue]Incremental fetch from timestamp: {last_fetch_timestamp}[/bold blue]")
                console.print(f"📋 [bold blue]Starting from post ID: {last_fetch_before}[/bold blue]")
        except (json.JSONDecodeError, FileNotFoundError) as e:
            console.print(f"⚠️ [bold yellow]Could not read last_fetch.json: {e}. Starting fresh fetch.[/bold yellow]")

    # Use `after` for force fetch (fetch ALL saved posts)
    if force_fetch or not os.path.exists(LAST_FETCH_FILE):
        fetch_mode = "after"
        cursor_param = None  # Reset to fetch all data from the start
        console.print("🚀 [bold cyan]Force Fetch Activated: Fetching ALL saved posts using pagination.[/bold cyan]")

    new_posts = []
    page_count = 0
    total_processed = 0
    
    # Load existing posts to check for duplicates in incremental mode
    existing_post_ids = set()
    if not force_fetch and os.path.exists(OUTPUT_JSON):
        try:
            with open(OUTPUT_JSON, "r", encoding="utf-8") as file:
                existing_posts = json.load(file)
                existing_post_ids = {post["fullname"] for post in existing_posts}
                console.print(f"📋 [blue]Loaded {len(existing_post_ids)} existing post IDs for duplicate checking[/blue]")
        except (json.JSONDecodeError, FileNotFoundError) as e:
            console.print(f"⚠️ [yellow]Could not load existing posts for duplicate checking: {e}[/yellow]")
    
    while True:
        endpoint = f"/user/{REDDIT_USERNAME}/saved?limit=100"
        if cursor_param:
            endpoint += f"&{fetch_mode}={cursor_param}"  # Dynamically switch between `after` and `before`

        page_count += 1
        console.print(f"📡 [dim]Fetching page {page_count}...[/dim]")
        saved_posts = make_request(endpoint)
        
        if not saved_posts or "data" not in saved_posts:
            console.print(f"⚠️ [yellow]No data received from Reddit API on page {page_count}[/yellow]")
            break

        posts = saved_posts["data"].get("children", [])
        if not posts:
            console.print(f"✅ [green]No more posts available. Fetched {page_count - 1} pages total.[/green]")
            break  # No more posts available

        total_processed += len(posts)
        console.print(f"📄 [blue]Processing {len(posts)} posts from page {page_count}[/blue]")

        posts_found_this_page = 0
        duplicate_count = 0
        
        for post in posts:
            data = post["data"]
            post_id = data["name"]
            
            # For incremental fetch, stop if we've seen this post before
            if not force_fetch and post_id in existing_post_ids:
                duplicate_count += 1
                console.print(f"🔄 [dim]Found existing post: {post_id} - stopping incremental fetch[/dim]")
                # Don't break immediately, process any new posts in this batch first
                continue
            
            # Handle both posts and comments
            post_type = "post" if data.get("title") else "comment"
            
            if post_type == "post":
                new_posts.append({
                    "title": data.get("title", "No Title"),
                    "url": data.get("url", f"https://reddit.com{data.get('permalink', '#')}"),
                    "subreddit": data.get("subreddit"),
                    "created_utc": data.get("created_utc"),
                    "fullname": data["name"],  # Store Reddit's unique identifier
                    "type": "post",
                    "author": data.get("author", "[deleted]"),
                    "score": data.get("score", 0)
                })
            else:
                # Handle saved comments
                new_posts.append({
                    "title": f"Comment in: {data.get('link_title', 'Unknown Post')}",
                    "url": f"https://reddit.com{data.get('permalink', '#')}",
                    "subreddit": data.get("subreddit"),
                    "created_utc": data.get("created_utc"),
                    "fullname": data["name"],
                    "type": "comment",
                    "author": data.get("author", "[deleted]"),
                    "score": data.get("score", 0),
                    "body": data.get("body", "")[:200] + "..." if len(data.get("body", "")) > 200 else data.get("body", "")
                })
            
            posts_found_this_page += 1

        console.print(f"🆕 [green]Found {posts_found_this_page} new posts on this page[/green]")
        if duplicate_count > 0:
            console.print(f"🔄 [yellow]Found {duplicate_count} duplicate posts - stopping incremental fetch[/yellow]")
            
        # For incremental fetch, stop if we found duplicates (we've caught up)
        if not force_fetch and duplicate_count > 0:
            console.print(f"✅ [green]Incremental fetch complete. Processed {page_count} pages, found {len(new_posts)} new posts.[/green]")
            break

        # Move pagination cursor
        if fetch_mode == "after":
            cursor_param = posts[-1]["data"]["name"]  # Take LAST post for force fetch
        else:
            cursor_param = posts[0]["data"]["name"]  # Take FIRST post for incremental

        # Add a small delay to be nice to Reddit's servers
        time.sleep(0.5)

    console.print(f"📊 [bold blue]Total: Processed {total_processed} posts across {page_count} pages, found {len(new_posts)} new posts[/bold blue]")

    # **Store last fetched post details**
    if new_posts:
        last_fetched_value = new_posts[-1]["created_utc"] if fetch_mode == "after" else new_posts[0]["created_utc"]
        last_fetched_after = new_posts[-1]["fullname"] if fetch_mode == "after" else None
        last_fetched_before = new_posts[0]["fullname"] if fetch_mode == "before" else None

        try:
            with open(LAST_FETCH_FILE, "w", encoding="utf-8") as file:
                json.dump({
                    "last_fetch": last_fetched_value, 
                    "after": last_fetched_after, 
                    "before": last_fetched_before,
                    "timestamp": time.time(),
                    "total_fetched": len(new_posts)
                }, file, indent=2)

            console.print(f"📌 Last fetch timestamp updated: {last_fetched_value}", style="bold cyan")
            console.print(f"📌 Last fetch `after` updated: {last_fetched_after if last_fetched_after else 'N/A'}", style="bold cyan")
            console.print(f"📌 Last fetch `before` updated: {last_fetched_before if last_fetched_before else 'N/A'}", style="bold cyan")
        except Exception as e:
            console.print(f"⚠️ [yellow]Could not save last fetch data: {e}[/yellow]")

        # Load existing posts and merge
        existing_posts = []
        if os.path.exists(OUTPUT_JSON) and not force_fetch:
            try:
                with open(OUTPUT_JSON, "r", encoding="utf-8") as file:
                    existing_posts = json.load(file)
                console.print(f"📋 [blue]Loaded {len(existing_posts)} existing posts from storage[/blue]")
            except (json.JSONDecodeError, FileNotFoundError) as e:
                console.print(f"⚠️ [yellow]Could not load existing posts: {e}. Starting fresh.[/yellow]")
        
        # Combine and deduplicate posts
        combined_posts = new_posts + existing_posts  # Prepend new posts instead of appending
        unique_posts = {post["fullname"]: post for post in combined_posts}.values()  # Remove duplicates
        unique_posts_list = list(unique_posts)
        
        console.print(f"🔄 [green]Combined {len(new_posts)} new + {len(existing_posts)} existing = {len(unique_posts_list)} unique posts[/green]")

        # Always save JSON version for data integrity
        try:
            with open(OUTPUT_JSON, "w", encoding="utf-8") as file:
                json.dump(unique_posts_list, file, indent=2, ensure_ascii=False)
            console.print(f"💾 [green]Saved {len(unique_posts_list)} posts to {OUTPUT_JSON}[/green]")
        except Exception as e:
            console.print(f"❌ [red]Could not save JSON file: {e}[/red]")
        
        # Return based on requested format
        if format == "html":
            html_output = generate_html_output(unique_posts_list)
            return {
                "content": html_output,
                "count": len(new_posts),  # Return count of NEW posts, not total
                "format": "html"
            }
        else:  # JSON format
            return {
                "content": unique_posts_list,
                "count": len(new_posts),  # Return count of NEW posts, not total
                "format": "json"
            }
   
    console.print("ℹ️ [bold blue]No new posts found.[/bold blue]")
    
    # Return consistent structure even when no posts found
    if format == "html":
        return {
            "content": "<html><head><title>Saved Reddit Posts</title></head><body><p>No posts found.</p></body></html>",
            "count": 0,
            "format": "html"
        }
    else:
        return {
            "content": [],
            "count": 0,
            "format": "json"
        }

def generate_html_output(posts_list):
    """Generate HTML output from posts list."""
    html_parts = []
    
    # HTML header
    html_parts.append('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Saved Reddit Posts</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 20px; 
            background-color: #f5f5f5; 
            line-height: 1.6;
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            background: white; 
            padding: 20px; 
            border-radius: 8px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
        }
        h1 { 
            color: #ff4500; 
            text-align: center; 
            border-bottom: 2px solid #ff4500; 
            padding-bottom: 10px; 
            margin-bottom: 20px;
        }
        .post { 
            margin: 15px 0; 
            padding: 15px; 
            border: 1px solid #ddd; 
            border-radius: 5px; 
            background: #fafafa; 
        }
        .post-title { 
            font-weight: bold; 
            color: #333; 
            text-decoration: none; 
            font-size: 16px; 
            display: inline-block;
            margin-bottom: 5px;
        }
        .post-title:hover { 
            color: #ff4500; 
            text-decoration: underline; 
        }
        .post-meta { 
            color: #666; 
            font-size: 12px; 
            margin-top: 5px; 
        }
        .subreddit { 
            color: #ff4500; 
            font-weight: bold; 
        }
        .comment-body { 
            margin-top: 8px; 
            padding: 8px; 
            background: #fff; 
            border-left: 3px solid #ff4500; 
            font-style: italic; 
            border-radius: 3px;
        }
        .stats { 
            text-align: center; 
            margin: 20px 0; 
            padding: 15px; 
            background: #e3f2fd; 
            border-radius: 5px; 
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Saved Reddit Posts</h1>
        <div class="stats">
            Total Saved Items: ''' + str(len(posts_list)) + '''
        </div>''')

    for index, post in enumerate(posts_list, start=1):
        post_type = post.get("type", "post")
        author = post.get("author", "[deleted]")
        score = post.get("score", 0)
        subreddit = post.get("subreddit", "unknown")
        
        # Convert timestamp to readable date
        created_utc = post.get("created_utc", 0)
        if created_utc:
            try:
                from datetime import datetime
                date_str = datetime.fromtimestamp(created_utc).strftime("%Y-%m-%d %H:%M")
            except (ValueError, OSError):
                date_str = "Unknown date"
        else:
            date_str = "Unknown date"
        
        # Escape HTML characters in title and other content
        title = post.get('title', 'No Title').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
        url = post.get('url', '#').replace('"', '&quot;')
        
        html_parts.append(f'''
        <div class="post">
            <div>
                <strong>{index}.</strong>
                <a href="{url}" target="_blank" class="post-title">{title}</a>
            </div>
            <div class="post-meta">
                r/{subreddit} • u/{author} • {score} points • {date_str} • {post_type}
            </div>''')
        
        # Add comment body if it's a comment
        if post_type == "comment" and post.get("body"):
            comment_body = post.get("body", "").replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            html_parts.append(f'            <div class="comment-body">{comment_body}</div>')
        
        html_parts.append('        </div>')

    # Add footer
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    html_parts.append(f'''
        <div class="stats">
            Generated on: {current_time}
        </div>
    </div>
</body>
</html>''')

    return '\n'.join(html_parts)

def fetch_saved_posts_legacy(format="json", force_fetch=False):
    """Legacy function that returns just the content for backward compatibility.
    
    Returns:
        list or str: Posts data (list for JSON, HTML string for HTML)
    """
    result = fetch_saved_posts(format, force_fetch)
    return result["content"] if result else ([] if format == "json" else "")