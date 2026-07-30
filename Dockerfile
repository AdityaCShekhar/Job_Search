FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies separately so Docker can reuse this layer when source changes.
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN pip install --no-cache-dir .

RUN useradd --create-home --uid 10001 monitor \
    && mkdir -p /data \
    && chown -R monitor:monitor /app /data

USER monitor

WORKDIR /data

VOLUME ["/data"]

ENTRYPOINT ["job-monitor"]
CMD ["--config", "/config/config.yaml", "run"]
