# Use a lightweight Python image
FROM python:3.10-alpine

WORKDIR /app

# Install dependencies
COPY requirements.txt ./
# Install dependencies with optimizations
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -e .

# Copy the rest of the application code
COPY . .

# Set environment variable to detect Docker runtime
ENV DOCKER=1  

# Define a persistent volume for data storage
VOLUME ["/data"]

# Default environment variables (override via Docker CLI or Compose)
ENV OUTPUT_FORMAT="json"
ENV FETCH_INTERVAL="3600"
ENV FORCE_FETCH="true"
# Ensure correct variable expansion and better log output in CMD
CMD ["sh", "-c", "\
      echo \"⏳ Fetching Reddit saved posts in ${OUTPUT_FORMAT} format...\" && \
      reddit-fetcher --format \"${OUTPUT_FORMAT}\" && \
      echo \"✅ Fetch complete. Sleeping for ${FETCH_INTERVAL} seconds...\" && \
      sleep ${FETCH_INTERVAL}\
    "]
