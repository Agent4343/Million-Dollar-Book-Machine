"""
Tests for:
1. draft_generation timeout-resilience (per-chapter timeout, failed_chapters list)
2. draft_generation progress_callback (called once per chapter with correct fields)
3. heartbeat events emitted during long-running agents in _run_pipeline
"""

import asyncio
import unittest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_outline(n: int):
    """Build a minimal chapter_outline list with n chapters."""
    return [
        {
            "number": i,
            "title": f"Chapter {i}",
            "act": 1,
            "chapter_goal": f"Goal {i}",
            "pov": "Protagonist",
            "opening_hook": f"Hook {i}",
            "closing_hook": f"Close {i}",
            "word_target": 100,
            "scenes": [
                {
                    "scene_number": 1,
                    "scene_question": "Q",
                    "characters": [],
                    "location": "L",
                    "conflict_type": "internal",
                    "outcome": "O",
                    "word_target": 100,
                }
            ],
        }
        for i in range(1, n + 1)
    ]


def _make_context(llm):
    """Build a minimal ExecutionContext with the given llm client."""
    from core.orchestrator import ExecutionContext

    project = MagicMock()
    inputs = {
        "chapter_blueprint": {"chapter_outline": _make_outline(3)},
        "voice_specification": {},
        "character_architecture": {},
        "world_rules": {},
    }
    return ExecutionContext(project=project, inputs=inputs, llm_client=llm)


# ---------------------------------------------------------------------------
# Test 1 – timeout on chapter 2 → chapter 2 in failed_chapters, others ok
# ---------------------------------------------------------------------------

class TestDraftGenerationTimeoutContinues(unittest.IsolatedAsyncioTestCase):
    """Chapter-level timeout should be skipped, not abort the whole agent."""

    async def test_timeout_chapter_in_failed_chapters_others_generated(self):
        from agents.structural import execute_draft_generation

        # For chapter 2, raise TimeoutError on the text-generation call;
        # detect chapter 2 from the prompt content.
        async def fake_generate(prompt, **kwargs):
            prompt_str = str(prompt)
            if "Write Chapter 2:" in prompt_str:
                raise asyncio.TimeoutError()
            if kwargs.get("response_format") == "json":
                return {
                    "outline_adherence_score": 90,
                    "scene_checks": [],
                    "chapter_deviations": [],
                }
            return "Chapter text with several words"

        llm = MagicMock()
        llm.generate = fake_generate

        # Pass-through wait_for so TimeoutError from fake_generate propagates.
        async def passthrough_wait_for(coro, timeout):
            return await coro

        with patch("agents.structural.asyncio.wait_for", new=passthrough_wait_for):
            result = await execute_draft_generation(_make_context(llm))

        chapters = result["chapters"]
        failed = result["failed_chapters"]

        chapter_nums = [c["number"] for c in chapters]
        self.assertIn(1, chapter_nums, "Chapter 1 should be generated")
        self.assertIn(3, chapter_nums, "Chapter 3 should be generated")
        self.assertNotIn(2, chapter_nums, "Chapter 2 timed out and must not appear in chapters")

        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0]["chapter"], 2)
        self.assertIn("timeout", failed[0]["error"].lower())


# ---------------------------------------------------------------------------
# Test 2 – progress_callback called once per chapter with correct fields
# ---------------------------------------------------------------------------

class TestDraftGenerationProgressCallback(unittest.IsolatedAsyncioTestCase):
    """progress_callback must be called once per chapter with required fields."""

    async def test_callback_called_per_chapter_with_correct_fields(self):
        from agents.structural import execute_draft_generation

        async def fake_generate(prompt, **kwargs):
            if kwargs.get("response_format") == "json":
                return {
                    "outline_adherence_score": 80,
                    "scene_checks": [],
                    "chapter_deviations": [],
                }
            return "Some chapter text with several words here"

        llm = MagicMock()
        llm.generate = fake_generate

        received: list = []

        async def cb(data: dict) -> None:
            received.append(dict(data))

        async def passthrough_wait_for(coro, timeout):
            return await coro

        with patch("agents.structural.asyncio.wait_for", new=passthrough_wait_for):
            result = await execute_draft_generation(_make_context(llm), progress_callback=cb)

        chapters_total = len(_make_outline(3))
        self.assertEqual(len(received), chapters_total, "callback must fire once per chapter")

        for i, data in enumerate(received, start=1):
            self.assertIn("chapter", data)
            self.assertIn("status", data)
            self.assertIn("word_count", data)
            self.assertIn("chapters_done", data)
            self.assertIn("chapters_total", data)
            self.assertEqual(data["chapters_total"], chapters_total)
            self.assertEqual(data["chapters_done"], i)
            self.assertEqual(data["status"], "ok")


# ---------------------------------------------------------------------------
# Test 3 – heartbeat events appear in job during long-running execute_agent
# ---------------------------------------------------------------------------

class TestHeartbeatEmittedDuringLongAgent(unittest.IsolatedAsyncioTestCase):
    """At least one heartbeat event should appear when the agent runs longer than the interval."""

    async def test_heartbeat_event_emitted(self):
        import uuid
        import core.jobs as jobs_module
        from core.jobs import JobManager, JobRecord, JobStatus
        from core.storage import get_job_store

        # Very short heartbeat interval so the test finishes in milliseconds.
        FAST_INTERVAL = 0.05  # seconds

        jm = JobManager()

        project_id = str(uuid.uuid4())
        job = JobRecord(job_id=str(uuid.uuid4()), project_id=project_id)
        job.status = JobStatus.running
        jm._jobs[job.job_id] = job

        store = get_job_store()
        store.save_raw(job.job_id, job.to_dict())

        call_count = {"n": 0}

        class FakeAgentOutput:
            gate_result = MagicMock(passed=True, message="ok")

        class FakeOrchestrator:
            def get_project(self, pid):
                return MagicMock(project_id=pid)

            def get_available_agents(self, project):
                call_count["n"] += 1
                return ["some_agent"] if call_count["n"] == 1 else []

            async def execute_agent(self, project, agent_id, executor=None, progress_callback=None):
                # Sleep for 5× the heartbeat interval so the heartbeat fires at
                # least once before this completes.
                await asyncio.sleep(FAST_INTERVAL * 5)
                return FakeAgentOutput()

            def get_project_status(self, project):
                return {
                    "status": "completed",
                    "current_layer": 0,
                    "current_agent": None,
                    "available_agents": [],
                }

            def get_blocked_agents_diagnostics(self, project):
                return {
                    "blocked_candidates": [],
                    "agent_status_counts": {},
                    "layer_status_counts": {},
                }

            def export_project_state(self, project):
                return {}

        orch = FakeOrchestrator()

        # Patch the module-level HEARTBEAT_INTERVAL so the _heartbeat closure
        # inside _run_pipeline picks up the short interval as its default value.
        with patch.object(jobs_module, "HEARTBEAT_INTERVAL", FAST_INTERVAL):
            await jm._run_pipeline(
                job_id=job.job_id,
                orchestrator=orch,
                max_iterations=10,
            )

        final_job = jm._jobs.get(job.job_id)
        self.assertIsNotNone(final_job)

        heartbeat_events = [e for e in final_job.events if e.get("kind") == "heartbeat"]
        self.assertGreater(len(heartbeat_events), 0, "Expected at least one heartbeat event")


if __name__ == "__main__":
    unittest.main()
