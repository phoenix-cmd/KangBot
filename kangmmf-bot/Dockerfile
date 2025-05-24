FROM python:3.11-slim

# Install ffmpeg and fonts
RUN apt-get update && apt-get install -y ffmpeg python3-pip fonts-dejavu-core && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Add ffmpeg to PATH (usually it's in /usr/bin, but be explicit)
ENV PATH="/usr/bin:${PATH}"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "bot.py"]
