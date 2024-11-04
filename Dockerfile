FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y sqlite3 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

ENV HOST 0.0.0.0

CMD ["bash", "-c", "alembic upgrade head && fastapi run src --host 0.0.0.0 --port 8000"]