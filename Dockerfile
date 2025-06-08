# Use the official lightweight Python image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Install system dependencies (including netcat-openbsd for the 'nc' command)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      gcc \
      libpq-dev \
      netcat-openbsd \
 && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Make the entrypoint script executable
RUN chmod +x ./entrypoint.sh

# Expose Django’s default port
EXPOSE 8000

# Use the entrypoint to dispatch between web, celery, and beat
ENTRYPOINT ["./entrypoint.sh"]
