# Reddit Saved Posts Retrieval and Execution System

## Overview
This system automates the process of retrieving saved posts from Reddit, storing them, and executing custom Python scripts on a self-hosted environment. The workflow integrates a Git-based deployment mechanism, enabling code execution on a Raspberry Pi (Nemesis) after every push from a Windows machine.

## Features
- **Automated Reddit Saved Posts Retrieval**: Fetches saved posts from Reddit using authenticated API requests.
- **Token Refresh Mechanism**: Uses long-lived refresh tokens to avoid manual authentication.
- **Scheduled Execution**: Can be configured to run at regular intervals.
- **Self-Hosted Git Repository**: Uses Gitea to store and manage Python scripts.
- **Automated Execution**: Runs Python scripts on Nemesis upon detecting new commits.
- **Post-Processing & Summarization**: Extracts and summarizes content from retrieved links.
- **Self-Hosted Dashboard** (Planned): A web UI for managing and browsing saved posts.

## Use Cases
- **Reddit Content Archival**: Automatically back up and organize saved posts.
- **Personalized News Aggregation**: Summarize and categorize saved posts.
- **Automation & Deployment**: Push Python scripts from a Windows machine and execute them on Nemesis.
- **Data Analysis**: Extract insights from saved Reddit posts for research or tracking trends.

## Future Enhancements
- **Advanced Filtering & Categorization**: Organizing posts based on subreddit, keywords, or post type.
- **Webhook Integration**: Trigger external notifications or API calls after execution.
- **Multi-User Support**: Extend functionality to support multiple Reddit accounts.

## Contribution
Users can modify the script to adapt it to their own workflow, integrate additional automation features, or extend its capabilities with new API endpoints.

