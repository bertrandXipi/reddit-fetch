
# Reddit Saved Posts Fetcher

## 📌 Overview

This script fetches your **saved Reddit posts and comments** using the Reddit API with OAuth authentication. It supports exporting saved posts in **plain text** or **HTML bookmarks**, making it easy to archive and integrate with tools like [**Linkwarden**](https://github.com/linkwarden/linkwarden) and [**Hoarder**](https://github.com/hoarder-app/hoarder).

### **Key Features**

- **Delta Fetching**: Retrieves only new saved posts, avoiding duplication.
- **Multiple Export Formats**: Supports **plain text** and **HTML bookmarks**.
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

### **2️⃣ Install Dependencies**

Ensure **Python 3.x** is installed, then install required packages:

```bash
pip install -r requirements.txt
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

### **1️⃣ Generate Authentication Tokens**

Run the following command to authenticate with Reddit and generate `tokens.json`:

```bash
python generate_tokens.py
```

### **2️⃣ Running on a Headless Server**

If running on a server without a browser:

1. Run `generate_tokens.py` on a desktop machine to authenticate.
2. Copy the generated `tokens.json` to the server:
   ```bash
   scp tokens.json user@your-server:/path/to/Reddit-Fetch/
   ```
3. Run the script on the server normally.

### **3️⃣ Handling Token Expiration**

- Access tokens expire every **1 hour**, but they are **automatically refreshed**.
- If the refresh token becomes invalid, rerun `generate_tokens.py`.

---

## 🚀 Running the Script

### **Fetching New Saved Posts**

To fetch new saved posts and export as text:

```bash
python main.py --format text
```

To export saved posts as **HTML bookmarks** for **[Linkwarden](https://github.com/linkwarden/linkwarden) & [Hoarder](https://github.com/hoarder-app/hoarder)**:

```bash
python main.py --format html
```

### **Force Fetch All Posts**

By default, the script fetches **only new posts** based on `last_fetch.json`. If you want to **re-fetch all saved posts**, use:

```bash
python main.py --format text --force-fetch
```

OR

```bash
python main.py --format html --force-fetch
```

This ignores `last_fetch.json` and retrieves all posts from Reddit.

---

## 📂 Data Storage

| File                | Purpose                                           |
| ------------------- | ------------------------------------------------- |
| `tokens.json`     | Stores authentication tokens                      |
| `saved_posts.txt` | Contains fetched posts and comments               |
| `bookmarks.html`  | HTML-formatted bookmarks for Linkwarden & Hoarder |
| `last_fetch.json` | Tracks last fetch timestamp                       |

---

## 🛠️ Advanced Features

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

---

💡 **Contributions & feedback are welcome!** 🚀
