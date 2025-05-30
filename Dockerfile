FROM python:3.11-slim

# Install MetaTrader5 dependencies
RUN apt-get update && \
    apt-get install -y gcc libc6-dev libglib2.0-0 libsm6 libxrender1 libxext6 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy all code
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Default command: launch the bot
CMD ["python", "main.py"]
