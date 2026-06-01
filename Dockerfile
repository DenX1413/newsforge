FROM python:3.11-slim

# Install Node.js 20
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Build frontend
COPY frontend/ frontend/
RUN cd frontend && npm install && npm run build

# Copy rest of the project
COPY . .

EXPOSE 8000

# Copy and make startup script executable
COPY start_prod.sh /app/start_prod.sh
RUN chmod +x /app/start_prod.sh

# Runs FastAPI (foreground, Railway port) + Telegram bot (background)
CMD ["/app/start_prod.sh"]
