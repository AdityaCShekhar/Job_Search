from app.config import Profile
from app.filters.engine import matches
from app.models.job import Job
from app.parser.extractor import extract_linkedin_jobs


HTML = """
<ul><li class="base-card">
<a class="base-card__full-link" href="https://www.linkedin.com/jobs/view/123/?trk=x">Backend Engineer</a>
<h3 class="base-search-card__title">Backend Engineer</h3>
<h4 class="base-search-card__subtitle">Acme</h4>
<span class="job-search-card__location">Bengaluru</span><time>12 minutes ago</time>
</li></ul>
"""


def test_extracts_normalized_job():
    jobs = extract_linkedin_jobs(HTML, "Java")
    assert len(jobs) == 1
    assert jobs[0].job_id == "123"
    assert jobs[0].url == "https://www.linkedin.com/jobs/view/123/"
    assert jobs[0].company == "Acme"


def test_filter_engine():
    job = Job("linkedin", "1", "Java Backend Engineer", "Acme", "Bengaluru", "https://example.com")
    profile = Profile(name="java", required_keywords=["Java"], exclude_companies=["TCS"], locations=["Bengaluru"])
    assert matches(job, profile)
    assert not matches(job, Profile(name="java", excluded_keywords=["Backend"]))

