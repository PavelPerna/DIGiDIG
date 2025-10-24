FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better layer caching
COPY apidocs/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY apidocs/src/ ./src/

# Add common module to path
ENV PYTHONPATH=/app:$PYTHONPATH

EXPOSE 8010

CMD ["python", "src/apidocs.py"]
