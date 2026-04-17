"""
Example NexusAgent Plugin: Task Logger
Logs all tasks executed by Nexus to a JSON file.

Usage:
  1. Copy this file to .nexus/plugins/task_logger.py
  2. Run: nexus plugin list  (should show task_logger)
"""

import json
import os
from datetime import datetime

LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "task_log.json")


def nexus_on_task(task: str) -> dict:
    """Called when Nexus starts a new task."""
    entry = {"task": task, "started_at": datetime.now().isoformat()}
    return entry


def nexus_on_complete(result: str) -> dict:
    """Called when Nexus finishes a task."""
    entry = {"completed_at": datetime.now().isoformat(), "result_preview": result[:200]}
    _append_log(entry)
    return entry


def _append_log(entry: dict):
    log_path = os.path.abspath(LOG_FILE)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    logs = []
    if os.path.exists(log_path):
        try:
            with open(log_path) as f:
                logs = json.load(f)
        except Exception:
            logs = []
    logs.append(entry)
    with open(log_path, "w") as f:
        json.dump(logs, f, indent=2)
