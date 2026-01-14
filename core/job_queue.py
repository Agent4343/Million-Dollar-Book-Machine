"""
Background Job Queue for Long-Running Tasks

Uses PostgreSQL for job persistence to handle Railway timeouts.
Jobs are stored in the database and can survive process restarts.
"""

import json
import logging
import os
import uuid
import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    """Types of background jobs."""
    WRITE_CHAPTER = "write_chapter"
    WRITE_ALL_CHAPTERS = "write_all_chapters"
    RUN_VALIDATION = "run_validation"
    EXPORT_MANUSCRIPT = "export_manuscript"
    REGENERATE_CHAPTER = "regenerate_chapter"


@dataclass
class Job:
    """Represents a background job."""
    job_id: str
    job_type: JobType
    project_id: str
    status: JobStatus
    created_at: str
    updated_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress: int = 0  # 0-100
    progress_message: str = ""
    input_data: Dict[str, Any] = None
    result: Dict[str, Any] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "job_id": self.job_id,
            "job_type": self.job_type.value if isinstance(self.job_type, JobType) else self.job_type,
            "project_id": self.project_id,
            "status": self.status.value if isinstance(self.status, JobStatus) else self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "progress": self.progress,
            "progress_message": self.progress_message,
            "input_data": self.input_data,
            "result": self.result,
            "error": self.error
        }


