FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Script to wait for TWS and then start the app
COPY wait-for-tws.sh .
RUN chmod +x wait-for-tws.sh

# Command to run the app
CMD ["./wait-for-tws.sh"] 