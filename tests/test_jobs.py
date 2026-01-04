import unittest


class TestJobs(unittest.TestCase):
    def test_job_store_import(self):
        # Smoke test that modules import (covers syntax / missing deps)
        from core.jobs import JobManager  # noqa: F401


if __name__ == "__main__":
    unittest.main()

