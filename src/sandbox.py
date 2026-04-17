"""
NexusAgent Sandbox
Sandboxed skill execution with subprocess isolation, timeout, and resource limits.
"""

import os
import signal
import subprocess
import tempfile
import textwrap
from pathlib import Path
from typing import Any, Optional


class SandboxResult:
    def __init__(self, stdout: str, stderr: str, returncode: int, timed_out: bool = False):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.timed_out = timed_out

    @property
    def success(self) -> bool:
        return self.returncode == 0 and not self.timed_out

    def __repr__(self):
        status = "TIMEOUT" if self.timed_out else ("OK" if self.success else f"ERR({self.returncode})")
        return f"SandboxResult({status})"


class Sandbox:
    """Execute code in an isolated subprocess."""

    def __init__(self, timeout: int = 30, max_memory_mb: int = 256, cwd: Optional[str] = None):
        self.timeout = timeout
        self.max_memory_mb = max_memory_mb
        self.cwd = cwd

    def execute(self, code: str, language: str = "python") -> SandboxResult:
        """Execute code in a sandboxed subprocess."""
        if language != "python":
            return SandboxResult("", f"Unsupported language: {language}", 1)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(textwrap.dedent(code))
            tmp_path = f.name

        try:
            env = os.environ.copy()
            # Resource limit via preexec
            def preexec():
                try:
                    import resource
                    resource.setrlimit(resource.RLIMIT_AS, (self.max_memory_mb * 1024 * 1024, self.max_memory_mb * 1024 * 1024))
                except (ImportError, ValueError):
                    pass

            proc = subprocess.run(
                ["python3", tmp_path],
                capture_output=True, text=True, timeout=self.timeout,
                cwd=self.cwd, env=env, preexec_fn=preexec
            )
            return SandboxResult(proc.stdout, proc.stderr, proc.returncode)
        except subprocess.TimeoutExpired:
            return SandboxResult("", "Execution timed out.", -1, timed_out=True)
        except Exception as e:
            return SandboxResult("", str(e), 1)
        finally:
            os.unlink(tmp_path)

    def execute_skill(self, skill_name: str, skill_code: str) -> SandboxResult:
        """Execute a named skill from the skill tree."""
        wrapper = f'''
import sys
try:
    exec("""{skill_code.replace('"""', '"""')}""")
except Exception as e:
    print(f"Skill error: {{e}}", file=sys.stderr)
    sys.exit(1)
'''
        return self.execute(wrapper)
