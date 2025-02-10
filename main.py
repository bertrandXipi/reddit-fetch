from api import fetch_saved_posts

# Fetch saved Reddit posts
saved_posts = fetch_saved_posts()

if not saved_posts:
    print("❌ No saved posts retrieved.")
else:
    print(f"✅ Retrieved {len(saved_posts)} saved posts.")

    # Write to file
    with open("saved_posts.txt", "w", encoding="utf-8") as file:
        for post in saved_posts:
            data = post.get("data", {})
            kind = post.get("kind", "")

            if kind == "t3":  # It's a post
                title = data.get("title", "No Title")
                url = data.get("url", "No URL")
                file.write(f"Post: {title}\n{url}\n\n")

            elif kind == "t1":  # It's a comment
                body = data.get("body", "No Content")
                link_title = data.get("link_title", "No Title")
                link_url = data.get("link_url", "No URL")
                file.write(f"Comment on: {link_title}\n{link_url}\nContent: {body}\n\n")

    print("✅ Saved posts and comments to saved_posts.txt")
