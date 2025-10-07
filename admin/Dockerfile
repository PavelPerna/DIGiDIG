FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ .

EXPOSE 8005

CMD ["uvicorn", "admin:app", "--host", "0.0.0.0", "--port", "8005"]