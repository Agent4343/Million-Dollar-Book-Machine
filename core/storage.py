"""
Simple project persistence layer (file-based).

Railway restarts will wipe in-memory state. This store writes each project as a
single JSON file so projects can be restored on startup.

Set PROJECT_STORAGE_DIR to a persistent volume path (recommended: /data/projects).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


def _default_storage_dir() -> str:
    # Railway persistent volumes are commonly mounted at /data
    if os.path.isdir("/data") and os.access("/data", os.W_OK):
        return "/data/projects"
    return os.path.join(os.getcwd(), "data", "projects")


def _atomic_write_json(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


@dataclass
class FileProjectStore:
    base_dir: str

    def project_path(self, project_id: str) -> str:
        return os.path.join(self.base_dir, f"{project_id}.json")

    def list_project_ids(self) -> List[str]:
        if not os.path.isdir(self.base_dir):
            return []
        ids: List[str] = []
        for name in os.listdir(self.base_dir):
            if name.endswith(".json"):
                ids.append(name[:-5])
        return ids

    def load_raw(self, project_id: str) -> Optional[Dict[str, Any]]:
        path = self.project_path(project_id)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_raw(self, project_id: str, data: Dict[str, Any]) -> None:
        _atomic_write_json(self.project_path(project_id), data)


@dataclass
class FileJobStore:
    base_dir: str

    def job_path(self, job_id: str) -> str:
        return os.path.join(self.base_dir, f"{job_id}.json")

    def list_ids(self) -> List[str]:
        if not os.path.isdir(self.base_dir):
            return []
        ids: List[str] = []
        for name in os.listdir(self.base_dir):
            if name.endswith(".json"):
                ids.append(name[:-5])
        return ids

    def load_raw(self, job_id: str) -> Optional[Dict[str, Any]]:
        path = self.job_path(job_id)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_raw(self, job_id: str, data: Dict[str, Any]) -> None:
        _atomic_write_json(self.job_path(job_id), data)


_store_singleton: Optional[FileProjectStore] = None
_job_store_singleton: Optional[FileJobStore] = None


def get_project_store() -> FileProjectStore:
    global _store_singleton
    if _store_singleton is None:
        base = os.environ.get("PROJECT_STORAGE_DIR") or _default_storage_dir()
        _store_singleton = FileProjectStore(base_dir=base)
        os.makedirs(_store_singleton.base_dir, exist_ok=True)
    return _store_singleton


def _default_jobs_dir() -> str:
    if os.path.isdir("/data") and os.access("/data", os.W_OK):
        return "/data/jobs"
    return os.path.join(os.getcwd(), "data", "jobs")


def get_job_store() -> FileJobStore:
    global _job_store_singleton
    if _job_store_singleton is None:
        base = os.environ.get("JOB_STORAGE_DIR") or _default_jobs_dir()
        _job_store_singleton = FileJobStore(base_dir=base)
        os.makedirs(_job_store_singleton.base_dir, exist_ok=True)
    return _job_store_singleton

