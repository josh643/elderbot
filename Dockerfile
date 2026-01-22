# Use official Python runtime as a parent image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set PYTHONPATH to include the current directory
ENV PYTHONPATH=/app

# Create data directory
RUN mkdir -p data

# Expose port for Streamlit
EXPOSE 8501

# Default command (overridden by docker-compose)
CMD ["python", "src/engine/bot.py"]
