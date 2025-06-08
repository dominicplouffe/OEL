# Use the official lightweight Python image
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (including stdio.h via build-essential)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential \        # brings in libc6-dev, make, etc.
      gcc \
      libpq-dev \
      netcat-openbsd \
 && rm -rf /var/lib/apt/lists/*

# Copy & install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy the rest of your code
COPY . .

# Make entrypoint executable
RUN chmod +x ./entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
