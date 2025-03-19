import os
import json
import sys
from reddit_fetch.api import fetch_saved_posts
from rich.console import Console
from rich.prompt import Confirm, Prompt

console = Console()

DATA_DIR = "/data/" if os.getenv("DOCKER", "0") == "1" else "./"
LAST_FETCH_FILE = f"{DATA_DIR}last_fetch.json"

def is_interactive():
    """Returns True if the script is running in an interactive terminal (TTY)"""
    try:
        return os.isatty(sys.stdin.fileno()) and os.isatty(sys.stdout.fileno())
    except:
        return False

def cli_entry():
    console.print("\n🚀 [bold cyan]Welcome to Reddit Saved Posts Fetcher![/bold cyan]", style="bold yellow")
    console.print("Fetch and save your Reddit saved posts easily.\n", style="italic green")

    # Detect if running inside Docker or a non-interactive session
    is_docker = os.getenv("DOCKER", "0") == "1"
    is_non_interactive = not is_interactive()
    console.print(f"🔍 Running inside Docker: {'Yes' if is_docker else 'No'}", style="bold blue")
    console.print(f"🖥️ Interactive Session: {'Yes' if not is_non_interactive else 'No'}", style="bold magenta")

    # Automatically set values if running in a non-interactive environment
    if is_docker or is_non_interactive:
        format_choice = os.getenv("OUTPUT_FORMAT", "json")
        force_fetch = os.getenv("FORCE_FETCH", "false").lower() == "true"
    else:
        format_choice = Prompt.ask("Select output format", choices=["json", "html"], default="json")
        force_fetch = Confirm.ask("Do you want to force fetch all saved posts?", default=False)

    # Ensure last_fetch.json is considered
    if force_fetch and os.path.exists(LAST_FETCH_FILE):
        os.remove(LAST_FETCH_FILE)
        console.print("🔄 [yellow]Force fetch enabled. Deleting last fetch record...[/yellow]")
    
    output_file = f"{DATA_DIR}saved_posts.{format_choice}"
    posts = fetch_saved_posts(format=format_choice, force_fetch=force_fetch)
    with open(output_file, "w", encoding="utf-8") as file:
        if format_choice == "json":
            json.dump(posts, file, indent=4)
        else:
            file.write(posts)
    
    console.print(f"✅ Output saved to [bold green]{output_file}[/bold green]", style="bold yellow")
    


if __name__ == "__main__":
    console.print("🟢 Script reached __main__, calling cli_entry()", style="bold magenta")
    cli_entry()
