FROM python:3.11-slim-bullseye as build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    fonts-dejavu-core \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --user --no-cache-dir -r requirements.txt

COPY . .

FROM python:3.11-slim-bullseye

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    fonts-dejavu-core \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=build /root/.local /root/.local
COPY --from=build /app /app

ENV PATH=/root/.local/bin:$PATH

CMD ["python", "bot.py"]
