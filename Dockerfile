FROM python:3.11-slim

LABEL org.opencontainers.image.title="FRIDAY AI OS"
LABEL org.opencontainers.image.description="A Personal AI Operating System"
LABEL org.opencontainers.image.source="https://github.com/anomalyco/friday"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install --no-cache-dir -e .

CMD ["python", "-m", "friday.main"]
