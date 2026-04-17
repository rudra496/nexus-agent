"""NexusAgent Skill: Parse system logs and extract error patterns."""

import re
from collections import Counter
from typing import Optional


def run(log_content: str, log_type: str = "nginx") -> dict:
    """Parse logs and return error summary."""
    errors = []
    if log_type == "nginx":
        pattern = re.compile(r'(\d+\.\d+\.\d+\.\d+).*?\[(.*?)\].*?"(.*?)"\s+(\d+)', re.DOTALL)
        for match in pattern.finditer(log_content):
            ip, timestamp, request, status = match.groups()
            if int(status) >= 400:
                errors.append({"ip": ip, "time": timestamp, "request": request, "status": int(status)})
    else:
        error_pattern = re.compile(r'(ERROR|CRITICAL|FATAL|WARN).*', re.IGNORECASE)
        for line in log_content.splitlines():
            if error_pattern.search(line):
                errors.append({"line": line.strip()[:200]})

    status_counts = Counter(e.get("status", "error") for e in errors)
    return {"total_errors": len(errors), "by_status": dict(status_counts), "errors": errors[:20]}
