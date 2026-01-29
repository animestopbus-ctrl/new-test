# ========================================================
# Rexbots
# Maintained by Dhanpal Sharma
# ========================================================

FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates gcc libffi-dev python3-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Optional healthcheck (only if keep_alive uses Flask)
HEALTHCHECK CMD curl -f http://localhost:${PORT:-8080}/ || exit 1

# ✅ Start the bot
CMD ["python3", "bot.py"]
