import unittest


class TestJobs(unittest.TestCase):
    def test_job_store_import(self):
        # Smoke test that modules import (covers syntax / missing deps)
        from core.jobs import JobManager  # noqa: F401

    def test_job_record_roundtrip(self):
        from core.jobs import JobRecord, JobStatus

        job = JobRecord(job_id="j1", project_id="p1", status=JobStatus.interrupted, resumed_from_job_id="j0")
        data = job.to_dict()
        job2 = JobRecord.from_dict(data)
        self.assertEqual(job2.job_id, "j1")
        self.assertEqual(job2.project_id, "p1")
        self.assertEqual(job2.status, JobStatus.interrupted)
        self.assertEqual(job2.resumed_from_job_id, "j0")


if __name__ == "__main__":
    unittest.main()

