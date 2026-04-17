"""
NexusAgent Self-Updater
Check for new versions and auto-update skills from a registry.
"""

import json
import shutil
import tempfile
from pathlib import Path
from typing import Optional

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from .config import get_config

REGISTRY_URL = "https://raw.githubusercontent.com/rudra496/nexus-agent/main/.nexus/registry.json"
PYPI_URL = "https://pypi.org/pypi/nexus-agent/json"


def check_version() -> dict:
    """Check if a newer version is available on PyPI."""
    if not HAS_REQUESTS:
        return {"current": "0.2.0", "latest": "unknown", "update_available": False, "error": "requests not installed"}

    try:
        resp = requests.get(PYPI_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        latest = data["info"]["version"]
        current = get_config().version
        return {
            "current": current,
            "latest": latest,
            "update_available": latest != current,
            "url": data["info"]["project_url"],
        }
    except Exception as e:
        return {"current": "0.2.0", "latest": "unknown", "update_available": False, "error": str(e)}


def check_skill_registry() -> list[dict]:
    """Fetch the skill registry for available skill updates."""
    if not HAS_REQUESTS:
        return []
    try:
        resp = requests.get(REGISTRY_URL, timeout=10)
        if resp.ok:
            return resp.json().get("skills", [])
    except Exception:
        pass
    return []


def update_skills() -> dict:
    """Update skills from the registry."""
    registry = check_skill_registry()
    updated = []
    for skill in registry:
        name = skill.get("name", "")
        url = skill.get("url", "")
        version = skill.get("version", "unknown")
        if not url:
            continue
        try:
            resp = requests.get(url, timeout=10)
            if resp.ok:
                skill_dir = Path(get_config().skills.directory)
                skill_dir.mkdir(parents=True, exist_ok=True)
                (skill_dir / f"{name}.py").write_text(resp.text, encoding="utf-8")
                updated.append(name)
        except Exception:
            pass
    return {"updated": updated, "total_available": len(registry)}


def self_update() -> dict:
    """Attempt to self-update via pip."""
    import subprocess
    try:
        result = subprocess.run(
            ["pip", "install", "--upgrade", "nexus-agent"],
            capture_output=True, text=True, timeout=120
        )
        return {"success": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr}
    except Exception as e:
        return {"success": False, "error": str(e)}
