from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True)
class Job:
    source: str
    job_id: str
    title: str
    company: str
    location: str
    url: str
    posted_time: Optional[str] = None
    employment_type: Optional[str] = None
    experience_level: Optional[str] = None
    salary: Optional[str] = None
    keyword: Optional[str] = None
    retrieved_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def identity(self) -> tuple[str, str]:
        return self.source, self.job_id

