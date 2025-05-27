# FROM python:3.11-slim

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


FROM python:3.11-slim

# Install system libraries needed for pangocffi, Pillow, and ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    fonts-noto-color-emoji \
    ffmpeg \
    git \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Default command
CMD ["python", "bot.py"]




