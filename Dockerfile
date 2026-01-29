# ========================================================
# Rexbots
# Don't Remove Credit 🥺
# Telegram Channel @RexBots_Official
#
# Maintained & Updated by:
# Dhanpal Sharma
# GitHub: https://github.com/LastPerson07
# ========================================================

FROM python:3.12-slim-bookworm  # Updated to 3.12 for performance

# Prevent Python from creating .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
# Ensure logs are shown instantly
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates gcc libffi-dev python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Health check for zero-downtime
HEALTHCHECK CMD curl -f http://localhost:${PORT:-8080}/ || exit 1

# Start the bot with gunicorn for better performance
CMD ["gunicorn", "--bind", "0.0.0.0:${PORT:-8080}", "keep_alive:app", "--workers", "2", "--timeout", "120", "&", "python3", "bot.py"]
