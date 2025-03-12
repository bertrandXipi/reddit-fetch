import requests
from reddit_fetch.auth import refresh_access_token_safe, load_tokens_safe, get_new_tokens
from reddit_fetch.config import USER_AGENT, REDDIT_USERNAME, exponential_backoff
from rich.console import Console

console = Console()

def make_request(endpoint):
    """Makes an API request to Reddit, handling authentication and errors."""
    
    tokens = load_tokens_safe()
    if not tokens:
        console.print("❌ [bold red]No stored tokens found. Re-authenticating...[/bold red]")
        tokens = get_new_tokens()
        if not tokens:
            console.print("❌ [bold red]Re-authentication failed. Exiting...[/bold red]")
            return None
    
    access_token = tokens.get("access_token")
    headers = {"Authorization": f"Bearer {access_token}", "User-Agent": USER_AGENT}
    url = f"https://oauth.reddit.com{endpoint}"

    attempt = 0
    while attempt < 5:
        response = requests.get(url, headers=headers)

        if response.status_code == 401:  # Token expired
            console.print("🔄 [yellow]Access token expired, refreshing...[/yellow]")
            new_access_token = refresh_access_token_safe()

            if not new_access_token:
                console.print("❌ [bold red]Refresh token failed, re-authenticating...[/bold red]")
                tokens = get_new_tokens()
                if not tokens:
                    console.print("❌ [bold red]Re-authentication failed. Exiting...[/bold red]")
                    return None
                access_token = tokens.get("access_token")
            else:
                access_token = new_access_token

            headers["Authorization"] = f"Bearer {access_token}"
            response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return response.json()

        elif response.status_code == 429:  # Rate limit hit
            console.print("⚠️ [bold yellow]Rate limited. Retrying with backoff...[/bold yellow]")
            attempt += 1
            exponential_backoff(attempt)

        else:
            console.print(f"❌ [bold red]Error: {response.status_code} - {response.text}[/bold red]")
            return None

    return None
