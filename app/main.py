import argparse
import logging

from app.config import load_config
from app.database.sqlite import Database
from app.notifications.telegram import TelegramNotifier
from app.models.job import Job
from app.scheduler import Monitor
from app.utils.logger import configure_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="job-monitor")
    parser.add_argument("command", choices=["run", "once", "validate-config", "stats", "clear-cache", "test-notification"])
    parser.add_argument("--config", default="config.yaml")
    return parser


def main() -> int:
    configure_logging()
    args = build_parser().parse_args()
    config = load_config(args.config)
    if args.command == "validate-config":
        print(f"Configuration valid: {len(config.profiles)} profile(s)")
        return 0
    if args.command == "stats":
        db = Database(config.database)
        print(db.stats())
        db.close()
        return 0
    if args.command == "clear-cache":
        db = Database(config.database)
        db.clear_cache()
        db.close()
        print("Job cache cleared")
        return 0
    if args.command == "test-notification":
        if not config.telegram.enabled:
            print("Telegram is not configured")
            return 1
        notifier = TelegramNotifier(config.telegram.token, config.telegram.chat_id)
        notifier.send(Job("test", "test", "Job Monitor Test", "Job Monitor", "Local", "https://example.com"))
        print("Test notification sent")
        return 0
    monitor = Monitor(config)
    if args.command == "once":
        monitor.run_once()
    else:
        monitor.run_forever()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as error:
        logging.error("Configuration error: %s", error)
        raise SystemExit(2)

