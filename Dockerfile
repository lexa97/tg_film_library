# Dockerfile for Telegram Film Library Bot

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create entrypoint script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "Waiting for postgres..."\n\
while ! pg_isready -h db -p 5432 -U $POSTGRES_USER; do\n\
  sleep 1\n\
done\n\
echo "PostgreSQL started"\n\
\n\
echo "Running migrations..."\n\
alembic upgrade head\n\
\n\
echo "Starting bot..."\n\
python -m app.main\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
