# Use official slim Python base image
FROM python:3.11-slim

# Install FFmpeg, pip, and fonts
RUN apt-get update && \
    apt-get install -y ffmpeg python3-pip fonts-dejavu-core && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Debug: check ffmpeg installation
RUN ffmpeg -version
RUN ls -l /usr/bin/ffmpeg
RUN ls -l /usr/share/fonts/truetype/dejavu/

# Set working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot source code
COPY . .

# Start the bot
CMD ["python3", "bot.py"]
