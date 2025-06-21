# Dockerfile for XKCD Comic Finder with Weaviate
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Set Python path
ENV PYTHONPATH=/app

# Expose port for any web interface (if needed later)
EXPOSE 8000

# Default command
CMD ["python", "-m", "src.database.weaviate_client", "--help"]
