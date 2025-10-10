FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Create downloads directory
RUN mkdir -p manga_downloads

# Run watcher for Docker mode
ENTRYPOINT ["python", "-m", "src.watcher"]
