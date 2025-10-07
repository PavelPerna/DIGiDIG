FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/storage.py .

EXPOSE 8002

CMD ["uvicorn", "storage:app", "--host", "0.0.0.0", "--port", "8002"]