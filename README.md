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

Docker Compose stores SQLite in a named `job-data` volume, so the database survives container restarts. Check or manage it with one-off commands:

```bash
docker compose run --rm job-monitor --config /config/config.yaml stats
docker compose run --rm job-monitor --config /config/config.yaml validate-config
docker compose run --rm job-monitor --config /config/config.yaml test-notification
docker compose down
```

The monitor container runs as a non-root user. Keep `config.yaml` out of public repositories if it contains Telegram credentials; alternatively, mount a private config file at `/config/config.yaml`. The monitor uses SQLite both locally and in Docker.

Commands are `run`, `once`, `validate-config`, `stats`, `clear-cache`, and `test-notification`. The default interval is five minutes. `run` keeps one process alive and is the recommended Termux mode.

## Configuration

Profiles contain search keywords and optional filters such as locations, required/excluded keywords, excluded companies, employment types, experience levels, and remote preference. Telegram is optional; when it is not configured, jobs are still stored and the run is logged.

You can run the monitor with the empty Telegram values in the sample config. It will not send notifications or fail because Telegram is unavailable.

For Docker, Telegram credentials can be supplied through environment variables instead of editing the config:

```bash
TELEGRAM_BOT_TOKEN=123:abc TELEGRAM_CHAT_ID=456 docker compose up -d --build
```

Docker Compose also reads these values from a local `.env` file. Do not commit that file.

LinkedIn's public search markup can change and may rate-limit automated requests. The adapter is isolated in `app/adapters/linkedin.py`, so another job board can implement the same `search(profile) -> list[Job]` method.

## Termux on Android

Termux is the runtime scheduler for the phone; GitHub remains only the source repository. The included wrapper keeps one monitor process alive, restarts it if it exits, writes a rotating log, and uses the existing SQLite database for deduplication.

On the phone, install Termux from F-Droid or GitHub Releases, then run:

```bash
pkg update -y
pkg upgrade -y
pkg install -y git python
termux-setup-storage
cd ~
git clone <your-repository-url> Job_Automation
cd ~/Job_Automation
python -m venv .venv
.venv/bin/pip install --no-cache-dir .
cp config.yaml my-config.yaml
${EDITOR:-nano} my-config.yaml
```

Put Telegram credentials in `my-config.yaml`, or export `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`. Set `general.interval` in seconds; use `900` for 15 minutes. Keep the database on local Termux storage, not shared phone storage.

Validate and test before enabling startup:

```bash
.venv/bin/python -m app.main --config my-config.yaml validate-config
.venv/bin/python -m app.main --config my-config.yaml test-notification
```

The wrapper defaults to `config.yaml`; for a private config, set `JOB_MONITOR_CONFIG=$HOME/Job_Automation/my-config.yaml` before using it:

```bash
chmod +x termux/job-monitor.sh termux/boot-job-monitor
JOB_MONITOR_CONFIG=$HOME/Job_Automation/my-config.yaml termux/job-monitor.sh start
JOB_MONITOR_CONFIG=$HOME/Job_Automation/my-config.yaml termux/job-monitor.sh status
termux/job-monitor.sh logs
termux/job-monitor.sh restart
termux/job-monitor.sh stop
```

To start after reboot, install and open the separate Termux:Boot add-on once, then copy the boot script:

```bash
mkdir -p ~/.termux/boot
cp termux/boot-job-monitor ~/.termux/boot/job-monitor
chmod +x ~/.termux/boot/job-monitor
```

Disable Android battery optimization for Termux and Termux:Boot. The wrapper does not hold a wake lock by default to conserve battery. For a phone that must run through deep sleep, enable one with `export JOB_MONITOR_WAKE_LOCK=1`; this increases battery use.

The monitor retries requests with exponential backoff, catches per-portal failures, and continues scheduled runs after failures. Telegram keeps its existing message format and retries; a job is marked notified only after a successful Telegram response, so temporary outages are retried later. A crash after Telegram accepts a request but before SQLite records success can theoretically produce one duplicate.

## Tests

```bash
pytest
```
