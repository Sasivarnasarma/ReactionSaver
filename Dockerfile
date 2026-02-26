# By @Sasivarnasarma

FROM python:3.9-slim-bookworm AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential cmake python3-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt
COPY . .


FROM python:3.9-slim-bookworm
WORKDIR /app
COPY --from=builder /install /usr/local
COPY --from=builder /app /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
CMD ["python", "main.py"]