FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    NETSENTINEL_BIND_HOST=0.0.0.0 \
    NETSENTINEL_BIND_PORT=8000

WORKDIR /app

COPY pyproject.toml README.md ./
COPY app ./app

RUN python -m pip install --upgrade pip && \
    python -m pip install .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 CMD python -c "import os,sys,urllib.request;url='http://127.0.0.1:%s/health' % os.getenv('NETSENTINEL_BIND_PORT','8000');resp=urllib.request.urlopen(url, timeout=2);sys.exit(0 if resp.status == 200 else 1)"

CMD ["sh", "-c", "uvicorn app.main:app --host ${NETSENTINEL_BIND_HOST} --port ${NETSENTINEL_BIND_PORT}"]
