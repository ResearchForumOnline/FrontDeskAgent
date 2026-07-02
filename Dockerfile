FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOST=0.0.0.0 \
    APP_PORT=8088

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /app/data && python -m compileall frontdeskagent

EXPOSE 8088
CMD ["gunicorn", "-b", "0.0.0.0:8088", "frontdeskagent.app:app"]
