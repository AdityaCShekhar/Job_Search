from app.models.job import Job
from app.config import Profile
import re


def _contains(value: str, terms: list[str]) -> bool:
    value = value.casefold()
    return any(term.casefold() in value for term in terms)


def _location_matches(location: str, requested: list[str]) -> bool:
    """Match explicit locations, or any identified Indian location."""
    if not location:
        return False
    if _contains(location, requested):
        return True
    if _contains("india", requested):
        return any(
            city in location.casefold()
            for city in (
                "india", "bengaluru", "bangalore", "hyderabad", "pune", "mumbai",
                "delhi", "new delhi", "chennai", "kolkata", "gurgaon", "gurugram",
                "noida", "ahmedabad", "jaipur", "kochi", "remote",
            )
        )
    return False


def _age_in_minutes(posted_time: str | None) -> int | None:
    """Parse LinkedIn relative timestamps such as '25 minutes ago'."""
    if not posted_time:
        return None
    value = posted_time.casefold().strip()
    if value in {"just now", "now"}:
        return 0
    match = re.search(r"(\d+)\s+(minute|hour|day|week|month)s?\s+ago", value)
    if not match:
        return None
    amount = int(match.group(1))
    multiplier = {"minute": 1, "hour": 60, "day": 1440, "week": 10080, "month": 43200}
    return amount * multiplier[match.group(2)]


def matches(job: Job, profile: Profile) -> bool:
    haystack = " ".join(filter(None, [job.title, job.company, job.location, job.employment_type, job.experience_level]))
    if profile.required_keywords and not _contains(haystack, profile.required_keywords):
        return False
    if profile.excluded_keywords and _contains(haystack, profile.excluded_keywords):
        return False
    if profile.exclude_companies and _contains(job.company, profile.exclude_companies):
        return False
    if profile.locations and not _location_matches(job.location, profile.locations):
        return False
    if profile.employment_types and not _contains(job.employment_type or "", profile.employment_types):
        return False
    # LinkedIn applies experience_levels in the search URL. Search cards often
    # omit the experience label, so only apply the local check when it exists.
    if profile.experience_levels and job.experience_level and not _contains(job.experience_level, profile.experience_levels):
        return False
    if profile.max_age_minutes is not None:
        age = _age_in_minutes(job.posted_time)
        if age is None or age > profile.max_age_minutes:
            return False
    if profile.remote is True and "remote" not in job.location.casefold():
        return False
    return True


def filter_jobs(jobs: list[Job], profile: Profile) -> list[Job]:
    return [job for job in jobs if matches(job, profile)]
