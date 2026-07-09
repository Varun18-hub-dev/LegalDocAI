# ==========================================
# STAGE 1: Build the React Frontend
# ==========================================
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ==========================================
# STAGE 2: Package Backend Runtime
# ==========================================
FROM python:3.11-slim AS backend-runtime
WORKDIR /app/server

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend dependencies and install
COPY server/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY server/ ./

# Copy compiled frontend build into FastAPI static folder
COPY --from=frontend-builder /app/frontend/dist ./app/static/

# Expose FastAPI port
EXPOSE 8000

# Start command
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
