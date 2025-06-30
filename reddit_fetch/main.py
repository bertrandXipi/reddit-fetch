import os
import json
import sys
import argparse # Import argparse

import requests
from reddit_fetch.api import fetch_saved_posts, export_to_google_sheet, OUTPUT_JSON # Import OUTPUT_JSON
from reddit_fetch.auth import is_headless, is_docker, show_headless_instructions, load_tokens_safe
from reddit_fetch.config import TOKEN_FILE, GOOGLE_SHEET_NAME # Import GOOGLE_SHEET_NAME
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.panel import Panel
from rich.text import Text

console = Console()

DATA_DIR = "data/"
LAST_FETCH_FILE = f"{DATA_DIR}last_fetch.json"

def is_interactive():
    """Returns True if the script is running in an interactive terminal (TTY)"""
    try:
        return os.isatty(sys.stdin.fileno()) and os.isatty(sys.stdout.fileno())
    except:
        return False

def check_authentication():
    """Check if authentication is available and show appropriate messages."""
    tokens = load_tokens_safe()
    
    if not tokens:
        if is_headless():
            console.print("\n❌ [bold red]Authentication tokens not found![/bold red]")
            show_headless_instructions()
            
            if is_docker():
                console.print(Panel.fit(
                    Text.from_markup(
                        "[bold yellow]💡 QUICK DOCKER SETUP REMINDER:[/bold yellow]\n\n"
                        "1. Generate tokens on a browser system:\n"
                        "   [bold]python generate_tokens.py[/bold]\n\n"
                        "2. Copy tokens.json to your Docker data directory:\n"
                        "   [bold]cp tokens.json /path/to/data/[/bold]\n\n"
                        "3. Restart the container:\n"
                        "   [bold]docker restart reddit-fetcher[/bold]"
                    ),
                    title="🚀 Docker Setup",
                    border_style="blue"
                ))
            
            sys.exit(1)
        else:
            console.print("❌ [bold red]No authentication tokens found.[/bold red]")
            console.print("🔄 [yellow]Starting authentication process...[/yellow]")
            # On browser systems, the auth flow will handle token generation
            return False
    
    # Check if tokens are valid
    if "refresh_token" not in tokens:
        console.print("❌ [bold red]Invalid token file: missing refresh_token[/bold red]")
        if is_headless():
            show_headless_instructions()
            sys.exit(1)
        return False
    
    console.print("✅ [bold green]Authentication tokens found and loaded.[/bold green]")
    return True

