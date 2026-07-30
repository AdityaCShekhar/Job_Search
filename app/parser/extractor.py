import json
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.models.job import Job


def _text(node, selector: str) -> str:
    found = node.select_one(selector)
    return found.get_text(" ", strip=True) if found else ""


def extract_linkedin_jobs(html: str, keyword: str = "") -> list[Job]:
    soup = BeautifulSoup(html, "html.parser")
    jobs: list[Job] = []
    seen: set[str] = set()
    for card in soup.select("li.jobs-search-results__list-item, li.base-card, div.base-card"):
        link = card.select_one("a.base-card__full-link, a[href*='/jobs/view/']")
        if not link or not link.get("href"):
            continue
        url = urljoin("https://www.linkedin.com", link["href"]).split("?")[0]
        match = re.search(r"/jobs/view/(\d+)", url)
        job_id = match.group(1) if match else url
        if job_id in seen:
            continue
        seen.add(job_id)
        jobs.append(Job(
            source="linkedin",
            job_id=job_id,
            title=_text(card, ".base-search-card__title, .job-card-list__title") or link.get_text(" ", strip=True),
            company=_text(card, ".base-search-card__subtitle, .job-card-container__company-name"),
            location=_text(card, ".job-search-card__location, .job-card-container__metadata-item"),
            url=url,
            posted_time=_text(card, "time"),
            keyword=keyword,
        ))
    return jobs

