# Use a lightweight Python image
FROM python:3.10-alpine

WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Install the package in editable mode
RUN pip install --no-cache-dir -e .

# Set environment variables (configurable)
ENV DOCKER=1  
ENV FETCH_INTERVAL=3600
ENV OUTPUT_FORMAT=json
ENV FORCE_FETCH=false
ENV FULL_FETCH=false
ENV REDDIT_CALLBACK_PORT=8080

# Expose the authentication port (configurable at runtime)
EXPOSE ${REDDIT_CALLBACK_PORT:-8080}

# Set up a volume for data storage
VOLUME ["/data"]

# Ensure correct variable expansion and better log output in CMD
CMD ["sh", "-c", "\
      echo \"⏳ Fetching Reddit saved posts in ${OUTPUT_FORMAT} format...\" && \
      reddit-fetcher --format \"${OUTPUT_FORMAT}\" && \
      echo \"✅ Fetch complete. Sleeping for ${FETCH_INTERVAL} seconds...\" && \
      sleep ${FETCH_INTERVAL}\
    "]
