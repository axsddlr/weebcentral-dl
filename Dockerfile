FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY main.py .

# Create downloads directory
RUN mkdir -p manga_downloads

# Set environment variable to enable Docker mode
ENV DOCKER_MODE=1

ENTRYPOINT ["python", "main.py"]
