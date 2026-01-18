FROM python:3.12-slim

# Tells Python not to write .pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1
# Ensures your Python logs (like print("Startup ready")) are sent straight to the terminal in real-time without being buffered.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System deps for Python packages with C extensions
RUN apt-get update \
    && apt-get install -y build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Production server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
