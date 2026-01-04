"""
Background job runner for long-running pipeline tasks.

Railway requests have time limits; generation can be long. This module provides
an in-process async job manager with file-based persistence of job state.

Note: This is not a distributed queue. If you scale to multiple instances,
jobs will live on the instance where they were started. For multi-instance
operation, swap the persistence + locking for Redis-based queueing.
"""

from __future__ import annotations

import asyncio
import os
import traceback
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from core.storage import get_job_store, get_project_store
from models.state import BookProject


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"
    interrupted = "interrupted"  # process restart / task lost


@dataclass
class JobRecord:
    job_id: str
    project_id: str
    status: JobStatus = JobStatus.queued
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    error: Optional[str] = None
    progress: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    cancel_requested: bool = False
    resumed_from_job_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "project_id": self.project_id,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "error": self.error,
            "progress": self.progress,
            "events": self.events[-200:],  # cap persisted chatter
            "cancel_requested": self.cancel_requested,
            "resumed_from_job_id": self.resumed_from_job_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JobRecord":
        return cls(
            job_id=str(data.get("job_id")),
            project_id=str(data.get("project_id")),
            status=JobStatus(str(data.get("status", JobStatus.queued.value))),
            created_at=str(data.get("created_at", datetime.utcnow().isoformat())),
            updated_at=str(data.get("updated_at", datetime.utcnow().isoformat())),
            started_at=data.get("started_at"),
            finished_at=data.get("finished_at"),
            error=data.get("error"),
            progress=data.get("progress") or {},
            events=data.get("events") or [],
            cancel_requested=bool(data.get("cancel_requested", False)),
            resumed_from_job_id=data.get("resumed_from_job_id"),
        )


