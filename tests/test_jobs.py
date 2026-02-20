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


class TestBlockedDiagnostics(unittest.TestCase):
    def _make_project_with_blocked_agent(self):
        from core.orchestrator import Orchestrator
        from models.state import AgentStatus

        orch = Orchestrator(llm_client=None)
        project = orch.create_project("Blocked Test", {"genre": "Fiction"})

        # Mark layer 0 as in_progress but leave orchestrator (layer 0) as pending
        # so that layer 1 stays locked and something in layer 0 has an unmet dep.
        # Inject a fake dep on the layer-0 agent to simulate a block.
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

        # At least one blocked candidate should reference the fake dep
        agent_ids = [c["agent_id"] for c in diag["blocked_candidates"]]
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

