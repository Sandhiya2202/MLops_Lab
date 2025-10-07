FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

# (optional) build tools if needed; remove to keep smallest
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
  && useradd -m appuser && mkdir -p /app/artifacts \
  && chown -R appuser /app

COPY src/ ./src
USER appuser
CMD ["python","src/main.py"]
