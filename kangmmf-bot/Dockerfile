FROM python:3.12-slim

# Install ffmpeg and dependencies
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies inside a venv
COPY requirements.txt .
RUN python -m venv /opt/venv && . /opt/venv/bin/activate && pip install --no-cache-dir -r requirements.txt

# Add venv to path
ENV PATH="/opt/venv/bin:$PATH"

# Copy your bot code
COPY . .

# Run the bot
CMD ["python", "main.py"]
