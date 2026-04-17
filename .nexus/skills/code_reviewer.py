"""NexusAgent Skill: Review Python code for common issues."""

import ast
import re
from typing import Optional


def run(code: str) -> dict:
    """Review Python code and return suggestions."""
    issues = []
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {"syntax_error": str(e), "issues": []}

    # Check for bare except
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            issues.append({"line": node.lineno, "type": "warning", "msg": "Bare except clause — catch specific exceptions"})

        # Check for mutable default arguments
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for default in node.args.defaults + node.args.kw_defaults:
                if default and isinstance(default, (ast.List, ast.Dict, ast.Set)):
                    issues.append({"line": node.lineno, "type": "warning", "msg": f"Mutable default argument in '{node.name}'"})

    # Check for TODO/FIXME/HACK
    for i, line in enumerate(code.splitlines(), 1):
        for tag in ["TODO", "FIXME", "HACK", "XXX"]:
            if tag in line:
                issues.append({"line": i, "type": "info", "msg": f"Found {tag} comment"})

    # Check line length
    for i, line in enumerate(code.splitlines(), 1):
        if len(line) > 120:
            issues.append({"line": i, "type": "style", "msg": f"Line too long ({len(line)} chars)"})

    return {"issues": issues, "total_issues": len(issues), "severity": {"errors": sum(1 for i in issues if i["type"] == "error"), "warnings": sum(1 for i in issues if i["type"] == "warning"), "info": sum(1 for i in issues if i["type"] == "info")}}
