FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    python3-pip \
    fonts-dejavu-core \
    pytgcalls \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*
 
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["python3", "bot.py"]
