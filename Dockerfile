## Base image with Python
FROM python:3.9.13-slim

# Avoid Python buffering and .pyc files in container
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Route all Hugging Face caches to a writable path inside the image
ENV HF_HOME=/app/.cache/huggingface \
    HF_HUB_CACHE=/app/.cache/huggingface/hub \
    TRANSFORMERS_CACHE=/app/.cache/transformers \
    XDG_CACHE_HOME=/app/.cache \
    SENTENCE_TRANSFORMERS_HOME=/app/.cache/sentence-transformers

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

# Pre-create cache directories with permissive permissions (for runtime/model downloads)
RUN mkdir -p /app/.cache /app/.cache/huggingface/hub /app/.cache/transformers /app/.cache/sentence-transformers \
    && chmod -R 777 /app/.cache

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
RUN mkdir -p /documentos_download && chmod 777 /documentos_download

# Pre-download the model during build (optional)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"


# Run the main application
CMD ["python", "-u", "main.py"]
