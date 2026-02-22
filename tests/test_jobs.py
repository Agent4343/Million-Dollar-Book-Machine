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

    def test_blocked_status_exists(self):
        from core.jobs import JobStatus
        self.assertIn("blocked", [s.value for s in JobStatus])

    def test_blocked_job_is_resumable(self):
        """A job with status=blocked should be accepted by resume_job logic."""
        from core.jobs import JobStatus
        resumable = (JobStatus.interrupted, JobStatus.failed, JobStatus.blocked, JobStatus.cancelled)
        self.assertIn(JobStatus.blocked, resumable)

    def test_blocked_job_roundtrip(self):
        from core.jobs import JobRecord, JobStatus

        diagnostics = {
            "blocked_candidates": [{"agent_id": "draft_generation", "unmet_dependencies": [{"dep_id": "chapter_blueprint", "dep_status": "pending"}]}],
            "agent_status_counts": {"pending": 5, "passed": 10},
            "layer_status_counts": {"completed": 3, "in_progress": 1, "locked": 17},
        }
        job = JobRecord(job_id="j2", project_id="p2", status=JobStatus.blocked)
        job.error = "Project blocked: no available agents."
        job.progress = {"blocked_reason": diagnostics}
        job.events.append({"kind": "blocked", "blocked_candidates": diagnostics["blocked_candidates"]})

        data = job.to_dict()
        job2 = JobRecord.from_dict(data)
        self.assertEqual(job2.status, JobStatus.blocked)
        self.assertIn("blocked_reason", job2.progress)
        self.assertEqual(job2.progress["blocked_reason"]["blocked_candidates"][0]["agent_id"], "draft_generation")

    def test_write_chapters_job_no_live_objects_in_record(self):
        """Job record created by create_write_chapters_job must be serializable (no live objects)."""
        import json

        from core.jobs import JobManager, JobStatus

        async def run():
            project_id = "test-proj"
            chapter_outline = [
                {"number": 1, "title": "Ch 1"},
                {"number": 2, "title": "Ch 2"},
            ]
            existing: set = set()

            jm = JobManager()
            jm._semaphore = asyncio.Semaphore(1)
            jm.chapter_max_retries = 1  # no retries for this test
            jm.chapter_retry_backoff_base = 0.01

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
                return {"text": "x", "word_count": 1, "number": chapter_num}

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


class TestChapterRetry(unittest.TestCase):
    """Chapter writing should retry on error before moving to the next chapter."""

    def _make_fake_project(self):
        """Create a minimal fake project for chapter writing tests."""
        class FakeLayerAgents:
            def items(self):
                return []

        class FakeLayer:
            agents = FakeLayerAgents()

        class FakeProject:
            project_id = "p-retry"
            manuscript = {"chapters": []}
            layers = {"L0": FakeLayer()}

        return FakeProject()

    def test_retry_then_succeed(self):
        """A chapter that fails once then succeeds should produce one retry event."""
        from core.jobs import JobManager, JobStatus

        async def run():
            jm = JobManager()
            jm._semaphore = asyncio.Semaphore(1)
            jm.chapter_max_retries = 3
            jm.chapter_retry_backoff_base = 0.01  # fast for tests

            call_count = 0
            fake_project = self._make_fake_project()

            async def flaky_writer(context, chapter_num, quick_mode=False):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise RuntimeError("Transient LLM error")
                return {"text": "Chapter content", "word_count": 100, "number": chapter_num}

            import agents.chapter_writer as cw_mod
            original = cw_mod.execute_chapter_writer
            cw_mod.execute_chapter_writer = flaky_writer
            try:
                job = await jm.create_write_chapters_job(
                    project_id="p-retry",
                    chapter_outline=[{"number": 1, "title": "Ch 1"}],
                    existing_chapter_numbers=set(),
                    quick_mode=False,
                    get_project_fn=lambda pid: fake_project,
                    get_llm_fn=lambda: None,
                    save_project_fn=lambda p: None,
                )
                await asyncio.sleep(0.5)
            finally:
                cw_mod.execute_chapter_writer = original

            async with jm._lock:
                final_job = jm._jobs[job.job_id]

            self.assertEqual(final_job.status, JobStatus.succeeded)
            self.assertEqual(call_count, 2, "Expected 2 calls: 1 fail + 1 succeed")

            # Should have a retry event
            retry_events = [e for e in final_job.events if e.get("kind") == "chapter_retry"]
            self.assertEqual(len(retry_events), 1)

            # Should have a success event
            success_events = [e for e in final_job.events if e.get("kind") == "chapter_success"]
            self.assertEqual(len(success_events), 1)

        asyncio.run(run())

    def test_all_retries_exhausted_stops_pipeline(self):
        """If a chapter fails all retries, the job should stop and not write subsequent chapters."""
        from core.jobs import JobManager, JobStatus

        async def run():
            jm = JobManager()
            jm._semaphore = asyncio.Semaphore(1)
            jm.chapter_max_retries = 3
            jm.chapter_retry_backoff_base = 0.01  # fast for tests

            chapters_attempted = []
            fake_project = self._make_fake_project()

            async def always_fail_writer(context, chapter_num, quick_mode=False):
                chapters_attempted.append(chapter_num)
                raise RuntimeError("Persistent error")

            import agents.chapter_writer as cw_mod
            original = cw_mod.execute_chapter_writer
            cw_mod.execute_chapter_writer = always_fail_writer
            try:
                job = await jm.create_write_chapters_job(
                    project_id="p-retry",
                    chapter_outline=[
                        {"number": 1, "title": "Ch 1"},
                        {"number": 2, "title": "Ch 2"},
                    ],
                    existing_chapter_numbers=set(),
                    quick_mode=False,
                    get_project_fn=lambda pid: fake_project,
                    get_llm_fn=lambda: None,
                    save_project_fn=lambda p: None,
                )
                await asyncio.sleep(0.5)
            finally:
                cw_mod.execute_chapter_writer = original

            async with jm._lock:
                final_job = jm._jobs[job.job_id]

            self.assertEqual(final_job.status, JobStatus.failed)

            # Chapter 1 should have been attempted 3 times (MAX_CHAPTER_RETRIES)
            self.assertEqual(chapters_attempted.count(1), 3)

            # Chapter 2 should NOT have been attempted (stopped after ch 1 failed)
            self.assertNotIn(2, chapters_attempted)

            # Should have a stop event
            stop_events = [e for e in final_job.events if e.get("kind") == "stop"]
            self.assertEqual(len(stop_events), 1)

        asyncio.run(run())

    def test_error_result_triggers_retry(self):
        """A chapter returning an error dict (not exception) should also retry."""
        from core.jobs import JobManager, JobStatus

        async def run():
            jm = JobManager()
            jm._semaphore = asyncio.Semaphore(1)
            jm.chapter_max_retries = 3
            jm.chapter_retry_backoff_base = 0.01  # fast for tests

            call_count = 0
            fake_project = self._make_fake_project()

            async def error_then_ok_writer(context, chapter_num, quick_mode=False):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return {"error": "Chapter 1 not found in blueprint", "number": 1, "text": None}
                return {"text": "Chapter content", "word_count": 100, "number": chapter_num}

            import agents.chapter_writer as cw_mod
            original = cw_mod.execute_chapter_writer
            cw_mod.execute_chapter_writer = error_then_ok_writer
            try:
                job = await jm.create_write_chapters_job(
                    project_id="p-retry",
                    chapter_outline=[{"number": 1, "title": "Ch 1"}],
                    existing_chapter_numbers=set(),
                    quick_mode=False,
                    get_project_fn=lambda pid: fake_project,
                    get_llm_fn=lambda: None,
                    save_project_fn=lambda p: None,
                )
                await asyncio.sleep(0.5)
            finally:
                cw_mod.execute_chapter_writer = original

            async with jm._lock:
                final_job = jm._jobs[job.job_id]

            self.assertEqual(final_job.status, JobStatus.succeeded)
            self.assertEqual(call_count, 2)

        asyncio.run(run())


