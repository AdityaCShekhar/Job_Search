# LinkedIn Job Monitor

A small, open-source monitor that searches public LinkedIn job results, applies YAML-configured filters, stores jobs in SQLite, and sends first-seen jobs to Telegram.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.yaml my-config.yaml
# edit my-config.yaml and add Telegram credentials
python -m app.main --config my-config.yaml validate-config
python -m app.main --config my-config.yaml once
python -m app.main --config my-config.yaml run
```

After `pip install -e .`, the equivalent installed command is `job-monitor --config my-config.yaml once`.

## Docker

Edit `config.yaml` with your search profiles and Telegram credentials, then start the monitor:

```bash
docker compose up -d --build
docker compose logs -f job-monitor
```

Docker Compose runs PostgreSQL with a named `postgres-data` volume, so the database survives container restarts. Check or manage it with one-off commands:

```bash
docker compose run --rm job-monitor --config /config/config.yaml stats
docker compose run --rm job-monitor --config /config/config.yaml validate-config
docker compose run --rm job-monitor --config /config/config.yaml test-notification
docker compose down
```

The monitor container runs as a non-root user. Keep `config.yaml` out of public repositories if it contains Telegram credentials; alternatively, mount a private config file at `/config/config.yaml`. Local non-Docker runs still use SQLite by default; Docker overrides the database with `JOB_MONITOR_DATABASE`.

Commands are `run`, `once`, `validate-config`, `stats`, `clear-cache`, and `test-notification`. The default interval is five minutes. `run` keeps one process alive; cron and Actions should invoke `once`.

## Configuration

Profiles contain search keywords and optional filters such as locations, required/excluded keywords, excluded companies, employment types, experience levels, and remote preference. Telegram is optional; when it is not configured, jobs are still stored and the run is logged.

You can run the monitor with the empty Telegram values in the sample config. It will not send notifications or fail because Telegram is unavailable.

For Docker, Telegram credentials can be supplied through environment variables instead of editing the config:

```bash
TELEGRAM_BOT_TOKEN=123:abc TELEGRAM_CHAT_ID=456 docker compose up -d --build
```

Docker Compose also reads these values from a local `.env` file. Do not commit that file.

LinkedIn's public search markup can change and may rate-limit automated requests. The adapter is isolated in `app/adapters/linkedin.py`, so another job board can implement the same `search(profile) -> list[Job]` method.

## GitHub Actions

The included workflow runs every five minutes. Add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` as repository secrets; the workflow writes a temporary config from the checked-in template and persists `jobs.db` as an artifact between runs only when configured for that use. For reliable long-lived deduplication, a local process or an external artifact/cache strategy is recommended because GitHub-hosted runners are ephemeral.

## Tests

```bash
pytest
```
