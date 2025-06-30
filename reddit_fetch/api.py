import gspread
from google.oauth2 import service_account
import os
from rich.console import Console
from dotenv import load_dotenv
import json
import requests
from datetime import datetime
import praw
from reddit_fetch.auth import refresh_access_token_safe, load_tokens_safe, is_headless, show_headless_instructions # Import authentication functions

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

console = Console()

DATA_DIR = "data/"
OUTPUT_JSON = f"{DATA_DIR}saved_posts.json"

def export_to_google_sheet(posts_data: list[dict], spreadsheet_name: str) -> bool:
    """
    Exports a list of post data to a Google Sheet.

    Args:
        posts_data: A list of dictionaries, where each dictionary represents a post
                    and contains at least 'title', 'score', 'subreddit', 'permalink', 'url'.
        spreadsheet_name: The name of the Google Sheet to export to.

    Returns:
        True if the export was successful, False otherwise.
    """
    try:
        # Authenticate with Google Sheets using service account credentials
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not credentials_path or not os.path.exists(credentials_path):
            console.print(
                "[bold red]Erreur:[/bold red] Le chemin vers le fichier de credentials Google n'est pas défini "
                "ou le fichier n'existe pas. Vérifiez GOOGLE_APPLICATION_CREDENTIALS dans votre .env",
                style="bold red"
            )
            return False

        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = service_account.Credentials.from_service_account_file(credentials_path, scopes=scope)
        client = gspread.authorize(creds)

        # Open the spreadsheet by name
        try:
            spreadsheet = client.open(spreadsheet_name)
            console.print(f"[bold green]Succès:[/bold green] Feuille de calcul '{spreadsheet_name}' ouverte.")
        except gspread.SpreadsheetNotFound:
            console.print(
                f"[bold red]Erreur:[/bold red] La feuille de calcul '{spreadsheet_name}' n'a pas été trouvée. "
                "Veuillez la créer et la partager avec l'adresse e-mail de votre compte de service.",
                style="bold red"
            )
            return False
        except gspread.exceptions.APIError as e:
            if "The caller does not have permission" in str(e):
                console.print(
                    f"[bold red]Erreur de permission:[/bold red] Le compte de service n'a pas les permissions "
                    f"nécessaires pour accéder à la feuille '{spreadsheet_name}'. "
                    f"Assurez-vous de l'avoir partagée avec le compte de service en tant qu'éditeur.",
                    style="bold red"
                )
            else:
                console.print(f"[bold red]Erreur API Google Sheets:[/bold red] {e}", style="bold red")
            return False

        # Select the first worksheet
        worksheet = spreadsheet.get_worksheet(0)
        console.print("[bold green]Succès:[/bold green] Première feuille de travail sélectionnée.")

        # Clear existing content
        worksheet.clear()
        console.print("[bold green]Succès:[/bold green] Contenu existant de la feuille effacé.")

        # Define headers
        headers = ['Title', 'Score', 'Subreddit', 'Reddit Link', 'External URL', 'Date Saved', 'Self Text', 'Comments Count']
        worksheet.append_row(headers)
        console.print("[bold green]Succès:[/bold green] En-têtes ajoutés.")

        # Apply formatting to headers (bold)
        worksheet.format('1:1', {'textFormat': {'bold': True}})

        # Apply formatting to all cells (wrap text, top vertical alignment)
        # This applies to all cells from row 2 onwards (data rows)
        worksheet.format('A:H', {
            'wrapStrategy': 'WRAP',
            'verticalAlignment': 'TOP'
        })

        # Prepare data for insertion
        rows_to_insert = []

        for i, post in enumerate(posts_data):
            date_saved = post.get('date_saved', '')
            if isinstance(date_saved, (int, float)): # Assuming timestamp
                date_saved = datetime.fromtimestamp(date_saved).strftime('%Y-%m-%d %H:%M:%S')
            
            full_selftext = str(post.get('selftext', '')) # Ensure it's a string
            
            row = [
                post.get('title', ''),
                post.get('score', ''),
                post.get('subreddit', ''),
                post.get('permalink', ''),
                post.get('url', ''),
                date_saved,
                full_selftext, # Display full text directly
                post.get('num_comments', '')
            ]
            rows_to_insert.append(row)

        # Insert all data in one batch
        if rows_to_insert:
            worksheet.append_rows(rows_to_insert)
            console.print(f"[bold green]Succès:[/bold green] {len(rows_to_insert)} lignes de données insérées.")
        else:
            console.print("[bold yellow]Avertissement:[/bold yellow] Aucune donnée à insérer.")

        return True

    except Exception as e:
        console.print(f"[bold red]Une erreur inattendue est survenue:[/bold red] {e}", style="bold red")
        return False

