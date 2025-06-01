FROM pytorch/pytorch:2.0.1-cpu

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    fonts-dejavu-core \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