def cli_entry():
    console.print("\n🚀 [bold cyan]Welcome to Reddit Saved Posts Fetcher![/bold cyan]", style="bold yellow")
    console.print("Fetch and save your Reddit saved posts easily.\n", style="italic green")

    parser = argparse.ArgumentParser(description="Fetch and export Reddit saved posts.")
    parser.add_argument(
        "--export-only",
        action="store_true",
        help="Export existing saved_posts.json to Google Sheet without fetching from Reddit."
    )
    args = parser.parse_args()

    # Show environment information
    is_docker_env = is_docker()
    is_headless_env = is_headless()
    
    # Determine if running in non-interactive mode based on environment variables
    # This is more robust for automated runs than checking TTY directly.
    env_output_format = os.getenv("OUTPUT_FORMAT")
    env_force_fetch = os.getenv("FORCE_FETCH")
    is_non_interactive_env = env_output_format is not None or env_force_fetch is not None

    console.print(f"🐳 Docker Environment: {'Yes' if is_docker_env else 'No'}", style="bold blue")
    console.print(f"🖥️  Headless System: {'Yes' if is_headless_env else 'No'}", style="bold blue")
    console.print(f"💬 Interactive Session: {'No' if is_non_interactive_env else 'Yes'}", style="bold magenta")
    
    # Check authentication before proceeding (only if not export-only)
    if not args.export_only:
        if not check_authentication():
            # If we're here, we're on a browser system but tokens are missing/invalid
            # The authentication will be handled by the API calls
            pass
    
    if args.export_only:
        console.print("🔄 [bold blue]Export-only mode activated. Reading from saved_posts.json...[/bold blue]")
        if not os.path.exists(OUTPUT_JSON):
            console.print(f"❌ [bold red]Error: {OUTPUT_JSON} not found. Cannot export without data.[/bold red]")
            sys.exit(1)
        
        try:
            with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
                posts_to_export = json.load(f)
            console.print(f"✅ [green]Loaded {len(posts_to_export)} posts from {OUTPUT_JSON}.[/green]")
            
            if not GOOGLE_SHEET_NAME:
                console.print("❌ [bold red]GOOGLE_SHEET_NAME is not set in .env. Cannot export to Google Sheet.[/bold red]")
                sys.exit(1)

            console.print(f"📡 [bold blue]Starting export to Google Sheet '{GOOGLE_SHEET_NAME}'[/bold blue]")
            success = export_to_google_sheet(posts_to_export, spreadsheet_name=GOOGLE_SHEET_NAME)
            
            if success:
                console.print("✅ [bold green]Export to Google Sheet completed successfully![/bold green]")
            else:
                console.print("❌ [bold red]Export to Google Sheet failed.[/bold red]")
            sys.exit(0)
            
        except json.JSONDecodeError as e:
            console.print(f"❌ [bold red]Error decoding {OUTPUT_JSON}: {e}. File might be corrupted.[/bold red]")
            sys.exit(1)
        except Exception as e:
            console.print(f"❌ [bold red]An unexpected error occurred during export: {e}[/bold red]")
            sys.exit(1)

    # Configure execution based on environment
    if is_docker_env or is_non_interactive_env:
        # Non-interactive mode - use environment variables
        format_choice = env_output_format if env_output_format else "json"
        force_fetch = env_force_fetch.lower() == "true" if env_force_fetch else False
        
        console.print(f"🔧 [bold blue]Non-interactive mode detected[/bold blue]")
        console.print(f"📄 Output format: [bold]{format_choice}[/bold]")
        console.print(f"🔄 Force fetch: [bold]{force_fetch}[/bold]")
    else:
        # Interactive mode - ask user for preferences
        try:
            format_choice = Prompt.ask("Select output format", choices=["json", "html", "google_sheet"], default="json")
            force_fetch = Confirm.ask("Do you want to force fetch all saved posts?", default=False)
        except KeyboardInterrupt:
            console.print("\n👋 [yellow]Operation cancelled by user.[/yellow]")
            sys.exit(0)
        except Exception as e:
            console.print(f"\n❌ [bold red]Error getting user input: {e}[/bold red]")
            console.print("🔧 [yellow]Falling back to default settings...[/yellow]")
            format_choice = "json"
            force_fetch = False

    # Handle force fetch
    if force_fetch and os.path.exists(LAST_FETCH_FILE):
        try:
            os.remove(LAST_FETCH_FILE)
            console.print("🔄 [yellow]Force fetch enabled. Deleting last fetch record...[/yellow]")
        except Exception as e:
            console.print(f"⚠️ [yellow]Could not delete last fetch file: {e}[/yellow]")
    
    # Attempt to fetch posts
    try:
        console.print(f"\n📡 [bold blue]Starting to fetch saved posts...[/bold blue]")
        result = fetch_saved_posts(format=format_choice, force_fetch=force_fetch)
        
        if not result or result["count"] == 0:
            console.print("ℹ️ [bold blue]No posts were fetched. This could mean:[/bold blue]")
            console.print("   • No new posts since last fetch")
            console.print("   • No saved posts in your Reddit account")
            console.print("   • Authentication or API issues")
            return
        
        # Extract data from result
        posts_content = result["content"]
        posts_count = result["count"]
        result_format = result["format"]
        
        # If the format is google_sheet, the export is already handled by fetch_saved_posts
        if result_format == "google_sheet":
            console.print(f"\n✅ [bold green]Export to Google Sheet completed via fetch process.[/bold green]")
            return

        # Save the output for json/html
        output_file = f"{DATA_DIR}saved_posts.{result_format}"
        
        with open(output_file, "w", encoding="utf-8") as file:
            if result_format == "json":
                json.dump(posts_content, file, indent=4)
            else:
                file.write(posts_content)
        
        console.print(f"\n✅ [bold green]Successfully fetched {posts_count} posts![/bold green]")
        console.print(f"💾 Output saved to [bold green]{output_file}[/bold green]")
        
        if is_docker_env:
            console.print(f"🐳 [bold blue]File available in your mounted data directory[/bold blue]")
    
    except KeyboardInterrupt:
        console.print("\n👋 [yellow]Operation cancelled by user.[/yellow]")
        sys.exit(0)
    except PermissionError as e:
        console.print(f"\n❌ [bold red]Permission error: {e}[/bold red]")
        console.print("🔧 [yellow]Check file permissions for the output directory.[/yellow]")
        sys.exit(1)
    except FileNotFoundError as e:
        console.print(f"\n❌ [bold red]File not found: {e}[/bold red]")
        console.print("🔧 [yellow]Check that all required files exist.[/yellow]")
        sys.exit(1)
    except json.JSONDecodeError as e:
        console.print(f"\n❌ [bold red]JSON parsing error: {e}[/bold red]")
        console.print("🔧 [yellow]There may be corrupted data files. Try using --force-fetch.[/yellow]")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        console.print(f"\n❌ [bold red]Network error: {e}[/bold red]")
        console.print("🔧 [yellow]Check your internet connection and try again.[/yellow]")
        sys.exit(1)
    except (AttributeError, KeyError, TypeError) as e:
        if "access_token" in str(e) or "refresh_token" in str(e) or "401" in str(e) or "403" in str(e):
            # This looks like an authentication error
            console.print(f"\n❌ [bold red]Authentication error: {e}[/bold red]")
            if is_headless_env:
                console.print("🔧 [yellow]Authentication failed in headless environment.[/yellow]")
                show_headless_instructions()
            else:
                console.print("🔧 [yellow]Try running the authentication process again.[/yellow]")
        else:
            # This is likely a code/data structure error
            console.print(f"\n❌ [bold red]Data processing error: {e}[/bold red]")
            console.print("🔧 [blue]This may be a bug. Please check the error details above.[/blue]")
            console.print("💡 [blue]You can try using --force-fetch to start fresh.[/blue]")
        sys.exit(1)
    except Exception as e:
        # Generic error handling with better context
        error_str = str(e).lower()
        console.print(f"\n❌ [bold red]Unexpected error: {e}[/bold red]")
        
        if any(auth_keyword in error_str for auth_keyword in ['token', 'auth', '401', '403', 'unauthorized', 'forbidden']):
            # Likely authentication related
            console.print("🔧 [yellow]This appears to be an authentication issue.[/yellow]")
            if is_headless_env:
                show_headless_instructions()
            else:
                console.print("🔧 [yellow]Try regenerating your authentication tokens.[/yellow]")
        elif any(network_keyword in error_str for network_keyword in ['connection', 'timeout', 'network', 'dns']):
            # Likely network related
            console.print("🔧 [yellow]This appears to be a network connectivity issue.[/yellow]")
            console.print("💡 [blue]Check your internet connection and try again.[/blue]")
        else:
            # Unknown error
            console.print("🔧 [yellow]This may be a bug or unexpected condition.[/yellow]")
            console.print("💡 [blue]Please report this issue with the error details above.[/blue]")
        
        sys.exit(1)

def main():
    """Main entry point for the CLI."""
    try:
        cli_entry()
    except Exception as e:
        console.print(f"\n💥 [bold red]Unexpected error: {e}[/bold red]")
        console.print("🐛 [yellow]Please report this issue if it persists.[/yellow]")
        sys.exit(1)

if __name__ == "__main__":
    console.print("🟢 Script reached __main__, calling cli_entry()", style="bold magenta")
    cli_entry()
