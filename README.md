
# Reddit Saved Posts Fetcher

## 📌 Overview

This script fetches your **saved Reddit posts and comments** using the Reddit API with OAuth authentication. It supports exporting saved posts in **JSON** and **HTML bookmarks**, making it easy to archive and integrate with tools like **Linkwarden** and **Hoarder**.

### **Key Features**

- ✅ **Incremental Fetching** → Retrieves only new saved posts using `before` (incremental) or `after` (full fetch).
- ✅ **JSON-First Approach** → Data is always stored in JSON first, ensuring correct ordering.
- ✅ **Multiple Export Formats** → Supports **JSON and HTML bookmarks**.
- ✅ **Python Library Support** → Can be used as a function call in external programs.
- ✅ **Docker Support** → Easily deploy and run the fetcher in a containerized environment.
- ✅ **Force Fetch Mode** → Optionally re-fetch all saved posts using `--force-fetch`.

---

## 🔧 Installation & Setup

### **1️⃣ Clone the Repository**

```bash
git clone https://github.com/akashpandey/Reddit-Fetch.git
cd Reddit-Fetch
```

### **2️⃣ Install as a Python Package**

```bash
pip install -e .
```

### **3️⃣ Configure Reddit API Credentials**

1. Go to [Reddit Apps](https://www.reddit.com/prefs/apps) and create a **Web App**.
2. Set the **Redirect URI** to `http://localhost:8080`.
3. Copy the **Client ID** and **Client Secret**.

### **4️⃣ Create `.env` File**

```ini
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
REDIRECT_URI=http://localhost:8080
USER_AGENT=YourRedditApp/1.0 (by /u/your_username)
REDDIT_USERNAME=your_reddit_username
FETCH_INTERVAL=3600
FORCE_FETCH=false
```

---

## 🔑 Authentication & Token Handling

Run the following command to authenticate and generate `tokens.json`:

```bash
python generate_tokens.py
```

### **Handling Tokens in a Headless Server**

1. Run `generate_tokens.py` on a **system with a browser**.
2. Copy the `tokens.json` file to the **server or Docker volume**.
3. **For Docker users**, place `tokens.json` inside the `/data/` directory.

Tokens are **automatically refreshed** as needed.

---

## 🚀 Running the Script

### **Using CLI After Package Installation**

```bash
reddit-fetcher
```

- The CLI will prompt for format selection (`json` or `html`) and whether to force fetch.
- Runs interactively without requiring additional arguments.

### **Fetching New Saved Posts (Non-Interactive Mode)**

#### ✅ **Incremental Fetch (Recommended)**

```bash
python main.py --format json
```

```bash
python main.py --format html
```

- Uses **`before`** for **incremental fetching** (fetches only new posts).

#### ✅ **Force Fetch (Re-Fetch Everything)**

```bash
python main.py --format json --force-fetch
```

```bash
python main.py --format html --force-fetch
```

- Uses **`after`** for **full fetch** (fetches all saved posts from the beginning).

---

## 📂 Using as a Python Library

This script can be used as a **function call inside another Python program**.

### ✅ **Expected Return Type**

- Returns **a list of dictionaries**, where each entry contains:

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

### ✅ **Sample External Program Usage**

```python
from reddit_fetch.api import fetch_saved_posts

# Fetch saved posts as JSON
data = fetch_saved_posts(format="json", force_fetch=False)
print(f"Fetched {len(data)} saved posts")
```

---

## 🐳 Running in Docker

### **1️⃣ Build the Docker Image**

```bash
docker build -t reddit-fetcher .
```

### **2️⃣ Run the Container**

```bash
docker run --rm -e OUTPUT_FORMAT=json -e FORCE_FETCH=false -e FETCH_INTERVAL=3600 -v $(pwd)/data:/data reddit-fetcher
```

- JSON will be saved in `data/saved_posts.json`.
- HTML will be saved in `data/saved_posts.html` if `OUTPUT_FORMAT=html`.
- `FETCH_INTERVAL` controls how frequently the script runs in Docker.
- `FORCE_FETCH` can be set to `true` to fetch all saved posts from scratch.

### **3️⃣ Using Docker Compose**

If you prefer using `docker-compose`, create a `docker-compose.yml` file:

```yaml
version: '3.8'
services:
  reddit-fetcher:
    image: reddit-fetcher
    container_name: reddit-fetcher
    environment:
      - OUTPUT_FORMAT=json
      - FORCE_FETCH=false
      - FETCH_INTERVAL=3600
    volumes:
      - ./data:/data
    restart: unless-stopped
```

Run the container using:

```bash
docker-compose up -d
```

### **4️⃣ Handling `tokens.json` in Docker**

- If using Docker, **place `tokens.json` inside the `/data/` directory** before starting the container.
- Example:

```bash
cp tokens.json data/
```

---

## 🔍 Troubleshooting

### **1️⃣ Token Errors**

- If `tokens.json` is missing, **run `generate_tokens.py` again**.
- Ensure **Reddit API credentials** are correctly set in `.env`.
- If using Docker, **copy `tokens.json` to `/data/` before running the container**.

### **2️⃣ Fetching Issues**

- Ensure the correct **Reddit username** is set in `.env`.
- Check if you've hit **Reddit API rate limits**.

---

## 🔍 Future Enhancements

- **Advanced Filtering** (by subreddit, date, etc.).
- **RSS Feed Generation** for easier integration.
- **Direct API Integration with Linkwarden**.

---

💡 **Contributions & feedback are welcome!** 🚀
