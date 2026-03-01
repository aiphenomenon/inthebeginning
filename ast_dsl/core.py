"""Core AST Engine - Multi-language AST introspection and transformation.

This module provides the central DSL engine that parses source code into ASTs,
queries them with a structured query language, and transforms them. It acts as
one half of a reactive agent pair: the local analysis tool that passes
structured state back and forth with an LLM.
"""
import ast
import json
import hashlib
import os
import sys
import time
import resource
import tracemalloc
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


class Language(Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    GO = "go"
    C = "c"
    CPP = "cpp"
    JAVA = "java"
    RUST = "rust"
    PERL = "perl"
    PHP = "php"
    WEBASSEMBLY = "webassembly"
    TYPESCRIPT = "typescript"
    SWIFT = "swift"
    KOTLIN = "kotlin"


@dataclass
class ASTNode:
    """Universal AST node representation across languages."""
    node_type: str
    name: str = ""
    children: list = field(default_factory=list)
    attributes: dict = field(default_factory=dict)
    line: int = 0
    col: int = 0
    end_line: int = 0
    end_col: int = 0
    source_text: str = ""

    def to_dict(self) -> dict:
        d = {
            "type": self.node_type,
            "name": self.name,
            "line": self.line,
            "col": self.col,
        }
        if self.end_line:
            d["end_line"] = self.end_line
            d["end_col"] = self.end_col
        if self.attributes:
            d["attrs"] = self.attributes
        if self.source_text:
            d["src"] = self.source_text
        if self.children:
            d["children"] = [c.to_dict() for c in self.children]
        return d

    def to_compact(self) -> str:
        """Minimal space representation readable by LLM."""
        parts = [f"{self.node_type}"]
        if self.name:
            parts[0] += f":{self.name}"
        if self.line:
            parts[0] += f"@{self.line}"
        if self.attributes:
            attrs = ",".join(f"{k}={v}" for k, v in self.attributes.items())
            parts.append(f"[{attrs}]")
        if self.children:
            kids = ";".join(c.to_compact() for c in self.children)
            parts.append(f"{{{kids}}}")
        return "".join(parts)

    def walk(self):
        """Depth-first walk yielding all nodes."""
        yield self
        for child in self.children:
            yield from child.walk()

    def find(self, node_type: str = None, name: str = None):
        """Find nodes matching criteria."""
        results = []
        for node in self.walk():
            if node_type and node.node_type != node_type:
                continue
            if name and node.name != name:
                continue
            results.append(node)
        return results


@dataclass
class ASTQuery:
    """Structured query for AST introspection."""
    action: str  # parse, find, transform, metrics, dependencies, callers
    target: str = ""  # file path or symbol name
    language: str = "python"
    filters: dict = field(default_factory=dict)
    depth: int = -1  # -1 = unlimited

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ASTQuery":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class PerformanceMetrics:
    """Runtime performance metrics for the analysis."""
    wall_time_ms: float = 0.0
    cpu_user_ms: float = 0.0
    cpu_system_ms: float = 0.0
    peak_memory_kb: int = 0
    current_memory_kb: int = 0
    disk_read_bytes: int = 0
    disk_write_bytes: int = 0
    prompt_tokens_approx: int = 0
    result_tokens_approx: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ASTResult:
    """Result from an AST query with performance metrics."""
    success: bool
    data: Any = None
    error: str = ""
    metrics: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    ast_node_count: int = 0
    source_hash: str = ""

    def to_dict(self) -> dict:
        d = {
            "success": self.success,
            "ast_node_count": self.ast_node_count,
            "source_hash": self.source_hash,
            "metrics": self.metrics.to_dict(),
        }
        if self.error:
            d["error"] = self.error
        if self.data is not None:
            if isinstance(self.data, ASTNode):
                d["data"] = self.data.to_dict()
            elif isinstance(self.data, list):
                d["data"] = [
                    x.to_dict() if isinstance(x, ASTNode) else x for x in self.data
                ]
            else:
                d["data"] = self.data
        return d

    def to_compact(self) -> str:
        """Minimal representation for LLM context efficiency."""
        parts = [f"ok={self.success}"]
        if self.error:
            parts.append(f"err={self.error}")
        parts.append(f"nodes={self.ast_node_count}")
        parts.append(f"mem={self.metrics.peak_memory_kb}kb")
        parts.append(f"cpu={self.metrics.cpu_user_ms:.1f}ms")
        if isinstance(self.data, ASTNode):
            parts.append(f"ast={self.data.to_compact()}")
        elif isinstance(self.data, list) and self.data:
            if isinstance(self.data[0], ASTNode):
                items = "|".join(n.to_compact() for n in self.data[:20])
                parts.append(f"results=[{items}]")
        return " ".join(parts)


class ASTEngine:
    """Multi-language AST engine with performance tracking."""

    def __init__(self):
        self._parsers = {
            Language.PYTHON: self._parse_python,
        }
        self._cache = {}

    def _measure(self, func, *args, **kwargs):
        """Execute function with full performance measurement."""
        tracemalloc.start()
        t0 = time.monotonic()
        r0 = resource.getrusage(resource.RUSAGE_SELF)
        try:
            result = func(*args, **kwargs)
        finally:
            r1 = resource.getrusage(resource.RUSAGE_SELF)
            t1 = time.monotonic()
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

        metrics = PerformanceMetrics(
            wall_time_ms=(t1 - t0) * 1000,
            cpu_user_ms=(r1.ru_utime - r0.ru_utime) * 1000,
            cpu_system_ms=(r1.ru_stime - r0.ru_stime) * 1000,
            peak_memory_kb=peak // 1024,
            current_memory_kb=current // 1024,
            disk_read_bytes=(r1.ru_inblock - r0.ru_inblock) * 512,
            disk_write_bytes=(r1.ru_oublock - r0.ru_oublock) * 512,
        )
        return result, metrics

    def execute(self, query: ASTQuery) -> ASTResult:
        """Execute an AST query with full metrics."""
        action_map = {
            "parse": self._action_parse,
            "find": self._action_find,
            "symbols": self._action_symbols,
            "dependencies": self._action_dependencies,
            "callers": self._action_callers,
            "metrics": self._action_code_metrics,
            "transform": self._action_transform,
            "coverage_map": self._action_coverage_map,
        }
        handler = action_map.get(query.action)
        if not handler:
            return ASTResult(success=False, error=f"Unknown action: {query.action}")

        try:
            result_data, perf = self._measure(handler, query)
            node_count = 0
            if isinstance(result_data, ASTNode):
                node_count = sum(1 for _ in result_data.walk())
            elif isinstance(result_data, list):
                for item in result_data:
                    if isinstance(item, ASTNode):
                        node_count += sum(1 for _ in item.walk())

            src_hash = ""
            if query.target and os.path.isfile(query.target):
                with open(query.target, "rb") as f:
                    src_hash = hashlib.sha256(f.read()).hexdigest()[:16]

            # Approximate token counts
            result_str = json.dumps(
                result_data.to_dict() if isinstance(result_data, ASTNode)
                else result_data if not isinstance(result_data, list)
                else [x.to_dict() if isinstance(x, ASTNode) else x for x in result_data],
                default=str
            )
            perf.result_tokens_approx = len(result_str) // 4
            if query.target and os.path.isfile(query.target):
                perf.prompt_tokens_approx = os.path.getsize(query.target) // 4

            return ASTResult(
                success=True,
                data=result_data,
                metrics=perf,
                ast_node_count=node_count,
                source_hash=src_hash,
            )
        except Exception as e:
            return ASTResult(success=False, error=str(e))

    def _get_python_ast(self, filepath: str) -> ast.AST:
        """Parse Python file, with caching."""
        mtime = os.path.getmtime(filepath)
        cache_key = (filepath, mtime)
        if cache_key in self._cache:
            return self._cache[cache_key]
        with open(filepath, "r") as f:
            source = f.read()
        tree = ast.parse(source, filename=filepath)
        self._cache[cache_key] = tree
        return tree

    def _parse_python(self, source: str, filename: str = "<string>") -> ASTNode:
        """Parse Python source into universal AST."""
        tree = ast.parse(source, filename=filename)
        return self._python_node_to_universal(tree, source)

    def _python_node_to_universal(self, node: ast.AST, source: str = "") -> ASTNode:
        """Convert Python AST node to universal ASTNode."""
        node_type = type(node).__name__
        name = ""
        attrs = {}

        if isinstance(node, ast.FunctionDef):
            name = node.name
            attrs["args"] = [a.arg for a in node.args.args]
            attrs["decorators"] = len(node.decorator_list)
            attrs["is_async"] = False
        elif isinstance(node, ast.AsyncFunctionDef):
            name = node.name
            attrs["args"] = [a.arg for a in node.args.args]
            attrs["decorators"] = len(node.decorator_list)
            attrs["is_async"] = True
        elif isinstance(node, ast.ClassDef):
            name = node.name
            attrs["bases"] = [
                getattr(b, "id", getattr(b, "attr", str(b)))
                for b in node.bases
            ]
            attrs["decorators"] = len(node.decorator_list)
        elif isinstance(node, ast.Import):
            name = ", ".join(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            name = node.module or ""
            attrs["names"] = [alias.name for alias in node.names]
        elif isinstance(node, ast.Name):
            name = node.id
        elif isinstance(node, ast.Attribute):
            name = node.attr
        elif isinstance(node, ast.Assign):
            targets = []
            for t in node.targets:
                if isinstance(t, ast.Name):
                    targets.append(t.id)
            if targets:
                name = ", ".join(targets)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr

        line = getattr(node, "lineno", 0)
        end_line = getattr(node, "end_lineno", 0)
        col = getattr(node, "col_offset", 0)
        end_col = getattr(node, "end_col_offset", 0)

        # Extract source text for this node
        src_text = ""
        if source and line and end_line:
            lines = source.splitlines()
            if line <= len(lines):
                if line == end_line:
                    src_text = lines[line - 1][col:end_col]
                else:
                    src_lines = lines[line - 1:end_line]
                    if src_lines:
                        src_text = "\n".join(src_lines)
                        if len(src_text) > 200:
                            src_text = src_text[:200] + "..."

        children = []
        for child_node in ast.iter_child_nodes(node):
            children.append(self._python_node_to_universal(child_node, source))

        return ASTNode(
            node_type=node_type,
            name=name,
            children=children,
            attributes=attrs,
            line=line,
            col=col,
            end_line=end_line,
            end_col=end_col,
            source_text=src_text,
        )

    def _action_parse(self, query: ASTQuery) -> ASTNode:
        """Parse a file into universal AST."""
        lang = Language(query.language)
        if query.target and os.path.isfile(query.target):
            with open(query.target, "r") as f:
                source = f.read()
        else:
            source = query.target

        parser = self._parsers.get(lang)
        if not parser:
            raise ValueError(f"No parser for language: {lang.value}")

        filename = query.target if os.path.isfile(query.target) else "<string>"
        return parser(source, filename)

    def _action_find(self, query: ASTQuery) -> list:
        """Find AST nodes matching criteria."""
        root = self._action_parse(query)
        node_type = query.filters.get("node_type")
        name = query.filters.get("name")
        return root.find(node_type=node_type, name=name)

    def _action_symbols(self, query: ASTQuery) -> list:
        """Extract all symbol definitions from a file."""
        root = self._action_parse(query)
        symbols = []
        for node in root.walk():
            if node.node_type in (
                "FunctionDef", "AsyncFunctionDef", "ClassDef",
            ):
                symbols.append({
                    "type": node.node_type,
                    "name": node.name,
                    "line": node.line,
                    "attributes": node.attributes,
                })
        return symbols

    def _action_dependencies(self, query: ASTQuery) -> list:
        """Extract import dependencies."""
        root = self._action_parse(query)
        deps = []
        for node in root.walk():
            if node.node_type in ("Import", "ImportFrom"):
                deps.append({
                    "type": node.node_type,
                    "module": node.name,
                    "line": node.line,
                    "names": node.attributes.get("names", []),
                })
        return deps

    def _action_callers(self, query: ASTQuery) -> list:
        """Find all call sites for a given symbol."""
        root = self._action_parse(query)
        target_name = query.filters.get("name", "")
        calls = []
        for node in root.walk():
            if node.node_type == "Call" and node.name == target_name:
                calls.append({
                    "line": node.line,
                    "col": node.col,
                    "source": node.source_text,
                })
        return calls

    def _action_code_metrics(self, query: ASTQuery) -> dict:
        """Compute code complexity metrics."""
        root = self._action_parse(query)
        total_nodes = 0
        functions = 0
        classes = 0
        imports = 0
        max_depth = 0
        branches = 0

        def _walk_depth(node, depth):
            nonlocal total_nodes, functions, classes, imports, max_depth, branches
            total_nodes += 1
            max_depth = max(max_depth, depth)
            if node.node_type in ("FunctionDef", "AsyncFunctionDef"):
                functions += 1
            elif node.node_type == "ClassDef":
                classes += 1
            elif node.node_type in ("Import", "ImportFrom"):
                imports += 1
            elif node.node_type in ("If", "While", "For", "ExceptHandler"):
                branches += 1
            for child in node.children:
                _walk_depth(child, depth + 1)

        _walk_depth(root, 0)
        return {
            "total_nodes": total_nodes,
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "max_depth": max_depth,
            "cyclomatic_complexity": branches + 1,
        }

    def _action_transform(self, query: ASTQuery) -> ASTNode:
        """Apply AST transformation (rename, extract, inline)."""
        root = self._action_parse(query)
        transform_type = query.filters.get("transform")
        if transform_type == "rename":
            old_name = query.filters.get("old_name", "")
            new_name = query.filters.get("new_name", "")
            for node in root.walk():
                if node.name == old_name:
                    node.name = new_name
        return root

    def _action_coverage_map(self, query: ASTQuery) -> list:
        """Map all testable code paths for coverage targeting."""
        root = self._action_parse(query)
        paths = []
        for node in root.walk():
            if node.node_type in ("FunctionDef", "AsyncFunctionDef"):
                branches_in_func = 0
                for child in node.walk():
                    if child.node_type in ("If", "While", "For",
                                           "ExceptHandler", "With"):
                        branches_in_func += 1
                paths.append({
                    "function": node.name,
                    "line": node.line,
                    "branches": branches_in_func,
                    "args": node.attributes.get("args", []),
                    "testable": True,
                })
        return paths

    def parse_file(self, filepath: str, language: str = "python") -> ASTResult:
        """Convenience: parse a file and return result."""
        query = ASTQuery(action="parse", target=filepath, language=language)
        return self.execute(query)

    def find_symbols(self, filepath: str, language: str = "python") -> ASTResult:
        """Convenience: find all symbols in a file."""
        query = ASTQuery(action="symbols", target=filepath, language=language)
        return self.execute(query)

    def get_dependencies(self, filepath: str, language: str = "python") -> ASTResult:
        """Convenience: get dependencies of a file."""
        query = ASTQuery(action="dependencies", target=filepath, language=language)
        return self.execute(query)
