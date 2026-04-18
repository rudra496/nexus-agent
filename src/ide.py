"""
NexusAgent IDE Integration
Base classes and protocol definitions for IDE extensions (VS Code, JetBrains, etc.).
Provides a JSON-RPC server that IDE extensions can connect to.
"""

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class IDEType(Enum):
    VSCODE = "vscode"
    JETBRAINS = "jetbrains"
    VIM = "vim"
    NEovim = "neovim"
    GENERIC = "generic"


@dataclass
class IDEConfig:
    ide_type: IDEType = IDEType.GENERIC
    host: str = "127.0.0.1"
    port: int = 8421
    auto_complete: bool = True
    inline_suggestions: bool = True
    diagnostic_reporting: bool = True


@dataclass
class CodeAction:
    title: str
    kind: str = "quickfix"  # quickfix, refactor, info
    edit: Optional[Dict[str, Any]] = None
    command: Optional[str] = None


@dataclass
class Diagnostic:
    file: str
    line: int
    column: int
    severity: str = "info"  # error, warning, info, hint
    message: str = ""
    source: str = "nexus"


@dataclass
class CompletionItem:
    label: str
    kind: int = 1  # Text=1, Method=6, Function=3, Class=7, Module=9
    detail: str = ""
    documentation: str = ""
    insert_text: str = ""


class IDEServer:
    """JSON-RPC server for IDE integration."""

    def __init__(self, config: Optional[IDEConfig] = None):
        self.config = config or IDEConfig()
        self._handlers: Dict[str, Callable] = {}
        self._running = False

    def register_handler(self, method: str, handler: Callable):
        """Register a JSON-RPC method handler."""
        self._handlers[method] = handler

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a JSON-RPC request."""
        method = request.get("method", "")
        params = request.get("params", {})
        req_id = request.get("id")

        handler = self._handlers.get(method)
        if not handler:
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}

        try:
            result = handler(params)
            return {"jsonrpc": "2.0", "id": req_id, "result": result}
        except Exception as e:
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32000, "message": str(e)}}

    def start(self):
        """Start the IDE server (placeholder for implementation)."""
        self._running = True


class IDEClient:
    """Client for communicating with a running NexusAgent IDE server."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8421):
        self.host = host
        self.port = port

    def _send_request(self, method: str, params: Optional[Dict] = None) -> Any:
        """Send a JSON-RPC request (HTTP-based)."""
        try:
            import requests
            resp = requests.post(
                f"http://{self.host}:{self.port}/rpc",
                json={"jsonrpc": "2.0", "method": method, "params": params or {}, "id": 1},
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json().get("result")
        except Exception:
            return None

    def get_completions(self, file: str, line: int, column: int, prefix: str = "") -> List[CompletionItem]:
        """Get code completions for a position."""
        result = self._send_request("textDocument/completion", {
            "file": file, "line": line, "column": column, "prefix": prefix
        })
        if isinstance(result, list):
            return [CompletionItem(**item) for item in result]
        return []

    def get_diagnostics(self, file: Optional[str] = None) -> List[Diagnostic]:
        """Get diagnostics (errors, warnings) for a file or all files."""
        result = self._send_request("textDocument/diagnostic", {"file": file})
        if isinstance(result, list):
            return [Diagnostic(**item) for item in result]
        return []

    def get_code_actions(self, file: str, line: int) -> List[CodeAction]:
        """Get available code actions for a position."""
        result = self._send_request("textDocument/codeAction", {"file": file, "line": line})
        if isinstance(result, list):
            return [CodeAction(**item) for item in result]
        return []

    def explain_code(self, file: str, line: int) -> Optional[str]:
        """Ask NexusAgent to explain code at a position."""
        return self._send_request("nexus/explain", {"file": file, "line": line})

    def fix_code(self, file: str, line: int) -> Optional[str]:
        """Ask NexusAgent to suggest a fix."""
        return self._send_request("nexus/fix", {"file": file, "line": line})


def generate_vscode_extensionManifest() -> dict:
    """Generate a VS Code extension manifest template."""
    return {
        "name": "nexus-agent",
        "displayName": "NexusAgent",
        "description": "Self-evolving local AI agent for VS Code",
        "version": "0.4.0",
        "engines": {"vscode": "^1.80.0"},
        "categories": ["Programming Languages", "Machine Learning", "Other"],
        "activationEvents": ["onCommand:nexus.run", "onCommand:nexus.explain"],
        "main": "./out/extension.js",
        "contributes": {
            "commands": [
                {"command": "nexus.run", "title": "Nexus: Run Task"},
                {"command": "nexus.explain", "title": "Nexus: Explain Code"},
                {"command": "nexus.fix", "title": "Nexus: Fix Code"},
                {"command": "nexus.evolve", "title": "Nexus: Evolve Memory"},
            ],
        },
    }
