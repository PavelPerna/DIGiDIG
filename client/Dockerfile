FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ .

EXPOSE 8004

CMD ["uvicorn", "client:app", "--host", "0.0.0.0", "--port", "8004"]