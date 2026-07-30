from app.database.sqlite import Database
from app.models.job import Job


def test_database_deduplicates_by_source_and_job_id(tmp_path):
    db = Database(tmp_path / "test.db")
    job = Job("linkedin", "1", "Engineer", "Acme", "Remote", "https://example.com/1")
    assert db.add_job_if_new(job)
    assert not db.add_job_if_new(job)
    assert db.stats() == {"jobs": 1, "runs": 0}
    db.close()

