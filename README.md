
# Reddit Saved Posts Fetcher

## 📌 Overview

This package fetches your **saved Reddit posts and comments** using the Reddit API with OAuth authentication. It supports exporting saved posts in **JSON** or **HTML bookmarks**, making it easy to archive and integrate with tools like [**Linkwarden**](https://github.com/linkwarden/linkwarden) and [**Hoarder**](https://github.com/hoarder-app/hoarder).

### **Key Features**

- **Python Package Support**: Can be used as a library in Python scripts.
- **Delta Fetching**: Retrieves only new saved posts, avoiding duplication.
- **Multiple Export Formats**: Supports **JSON** and **HTML bookmarks**.
- **Automation-Friendly**: Can be scheduled to run at intervals.
- **Integration Support**: Compatible with [**Linkwarden**](https://github.com/linkwarden/linkwarden) and [**Hoarder**](https://github.com/hoarder-app/hoarder).
- **Force Fetching**: Optionally re-fetch all saved posts.

---

## 🔧 Setup & Installation

### **1️⃣ Clone the Repository**

```bash
git clone https://github.com/akashpandey/Reddit-Fetch.git
cd Reddit-Fetch
```

### **2️⃣ Install the Package Locally**

Ensure **Python 3.x** is installed, then install the package:

```bash
pip install -e .
```

### **3️⃣ Configure Reddit API Credentials**

1. Go to [Reddit Apps](https://www.reddit.com/prefs/apps) and create a **Web App**.
2. Set the **Redirect URI** to `http://localhost:8080`.
3. Copy the **Client ID** and **Client Secret**.

### **4️⃣ Create `.env` File**

Create a `.env` file in the project directory and add your credentials:

```ini
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
REDIRECT_URI=http://localhost:8080
USER_AGENT=YourRedditApp/1.0 (by /u/your_username)
REDDIT_USERNAME=your_reddit_username
```

---

## 🔑 Authentication & Token Handling

### **1️⃣ Generate Authentication Tokens (With Browser)**

Run the following command to authenticate with Reddit and generate `tokens.json`:

```bash
python generate_tokens.py
```

### **2️⃣ Running on a Headless Server (Without a Browser)**

If running on a server without a browser:

1. Run `generate_tokens.py` **on a desktop machine** to authenticate.
2. Copy the generated `tokens.json` to the server:
   ```bash
   scp tokens.json user@your-server:/path/to/Reddit-Fetch/
   ```
3. Run the script normally on the headless system.

### **3️⃣ Handling Token Expiration**

- Access tokens expire every **1 hour**, but they **refresh automatically**.
- If the refresh token becomes invalid, rerun `generate_tokens.py` and **replace `tokens.json`**.

---

## 🚀 Running the Script (CLI Usage)

### **Fetching New Saved Posts**

To fetch new saved posts and export as **JSON**:

```bash
reddit-fetcher --format json
```

#### **Sample JSON Output:**

```json
[
    {
        "type": "post",
        "title": "Interesting Reddit Post",
        "url": "https://www.reddit.com/r/python/comments/xyz",
        "subreddit": "python",
        "created_utc": 1714567890
    },
    {
        "type": "comment",
        "body": "This is a saved comment.",
        "url": "https://www.reddit.com/r/learnprogramming/comments/abc",
        "subreddit": "learnprogramming",
        "created_utc": 1714567891
    }
]
```

To export saved posts as **HTML bookmarks**:

```bash
reddit-fetcher --format html
```

#### **Sample HTML Output:**

```html
<html>
<head><title>Reddit Saved Posts</title></head>
<body>
<h1>Saved Posts</h1>
<ul>
    <li>1. <a href="https://www.reddit.com/r/python/comments/xyz">Interesting Reddit Post</a></li>
    <li>2. <a href="https://www.reddit.com/r/learnprogramming/comments/abc">This is a saved comment.</a></li>
</ul>
</body>
</html>
```

### **Force Fetch All Posts**

If you want to **re-fetch all saved posts**, use:

```bash
reddit-fetcher --format json --force-fetch
```

OR

```bash
reddit-fetcher --format html --force-fetch
```

This ignores `last_fetch.json` and retrieves all posts from Reddit.

---

## 📚 Using as a Python Library

The package can also be used within Python scripts:

```python
from reddit_fetch import fetch_saved_posts

# Fetch saved posts as JSON
posts = fetch_saved_posts(format="json", force_fetch=True)
print(posts)
```

This allows integration with other Python projects and custom automation.

---

## 📂 Data Storage

| File                 | Purpose                                           |
| -------------------- | ------------------------------------------------- |
| `tokens.json`      | Stores authentication tokens                      |
| `saved_posts.json` | Contains fetched posts and comments               |
| `bookmarks.html`   | HTML-formatted bookmarks for Linkwarden & Hoarder |
| `last_fetch.json`  | Tracks last fetch timestamp                       |

---

## 🛠️ Advanced Features

- **Python Package Support**: Import the package and use it in Python scripts.
- **Delta Fetching**: Avoids duplicate retrieval using timestamps.
- **Automated Execution**: Schedule via **cron jobs** or **Windows Task Scheduler**.
- **Headless Server Support**: Runs on cloud servers or Raspberry Pi.
- **Bookmark Manager Integration**: Direct import into **[Linkwarden](https://github.com/linkwarden/linkwarden)** and **[Hoarder](https://github.com/hoarder-app/hoarder)**.

---

## 🔍 Troubleshooting

### **1️⃣ Token Errors**

- If `tokens.json` is missing or corrupted, **delete it** and rerun `generate_tokens.py`.
- Ensure the correct **Reddit API credentials** are set in `.env`.

### **2️⃣ Fetching Issues**

- Make sure your **Reddit username** is correctly set in `config.py`.
- Check if you've hit **Reddit API rate limits**.

---

## 📌 Future Enhancements

- **Direct API integration with Linkwarden**.
- **RSS Feed Generation for Hoarder**.
- **Content summarization using AI**.
- **Improved retry mechanisms for API errors**.
- **Docker Support**.

---

💡 **Contributions & feedback are welcome!** 🚀
