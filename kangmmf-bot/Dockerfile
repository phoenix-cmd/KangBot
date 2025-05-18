FROM jrottenberg/ffmpeg:5.1-alpine

# Install Python3 and pip
RUN apk add --no-cache python3 py3-pip

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy your bot source code
COPY . .

CMD ["python3", "bot.py"]
