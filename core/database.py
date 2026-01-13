"""
Database persistence layer for Railway PostgreSQL.

Stores project data as JSON in PostgreSQL for persistence across deploys.
"""

import json
import logging
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Database connection
_connection = None


def get_connection():
    """Get or create database connection."""
    global _connection

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.warning("DATABASE_URL not set - running without persistence")
        return None

    if _connection is None:
        try:
            import psycopg2
            _connection = psycopg2.connect(database_url)
            _connection.autocommit = True
            _init_schema()
            logger.info("Connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return None

    return _connection


def _init_schema():
    """Initialize database schema."""
    conn = _connection
    if not conn:
        return

    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    project_id VARCHAR(255) PRIMARY KEY,
                    title VARCHAR(500),
                    data JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            logger.info("Database schema initialized")
    except Exception as e:
        logger.error(f"Failed to initialize schema: {e}")


def save_project(project_id: str, title: str, data: Dict[str, Any]) -> bool:
    """Save project to database."""
    conn = get_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO projects (project_id, title, data, updated_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (project_id)
                DO UPDATE SET
                    title = EXCLUDED.title,
                    data = EXCLUDED.data,
                    updated_at = CURRENT_TIMESTAMP
            """, (project_id, title, json.dumps(data)))
        logger.debug(f"Saved project {project_id} to database")
        return True
    except Exception as e:
        logger.error(f"Failed to save project: {e}")
        return False


def load_project(project_id: str) -> Optional[Dict[str, Any]]:
    """Load project from database."""
    conn = get_connection()
    if not conn:
        return None

    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT data FROM projects WHERE project_id = %s",
                (project_id,)
            )
            row = cur.fetchone()
            if row:
                logger.debug(f"Loaded project {project_id} from database")
                return row[0] if isinstance(row[0], dict) else json.loads(row[0])
        return None
    except Exception as e:
        logger.error(f"Failed to load project: {e}")
        return None


def list_projects() -> list:
    """List all projects from database."""
    conn = get_connection()
    if not conn:
        return []

    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT project_id, title, created_at, updated_at FROM projects ORDER BY updated_at DESC"
            )
            rows = cur.fetchall()
            return [
                {
                    "project_id": row[0],
                    "title": row[1],
                    "created_at": row[2].isoformat() if row[2] else None,
                    "updated_at": row[3].isoformat() if row[3] else None
                }
                for row in rows
            ]
    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        return []


def delete_project(project_id: str) -> bool:
    """Delete project from database."""
    conn = get_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM projects WHERE project_id = %s",
                (project_id,)
            )
        logger.debug(f"Deleted project {project_id} from database")
        return True
    except Exception as e:
        logger.error(f"Failed to delete project: {e}")
        return False


def is_database_available() -> bool:
    """Check if database is available."""
    return get_connection() is not None
