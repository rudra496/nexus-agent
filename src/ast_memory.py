"""
NexusAgent AST-Aware Code Memory
Parses Python source files into an AST and extracts structural information
for enhanced code understanding: imports, function signatures, class hierarchies,
and dependency graphs.
"""

import ast
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class FunctionInfo:
    name: str
    args: List[str]
    returns: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    line_start: int = 0
    line_end: int = 0
    docstring: Optional[str] = None
    is_async: bool = False


@dataclass
class ClassInfo:
    name: str
    bases: List[str] = field(default_factory=list)
    methods: List[FunctionInfo] = field(default_factory=list)
    line_start: int = 0
    line_end: int = 0
    docstring: Optional[str] = None


@dataclass
class ImportInfo:
    module: str
    names: List[str] = field(default_factory=list)
    is_from: bool = False
    line: int = 0
    is_relative: bool = False


@dataclass
class FileAnalysis:
    path: str
    functions: List[FunctionInfo] = field(default_factory=list)
    classes: List[ClassInfo] = field(default_factory=list)
    imports: List[ImportInfo] = field(default_factory=list)
    globals_used: Set[str] = field(default_factory=set)
    line_count: int = 0
    complexity: int = 0


class ASTParser:
    """Parse Python files into structured AST information."""

    def __init__(self):
        self._cache: Dict[str, FileAnalysis] = {}

    def parse_file(self, filepath: str) -> Optional[FileAnalysis]:
        """Parse a single Python file."""
        filepath = str(filepath)
        if filepath in self._cache:
            return self._cache[filepath]

        if not os.path.exists(filepath):
            return None

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                source = f.read()
            return self._parse_source(source, filepath)
        except (SyntaxError, UnicodeDecodeError):
            return None

    def _parse_source(self, source: str, filepath: str) -> FileAnalysis:
        """Parse Python source into FileAnalysis."""
        tree = ast.parse(source)
        analysis = FileAnalysis(
            path=filepath,
            line_count=source.count("\n") + 1,
        )

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                info = FunctionInfo(
                    name=node.name,
                    args=[a.arg for a in node.args.args],
                    decorators=[self._get_decorator_name(d) for d in node.decorator_list],
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    docstring=ast.get_docstring(node),
                    is_async=isinstance(node, ast.AsyncFunctionDef),
                )
                # Check return annotation
                if node.returns and isinstance(node.returns, ast.Name):
                    info.returns = node.returns.id
                elif node.returns and isinstance(node.returns, ast.Constant):
                    info.returns = str(node.returns.value)

                # Check if it's a method inside a class
                analysis.functions.append(info)
                analysis.complexity += 1

            elif isinstance(node, ast.ClassDef):
                bases = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        bases.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        bases.append(f"{base.value.id}.{base.attr}")

                class_info = ClassInfo(
                    name=node.name,
                    bases=bases,
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    docstring=ast.get_docstring(node),
                )

                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method = FunctionInfo(
                            name=item.name,
                            args=[a.arg for a in item.args.args],
                            decorators=[self._get_decorator_name(d) for d in item.decorator_list],
                            line_start=item.lineno,
                            line_end=item.end_lineno or item.lineno,
                            docstring=ast.get_docstring(item),
                            is_async=isinstance(item, ast.AsyncFunctionDef),
                        )
                        class_info.methods.append(method)

                analysis.classes.append(class_info)

            elif isinstance(node, ast.Import):
                analysis.imports.append(ImportInfo(
                    module=node.names[0].name if node.names else "",
                    names=[a.name for a in node.names],
                    is_from=False,
                    line=node.lineno,
                ))

            elif isinstance(node, ast.ImportFrom):
                analysis.imports.append(ImportInfo(
                    module=node.module or "",
                    names=[a.name for a in node.names],
                    is_from=True,
                    line=node.lineno,
                    is_relative=(node.level or 0) > 0,
                ))

            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                analysis.globals_used.add(node.id)

        self._cache[filepath] = analysis
        return analysis

    def _get_decorator_name(self, decorator) -> str:
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{decorator.value.id}.{decorator.attr}"
        elif isinstance(decorator, ast.Call):
            return self._get_decorator_name(decorator.func)
        return str(decorator)

    def get_dependency_graph(self, filepaths: List[str]) -> Dict[str, Set[str]]:
        """Build a dependency graph from imports across multiple files."""
        deps: Dict[str, Set[str]] = {fp: set() for fp in filepaths}
        file_basenames = {Path(fp).stem: fp for fp in filepaths}

        for fp in filepaths:
            analysis = self.parse_file(fp)
            if not analysis:
                continue
            for imp in analysis.imports:
                if imp.module in file_basenames and file_basenames[imp.module] != fp:
                    deps[fp].add(file_basenames[imp.module])
                # Check individual imported names
                for name in imp.names:
                    if name in file_basenames and file_basenames[name] != fp:
                        deps[fp].add(file_basenames[name])

        return deps

    def get_function_signature(self, filepath: str, func_name: str) -> Optional[str]:
        """Get a formatted function signature."""
        analysis = self.parse_file(filepath)
        if not analysis:
            return None
        for fn in analysis.functions:
            if fn.name == func_name:
                prefix = "async " if fn.is_async else ""
                args = ", ".join(fn.args)
                ret = f" -> {fn.returns}" if fn.returns else ""
                return f"{prefix}def {fn.name}({args}){ret}"
        return None

    def get_class_hierarchy(self, filepaths: List[str]) -> Dict[str, List[str]]:
        """Get class inheritance across multiple files."""
        hierarchy: Dict[str, List[str]] = {}
        for fp in filepaths:
            analysis = self.parse_file(fp)
            if not analysis:
                continue
            for cls in analysis.classes:
                key = f"{fp}::{cls.name}"
                hierarchy[key] = cls.bases
        return hierarchy

    def search_symbols(self, filepaths: List[str], query: str) -> List[Dict[str, Any]]:
        """Search for functions, classes, and imports matching a query."""
        results = []
        query_lower = query.lower()
        for fp in filepaths:
            analysis = self.parse_file(fp)
            if not analysis:
                continue
            for fn in analysis.functions:
                if query_lower in fn.name.lower():
                    results.append({"type": "function", "name": fn.name, "file": fp,
                                    "line": fn.line_start, "docstring": fn.docstring})
            for cls in analysis.classes:
                if query_lower in cls.name.lower():
                    results.append({"type": "class", "name": cls.name, "file": fp,
                                    "line": cls.line_start, "docstring": cls.docstring,
                                    "methods": [m.name for m in cls.methods]})
        return results

    def clear_cache(self):
        self._cache.clear()

    def get_stats(self) -> Dict[str, int]:
        return {
            "files_cached": len(self._cache),
        }
