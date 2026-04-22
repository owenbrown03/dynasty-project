# 1. Use an official Python runtime as a parent image
# 'slim' versions are smaller and better for production
FROM python:3.12-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Prevent Python from writing .pyc files and enable unbuffered logging
# This is crucial for seeing your logs in real-time in Docker
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 4. Install system dependencies (if needed for PostgreSQL/Psychopg2)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*
    
# 5. Copy only the requirements file first
# This allows Docker to cache your 'pip install' layer
COPY requirements.txt .

# 6. Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 7. Copy the rest of your application code
COPY . .

# 8. Command to run the application
# We use 0.0.0.0 so it's accessible outside the container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]