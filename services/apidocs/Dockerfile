FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better layer caching
COPY services/apidocs/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY services/apidocs/src/ ./src/

ENV PYTHONPATH=/app

EXPOSE 8010

CMD ["python", "src/apidocs.py"]
