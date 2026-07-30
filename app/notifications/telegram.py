import logging

import requests

from app.models.job import Job
from app.utils.retry import with_retries

LOGGER = logging.getLogger(__name__)


def format_job(job: Job) -> str:
    return (f"🚀 New Backend Job\n\nCompany: {job.company}\n\nRole: {job.title}\n\n"
            f"Location: {job.location}\n\nPosted: {job.posted_time or 'Unknown'}\n\n"
            f"Keyword: {job.keyword or 'Unknown'}\n\nApply: {job.url}")


class TelegramNotifier:
    def __init__(self, token: str, chat_id: str, timeout: int = 30, session: requests.Session | None = None):
        self.token, self.chat_id, self.timeout = token, chat_id, timeout
        self.session = session or requests.Session()

    @property
    def enabled(self) -> bool:
        return bool(self.token and self.chat_id)

    def send(self, job: Job) -> None:
        if not self.enabled:
            LOGGER.info("Telegram is not configured; notification skipped for %s", job.job_id)
            return
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        with_retries(lambda: self.session.post(url, data={"chat_id": self.chat_id, "text": format_job(job)}, timeout=self.timeout).raise_for_status(), 3)
