FROM python:3.10-slim

WORKDIR /app

# Copy common module and config files (from project root)
COPY lib/ ./lib/
COPY config/ ./config/

# Copy service-specific files
COPY services/imap/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/imap/src/imap.py .

ENV PYTHONPATH=/app

EXPOSE 8003

CMD ["uvicorn", "imap:app", "--host", "0.0.0.0", "--port", "8003"]