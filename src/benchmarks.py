"""Performance Benchmark Suite for NexusAgent."""

from __future__ import annotations

import json
import os
import time
import traceback
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BenchmarkResult:
    name: str
    wall_time_s: float
    memory_mb: float = 0.0
    iterations: int = 1
    success: bool = True
    error: str = ""
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name, "wall_time_s": round(self.wall_time_s, 6),
            "memory_mb": round(self.memory_mb, 2), "iterations": self.iterations,
            "success": self.success, "error": self.error, "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict) -> BenchmarkResult:
        return cls(**d)


@dataclass
class BenchmarkSuite:
    name: str
    timestamp: float
    results: list[BenchmarkResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"name": self.name, "timestamp": self.timestamp, "results": [r.to_dict() for r in self.results]}

    @classmethod
    def from_dict(cls, d: dict) -> BenchmarkSuite:
        return cls(name=d["name"], timestamp=d["timestamp"], results=[BenchmarkResult.from_dict(r) for r in d["results"]])

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def to_markdown(self) -> str:
        lines = [f"# Benchmark: {self.name}", f"*Ran: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.timestamp))}*\n"]
        lines.append("| Benchmark | Time (s) | Memory (MB) | Iterations | Status |")
        lines.append("|-----------|----------|-------------|------------|--------|")
        for r in self.results:
            status = "✅" if r.success else f"❌ {r.error}"
            lines.append(f"| {r.name} | {r.wall_time_s:.4f} | {r.memory_mb:.2f} | {r.iterations} | {status} |")
        return "\n".join(lines)


def _get_memory_mb() -> float:
    """Get current process memory usage in MB."""
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # Linux: KB -> MB
    except (ImportError, AttributeError):
        return 0.0


class BenchmarkRunner:
    """Run and compare performance benchmarks."""

    RESULTS_DIR = ".nexus/benchmarks"

    def __init__(self, results_dir: Optional[str] = None):
        self.results_dir = results_dir or self.RESULTS_DIR
        os.makedirs(self.results_dir, exist_ok=True)

    def _run_single(self, name: str, fn, iterations: int = 1) -> BenchmarkResult:
        start_mem = _get_memory_mb()
        start_time = time.perf_counter()
        try:
            for _ in range(iterations):
                fn()
            elapsed = time.perf_counter() - start_time
            end_mem = _get_memory_mb()
            return BenchmarkResult(name=name, wall_time_s=elapsed, memory_mb=end_mem - start_mem, iterations=iterations, success=True)
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            return BenchmarkResult(name=name, wall_time_s=elapsed, iterations=iterations, success=False, error=str(e))

    def benchmark_memory_retrieval(self, iterations: int = 100) -> BenchmarkResult:
        """Benchmark memory graph retrieval."""
        from .memory import GraphMemory
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            mem = GraphMemory(storage_path=os.path.join(d, "bench.json"))
            for i in range(50):
                mem.add_node(f"node_{i}", {"type": "test", "data": f"value_{i}"})
                if i > 0:
                    mem.add_edge(f"node_{i-1}", f"node_{i}", "related")
            def run():
                mem.retrieve_context("node_25")
            return self._run_single("memory_retrieval", run, iterations)

    def benchmark_skill_execution(self, iterations: int = 50) -> BenchmarkResult:
        """Benchmark skill tree operations."""
        from .skills import SkillTree
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            st = SkillTree(skill_dir=d)
            for i in range(20):
                st.add_skill(f"skill_{i}", f"Test skill {i}", f"def run(): return {i}")
            def run():
                st.list_skills()
            return self._run_single("skill_execution", run, iterations)

    def benchmark_context_building(self, iterations: int = 50) -> BenchmarkResult:
        """Benchmark context window manager."""
        from .context_manager import ContextWindowManager, ContextEntry
        def run():
            cm = ContextWindowManager()
            cm.set_system_prompt("You are NexusAgent.")
            for i in range(10):
                cm.add_message("user", f"Message {i}")
                cm.add_message("assistant", f"Response {i}")
            entries = [ContextEntry(content=f"context {i}", source="memory", priority=i % 5, tokens=20) for i in range(20)]
            cm.build_context_messages(entries)
        return self._run_single("context_building", run, iterations)

    def benchmark_ast_parsing(self, iterations: int = 50) -> BenchmarkResult:
        """Benchmark AST parsing."""
        from .ast_memory import ASTParser
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            # Create a sample file
            fpath = os.path.join(d, "sample.py")
            with open(fpath, "w") as f:
                f.write("def a(x): return x+1\ndef b(y): return y*2\nclass C:\n    def d(self): pass\n" * 10)
            parser = ASTParser()
            def run():
                parser.parse_file(fpath)
            return self._run_single("ast_parsing", run, iterations)

    def run_all(self) -> BenchmarkSuite:
        """Run all benchmarks."""
        suite = BenchmarkSuite(name="nexus-full", timestamp=time.time())
        benchmarks = [
            self.benchmark_memory_retrieval,
            self.benchmark_skill_execution,
            self.benchmark_context_building,
            self.benchmark_ast_parsing,
        ]
        for fn in benchmarks:
            result = fn(iterations=50)
            suite.results.append(result)
        return suite

    def save_results(self, suite: BenchmarkSuite, filename: Optional[str] = None) -> str:
        """Save benchmark results to file."""
        ts = time.strftime("%Y%m%d_%H%M%S")
        filename = filename or f"benchmark_{ts}.json"
        path = os.path.join(self.results_dir, filename)
        with open(path, "w") as f:
            f.write(suite.to_json())
        return path

    def compare(self, file1: str, file2: str) -> str:
        """Compare two benchmark result files and return markdown."""
        with open(file1) as f:
            suite1 = BenchmarkSuite.from_dict(json.load(f))
        with open(file2) as f:
            suite2 = BenchmarkSuite.from_dict(json.load(f))

        lines = ["# Benchmark Comparison", ""]
        lines.append(f"| Benchmark | Run 1 (s) | Run 2 (s) | Change |")
        lines.append("|-----------|-----------|-----------|--------|")
        for r1, r2 in zip(suite1.results, suite2.results):
            if r1.name == r2.name:
                change = ((r2.wall_time_s - r1.wall_time_s) / r1.wall_time_s * 100) if r1.wall_time_s > 0 else 0
                arrow = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                lines.append(f"| {r1.name} | {r1.wall_time_s:.4f} | {r2.wall_time_s:.4f} | {arrow} {abs(change):.1f}% |")
        return "\n".join(lines)
