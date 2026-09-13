FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml .
COPY src/ ./src/
COPY sample-data/ ./sample-data/

RUN pip install --no-cache-dir . \
    && useradd --create-home --uid 10001 atlas \
    && chown -R atlas:atlas /app

USER atlas

ENTRYPOINT ["atlas"]
CMD ["--help"]
