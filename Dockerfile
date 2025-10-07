## Base image with Python
FROM python:3.9.13-slim

# Avoid Python buffering and .pyc files in container
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# System deps required by camelot-py[cv] (ghostscript, opencv runtime libs),
# tabula-py (Java runtime), and general utilities
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       openjdk-17-jre-headless \
       ghostscript \
       libglib2.0-0 \
       libgl1 \
       libsm6 \
       libxrender1 \
       libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Workdir
WORKDIR /app

# Copy only requirements first for better layer caching
COPY requirements.txt /app/requirements.txt

# Upgrade pip and install Python dependencies
RUN python -m pip install --upgrade pip \
 && pip install --no-cache-dir -r /app/requirements.txt

# Copy app source code
COPY . /app

# Create data directory used by the app for downloaded documents
RUN mkdir -p /documentos_download
VOLUME ["/documentos_download"]

# Run the main application
CMD ["python", "-u", "main.py"]
