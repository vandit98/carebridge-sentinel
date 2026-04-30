FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY carebridge_sentinel ./carebridge_sentinel
COPY examples ./examples

ENV CAREBRIDGE_SYNTHETIC_FHIR=false
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

CMD ["sh", "-c", "uvicorn carebridge_sentinel.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
