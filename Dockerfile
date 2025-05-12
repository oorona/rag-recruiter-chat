# Use an official Python runtime as a parent image
FROM python:3.11-slim AS builder

# Set environment variables to prevent writing pyc files and buffer logs
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies if any are needed (e.g., for certain libraries)
# RUN apt-get update && apt-get install -y --no-install-recommends some-package && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Copy only requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend application code (excluding mdata now)
COPY ./backend ./backend
# COPY ./mdata ./mdata  # <--- REMOVE OR COMMENT OUT THIS LINE

# Note: .env is not copied; it will be injected via docker-compose

# --- Final Stage ---
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages and dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code from the builder stage (excluding mdata)
COPY --from=builder /app/backend ./backend
# DO NOT copy mdata here either

# Expose the port the app runs on
EXPOSE 5000

# Define the command to run the application using Gunicorn
# Ensure backend.app points correctly to the Flask app instance in backend/app.py
# Use a reasonable number of workers (e.g., 2*CPU + 1)
# Bind to 0.0.0.0 to accept connections from outside the container
CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:5000", "backend.app:app"]