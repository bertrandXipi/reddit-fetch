from reddit_fetch.auth import load_tokens, get_new_tokens, refresh_access_token
from reddit_fetch.api import make_request
from reddit_fetch.config import REDDIT_USERNAME
import json
import argparse
import os
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.progress import track

console = Console()

DEFAULT_OUTPUT_FILE = "saved_posts"

def fetch_saved_posts(format="json", force_fetch=False):
    """
    Fetch saved Reddit posts and return them as structured data.
    
    :param format: Output format ("json" or "html"). Default is "json".
    :param force_fetch: If True, fetches all saved posts ignoring last fetch timestamp.
    :return: List of saved posts (JSON structure if format="json", HTML string if format="html").
    """
    tokens = load_tokens() or get_new_tokens()
    if not tokens:
        raise Exception("Authentication failed. Please check your credentials.")
    
    console.print("📡 Fetching saved Reddit posts...", style="bold blue")

    all_posts = []
    after = None

    while True:
        endpoint = f"/user/{REDDIT_USERNAME}/saved?limit=100"
        if after:
            endpoint += f"&after={after}"
        
        saved_posts = make_request(endpoint)
        if not saved_posts or "data" not in saved_posts:
            break

        posts = saved_posts["data"].get("children", [])
        all_posts.extend(posts)

        after = saved_posts["data"].get("after")  # Get the next batch cursor
        if not after:  # Stop when there's no more data
            break

    if format == "json":
        cleaned_posts = []
        for post in track(all_posts, description="Processing posts..."):
            data = post["data"]
            post_type = "post" if post["kind"] == "t3" else "comment"
            cleaned_post = {
                "type": post_type,
                "title": data.get("title") if post_type == "post" else None,
                "body": data.get("body") if post_type == "comment" else data.get("selftext", None),
                "url": data.get("url", "#") if post_type == "post" else data.get("permalink", "#"),
                "subreddit": data.get("subreddit"),
                "created_utc": data.get("created_utc")
            }
            cleaned_posts.append(cleaned_post)
        return cleaned_posts
    
    elif format == "html":
        html_output = "<html><head><title>Reddit Saved Posts</title></head><body><h1>Saved Posts</h1><ul>"
        for index, post in enumerate(all_posts, start=1):
            data = post["data"]
            title = data.get("title", "No Title")
            url = data.get("url", "#")
            html_output += f'<li>{index}. <a href="{url}">{title}</a></li>'
        html_output += "</ul></body></html>"
        return html_output

def cli_entry():
    """
    CLI entry point for `reddit-fetcher` command.
    """
    console.print("\n🚀 [bold cyan]Welcome to Reddit Saved Posts Fetcher![/bold cyan]", style="bold yellow")
    console.print("Fetch and save your Reddit saved posts easily.\n", style="italic green")
    
    format_choice = Prompt.ask("Select output format", choices=["json", "html"], default="json")
    force_fetch = Confirm.ask("Do you want to force fetch all saved posts?", default=False)
    output_file = Prompt.ask("Enter output file name (press Enter to use default)", default=f"{DEFAULT_OUTPUT_FILE}.{format_choice}")
    
    posts = fetch_saved_posts(format=format_choice, force_fetch=force_fetch)
    
    if os.path.exists(output_file):
        overwrite = Confirm.ask(f"⚠️ File '{output_file}' already exists. Overwrite?", default=False)
        if not overwrite:
            console.print("❌ Operation cancelled.", style="bold red")
            return
    
    with open(output_file, "w", encoding="utf-8") as file:
        if format_choice == "json":
            json.dump(posts, file, indent=4)
        else:
            file.write(posts)
    
    console.print(f"✅ Output saved to [bold green]{output_file}[/bold green]", style="bold yellow")

if __name__ == "__main__":
    cli_entry()
