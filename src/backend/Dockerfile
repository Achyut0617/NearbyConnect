# NearbyConnect backend — build: docker build -t nearbyconnect-api src/backend
FROM python:3.12-slim

# Don't write .pyc, flush logs immediately.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install deps first (better layer caching).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code.
COPY . .

# Build the profiling model at image-build time so /me/analyze uses the
# trained v2 model. (Uses synthetic data; no network, no real people.)
RUN python -m scripts.train_profiling --n 4000 || echo "model build skipped"

EXPOSE 8000

# DATABASE_URL, REDDIT_*, YOUTUBE_API_KEY, CORS_ORIGINS come from the environment.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
