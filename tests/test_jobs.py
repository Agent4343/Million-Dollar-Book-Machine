import asyncio
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

    def test_write_chapters_job_no_live_objects_in_record(self):
        """Job record created by create_write_chapters_job must be serializable (no live objects)."""
        import json

        from core.jobs import JobManager, JobStatus

        async def run():
            # Minimal stubs – callables are passed but never stored in the record.
            project_id = "test-proj"
            chapter_outline = [
                {"number": 1, "title": "Ch 1"},
                {"number": 2, "title": "Ch 2"},
            ]
            existing: set = set()

            # Worker will try to call get_project_fn immediately; return None so it
            # raises and marks the chapter as failed – we just want to verify the record
            # is serializable and chapters are attempted in order.
            jm = JobManager()
            # Patch semaphore to prevent blocking in tests
            jm._semaphore = asyncio.Semaphore(1)

            def get_proj(pid):
                return None  # simulate project not found

            job = await jm.create_write_chapters_job(
                project_id=project_id,
                chapter_outline=chapter_outline,
                existing_chapter_numbers=existing,
                quick_mode=False,
                get_project_fn=get_proj,
                get_llm_fn=lambda: None,
                save_project_fn=lambda p: None,
            )

            # Record must be JSON-serializable (no live objects)
            record_dict = job.to_dict()
            json.dumps(record_dict)  # raises if not serializable

            # progress fields should be correct
            self.assertEqual(record_dict["progress"]["total"], 2)
            self.assertIsInstance(record_dict["progress"]["remaining"], list)
            self.assertEqual(len(record_dict["progress"]["remaining"]), 2)
            self.assertEqual(record_dict["progress"]["written"], [])
            self.assertFalse(record_dict["progress"]["quick_mode"])

            # Wait for the background task to finish
            await asyncio.sleep(0.5)

            # Job should be failed (project not found for both chapters)
            async with jm._lock:
                final_job = jm._jobs[job.job_id]
            self.assertIn(final_job.status, (JobStatus.failed, JobStatus.succeeded))

        asyncio.run(run())

    def test_write_chapters_job_in_order(self):
        """Chapters must be written in ascending number order."""
        from core.jobs import JobManager, JobStatus
        from core.orchestrator import ExecutionContext

        async def run():
            jm = JobManager()
            jm._semaphore = asyncio.Semaphore(1)

            order = []

            # Shuffle outline to confirm sorting is applied
            chapter_outline = [
                {"number": 3, "title": "C3"},
                {"number": 1, "title": "C1"},
                {"number": 2, "title": "C2"},
            ]

            # We need a real-ish project object with .layers and .manuscript.
            # Use a mock that satisfies the worker's attribute access.
            class FakeLayerAgents:
                def items(self):
                    return []

            class FakeLayer:
                agents = FakeLayerAgents()

            class FakeProject:
                project_id = "p-order"
                manuscript = {"chapters": []}
                layers = {"L0": FakeLayer()}

            fake_project = FakeProject()

            def get_proj(pid):
                return fake_project

            async def fake_writer(context, chapter_num, quick_mode=False):
                order.append(chapter_num)
                return {"text": "x", "word_count": 1, "chapter_number": chapter_num}

            # Monkey-patch execute_chapter_writer inside the worker module
            import agents.chapter_writer as cw_mod
            original = cw_mod.execute_chapter_writer
            cw_mod.execute_chapter_writer = fake_writer
            try:
                job = await jm.create_write_chapters_job(
                    project_id="p-order",
                    chapter_outline=chapter_outline,
                    existing_chapter_numbers=set(),
                    quick_mode=False,
                    get_project_fn=get_proj,
                    get_llm_fn=lambda: None,
                    save_project_fn=lambda p: None,
                )
                await asyncio.sleep(0.5)
            finally:
                cw_mod.execute_chapter_writer = original

            self.assertEqual(order, [1, 2, 3], f"Expected chapters in order 1,2,3 but got {order}")

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()

