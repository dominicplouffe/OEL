FROM python:3.10-slim

WORKDIR /app

# system deps
RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc libpq-dev netcat \
 && rm -rf /var/lib/apt/lists/*

# python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy project
COPY . .

# make entrypoint executable
RUN chmod +x ./entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
