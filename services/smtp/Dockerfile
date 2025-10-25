FROM python:3.10-slim

WORKDIR /app

# Copy common module and config files (from project root)
COPY common/ ./common/
COPY config/ ./config/

# Copy service-specific files
COPY services/smtp/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/smtp/src/ .

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "smtp:app", "--host", "0.0.0.0", "--port", "8000"]