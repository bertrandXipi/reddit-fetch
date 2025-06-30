import os
import time
from dotenv import load_dotenv

# Load environment variables from the project root
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))

# Reddit API credentials
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")  # Must match the Reddit App settings
USER_AGENT = os.getenv("USER_AGENT")  # Fetch dynamically
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME")  # Fetch dynamically
TOKEN_FILE = "/data/tokens.json" if os.getenv("DOCKER", "0") == "1" else "tokens.json"

# Google Sheets API credentials
# IMPORTANT: Replace with the actual path to your service account key JSON file
GOOGLE_SERVICE_ACCOUNT_KEY_PATH = os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY_PATH")
print(f"DEBUG: GOOGLE_SERVICE_ACCOUNT_KEY_PATH = {GOOGLE_SERVICE_ACCOUNT_KEY_PATH}")
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "Reddit Saved Posts") # Default name if not set

def exponential_backoff(attempt, base_delay=1.0, max_delay=16.0):
    """Implements exponential backoff to avoid rate limiting."""
    delay = min(base_delay * (2 ** attempt), max_delay)
    time.sleep(delay)