class JobManager:
    def __init__(self):
        self._lock = asyncio.Lock()
        self._tasks: Dict[str, asyncio.Task] = {}
        self._jobs: Dict[str, JobRecord] = {}
        max_concurrent = int(os.environ.get("MAX_CONCURRENT_JOBS", "1") or "1")
        if max_concurrent < 1:
            max_concurrent = 1
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def load_persisted_jobs(self) -> None:
        """Load persisted jobs and mark running ones as interrupted."""
        store = get_job_store()
        async with self._lock:
            for jid in store.list_ids():
                raw = store.load_raw(jid)
                if not isinstance(raw, dict):
                    continue
                job = JobRecord.from_dict(raw)
                # A job that was RUNNING during a process restart is interrupted.
                # A job that was QUEUED can still be executed.
                if job.status == JobStatus.running:
                    job.status = JobStatus.interrupted
                    job.error = "Job was interrupted (process restart). Start a new job to resume."
                    job.finished_at = datetime.utcnow().isoformat()
                self._jobs[job.job_id] = job
                store.save_raw(job.job_id, job.to_dict())

    async def create_run_pipeline_job(
        self,
        *,
        project: BookProject,
        orchestrator: Any,
        max_iterations: int = 200,
    ) -> JobRecord:
        """
        Start a background job that runs the project through available agents,
        persisting project state and job state after each step.
        """
        # Concurrency guard: only one active job per project.
        active = await self.find_active_job_for_project(project.project_id)
        if active is not None:
            raise RuntimeError(f"Project already has an active job: {active.job_id}")

        job = JobRecord(job_id=str(uuid.uuid4()), project_id=project.project_id)

        store = get_job_store()
        store.save_raw(job.job_id, job.to_dict())

        async with self._lock:
            self._jobs[job.job_id] = job
            task = asyncio.create_task(
                self._run_pipeline(job_id=job.job_id, orchestrator=orchestrator, max_iterations=max_iterations)
            )
            self._tasks[job.job_id] = task

        return job

    async def resume_job(self, *, job_id: str, orchestrator: Any, max_iterations: int = 200) -> JobRecord:
        """
        Resume an interrupted/failed/cancelled job by starting a new job for the same project.
        The project state is already persisted; this simply continues running available agents.
        """
        prior = await self.get(job_id)
        if prior is None:
            raise KeyError(job_id)
        if prior.status not in (JobStatus.interrupted, JobStatus.failed, JobStatus.cancelled):
            raise RuntimeError(f"Job {job_id} is not resumable (status={prior.status.value}).")

        # Load project from orchestrator
        project = orchestrator.get_project(prior.project_id)
        if project is None:
            raise RuntimeError("Project not found in orchestrator.")

        active = await self.find_active_job_for_project(project.project_id)
        if active is not None:
            raise RuntimeError(f"Project already has an active job: {active.job_id}")

        job = JobRecord(job_id=str(uuid.uuid4()), project_id=project.project_id, resumed_from_job_id=prior.job_id)
        store = get_job_store()
        store.save_raw(job.job_id, job.to_dict())
        async with self._lock:
            self._jobs[job.job_id] = job
            task = asyncio.create_task(
                self._run_pipeline(job_id=job.job_id, orchestrator=orchestrator, max_iterations=max_iterations)
            )
            self._tasks[job.job_id] = task
        return job

    async def cancel(self, job_id: str) -> JobRecord:
        store = get_job_store()
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                raw = store.load_raw(job_id)
                if isinstance(raw, dict):
                    job = JobRecord.from_dict(raw)
                    self._jobs[job.job_id] = job
            if not job:
                raise KeyError(job_id)
            job.cancel_requested = True
            job.updated_at = datetime.utcnow().isoformat()
            store.save_raw(job.job_id, job.to_dict())
            return job

    async def get(self, job_id: str) -> Optional[JobRecord]:
        store = get_job_store()
        async with self._lock:
            job = self._jobs.get(job_id)
            if job:
                return job
        raw = store.load_raw(job_id)
        if not isinstance(raw, dict):
            return None
        job = JobRecord.from_dict(raw)
        async with self._lock:
            self._jobs[job.job_id] = job
        return job

    async def list(self, project_id: Optional[str] = None) -> List[JobRecord]:
        async with self._lock:
            jobs = list(self._jobs.values())
        if project_id:
            jobs = [j for j in jobs if j.project_id == project_id]
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs[:200]

    async def find_active_job_for_project(self, project_id: str) -> Optional[JobRecord]:
        """Return a queued/running job for a project if one exists."""
        async with self._lock:
            for job in self._jobs.values():
                if job.project_id == project_id and job.status in (JobStatus.queued, JobStatus.running):
                    return job
        return None

    def _append_event(self, job: JobRecord, kind: str, message: str, **extra: Any) -> None:
        job.events.append(
            {
                "ts": datetime.utcnow().isoformat(),
                "kind": kind,
                "message": message,
                **extra,
            }
        )

    async def _run_pipeline(self, *, job_id: str, orchestrator: Any, max_iterations: int) -> None:
        store = get_job_store()
        pstore = get_project_store()
        iterations = 0

        # Global concurrency cap (per instance)
        await self._semaphore.acquire()
        async with self._lock:
            job = self._jobs[job_id]
            job.status = JobStatus.running
            job.started_at = datetime.utcnow().isoformat()
            job.updated_at = datetime.utcnow().isoformat()
            self._append_event(job, "start", "Job started")
            store.save_raw(job.job_id, job.to_dict())

        try:
            while iterations < max_iterations:
                # Load cancel flag from disk (supports cancelling from another instance/process)
                raw = store.load_raw(job_id)
                if isinstance(raw, dict) and raw.get("cancel_requested") is True:
                    async with self._lock:
                        job = self._jobs.get(job_id)
                        if job:
                            job.cancel_requested = True

                async with self._lock:
                    job = self._jobs[job_id]
                    if job.cancel_requested:
                        job.status = JobStatus.cancelled
                        job.finished_at = datetime.utcnow().isoformat()
                        job.updated_at = datetime.utcnow().isoformat()
                        self._append_event(job, "cancel", "Cancellation requested; stopping.")
                        store.save_raw(job.job_id, job.to_dict())
                        return

                # Reload project from orchestrator (in case it changed)
                project = orchestrator.get_project(job.project_id)
                if project is None:
                    raise RuntimeError("Project not found in orchestrator.")

                available = orchestrator.get_available_agents(project)
                if not available:
                    # done or blocked
                    status = orchestrator.get_project_status(project)
                    async with self._lock:
                        job = self._jobs[job_id]
                        job.progress = {
                            "iterations": iterations,
                            "project_status": status.get("status"),
                            "current_layer": status.get("current_layer"),
                            "current_agent": status.get("current_agent"),
                        }
                        if status.get("status") == "completed":
                            job.status = JobStatus.succeeded
                            self._append_event(job, "complete", "Project completed")
                        else:
                            job.status = JobStatus.failed
                            job.error = "Project blocked (no available agents)."
                            self._append_event(job, "blocked", "Project blocked: no available agents")
                        job.finished_at = datetime.utcnow().isoformat()
                        job.updated_at = datetime.utcnow().isoformat()
                        store.save_raw(job.job_id, job.to_dict())
                    # Persist project state snapshot too
                    pstore.save_raw(project.project_id, orchestrator.export_project_state(project))
                    return

                agent_id = available[0]
                self._append_event(job, "step", f"Executing agent {agent_id}", agent_id=agent_id)

                output = await orchestrator.execute_agent(project, agent_id)
                # Persist project after each step
                pstore.save_raw(project.project_id, orchestrator.export_project_state(project))

                # Update job progress
                status = orchestrator.get_project_status(project)
                async with self._lock:
                    job = self._jobs[job_id]
                    job.progress = {
                        "iterations": iterations + 1,
                        "last_agent": agent_id,
                        "last_gate_passed": bool(output.gate_result.passed) if output.gate_result else False,
                        "last_gate_message": output.gate_result.message if output.gate_result else None,
                        "project_status": status.get("status"),
                        "current_layer": status.get("current_layer"),
                        "current_agent": status.get("current_agent"),
                        "available_agents_count": len(status.get("available_agents") or []),
                    }
                    job.updated_at = datetime.utcnow().isoformat()
                    store.save_raw(job.job_id, job.to_dict())

                iterations += 1

            # Iteration cap hit
            async with self._lock:
                job = self._jobs[job_id]
                job.status = JobStatus.failed
                job.error = f"Max iterations reached ({max_iterations})."
                job.finished_at = datetime.utcnow().isoformat()
                job.updated_at = datetime.utcnow().isoformat()
                self._append_event(job, "error", job.error)
                store.save_raw(job.job_id, job.to_dict())

        except Exception as e:
            async with self._lock:
                job = self._jobs[job_id]
                job.status = JobStatus.failed
                job.error = f"{e}\n{traceback.format_exc()}"
                job.finished_at = datetime.utcnow().isoformat()
                job.updated_at = datetime.utcnow().isoformat()
                self._append_event(job, "exception", "Job failed with exception", error=str(e))
                store.save_raw(job.job_id, job.to_dict())

        finally:
            async with self._lock:
                self._tasks.pop(job_id, None)
            self._semaphore.release()

