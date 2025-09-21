# Dockerfile for Akash Institute Outreach System
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY init_database.py .

# Create necessary directories
RUN mkdir -p data/uploads
RUN mkdir -p data/recordings

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose ports (FastAPI and Streamlit)
EXPOSE 8000 8501

# Initialize database and start services
CMD ["sh", "-c", "python init_database.py && uvicorn app.main:app --host 0.0.0.0 --port 8000 & streamlit run app/streamlit_app.py --server.port 8501 --server.address 0.0.0.0 & wait"]
