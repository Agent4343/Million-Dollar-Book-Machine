"""
Disk Persistence Manager for Book Projects

Adds automatic disk persistence, chapter versioning, and content
deduplication to the existing BookProject system.
"""

import hashlib
import json
import os
import shutil
from datetime import datetime
from typing import Dict, Optional, List, Any

from models.state import BookProject, LayerStatus, AgentStatus


class DiskPersistenceManager:
    """
    Manages disk persistence for BookProject instances.

    Features:
    - Auto-save project state to JSON
    - Per-chapter markdown files with version history
    - Content hashing for duplicate detection
    - Automatic backups on chapter updates
    """

    def __init__(self, output_dir: str = "./book_projects"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Cache of content hashes to detect duplicates
        self._content_hashes: Dict[str, Dict[str, str]] = {}  # project_id -> {hash: chapter_num}

    def _get_project_dir(self, project_id: str) -> str:
        """Get the directory for a specific project."""
        project_dir = os.path.join(self.output_dir, project_id)
        os.makedirs(project_dir, exist_ok=True)
        return project_dir

    def _get_chapters_dir(self, project_id: str) -> str:
        """Get the chapters directory for a project."""
        chapters_dir = os.path.join(self._get_project_dir(project_id), "chapters")
        os.makedirs(chapters_dir, exist_ok=True)
        return chapters_dir

    def _get_backups_dir(self, project_id: str) -> str:
        """Get the backups directory for a project."""
        backups_dir = os.path.join(self._get_project_dir(project_id), "backups")
        os.makedirs(backups_dir, exist_ok=True)
        return backups_dir

    def _compute_content_hash(self, content: str) -> str:
        """Compute a hash of chapter content for duplicate detection."""
        # Normalize whitespace before hashing
        normalized = ' '.join(content.split())
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def _load_content_hashes(self, project_id: str) -> Dict[str, str]:
        """Load content hashes for a project."""
        if project_id in self._content_hashes:
            return self._content_hashes[project_id]

        hash_file = os.path.join(self._get_project_dir(project_id), "content_hashes.json")
        if os.path.exists(hash_file):
            with open(hash_file, 'r') as f:
                self._content_hashes[project_id] = json.load(f)
        else:
            self._content_hashes[project_id] = {}

        return self._content_hashes[project_id]

    def _save_content_hashes(self, project_id: str):
        """Save content hashes for a project."""
        hash_file = os.path.join(self._get_project_dir(project_id), "content_hashes.json")
        with open(hash_file, 'w') as f:
            json.dump(self._content_hashes.get(project_id, {}), f, indent=2)

    def check_duplicate_content(self, project_id: str, content: str) -> Optional[int]:
        """
        Check if content is a duplicate of an existing chapter.

        Returns the chapter number if duplicate found, None otherwise.
        """
        content_hash = self._compute_content_hash(content)
        hashes = self._load_content_hashes(project_id)

        if content_hash in hashes:
            return int(hashes[content_hash])
        return None

    def save_project_state(self, project: BookProject):
        """Save the complete project state to disk."""
        project_dir = self._get_project_dir(project.project_id)
        state_file = os.path.join(project_dir, "project_state.json")

        # Build serializable state
        state = {
            "version": "1.0",
            "project_id": project.project_id,
            "title": project.title,
            "status": project.status,
            "current_layer": project.current_layer,
            "user_constraints": project.user_constraints,
            "created_at": project.created_at,
            "updated_at": datetime.now().isoformat(),
            "manuscript": project.manuscript,
            "layers": {}
        }

        # Serialize layer states
        for layer_id, layer in project.layers.items():
            state["layers"][str(layer_id)] = {
                "name": layer.name,
                "status": layer.status.value,
                "agents": {}
            }
            for agent_id, agent_state in layer.agents.items():
                agent_data = {
                    "status": agent_state.status.value,
                    "attempts": agent_state.attempts,
                    "output": None
                }
                if agent_state.current_output:
                    agent_data["output"] = {
                        "content": agent_state.current_output.content,
                        "gate_passed": agent_state.current_output.gate_result.passed if agent_state.current_output.gate_result else None,
                        "gate_message": agent_state.current_output.gate_result.message if agent_state.current_output.gate_result else None
                    }
                state["layers"][str(layer_id)]["agents"][agent_id] = agent_data

        # Write state file
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)

        # Also save individual chapter files
        self._save_chapter_files(project)

    def _save_chapter_files(self, project: BookProject):
        """Save each chapter as a separate markdown file."""
        chapters = project.manuscript.get("chapters", [])
        chapters_dir = self._get_chapters_dir(project.project_id)
        hashes = self._load_content_hashes(project.project_id)

        for chapter in chapters:
            chapter_num = chapter.get("number", 0)
            title = chapter.get("title", f"Chapter {chapter_num}")
            text = chapter.get("text", "")

            if not text:
                continue

            # Create safe filename
            safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in title)
            filename = f"chapter_{chapter_num:02d}_{safe_title[:30]}.md"
            filepath = os.path.join(chapters_dir, filename)

            # Compute and store content hash
            content_hash = self._compute_content_hash(text)
            hashes[content_hash] = str(chapter_num)

            # Write chapter file
            with open(filepath, 'w') as f:
                f.write(f"# Chapter {chapter_num}: {title}\n\n")
                f.write(text)

        self._save_content_hashes(project.project_id)

    def save_chapter_with_backup(
        self,
        project: BookProject,
        chapter_num: int,
        new_content: str,
        editor: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Save a chapter update with automatic backup of previous version.

        Returns info about the save operation.
        """
        chapters = project.manuscript.get("chapters", [])
        existing_chapter = None
        existing_index = None

        for i, ch in enumerate(chapters):
            if ch.get("number") == chapter_num:
                existing_chapter = ch
                existing_index = i
                break

        result = {
            "chapter_num": chapter_num,
            "is_new": existing_chapter is None,
            "backup_created": False,
            "duplicate_warning": None
        }

        # Check for duplicate content
        duplicate_of = self.check_duplicate_content(project.project_id, new_content)
        if duplicate_of and duplicate_of != chapter_num:
            result["duplicate_warning"] = f"Content is similar to chapter {duplicate_of}"

        # Create backup if chapter exists
        if existing_chapter and existing_chapter.get("text"):
            backup_dir = self._get_backups_dir(project.project_id)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"chapter_{chapter_num:02d}_backup_{timestamp}.md"
            backup_path = os.path.join(backup_dir, backup_filename)

            with open(backup_path, 'w') as f:
                f.write(f"# Chapter {chapter_num}: {existing_chapter.get('title', 'Untitled')}\n")
                f.write(f"# Backup created: {timestamp}\n")
                f.write(f"# Previous editor: {existing_chapter.get('last_editor', 'unknown')}\n\n")
                f.write(existing_chapter["text"])

            result["backup_created"] = True
            result["backup_file"] = backup_filename

        # Update chapter metadata
        word_count = len(new_content.split())
        content_hash = self._compute_content_hash(new_content)

        chapter_data = {
            "number": chapter_num,
            "title": existing_chapter.get("title", f"Chapter {chapter_num}") if existing_chapter else f"Chapter {chapter_num}",
            "text": new_content,
            "word_count": word_count,
            "content_hash": content_hash,
            "last_editor": editor,
            "last_updated": datetime.now().isoformat()
        }

        if existing_index is not None:
            # Preserve original fields
            for key in ["title", "pov", "summary"]:
                if key in existing_chapter and key not in chapter_data:
                    chapter_data[key] = existing_chapter[key]
            project.manuscript["chapters"][existing_index] = chapter_data
        else:
            if "chapters" not in project.manuscript:
                project.manuscript["chapters"] = []
            project.manuscript["chapters"].append(chapter_data)
            project.manuscript["chapters"].sort(key=lambda x: x.get("number", 0))

        # Save to disk
        self.save_project_state(project)

        return result

    def load_project_state(self, project_id: str) -> Optional[Dict]:
        """Load project state from disk."""
        state_file = os.path.join(self._get_project_dir(project_id), "project_state.json")

        if not os.path.exists(state_file):
            return None

        with open(state_file, 'r') as f:
            return json.load(f)

    def list_saved_projects(self) -> List[Dict[str, str]]:
        """List all saved projects."""
        projects = []

        if not os.path.exists(self.output_dir):
            return projects

        for project_id in os.listdir(self.output_dir):
            state_file = os.path.join(self.output_dir, project_id, "project_state.json")
            if os.path.exists(state_file):
                try:
                    with open(state_file, 'r') as f:
                        state = json.load(f)
                        projects.append({
                            "project_id": project_id,
                            "title": state.get("title", "Untitled"),
                            "updated_at": state.get("updated_at", "Unknown"),
                            "status": state.get("status", "unknown")
                        })
                except (json.JSONDecodeError, KeyError):
                    continue

        return projects

    def get_chapter_versions(self, project_id: str, chapter_num: int) -> List[Dict]:
        """Get list of backup versions for a chapter."""
        backups_dir = self._get_backups_dir(project_id)
        versions = []

        prefix = f"chapter_{chapter_num:02d}_backup_"

        for filename in os.listdir(backups_dir):
            if filename.startswith(prefix):
                filepath = os.path.join(backups_dir, filename)
                stat = os.stat(filepath)
                versions.append({
                    "filename": filename,
                    "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "size_bytes": stat.st_size
                })

        return sorted(versions, key=lambda x: x["created_at"], reverse=True)

    def restore_chapter_version(
        self,
        project: BookProject,
        chapter_num: int,
        backup_filename: str
    ) -> bool:
        """Restore a chapter from a backup version."""
        backup_path = os.path.join(
            self._get_backups_dir(project.project_id),
            backup_filename
        )

        if not os.path.exists(backup_path):
            return False

        with open(backup_path, 'r') as f:
            content = f.read()

        # Remove header lines (first 3 lines are metadata)
        lines = content.split('\n')
        content = '\n'.join(lines[4:])  # Skip header lines

        # Save current as backup, then restore
        self.save_chapter_with_backup(
            project,
            chapter_num,
            content,
            editor="restore_operation"
        )

        return True

    def export_manuscript(self, project: BookProject, output_path: Optional[str] = None) -> str:
        """Export complete manuscript as a single markdown file."""
        if output_path is None:
            safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in project.title)
            output_path = os.path.join(
                self._get_project_dir(project.project_id),
                f"{safe_title}_manuscript.md"
            )

        chapters = project.manuscript.get("chapters", [])
        total_words = sum(ch.get("word_count", 0) for ch in chapters)

        with open(output_path, 'w') as f:
            f.write(f"# {project.title}\n\n")
            f.write(f"*Total chapters: {len(chapters)} | Total words: {total_words:,}*\n\n")
            f.write("---\n\n")

            for chapter in sorted(chapters, key=lambda x: x.get("number", 0)):
                ch_num = chapter.get("number", "?")
                title = chapter.get("title", f"Chapter {ch_num}")
                text = chapter.get("text", "*Chapter not yet written.*")

                f.write(f"## Chapter {ch_num}: {title}\n\n")
                f.write(text)
                f.write("\n\n---\n\n")

        return output_path


# Singleton instance for easy access
_persistence_manager: Optional[DiskPersistenceManager] = None


def get_persistence_manager(output_dir: str = "./book_projects") -> DiskPersistenceManager:
    """Get or create the singleton persistence manager."""
    global _persistence_manager
    if _persistence_manager is None:
        _persistence_manager = DiskPersistenceManager(output_dir)
    return _persistence_manager
