import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Reddit API credentials
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8080"  # Must match Reddit App
USER_AGENT = "MyRedditScript/1.0 (by /u/GeekIsTheNewSexy)"
