"""AST Self-Introspection Module.

Provides a universal self-introspection interface that any application
can use to parse and analyze its own source code using the appropriate
AST parser. Supports all 13 languages in the AST DSL framework.

Usage:
    from ast_dsl.introspect import introspect_app
    report = introspect_app("/path/to/app/src", language="python")
    print(report.summary())
"""
import os
import json
import time
from dataclasses import dataclass, field
from typing import Optional
from ast_dsl.core import ASTNode, ASTEngine, ASTQuery, Language


# Language → file extension mapping
LANG_EXTENSIONS = {
    "python": [".py"],
    "javascript": [".js", ".mjs"],
    "typescript": [".ts", ".tsx"],
    "go": [".go"],
    "c": [".c", ".h"],
    "cpp": [".cpp", ".hpp", ".cc", ".hh", ".cxx"],
    "java": [".java"],
    "rust": [".rs"],
    "perl": [".pl", ".pm"],
    "php": [".php"],
    "swift": [".swift"],
    "kotlin": [".kt", ".kts"],
    "webassembly": [".wat", ".wast"],
}

# Language → parser function mapping
_PARSER_REGISTRY = {}


def _ensure_parsers_loaded():
    """Lazy-load all parser modules."""
    if _PARSER_REGISTRY:
        return

    try:
        from ast_dsl.python_ast import parse_python_source
        _PARSER_REGISTRY["python"] = parse_python_source
    except ImportError:
        pass

    try:
        from ast_dsl.c_ast import parse_c_source
        _PARSER_REGISTRY["c"] = parse_c_source
        _PARSER_REGISTRY["cpp"] = parse_c_source
    except ImportError:
        pass

    try:
        from ast_dsl.java_ast import parse_java_source
        _PARSER_REGISTRY["java"] = parse_java_source
    except ImportError:
        pass

    try:
        from ast_dsl.rust_ast import parse_rust_source
        _PARSER_REGISTRY["rust"] = parse_rust_source
    except ImportError:
        pass

    try:
        from ast_dsl.go_ast import parse_go_source
        _PARSER_REGISTRY["go"] = parse_go_source
    except ImportError:
        pass

    try:
        from ast_dsl.perl_ast import parse_perl_source
        _PARSER_REGISTRY["perl"] = parse_perl_source
    except ImportError:
        pass

    try:
        from ast_dsl.php_ast import parse_php_source
        _PARSER_REGISTRY["php"] = parse_php_source
    except ImportError:
        pass

    try:
        from ast_dsl.swift_ast import parse_swift_source
        _PARSER_REGISTRY["swift"] = parse_swift_source
    except ImportError:
        pass

    try:
        from ast_dsl.kotlin_ast import parse_kotlin_source
        _PARSER_REGISTRY["kotlin"] = parse_kotlin_source
    except ImportError:
        pass

    try:
        from ast_dsl.typescript_ast import parse_typescript_source
        _PARSER_REGISTRY["typescript"] = parse_typescript_source
    except ImportError:
        pass

    try:
        from ast_dsl.wasm_ast import parse_wasm_source
        _PARSER_REGISTRY["webassembly"] = parse_wasm_source
    except ImportError:
        pass


@dataclass
class FileIntrospection:
    """Introspection result for a single source file."""
    filepath: str
    language: str
    lines: int = 0
    bytes: int = 0
    ast_nodes: int = 0
    functions: int = 0
    classes: int = 0
    imports: int = 0
    comments: int = 0
    compact_ast: str = ""
    parse_time_ms: float = 0.0
    source_tokens_approx: int = 0
    ast_tokens_approx: int = 0

    @property
    def compaction_ratio(self) -> float:
        if self.source_tokens_approx == 0:
            return 0.0
        return self.source_tokens_approx / max(self.ast_tokens_approx, 1)

    def to_dict(self) -> dict:
        return {
            "file": self.filepath,
            "lang": self.language,
            "lines": self.lines,
            "bytes": self.bytes,
            "ast_nodes": self.ast_nodes,
            "functions": self.functions,
            "classes": self.classes,
            "imports": self.imports,
            "compact_ratio": round(self.compaction_ratio, 1),
            "parse_ms": round(self.parse_time_ms, 2),
        }


@dataclass
class IntrospectionReport:
    """Aggregate introspection report for an application."""
    app_name: str
    language: str
    root_path: str
    files: list = field(default_factory=list)
    total_lines: int = 0
    total_bytes: int = 0
    total_ast_nodes: int = 0
    total_functions: int = 0
    total_classes: int = 0
    total_imports: int = 0
    total_parse_time_ms: float = 0.0
    avg_compaction_ratio: float = 0.0
    source_tokens_total: int = 0
    ast_tokens_total: int = 0

    def summary(self) -> str:
        lines = [
            f"=== AST Self-Introspection: {self.app_name} ({self.language}) ===",
            f"Root: {self.root_path}",
            f"Files: {len(self.files)}",
            f"Lines: {self.total_lines:,}",
            f"Bytes: {self.total_bytes:,}",
            f"AST Nodes: {self.total_ast_nodes:,}",
            f"Functions: {self.total_functions}",
            f"Classes/Structs: {self.total_classes}",
            f"Imports: {self.total_imports}",
            f"Parse Time: {self.total_parse_time_ms:.1f}ms",
            f"Source Tokens (approx): {self.source_tokens_total:,}",
            f"AST Tokens (approx): {self.ast_tokens_total:,}",
            f"Compaction Ratio: {self.avg_compaction_ratio:.1f}x",
        ]
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "app": self.app_name,
            "language": self.language,
            "root": self.root_path,
            "file_count": len(self.files),
            "total_lines": self.total_lines,
            "total_bytes": self.total_bytes,
            "total_ast_nodes": self.total_ast_nodes,
            "total_functions": self.total_functions,
            "total_classes": self.total_classes,
            "total_imports": self.total_imports,
            "parse_time_ms": round(self.total_parse_time_ms, 2),
            "compaction_ratio": round(self.avg_compaction_ratio, 1),
            "source_tokens": self.source_tokens_total,
            "ast_tokens": self.ast_tokens_total,
            "files": [f.to_dict() for f in self.files],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


