FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y netcat-traditional curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
