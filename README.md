# Reddit Saved Posts Fetcher

Automatically fetch and export your saved Reddit posts and comments to JSON or HTML format.

## Features

- **Incremental Sync**: Only fetches new posts since the last run.
- **Force Fetch**: Option to re-download all saved posts from scratch.
- **Multiple Formats**: Export to JSON or a beautiful, self-contained HTML file.
- **Smart Authentication**: Handles token generation and refresh automatically.

---

## Requirements

- Python 3.8+
- Pip (Python package installer)

---

## Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/Reddit-Fetch.git
    cd Reddit-Fetch
    ```

2.  **Install dependencies:**
    ```bash
    pip install -e .
    ```
    This command installs the necessary packages and makes the `reddit-fetcher` command available.

---

## Configuration

1.  **Get Reddit API Credentials:**
    - Go to [Reddit Apps](https://www.reddit.com/prefs/apps).
    - Click **"Create App"** or **"Create Another App"**.
    - Fill out the form:
        - **Name**: `My Reddit Fetcher` (or any name)
        - **App type**: Select **"web app"**.
        - **Redirect URI**: `http://localhost:8080`
    - Click **"Create app"**.
    - Copy your **Client ID** (under the app name) and **Client Secret**.

2.  **Create the `.env` file:**
    - In the root of the `Reddit-Fetch` directory, create a file named `.env`.
    - Add your credentials to it like this:

    ```ini
    CLIENT_ID=your_client_id_here
    CLIENT_SECRET=your_client_secret_here
    REDIRECT_URI=http://localhost:8080
    USER_AGENT=RedditFetcher/1.0 (by /u/your_reddit_username)
    REDDIT_USERNAME=your_reddit_username
    ```

---

## How to Use

1.  **Generate Authentication Tokens:**
    - Run the following command in your terminal:
    ```bash
    python -m reddit_fetch.generate_tokens
    ```
    - This will open a browser window asking you to authorize the application.
    - After authorization, a `tokens.json` file will be created in the `data/` directory. This file stores your authentication tokens securely.

2.  **Fetch Your Saved Posts:**
    - Simply run the main command:
    ```bash
    reddit-fetcher
    ```
    - The script will run in interactive mode, asking you for the desired output format and whether to perform a force fetch.

### Non-Interactive Mode

You can also run the script with environment variables for non-interactive use:

```bash
# Example: Fetch in JSON format without forcing a full re-download
OUTPUT_FORMAT=json FORCE_FETCH=false reddit-fetcher
```

---

## Output Files

All output files are stored in the `data/` directory, which is created automatically.

-   **`tokens.json`**: Stores your authentication tokens.
-   **`last_fetch.json`**: Keeps track of the last fetched post to allow for incremental updates.
-   **`saved_posts.json`**: The output file containing your saved posts in JSON format.
-   **`saved_posts.html`**: The output file in HTML format, creating a clean, searchable, and offline-ready webpage of your posts.

### HTML Output Preview:

The HTML format creates a clean, Reddit-inspired webpage with your saved posts:

<div style="border: 2px solid #ddd; border-radius: 8px; padding: 10px; background: #f9f9f9; margin: 10px 0;">

**Preview of saved_posts.html:**
![image](https://github.com/user-attachments/assets/e49bbb7f-6aac-4fb7-9262-9d10c04f7da8)
</div>

---

## Troubleshooting

-   **`No authentication tokens found`**: Make sure you have run `python -m reddit_fetch.generate_tokens` successfully and that `data/tokens.json` exists.
-   **`Failed to refresh access token`**: Your tokens might have expired or been revoked. Delete `data/tokens.json` and regenerate them.
-   **`Permission denied`**: Ensure you have write permissions in the project directory, as the script needs to create the `data/` folder and its files.

---

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## License

MIT License - see the LICENSE file for details.