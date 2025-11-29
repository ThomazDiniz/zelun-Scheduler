FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY youtube_bulk_scheduler.py .
COPY config.json .
COPY CONFIG_EXAMPLES.md .
COPY README.md .

# Create necessary directories
RUN mkdir -p clips sent backups logs

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the script
CMD ["python", "youtube_bulk_scheduler.py"]

