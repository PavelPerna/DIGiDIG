FROM python:3.10-slim

WORKDIR /app

# Copy lib and config files (from project root)
COPY lib/ ./lib/
COPY config/ ./config/

# Copy service-specific files
COPY services/storage/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/storage/src/storage.py .

ENV PYTHONPATH=/app:$PYTHONPATH

EXPOSE 8002

CMD ["uvicorn", "storage:app", "--host", "0.0.0.0", "--port", "8002"]