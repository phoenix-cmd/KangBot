# FROM python:3.10-slim

# RUN apt-get update && apt-get install -y \
#     ffmpeg \
#     fonts-dejavu-core \
#  && apt-get clean \
#  && rm -rf /var/lib/apt/lists/*

# WORKDIR /app

# COPY requirements.txt .

# RUN pip install --no-cache-dir -r requirements.txt

# COPY . .

# CMD ["python", "bot.py"]


FROM python:3.10-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    fonts-dejavu-core \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source files
COPY . .

# Run your bot
CMD ["python", "bot.py"]
