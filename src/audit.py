"""Audit Logging & Role-Based Access Control for NexusAgent.

Structured JSON-lines audit log with RBAC enforcement.
"""

from __future__ import annotations

import json
import os
import time
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class LogLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SECURITY = "security"


class Role(str, Enum):
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class Permission(str, Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    MANAGE = "manage"


ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.ADMIN: {Permission.READ, Permission.WRITE, Permission.EXECUTE, Permission.MANAGE},
    Role.USER: {Permission.READ, Permission.WRITE, Permission.EXECUTE},
    Role.VIEWER: {Permission.READ},
}


@dataclass
class AuditEntry:
    timestamp: float
    level: LogLevel
    action: str
    actor: str = "system"
    details: dict = field(default_factory=dict)
    result: str = "ok"

    def to_json(self) -> str:
        return json.dumps({
            "timestamp": self.timestamp,
            "level": self.level.value,
            "action": self.action,
            "actor": self.actor,
            "details": self.details,
            "result": self.result,
        })

    @classmethod
    def from_json(cls, data: str) -> AuditEntry:
        d = json.loads(data)
        return cls(
            timestamp=d["timestamp"],
            level=LogLevel(d["level"]),
            action=d["action"],
            actor=d.get("actor", "system"),
            details=d.get("details", {}),
            result=d.get("result", "ok"),
        )


@dataclass
class RBACUser:
    username: str
    role: Role = Role.USER

    def has_permission(self, perm: Permission) -> bool:
        return perm in ROLE_PERMISSIONS.get(self.role, set())


class AuditLogger:
    """Structured audit logging with file and stdout output."""

    def __init__(self, log_path: Optional[str] = None, stdout: bool = False, max_size_mb: int = 50):
        self.log_path = log_path
        self.stdout = stdout
        self.max_size_mb = max_size_mb

    def log(self, level: LogLevel, action: str, actor: str = "system", details: Optional[dict] = None, result: str = "ok"):
        entry = AuditEntry(timestamp=time.time(), level=level, action=action, actor=actor, details=details or {}, result=result)
        if self.stdout:
            print(entry.to_json(), file=sys.stdout)
        if self.log_path:
            self._rotate_if_needed()
            with open(self.log_path, "a") as f:
                f.write(entry.to_json() + "\n")

    def info(self, action: str, **kwargs):
        self.log(LogLevel.INFO, action, **kwargs)

    def warning(self, action: str, **kwargs):
        self.log(LogLevel.WARNING, action, **kwargs)

    def error(self, action: str, **kwargs):
        self.log(LogLevel.ERROR, action, **kwargs)

    def security(self, action: str, **kwargs):
        self.log(LogLevel.SECURITY, action, **kwargs)

    def _rotate_if_needed(self):
        if not self.log_path or not os.path.exists(self.log_path):
            return
        size = os.path.getsize(self.log_path)
        if size > self.max_size_mb * 1024 * 1024:
            backup = self.log_path + f".{int(time.time())}.bak"
            os.rename(self.log_path, backup)
            # Keep only the last 3 backups
            self._cleanup_backups()

    def _cleanup_backups(self):
        if not self.log_path:
            return
        import glob
        backups = sorted(glob.glob(self.log_path + ".*.bak"), reverse=True)
        for old in backups[3:]:
            os.unlink(old)

    def read_logs(self, limit: int = 100, level: Optional[LogLevel] = None) -> list[AuditEntry]:
        entries = []
        if not self.log_path or not os.path.exists(self.log_path):
            return entries
        with open(self.log_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = AuditEntry.from_json(line)
                    if level and entry.level != level:
                        continue
                    entries.append(entry)
                except (json.JSONDecodeError, KeyError):
                    continue
        return entries[-limit:]

    def stats(self) -> dict:
        entries = self.read_logs(limit=10000)
        stats = {"total": len(entries)}
        for level in LogLevel:
            stats[level.value] = sum(1 for e in entries if e.level == level)
        return stats


class RBACManager:
    """Role-based access control manager."""

    def __init__(self):
        self._users: dict[str, RBACUser] = {}
        self._logger: Optional[AuditLogger] = None

    def set_logger(self, logger: AuditLogger):
        self._logger = logger

    def add_user(self, username: str, role: Role = Role.USER):
        self._users[username] = RBACUser(username=username, role=role)
        if self._logger:
            self._logger.security("user_created", actor="admin", details={"username": username, "role": role.value})

    def remove_user(self, username: str):
        if username in self._users:
            del self._users[username]
            if self._logger:
                self._logger.security("user_removed", actor="admin", details={"username": username})

    def get_user(self, username: str) -> Optional[RBACUser]:
        return self._users.get(username)

    def check_permission(self, username: str, permission: Permission) -> bool:
        user = self._users.get(username)
        if not user:
            if self._logger:
                self._logger.security("auth_failed", actor=username, details={"permission": permission.value})
            return False
        has = user.has_permission(permission)
        if not has and self._logger:
            self._logger.security("permission_denied", actor=username, details={"permission": permission.value, "role": user.role.value})
        return has

    def list_users(self) -> list[dict]:
        return [{"username": u.username, "role": u.role.value} for u in self._users.values()]
