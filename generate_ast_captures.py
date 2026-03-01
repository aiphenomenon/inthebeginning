#!/usr/bin/env python3
"""Generate full and compact AST capture files for the entire codebase."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ast_dsl.core import ASTEngine, ASTQuery


def main():
    engine = ASTEngine()
    base = os.path.dirname(os.path.abspath(__file__))

    # Collect all Python files
    py_files = []
    for dirpath, dirnames, filenames in os.walk(base):
        # Skip hidden dirs and node_modules
        dirnames[:] = [d for d in dirnames
                       if not d.startswith('.') and d != 'node_modules']
        for f in sorted(filenames):
            if f.endswith('.py') and not f.startswith('__'):
                py_files.append(os.path.join(dirpath, f))

    # Full AST capture
    full_ast = {}
    for filepath in py_files:
        relpath = os.path.relpath(filepath, base)
        result = engine.execute(ASTQuery(
            action="parse", target=filepath, language="python"
        ))
        if result.success:
            full_ast[relpath] = result.to_dict()

    full_path = os.path.join(base, "ast_captures", "full_ast.json")
    with open(full_path, "w") as f:
        json.dump(full_ast, f, indent=2, default=str)
    full_size = os.path.getsize(full_path)
    print(f"Full AST: {full_path} ({full_size:,} bytes)")

    # Compact AST capture
    compact_lines = []
    for filepath in py_files:
        relpath = os.path.relpath(filepath, base)
        result = engine.execute(ASTQuery(
            action="parse", target=filepath, language="python"
        ))
        if result.success:
            compact_lines.append(f"# {relpath}")
            compact_lines.append(result.to_compact())
            compact_lines.append("")

    compact_path = os.path.join(base, "ast_captures", "compact_ast.txt")
    with open(compact_path, "w") as f:
        f.write("\n".join(compact_lines))
    compact_size = os.path.getsize(compact_path)
    print(f"Compact AST: {compact_path} ({compact_size:,} bytes)")

    # Stats
    ratio = compact_size / full_size * 100 if full_size > 0 else 0
    print(f"Compression ratio: {ratio:.1f}% of full size")
    print(f"Token estimate (full): ~{full_size // 4} tokens")
    print(f"Token estimate (compact): ~{compact_size // 4} tokens")

    # Also generate per-module symbol summaries
    symbols_path = os.path.join(base, "ast_captures", "symbols.json")
    all_symbols = {}
    for filepath in py_files:
        relpath = os.path.relpath(filepath, base)
        result = engine.execute(ASTQuery(
            action="symbols", target=filepath, language="python"
        ))
        if result.success and isinstance(result.data, list):
            all_symbols[relpath] = result.data

    with open(symbols_path, "w") as f:
        json.dump(all_symbols, f, indent=2, default=str)
    print(f"Symbols: {symbols_path} ({os.path.getsize(symbols_path):,} bytes)")

    # Coverage map
    coverage_path = os.path.join(base, "ast_captures", "coverage_map.json")
    coverage = {}
    for filepath in py_files:
        relpath = os.path.relpath(filepath, base)
        result = engine.execute(ASTQuery(
            action="coverage_map", target=filepath, language="python"
        ))
        if result.success and isinstance(result.data, list):
            coverage[relpath] = result.data

    with open(coverage_path, "w") as f:
        json.dump(coverage, f, indent=2, default=str)
    print(f"Coverage map: {coverage_path} ({os.path.getsize(coverage_path):,} bytes)")


if __name__ == "__main__":
    main()
