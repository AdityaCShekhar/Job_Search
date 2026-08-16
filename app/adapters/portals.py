"""Best-effort public-search adapters for additional job portals."""

import hashlib
import logging
import re
from urllib.parse import quote_plus, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from app.adapters.linkedin import LinkedInAdapter
from app.config import Profile
from app.models.job import Job
from app.utils.retry import with_retries

LOGGER = logging.getLogger(__name__)


class MultiPortalAdapter:
    def __init__(self, timeout: int = 30, retries: int = 3, session: requests.Session | None = None):
        self.timeout = timeout
        self.retries = retries
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; JobMonitor/1.0)"})
        self.linkedin = LinkedInAdapter(timeout, retries, self.session)

    def search(self, profile: Profile) -> list[Job]:
        jobs: list[Job] = []
        for source in profile.sources:
            try:
                if source.casefold().strip() == "linkedin":
                    jobs.extend(self.linkedin.search(profile))
                else:
                    jobs.extend(self._search_portal(source, profile))
            except Exception:
                LOGGER.exception("Portal search failed source=%s", source)
        return list({(job.source, job.job_id): job for job in jobs}.values())

    def _search_portal(self, source: str, profile: Profile) -> list[Job]:
        source = source.casefold().strip()
        base_urls = {
            "naukri": "https://www.naukri.com/jobs-in-india",
            "indeed": "https://in.indeed.com/jobs",
            "wellfound": "https://wellfound.com/jobs",
            "instahyre": "https://www.instahyre.com/search-jobs/",
            "cutshort": "https://cutshort.io/jobs",
        }
        if source not in base_urls:
            LOGGER.warning("Unknown job portal source=%s", source)
            return []
        location = profile.locations[0] if profile.locations else ""
        jobs: list[Job] = []
        for keyword in profile.keywords or [profile.name]:
            if source == "wellfound":
                query = f"?query={quote_plus(keyword)}"
            else:
                query = f"?q={quote_plus(keyword)}&l={quote_plus(location)}"
            url = base_urls[source] + query
            response = with_retries(
                lambda: self._get_checked(url), self.retries
            )
            jobs.extend(self._extract_cards(response.text, source, url, keyword))
        LOGGER.info("Portal source=%s found=%d", source, len(jobs))
        return jobs

    def _get_checked(self, url: str) -> requests.Response:
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response

    @staticmethod
    def _extract_cards(html: str, source: str, page_url: str, keyword: str) -> list[Job]:
        soup = BeautifulSoup(html, "html.parser")
        jobs: list[Job] = []
        seen: set[str] = set()
        host = urlparse(page_url).netloc
        for link in soup.select("a[href]"):
            href = link.get("href", "")
            if not re.search(r"job|career|position|opening|vacanc", href, re.I):
                continue
            url = urljoin(page_url, href).split("?")[0]
            if urlparse(url).netloc != host:
                continue
            title = link.get_text(" ", strip=True)
            if not 3 <= len(title) <= 180:
                continue
            job_id = hashlib.sha1(url.encode()).hexdigest()[:24]
            if job_id in seen:
                continue
            seen.add(job_id)
            card = link.find_parent(["li", "article", "div", "section"]) or link
            text = card.get_text(" ", strip=True)
            jobs.append(Job(
                source=source,
                job_id=job_id,
                title=title,
                company="",
                location=_location_from_text(text),
                url=url,
                posted_time=_posted_from_text(text),
                keyword=keyword,
            ))
        return jobs


def _posted_from_text(text: str) -> str | None:
    match = re.search(r"(?:just now|\d+\s+(?:minute|hour|day|week|month)s?\s+ago)", text, re.I)
    return match.group(0) if match else None


def _location_from_text(text: str) -> str:
    for value in ("Remote", "Bengaluru", "Bangalore", "Hyderabad", "Pune", "Mumbai", "Delhi"):
        if value.casefold() in text.casefold():
            return value
    return ""
