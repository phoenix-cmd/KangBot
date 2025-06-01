FROM python:3.11-slim-bullseye

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    fonts-dejavu-core \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip

# Install CPU-only torch to reduce size
RUN pip install torch==2.0.0+cpu -f https://download.pytorch.org/whl/cpu/torch_stable.html

# Install other requirements except torch separately if needed
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