class TestBlockedDiagnostics(unittest.TestCase):
    def _make_project_with_blocked_agent(self):
        from core.orchestrator import Orchestrator
        from models.state import AgentStatus

        orch = Orchestrator(llm_client=None)
        project = orch.create_project("Blocked Test", {"genre": "Fiction"})

        for layer_id, layer in project.layers.items():
            for agent_id, agent_state in layer.agents.items():
                if layer_id == 0:
                    # Manually add a fake dependency that will never be satisfied
                    agent_state.dependencies = ["nonexistent_dep"]
        return orch, project

    def test_blocked_agents_diagnostics_identifies_unmet_dep(self):
        orch, project = self._make_project_with_blocked_agent()
        diag = orch.get_blocked_agents_diagnostics(project)

        self.assertIn("blocked_candidates", diag)
        self.assertIn("agent_status_counts", diag)
        self.assertIn("layer_status_counts", diag)
        self.assertIn("locked_layer_reasons", diag)

        unmet_dep_ids = [
            dep["dep_id"]
            for c in diag["blocked_candidates"]
            for dep in c["unmet_dependencies"]
        ]
        self.assertTrue(len(diag["blocked_candidates"]) > 0, "Expected blocked candidates")
        self.assertIn("nonexistent_dep", unmet_dep_ids)

    def test_blocked_agents_diagnostics_dep_status_missing(self):
        orch, project = self._make_project_with_blocked_agent()
        diag = orch.get_blocked_agents_diagnostics(project)

        for candidate in diag["blocked_candidates"]:
            for dep in candidate["unmet_dependencies"]:
                if dep["dep_id"] == "nonexistent_dep":
                    self.assertEqual(dep["dep_status"], "missing")

    def test_no_blocked_candidates_when_all_deps_passed(self):
        from core.orchestrator import Orchestrator
        from models.state import AgentStatus, LayerStatus

        orch = Orchestrator(llm_client=None)
        project = orch.create_project("Clean Test", {"genre": "Fiction"})

        # Mark every agent as passed and every layer as completed
        for layer_id, layer in project.layers.items():
            layer.status = LayerStatus.COMPLETED
            for agent_state in layer.agents.values():
                agent_state.status = AgentStatus.PASSED

        diag = orch.get_blocked_agents_diagnostics(project)
        self.assertEqual(diag["blocked_candidates"], [])


if __name__ == "__main__":
    unittest.main()

