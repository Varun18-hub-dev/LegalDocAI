# ==========================================
# FastAPI Backend and Pre-built Frontend
# ==========================================
FROM python:3.11-slim

WORKDIR /app/server

# Copy backend dependencies and install
COPY server/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire server directory (pre-built frontend assets are in server/app/static)
COPY server/ ./

# Expose FastAPI port
EXPOSE 8000

# Start command
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
