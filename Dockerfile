# Use a lightweight Python image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install Chromium for OAuth authentication
RUN apt-get update && apt-get install -y \
    chromium \
    && rm -rf /var/lib/apt/lists/*

# Copy the application code
COPY . .

# Install the package in editable mode
RUN pip install -e .

# Expose the authentication port (configurable)
EXPOSE ${REDDIT_CALLBACK_PORT:-8080}

# Set up a volume for data storage
VOLUME ["/data"]

# Run fetcher in a loop with scheduling
CMD while true; do \
      echo "⏳ Fetching Reddit saved posts in ${OUTPUT_FORMAT:-json} format..."; \
      reddit-fetcher --format ${OUTPUT_FORMAT:-json}; \
      echo "✅ Fetch complete. Sleeping for ${FETCH_INTERVAL:-3600} seconds..."; \
      sleep ${FETCH_INTERVAL:-3600}; \
    done