def fetch_saved_posts(format: str = "json", force_fetch: bool = False) -> dict:
    """
    Fetches saved posts from Reddit and saves them in the specified format.

    Args:
        format: The desired output format ('json', 'html', 'google_sheet').
        force_fetch: If True, forces a new fetch regardless of existing data.

    Returns:
        A dictionary containing the fetched content, count, and format.
    """
    console.print(f"[bold blue]Fetching saved posts from Reddit...[/bold blue]")
    
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    user_agent = os.getenv("USER_AGENT")
    reddit_username = os.getenv("REDDIT_USERNAME")

    if not all([client_id, client_secret, user_agent, reddit_username]):
        console.print("[bold red]Erreur:[/bold red] Les variables d'environnement CLIENT_ID, CLIENT_SECRET, USER_AGENT, REDDIT_USERNAME doivent être définies dans .env pour l'authentification Reddit.", style="bold red")
        return {"content": [], "count": 0, "format": format}

    # Ensure we have a valid refresh token
    tokens = load_tokens_safe()
    if not tokens or "refresh_token" not in tokens:
        console.print("[bold red]Erreur:[/bold red] Jeton de rafraîchissement Reddit introuvable. Veuillez vous authentifier.", style="bold red")
        if is_headless():
            show_headless_instructions()
        return {"content": [], "count": 0, "format": format}

    refresh_token = tokens["refresh_token"]

    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
            username=reddit_username,
            refresh_token=refresh_token
        )
        
        posts_data = []
        for item in reddit.user.me().saved(limit=None):
            if isinstance(item, praw.models.Submission):
                posts_data.append({
                    'title': item.title,
                    'score': item.score,
                    'subreddit': item.subreddit.display_name,
                    'permalink': f"https://www.reddit.com{item.permalink}",
                    'url': item.url,
                    'date_saved': item.created_utc, # Unix timestamp
                    'selftext': item.selftext,
                    'num_comments': item.num_comments
                })
            elif isinstance(item, praw.models.Comment):
                # Handle saved comments as well, if desired
                posts_data.append({
                    'title': f"Comment on {item.submission.title}",
                    'score': item.score,
                    'subreddit': item.subreddit.display_name,
                    'permalink': f"https://www.reddit.com{item.permalink}",
                    'url': item.submission.url, # Link to the submission the comment is on
                    'date_saved': item.created_utc,
                    'selftext': item.body, # Comment body is selftext for comments
                    'num_comments': 'N/A' # Not applicable for a single comment
                })
        console.print(f"[bold green]Fetched {len(posts_data)} saved posts and comments from Reddit.[/bold green]")

        # Always save to JSON
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(posts_data, f, indent=4)
        console.print(f"[bold green]Saved {len(posts_data)} posts to {OUTPUT_JSON}.[/bold green]")

        if format == "google_sheet":
            spreadsheet_name = os.getenv("GOOGLE_SHEET_NAME")
            if not spreadsheet_name:
                console.print("[bold red]Erreur:[/bold red] GOOGLE_SHEET_NAME n'est pas défini dans .env. Impossible d'exporter vers Google Sheet.", style="bold red")
                return {"content": [], "count": 0, "format": format}
            
            success = export_to_google_sheet(posts_data, spreadsheet_name)
            if success:
                console.print("[bold green]Exportation vers Google Sheet terminée avec succès![/bold green]")
                return {"content": posts_data, "count": len(posts_data), "format": format}
            else:
                console.print("[bold red]Échec de l'exportation vers Google Sheet.[/bold red]")
                return {"content": [], "count": 0, "format": format}
        
        return {"content": posts_data, "count": len(posts_data), "format": format}

    except Exception as e:
        console.print(f"[bold red]Une erreur est survenue lors de la récupération des posts Reddit:[/bold red] {e}", style="bold red")
        return {"content": [], "count": 0, "format": format}