FROM python:3.12-slim

WORKDIR /workspace/backend

RUN apt-get update && apt-get install -y \
    libpq-dev gcc postgresql-client postgresql-client-common \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "./start.sh"]