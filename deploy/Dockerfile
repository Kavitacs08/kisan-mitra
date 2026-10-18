# Prompt 21 — Cloud Run deployment container for the FastAPI backend.
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY data/ ./data/

ENV USE_MOCK=true
ENV PORT=8080
WORKDIR /app/backend

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
