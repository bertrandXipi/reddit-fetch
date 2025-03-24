# Reddit Saved Posts Fetcher

## Overview

This script fetches your **saved Reddit posts and comments** using the Reddit API with OAuth authentication. It supports exporting saved posts in **JSON** and **HTML bookmarks**, making it easy to archive and integrate with tools like [**Linkwarden**](https://github.com/linkwarden/linkwarden) and [**Hoarder**](https://github.com/hoarder-app/hoarder).

### Key Features

- **Incremental Fetching** – Retrieves only new saved posts using `before` (incremental) or `after` (full fetch).
- **JSON-First Approach** – Data is always stored in JSON first, ensuring correct ordering.
- **Multiple Export Formats** – Supports **JSON and HTML bookmarks**.
- **Python Library Support** – Can be used as a function call in external programs.
- **Docker Support** – Easily deploy and run the fetcher in a containerized environment.
- **Force Fetch Mode** – Optionally re-fetch all saved posts using `--force-fetch`.
- **Deduplication Mechanism** – Ensures unique entries using the `fullname` identifier.

---

## Installation & Setup

### 1. Running Locally (Browser-Based Systems)
If you are using only a **browser-based system** and do not need Docker or a headless setup, follow these steps:

1. **Clone the repository**
   ```bash
   git clone https://github.com/akashpandey/Reddit-Fetch.git
   cd Reddit-Fetch
   ```

2. **Install as a Python package**
   ```bash
   pip install -e .
   ```

3. **Get Reddit API Credentials**
   - Go to [https://www.reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
   - Click **Create App** or **Create Another App**.
   - Select **Web App**.
   - Fill in:
     - **Name**: Choose any app name.
     - **Redirect URI**: Use `http://localhost:8080`
   - After creation, copy the **Client ID** (just below the app name) and **Client Secret**.

4. **Create a `.env` file**
   ```ini
   CLIENT_ID=your_client_id
   CLIENT_SECRET=your_client_secret
   REDIRECT_URI=http://localhost:8080
   USER_AGENT=YourRedditApp/1.0 (by /u/your_username)
   REDDIT_USERNAME=your_reddit_username
   FETCH_INTERVAL=3600
   FORCE_FETCH=false
   ```

5. **Generate authentication tokens**
   ```bash
   python generate_tokens.py
   ```
   This will create `tokens.json` **inside the cloned repo**.

6. **Run the script**
   ```bash
   reddit-fetcher
   ```

✔️ No need to copy `tokens.json` anywhere – everything runs on the same machine.

---

### 2. Running on Both Browser and Headless Systems
If you need to run the fetcher on a headless system, follow these additional steps:

1. Clone the repository on **both** systems:
   ```bash
   git clone https://github.com/akashpandey/Reddit-Fetch.git
   cd Reddit-Fetch
   ```

2. Follow **Steps 2–5** above on the **browser-based system** to generate `tokens.json`.

3. **Copy `tokens.json` to the headless system**:
   ```bash
   scp tokens.json user@headless-server:/path/to/Reddit-Fetch/
   ```

4. On the headless system, run the script:
   ```bash
   reddit-fetcher
   ```

✔️ No need for `.env` on the headless system—just copy `tokens.json`!

---

## Authentication & Token Handling

### For Docker-Based Execution
- Generate `tokens.json` on a browser-based system (see above).
- Place `tokens.json` inside `/data/` before starting the container.

```bash
cp tokens.json data/
docker run -v $(pwd)/data:/data pandeyak/reddit-fetcher:latest
```

---

## Running the Script

### Execution Methods Overview

| Method                        | Command                                                                 | Best For               |
|------------------------------|-------------------------------------------------------------------------|------------------------|
| CLI (Interactive)            | `reddit-fetcher`                                                        | Manual use             |
| Python Function              | `fetch_saved_posts(format="json")`                                    | Integration in code    |
| Docker (Prebuilt Image)      | `docker run -e OUTPUT_FORMAT=json -v $(pwd)/data:/data pandeyak/reddit-fetcher:latest` | Quick deployment       |
| Docker (Built from Source)   | `docker run -e OUTPUT_FORMAT=json -v $(pwd)/data:/data reddit-fetcher` | Custom modifications   |

### Force Fetch (Re-Fetch Everything)

```bash
reddit-fetcher --force-fetch
```

---

## Using as a Python Library

### Expected Return Type
Returns a list of dictionaries, where each entry contains:

```json
[
    {
        "title": "Post Title",
        "url": "https://reddit.com/r/example",
        "subreddit": "example",
        "created_utc": 1700000000,
        "fullname": "t3_xxxxxx"
    }
]
```

### Sample External Program Usage
```python
from reddit_fetch.api import fetch_saved_posts

data = fetch_saved_posts(format="json", force_fetch=False)
print(f"Fetched {len(data)} saved posts")
```

---

## Running in Docker

### Using the Prebuilt Docker Image
```bash
docker run --rm -e OUTPUT_FORMAT=json -e FETCH_INTERVAL=3600 -v $(pwd)/data:/data pandeyak/reddit-fetcher:latest
```

### Building Docker Image from Source
```bash
docker build -t reddit-fetcher .
```

### Running Locally with the Built Image
```bash
docker run --rm -e OUTPUT_FORMAT=json -e FETCH_INTERVAL=3600 -v $(pwd)/data:/data reddit-fetcher
```

### Using Docker Compose
```yaml
version: '3.8'
services:
  reddit-fetcher:
    image: pandeyak/reddit-fetcher:latest  # Use prebuilt image
    container_name: reddit-fetcher
    environment:
      - OUTPUT_FORMAT=json
      - FORCE_FETCH=false
      - FETCH_INTERVAL=3600
    volumes:
      - ./data:/data
    restart: unless-stopped
```
For a locally built image, replace `pandeyak/reddit-fetcher:latest` with `reddit-fetcher`.

---

## Troubleshooting

### Token Errors
- If `tokens.json` is missing, run `generate_tokens.py` again.
- Ensure Reddit API credentials are correctly set in `.env`.
- If using Docker, copy `tokens.json` to `/data/` before running the container.

### Fetching Issues
- Ensure the correct Reddit username is set in `.env`.
- Check if you've hit Reddit API rate limits.

---

## Future Enhancements

- Advanced Filtering (by subreddit, date, etc.)
- RSS Feed Generation for easier integration
- Direct API Integration with Linkwarden

---

**Contributions & feedback are welcome!**

