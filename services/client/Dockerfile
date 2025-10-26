FROM python:3.10-slim

WORKDIR /app

# Copy common module and config files (from project root)
COPY lib/ ./lib/
COPY config/ ./config/
COPY locales/ ./locales/

# Copy service-specific files
COPY services/client/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/client/src/ .

ENV PYTHONPATH=/app

EXPOSE 8004

CMD ["uvicorn", "client:app", "--host", "0.0.0.0", "--port", "8004"]