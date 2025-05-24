# FROM python:3.11-slim

# RUN apt-get update && apt-get install -y \
#     ffmpeg \
#     python3-pip \
#     fonts-dejavu-core \
#  && apt-get clean \
#  && rm -rf /var/lib/apt/lists/*
 
# WORKDIR /app
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt
# COPY . .

# CMD ["python3", "bot.py"]


FROM python:3.11-slim

# Install ffmpeg and necessary build tools & fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    build-essential \
    gcc \
    libffi-dev \
    libssl-dev \
    fonts-dejavu-core \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "bot.py"]
