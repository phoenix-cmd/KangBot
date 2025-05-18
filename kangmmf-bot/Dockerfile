# Dockerfile
FROM python:3.11-alpine

# Install system dependencies
RUN apk update && apk add --no-cache ffmpeg build-base

# Create app directory
WORKDIR /app

# Copy files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run your bot
CMD ["python", "bot.py"]