def _count_node_types(ast_node: ASTNode) -> dict:
    """Count functions, classes, imports from an AST tree."""
    counts = {"functions": 0, "classes": 0, "imports": 0, "total": 0}
    for node in ast_node.walk():
        counts["total"] += 1
        nt = node.node_type.lower()
        if "function" in nt or "method" in nt or nt == "funcdef" or nt == "sub":
            counts["functions"] += 1
        elif "class" in nt or "struct" in nt or "interface" in nt or "trait" in nt:
            counts["classes"] += 1
        elif "import" in nt or "use" in nt or "require" in nt or "include" in nt:
            counts["imports"] += 1
    return counts


def introspect_file(filepath: str, language: str) -> FileIntrospection:
    """Introspect a single source file."""
    _ensure_parsers_loaded()

    result = FileIntrospection(filepath=filepath, language=language)

    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
    except (OSError, IOError):
        return result

    result.lines = source.count("\n") + 1
    result.bytes = len(source.encode("utf-8"))
    result.source_tokens_approx = len(source) // 4

    parser = _PARSER_REGISTRY.get(language)
    if parser is None:
        # Fall back to regex-based line counting
        result.compact_ast = f"[no parser for {language}]"
        return result

    t0 = time.monotonic()
    try:
        ast_node = parser(source, filename=filepath)
        result.parse_time_ms = (time.monotonic() - t0) * 1000

        counts = _count_node_types(ast_node)
        result.ast_nodes = counts["total"]
        result.functions = counts["functions"]
        result.classes = counts["classes"]
        result.imports = counts["imports"]
        result.compact_ast = ast_node.to_compact()
        result.ast_tokens_approx = len(result.compact_ast) // 4
    except Exception:
        result.parse_time_ms = (time.monotonic() - t0) * 1000
        result.compact_ast = "[parse error]"

    return result


def introspect_app(
    root_path: str,
    language: str,
    app_name: Optional[str] = None,
    exclude_dirs: Optional[set] = None,
) -> IntrospectionReport:
    """Introspect an entire application directory.

    Args:
        root_path: Root directory of the application source.
        language: Language identifier (e.g., "python", "rust", "go").
        app_name: Display name for the report. Defaults to directory name.
        exclude_dirs: Set of directory names to skip (e.g., {"node_modules", "target"}).

    Returns:
        IntrospectionReport with per-file and aggregate metrics.
    """
    if app_name is None:
        app_name = os.path.basename(os.path.abspath(root_path))

    if exclude_dirs is None:
        exclude_dirs = {
            "node_modules", "target", "build", "dist", ".gradle",
            "__pycache__", ".git", "vendor", "pkg",
        }

    extensions = set(LANG_EXTENSIONS.get(language, []))
    report = IntrospectionReport(
        app_name=app_name,
        language=language,
        root_path=root_path,
    )

    # Collect source files
    source_files = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        # Skip excluded directories
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        for fname in filenames:
            if any(fname.endswith(ext) for ext in extensions):
                source_files.append(os.path.join(dirpath, fname))

    source_files.sort()

    for fpath in source_files:
        fi = introspect_file(fpath, language)
        report.files.append(fi)
        report.total_lines += fi.lines
        report.total_bytes += fi.bytes
        report.total_ast_nodes += fi.ast_nodes
        report.total_functions += fi.functions
        report.total_classes += fi.classes
        report.total_imports += fi.imports
        report.total_parse_time_ms += fi.parse_time_ms
        report.source_tokens_total += fi.source_tokens_approx
        report.ast_tokens_total += fi.ast_tokens_approx

    if report.ast_tokens_total > 0:
        report.avg_compaction_ratio = (
            report.source_tokens_total / report.ast_tokens_total
        )

    return report


def introspect_all_apps(project_root: str) -> dict:
    """Introspect all applications in the project.

    Returns a dict mapping app name to IntrospectionReport.
    """
    apps_dir = os.path.join(project_root, "apps")
    if not os.path.isdir(apps_dir):
        return {}

    # App directory → language mapping
    app_languages = {
        "c": "c",
        "cpp": "cpp",
        "rust": "rust",
        "go": "go",
        "java": "java",
        "nodejs": "javascript",
        "typescript": "typescript",
        "perl": "perl",
        "php": "php",
        "swift": "swift",
        "kotlin": "kotlin",
        "wasm": "rust",  # WASM app is written in Rust
        "screensaver-ubuntu": "c",
        "screensaver-macos": "swift",
    }

    reports = {}
    for app_dir, lang in app_languages.items():
        app_path = os.path.join(apps_dir, app_dir)
        if os.path.isdir(app_path):
            report = introspect_app(
                root_path=app_path,
                language=lang,
                app_name=app_dir,
            )
            reports[app_dir] = report

    return reports
