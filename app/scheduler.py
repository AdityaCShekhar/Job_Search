import logging
import time
from dataclasses import dataclass

from app.adapters.portals import MultiPortalAdapter
from app.config import Config, Profile
from app.database.sqlite import Database
from app.filters.engine import filter_jobs
from app.notifications.telegram import TelegramNotifier

LOGGER = logging.getLogger(__name__)


@dataclass
class RunResult:
    jobs_found: int = 0
    new_jobs: int = 0
    duplicates: int = 0


class Monitor:
    def __init__(self, config: Config, database: Database | None = None, adapter=None, notifier=None):
        self.config = config
        self.database = database or Database(config.database)
        self.adapter = adapter or MultiPortalAdapter(config.request_timeout, config.retries)
        self.notifier = notifier or TelegramNotifier(config.telegram.token, config.telegram.chat_id, config.request_timeout)

    def run_once(self) -> RunResult:
        result = RunResult()
        run_id = self.database.start_run()
        try:
            for profile in self.config.profiles:
                if not profile.enabled:
                    continue
                jobs = filter_jobs(self.adapter.search(profile), profile)
                result.jobs_found += len(jobs)
                for job in jobs:
                    if self.database.add_job_if_new(job):
                        result.new_jobs += 1
                        if profile.notifications:
                            self.notifier.send(job)
                    else:
                        result.duplicates += 1
            self.database.finish_run(run_id, result.jobs_found, result.new_jobs, result.duplicates)
            LOGGER.info("Run complete found=%d new=%d duplicates=%d", result.jobs_found, result.new_jobs, result.duplicates)
            return result
        except Exception as error:
            self.database.finish_run(run_id, result.jobs_found, result.new_jobs, result.duplicates, "failed", str(error))
            LOGGER.exception("Run failed")
            raise

    def run_forever(self) -> None:
        while True:
            started = time.monotonic()
            try:
                self.run_once()
            except Exception:
                LOGGER.exception("Scheduled run failed; continuing")
            elapsed = time.monotonic() - started
            time.sleep(max(0, self.config.interval - elapsed))
