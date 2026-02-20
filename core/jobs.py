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
        # Mark as running immediately so clients don't see a long "queued" period
        # before the async task gets CPU time.
        job.status = JobStatus.running
        job.started_at = datetime.utcnow().isoformat()
        job.updated_at = datetime.utcnow().isoformat()
        self._append_event(job, "start", "Job scheduled")
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
        job.status = JobStatus.running
        job.started_at = datetime.utcnow().isoformat()
        job.updated_at = datetime.utcnow().isoformat()
        self._append_event(job, "start", "Job scheduled (resume)", resumed_from=prior.job_id)
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

        # Mark running immediately so the UI doesn't appear "stuck queued"
        # if we're waiting for a concurrency slot.
        async with self._lock:
            job = self._jobs[job_id]
            job.status = JobStatus.running
            job.started_at = datetime.utcnow().isoformat()
            job.updated_at = datetime.utcnow().isoformat()
            self._append_event(job, "start", "Job started")
            store.save_raw(job.job_id, job.to_dict())

        # Global concurrency cap (per instance) with a short timeout to avoid
        # "queued forever" if something goes wrong with semaphore release.
        acquired = False
        try:
            await asyncio.wait_for(self._semaphore.acquire(), timeout=10.0)
            acquired = True
        except Exception:
            async with self._lock:
                job = self._jobs[job_id]
                job.status = JobStatus.failed
                job.error = "Could not acquire job slot (MAX_CONCURRENT_JOBS limit). Try again or increase MAX_CONCURRENT_JOBS."
                job.finished_at = datetime.utcnow().isoformat()
                job.updated_at = datetime.utcnow().isoformat()
                self._append_event(job, "error", job.error)
                store.save_raw(job.job_id, job.to_dict())
            return

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
            if acquired:
                self._semaphore.release()

    async def create_write_chapters_job(
        self,
        *,
        project_id: str,
        chapter_outline: List[Dict[str, Any]],
        existing_chapter_numbers: set,
        quick_mode: bool = False,
        get_project_fn: Any,
        get_llm_fn: Any,
        save_project_fn: Any,
    ) -> "JobRecord":
        """
        Start a background job that writes all remaining chapters in order.

        get_project_fn(project_id) -> BookProject  (callable, not persisted)
        get_llm_fn() -> LLM client                (callable, not persisted)
        save_project_fn(project) -> None           (callable, not persisted)

        Only serializable values are stored in the job record.
        """
        active = await self.find_active_job_for_project(project_id)
        if active is not None:
            raise RuntimeError(f"Project already has an active job: {active.job_id}")

        # Sort chapters by number to guarantee in-order writing.
        ordered = sorted(chapter_outline, key=lambda c: c.get("number", 0))
        chapters_to_write = [c for c in ordered if c.get("number") not in existing_chapter_numbers]

        job = JobRecord(job_id=str(uuid.uuid4()), project_id=project_id)
        store = get_job_store()
        job.status = JobStatus.running
        job.started_at = datetime.utcnow().isoformat()
        job.updated_at = datetime.utcnow().isoformat()
        job.progress = {
            "total": len(chapter_outline),
            "remaining": [c.get("number") for c in chapters_to_write],
            "written": sorted(existing_chapter_numbers),
            "failed": [],
            "quick_mode": quick_mode,
        }
        self._append_event(
            job, "start",
            f"Chapter writing job started; {len(chapters_to_write)} chapter(s) to write",
        )
        store.save_raw(job.job_id, job.to_dict())

        async with self._lock:
            self._jobs[job.job_id] = job
            task = asyncio.create_task(
                self._run_write_chapters(
                    job_id=job.job_id,
                    project_id=project_id,
                    chapter_outline=ordered,
                    existing_chapter_numbers=set(existing_chapter_numbers),
                    quick_mode=quick_mode,
                    get_project_fn=get_project_fn,
                    get_llm_fn=get_llm_fn,
                    save_project_fn=save_project_fn,
                )
            )
            self._tasks[job.job_id] = task

        return job

    async def _run_write_chapters(
        self,
        *,
        job_id: str,
        project_id: str,
        chapter_outline: List[Dict[str, Any]],
        existing_chapter_numbers: set,
        quick_mode: bool,
        get_project_fn: Any,
        get_llm_fn: Any,
        save_project_fn: Any,
    ) -> None:
        from core.orchestrator import ExecutionContext
        from agents.chapter_writer import execute_chapter_writer

        store = get_job_store()
        written: List[int] = sorted(existing_chapter_numbers)
        failed: List[Dict[str, Any]] = []

        # Acquire concurrency slot with short timeout to avoid waiting forever.
        acquired = False
        try:
            await asyncio.wait_for(self._semaphore.acquire(), timeout=10.0)
            acquired = True
        except Exception:
            async with self._lock:
                job = self._jobs[job_id]
                job.status = JobStatus.failed
                job.error = (
                    "Could not acquire job slot (MAX_CONCURRENT_JOBS limit). "
                    "Try again or increase MAX_CONCURRENT_JOBS."
                )
                job.finished_at = datetime.utcnow().isoformat()
                job.updated_at = datetime.utcnow().isoformat()
                self._append_event(job, "error", job.error)
                store.save_raw(job.job_id, job.to_dict())
            return

        try:
            # Chapters to write in ascending order, skipping already-written ones.
            chapters_to_write = [
                c for c in chapter_outline
                if c.get("number") not in existing_chapter_numbers
            ]

            for ch in chapters_to_write:
                # Check cancellation before each chapter.
                raw = store.load_raw(job_id)
                if isinstance(raw, dict) and raw.get("cancel_requested"):
                    async with self._lock:
                        job = self._jobs[job_id]
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

                chapter_num = ch.get("number")

                async with self._lock:
                    self._append_event(
                        self._jobs[job_id], "step",
                        f"Writing chapter {chapter_num}",
                        chapter=chapter_num,
                    )
                    store.save_raw(job_id, self._jobs[job_id].to_dict())

                try:
                    # Rebuild project and LLM client fresh for each chapter so
                    # transient objects are not stored in persisted job state.
                    project = get_project_fn(project_id)
                    if project is None:
                        raise RuntimeError(f"Project {project_id} not found")

                    llm_client = get_llm_fn()

                    # Gather all agent outputs as inputs for the chapter writer.
                    inputs: Dict[str, Any] = {}
                    for layer in project.layers.values():
                        for aid, agent_state in layer.agents.items():
                            if agent_state.current_output:
                                inputs[aid] = agent_state.current_output.content

                    context = ExecutionContext(
                        project=project,
                        inputs=inputs,
                        llm_client=llm_client,
                    )

                    result = await execute_chapter_writer(context, chapter_num, quick_mode=quick_mode)

                    if result.get("text") is not None and not result.get("error"):
                        # Persist chapter into manuscript.
                        if "chapters" not in project.manuscript:
                            project.manuscript["chapters"] = []
                        chapter_exists = False
                        for idx, existing_ch in enumerate(project.manuscript["chapters"]):
                            if existing_ch.get("number") == chapter_num:
                                project.manuscript["chapters"][idx] = result
                                chapter_exists = True
                                break
                        if not chapter_exists:
                            project.manuscript["chapters"].append(result)
                        project.manuscript["chapters"].sort(key=lambda x: x.get("number", 0))
                        written.append(chapter_num)
                        save_project_fn(project)

                        async with self._lock:
                            self._append_event(
                                self._jobs[job_id], "chapter_success",
                                f"Chapter {chapter_num} written ({result.get('word_count', 0)} words)",
                                chapter=chapter_num,
                                word_count=result.get("word_count", 0),
                            )
                    else:
                        err_msg = result.get("error") or "No text returned"
                        failed.append({"number": chapter_num, "error": err_msg})
                        async with self._lock:
                            self._append_event(
                                self._jobs[job_id], "chapter_fail",
                                f"Chapter {chapter_num} failed: {err_msg}",
                                chapter=chapter_num,
                                error=err_msg,
                            )

                except Exception as exc:
                    err_detail = f"{exc}\n{traceback.format_exc()}"
                    failed.append({"number": chapter_num, "error": str(exc)})
                    async with self._lock:
                        self._append_event(
                            self._jobs[job_id], "chapter_fail",
                            f"Chapter {chapter_num} failed: {exc}",
                            chapter=chapter_num,
                            error=err_detail,
                        )

                # Update progress after each chapter attempt.
                async with self._lock:
                    job = self._jobs[job_id]
                    remaining = [
                        c.get("number") for c in chapter_outline
                        if c.get("number") not in set(written)
                    ]
                    job.progress = {
                        "total": len(chapter_outline),
                        "written": sorted(written),
                        "remaining": remaining,
                        "failed": failed,
                        "quick_mode": quick_mode,
                    }
                    job.updated_at = datetime.utcnow().isoformat()
                    store.save_raw(job.job_id, job.to_dict())

            # All chapters attempted; compute final state.
            async with self._lock:
                job = self._jobs[job_id]
                remaining = [
                    c.get("number") for c in chapter_outline
                    if c.get("number") not in set(written)
                ]
                job.progress = {
                    "total": len(chapter_outline),
                    "written": sorted(written),
                    "remaining": remaining,
                    "failed": failed,
                    "quick_mode": quick_mode,
                }
                if not remaining and not failed:
                    job.status = JobStatus.succeeded
                    self._append_event(
                        job, "complete",
                        f"All {len(written)} chapter(s) written successfully.",
                    )
                elif not remaining and failed:
                    # All planned chapters attempted; some failed.
                    job.status = JobStatus.failed
                    job.error = (
                        f"{len(failed)} chapter(s) failed: "
                        + ", ".join(str(f['number']) for f in failed)
                    )
                    self._append_event(job, "complete", job.error)
                else:
                    job.status = JobStatus.failed
                    job.error = (
                        f"{len(failed)} chapter(s) failed, "
                        f"{len(remaining)} chapter(s) remaining."
                    )
                    self._append_event(job, "error", job.error)
                job.finished_at = datetime.utcnow().isoformat()
                job.updated_at = datetime.utcnow().isoformat()
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
            if acquired:
                self._semaphore.release()

