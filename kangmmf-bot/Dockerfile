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

RUN apt-get update && apt-get install -y \
    ffmpeg \
    fonts-dejavu-core \
    fonts-noto-color-emoji \
    libcairo2 \
    libcairo2-dev \
    libpango-1.0-0 \
    libpango-1.0-dev \
    libgdk-pixbuf2.0-0 \
    libgdk-pixbuf2.0-dev \
    libffi-dev \
    pkg-config \
    libglib-2.0-0 \
    libgtk-3-0 \
    libpangocairo-1.0-0 \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* \
 && ldconfig

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]

