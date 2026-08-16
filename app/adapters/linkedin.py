import logging
from urllib.parse import quote_plus

import requests

from app.config import Profile
from app.models.job import Job
from app.parser.extractor import extract_linkedin_jobs
from app.utils.retry import with_retries

LOGGER = logging.getLogger(__name__)

# LinkedIn's f_E values: Internship, Entry level, Associate, Mid-Senior level,
# Director, and Executive.
LINKEDIN_EXPERIENCE_LEVELS = {
    "internship": "1",
    "entry level": "2",
    "associate": "3",
    "mid-senior level": "4",
    "director": "5",
    "executive": "6",
}


class LinkedInAdapter:
    source = "linkedin"

    def __init__(self, timeout: int = 30, retries: int = 3, session: requests.Session | None = None):
        self.timeout = timeout
        self.retries = retries
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; JobMonitor/1.0)"})

    def search(self, profile: Profile) -> list[Job]:
        jobs: list[Job] = []
        for keyword in profile.keywords or [profile.name]:
            params = {"keywords": keyword}
            if profile.locations:
                params["location"] = profile.locations[0]
            if profile.max_age_minutes is not None:
                # LinkedIn's f_TPR value is a lookback window in seconds.
                params["f_TPR"] = f"r{profile.max_age_minutes * 60}"
                params["sortBy"] = "DD"
            experience_ids = [
                LINKEDIN_EXPERIENCE_LEVELS[level.casefold().strip()]
                for level in profile.experience_levels
                if level.casefold().strip() in LINKEDIN_EXPERIENCE_LEVELS
            ]
            if experience_ids:
                params["f_E"] = ",".join(dict.fromkeys(experience_ids))
            url = "https://www.linkedin.com/jobs/search/?" + "&".join(f"{key}={quote_plus(value)}" for key, value in params.items())
            response = with_retries(
                lambda: self._get_checked(url), self.retries
            )
            jobs.extend(extract_linkedin_jobs(response.text, keyword))
        unique = {job.job_id: job for job in jobs}
        LOGGER.info("LinkedIn profile=%s found=%d", profile.name, len(unique))
        return list(unique.values())

    def _get_checked(self, url: str) -> requests.Response:
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response
