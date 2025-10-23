FROM python:3.10-slim

WORKDIR /app

# Copy common module and config files (from project root)
COPY common/ ./common/
COPY config/ ./config/

# Copy service-specific files
COPY imap/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY imap/src/imap.py .

ENV PYTHONPATH=/app:$PYTHONPATH

EXPOSE 8003

CMD ["uvicorn", "imap:app", "--host", "0.0.0.0", "--port", "8003"]