class JobQueue:
    """
    PostgreSQL-backed job queue for background task processing.

    Designed to work with Railway's serverless environment where
    long-running HTTP requests may timeout.
    """

    def __init__(self):
        self._connection = None
        self._initialized = False
        # In-memory tracking of running jobs (for current process)
        self._running_jobs: Dict[str, asyncio.Task] = {}

    def _get_connection(self):
        """Get or create database connection."""
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            logger.warning("DATABASE_URL not set - job queue disabled")
            return None

        if self._connection is None:
            try:
                import psycopg2
                self._connection = psycopg2.connect(database_url)
                self._connection.autocommit = True
                self._init_schema()
                logger.info("Job queue connected to PostgreSQL")
            except Exception as e:
                logger.error(f"Failed to connect job queue to database: {e}")
                return None

        return self._connection

    def _init_schema(self):
        """Initialize job queue table."""
        if self._initialized:
            return

        conn = self._connection
        if not conn:
            return

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS jobs (
                        job_id VARCHAR(255) PRIMARY KEY,
                        job_type VARCHAR(100) NOT NULL,
                        project_id VARCHAR(255) NOT NULL,
                        status VARCHAR(50) NOT NULL DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        started_at TIMESTAMP,
                        completed_at TIMESTAMP,
                        progress INTEGER DEFAULT 0,
                        progress_message TEXT DEFAULT '',
                        input_data JSONB,
                        result JSONB,
                        error TEXT
                    )
                """)

                # Index for efficient queries
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_jobs_project_status
                    ON jobs (project_id, status)
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_jobs_status
                    ON jobs (status)
                """)

                self._initialized = True
                logger.info("Job queue schema initialized")
        except Exception as e:
            logger.error(f"Failed to initialize job queue schema: {e}")

    def create_job(
        self,
        job_type: JobType,
        project_id: str,
        input_data: Dict[str, Any] = None
    ) -> Optional[Job]:
        """
        Create a new job in pending state.

        Returns the job immediately - caller should start processing separately.
        """
        conn = self._get_connection()
        if not conn:
            return None

        job_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        job = Job(
            job_id=job_id,
            job_type=job_type,
            project_id=project_id,
            status=JobStatus.PENDING,
            created_at=now,
            updated_at=now,
            input_data=input_data or {}
        )

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO jobs (job_id, job_type, project_id, status,
                                     created_at, updated_at, input_data)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    job.job_id,
                    job.job_type.value,
                    job.project_id,
                    job.status.value,
                    job.created_at,
                    job.updated_at,
                    json.dumps(job.input_data)
                ))

            logger.info(f"Created job {job_id} ({job_type.value}) for project {project_id}")
            return job
        except Exception as e:
            logger.error(f"Failed to create job: {e}")
            return None

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID."""
        conn = self._get_connection()
        if not conn:
            return None

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT job_id, job_type, project_id, status,
                           created_at, updated_at, started_at, completed_at,
                           progress, progress_message, input_data, result, error
                    FROM jobs WHERE job_id = %s
                """, (job_id,))

                row = cur.fetchone()
                if not row:
                    return None

                return Job(
                    job_id=row[0],
                    job_type=JobType(row[1]),
                    project_id=row[2],
                    status=JobStatus(row[3]),
                    created_at=row[4].isoformat() if row[4] else None,
                    updated_at=row[5].isoformat() if row[5] else None,
                    started_at=row[6].isoformat() if row[6] else None,
                    completed_at=row[7].isoformat() if row[7] else None,
                    progress=row[8] or 0,
                    progress_message=row[9] or "",
                    input_data=row[10] if isinstance(row[10], dict) else json.loads(row[10] or "{}"),
                    result=row[11] if isinstance(row[11], dict) else json.loads(row[11] or "null"),
                    error=row[12]
                )
        except Exception as e:
            logger.error(f"Failed to get job {job_id}: {e}")
            return None

    def update_job_progress(
        self,
        job_id: str,
        progress: int,
        message: str = ""
    ) -> bool:
        """Update job progress (0-100)."""
        conn = self._get_connection()
        if not conn:
            return False

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE jobs
                    SET progress = %s,
                        progress_message = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE job_id = %s
                """, (progress, message, job_id))
            return True
        except Exception as e:
            logger.error(f"Failed to update job progress: {e}")
            return False

    def start_job(self, job_id: str) -> bool:
        """Mark job as running."""
        conn = self._get_connection()
        if not conn:
            return False

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE jobs
                    SET status = %s,
                        started_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE job_id = %s AND status = %s
                """, (JobStatus.RUNNING.value, job_id, JobStatus.PENDING.value))

            logger.info(f"Job {job_id} started")
            return True
        except Exception as e:
            logger.error(f"Failed to start job: {e}")
            return False

    def complete_job(self, job_id: str, result: Dict[str, Any] = None) -> bool:
        """Mark job as completed with result."""
        conn = self._get_connection()
        if not conn:
            return False

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE jobs
                    SET status = %s,
                        completed_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP,
                        progress = 100,
                        result = %s
                    WHERE job_id = %s
                """, (JobStatus.COMPLETED.value, json.dumps(result), job_id))

            logger.info(f"Job {job_id} completed")
            return True
        except Exception as e:
            logger.error(f"Failed to complete job: {e}")
            return False

    def fail_job(self, job_id: str, error: str) -> bool:
        """Mark job as failed with error message."""
        conn = self._get_connection()
        if not conn:
            return False

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE jobs
                    SET status = %s,
                        completed_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP,
                        error = %s
                    WHERE job_id = %s
                """, (JobStatus.FAILED.value, error, job_id))

            logger.error(f"Job {job_id} failed: {error}")
            return True
        except Exception as e:
            logger.error(f"Failed to mark job as failed: {e}")
            return False

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending or running job."""
        conn = self._get_connection()
        if not conn:
            return False

        # Cancel in-memory task if running
        if job_id in self._running_jobs:
            task = self._running_jobs[job_id]
            task.cancel()
            del self._running_jobs[job_id]

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE jobs
                    SET status = %s,
                        completed_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE job_id = %s AND status IN (%s, %s)
                """, (
                    JobStatus.CANCELLED.value,
                    job_id,
                    JobStatus.PENDING.value,
                    JobStatus.RUNNING.value
                ))

            logger.info(f"Job {job_id} cancelled")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel job: {e}")
            return False

    def get_project_jobs(
        self,
        project_id: str,
        status: Optional[JobStatus] = None,
        limit: int = 50
    ) -> List[Job]:
        """Get jobs for a project."""
        conn = self._get_connection()
        if not conn:
            return []

        try:
            with conn.cursor() as cur:
                if status:
                    cur.execute("""
                        SELECT job_id, job_type, project_id, status,
                               created_at, updated_at, started_at, completed_at,
                               progress, progress_message, input_data, result, error
                        FROM jobs
                        WHERE project_id = %s AND status = %s
                        ORDER BY created_at DESC
                        LIMIT %s
                    """, (project_id, status.value, limit))
                else:
                    cur.execute("""
                        SELECT job_id, job_type, project_id, status,
                               created_at, updated_at, started_at, completed_at,
                               progress, progress_message, input_data, result, error
                        FROM jobs
                        WHERE project_id = %s
                        ORDER BY created_at DESC
                        LIMIT %s
                    """, (project_id, limit))

                jobs = []
                for row in cur.fetchall():
                    jobs.append(Job(
                        job_id=row[0],
                        job_type=JobType(row[1]),
                        project_id=row[2],
                        status=JobStatus(row[3]),
                        created_at=row[4].isoformat() if row[4] else None,
                        updated_at=row[5].isoformat() if row[5] else None,
                        started_at=row[6].isoformat() if row[6] else None,
                        completed_at=row[7].isoformat() if row[7] else None,
                        progress=row[8] or 0,
                        progress_message=row[9] or "",
                        input_data=row[10] if isinstance(row[10], dict) else json.loads(row[10] or "{}"),
                        result=row[11] if isinstance(row[11], dict) else json.loads(row[11] or "null"),
                        error=row[12]
                    ))
                return jobs
        except Exception as e:
            logger.error(f"Failed to get project jobs: {e}")
            return []

    def cleanup_old_jobs(self, days: int = 7) -> int:
        """Delete jobs older than specified days."""
        conn = self._get_connection()
        if not conn:
            return 0

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM jobs
                    WHERE created_at < NOW() - INTERVAL '%s days'
                    AND status IN (%s, %s, %s)
                """, (days, JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.CANCELLED.value))

                deleted = cur.rowcount
                logger.info(f"Cleaned up {deleted} old jobs")
                return deleted
        except Exception as e:
            logger.error(f"Failed to cleanup old jobs: {e}")
            return 0

    def get_pending_jobs(self, limit: int = 10) -> List[Job]:
        """Get pending jobs for processing."""
        conn = self._get_connection()
        if not conn:
            return []

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT job_id, job_type, project_id, status,
                           created_at, updated_at, started_at, completed_at,
                           progress, progress_message, input_data, result, error
                    FROM jobs
                    WHERE status = %s
                    ORDER BY created_at ASC
                    LIMIT %s
                """, (JobStatus.PENDING.value, limit))

                jobs = []
                for row in cur.fetchall():
                    jobs.append(Job(
                        job_id=row[0],
                        job_type=JobType(row[1]),
                        project_id=row[2],
                        status=JobStatus(row[3]),
                        created_at=row[4].isoformat() if row[4] else None,
                        updated_at=row[5].isoformat() if row[5] else None,
                        started_at=row[6].isoformat() if row[6] else None,
                        completed_at=row[7].isoformat() if row[7] else None,
                        progress=row[8] or 0,
                        progress_message=row[9] or "",
                        input_data=row[10] if isinstance(row[10], dict) else json.loads(row[10] or "{}"),
                        result=row[11] if isinstance(row[11], dict) else json.loads(row[11] or "null"),
                        error=row[12]
                    ))
                return jobs
        except Exception as e:
            logger.error(f"Failed to get pending jobs: {e}")
            return []


# Singleton instance
_job_queue: Optional[JobQueue] = None


def get_job_queue() -> JobQueue:
    """Get the global job queue instance."""
    global _job_queue
    if _job_queue is None:
        _job_queue = JobQueue()
    return _job_queue
