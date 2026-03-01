"""Rust AST introspection using rustc and regex-based parsing.

Provides Rust AST analysis by invoking rustc --emit=metadata or using
a lightweight regex-based parser for quick symbol extraction.
"""
import os
import re
import subprocess
import tempfile
from ast_dsl.core import ASTNode


def parse_rust_source(source: str,
                      filename: str = "<string>") -> ASTNode:
    """Parse Rust source into universal AST using lightweight parser."""
    root = ASTNode(node_type="Crate", name=filename)

    # Use declarations
    for m in re.finditer(r"use\s+([\w:*{},\s]+)\s*;", source):
        line = source[:m.start()].count("\n") + 1
        root.children.append(ASTNode(
            node_type="UseDecl",
            name=m.group(1).strip(),
            line=line,
        ))

    # Mod declarations
    for m in re.finditer(r"mod\s+(\w+)\s*[;{]", source):
        line = source[:m.start()].count("\n") + 1
        root.children.append(ASTNode(
            node_type="ModDecl",
            name=m.group(1),
            line=line,
        ))

    # Struct declarations
    struct_pat = re.compile(
        r"(pub\s+)?struct\s+(\w+)(?:<[^>]+>)?\s*[({]",
        re.MULTILINE
    )
    for m in struct_pat.finditer(source):
        line = source[:m.start()].count("\n") + 1
        attrs = {}
        if m.group(1):
            attrs["visibility"] = "pub"
        root.children.append(ASTNode(
            node_type="StructDecl",
            name=m.group(2),
            line=line,
            attributes=attrs,
        ))

    # Enum declarations
    for m in re.finditer(r"(pub\s+)?enum\s+(\w+)(?:<[^>]+>)?\s*\{",
                         source):
        line = source[:m.start()].count("\n") + 1
        attrs = {}
        if m.group(1):
            attrs["visibility"] = "pub"
        root.children.append(ASTNode(
            node_type="EnumDecl",
            name=m.group(2),
            line=line,
            attributes=attrs,
        ))

    # Trait declarations
    for m in re.finditer(r"(pub\s+)?trait\s+(\w+)(?:<[^>]+>)?\s*\{",
                         source):
        line = source[:m.start()].count("\n") + 1
        root.children.append(ASTNode(
            node_type="TraitDecl",
            name=m.group(2),
            line=line,
        ))

    # Impl blocks
    impl_pat = re.compile(
        r"impl(?:<[^>]+>)?\s+(?:(\w+)\s+for\s+)?(\w+)(?:<[^>]+>)?\s*\{",
        re.MULTILINE
    )
    for m in impl_pat.finditer(source):
        line = source[:m.start()].count("\n") + 1
        attrs = {}
        if m.group(1):
            attrs["trait"] = m.group(1)
        root.children.append(ASTNode(
            node_type="ImplBlock",
            name=m.group(2),
            line=line,
            attributes=attrs,
        ))

    # Function declarations
    fn_pat = re.compile(
        r"(pub\s+)?(async\s+)?fn\s+(\w+)\s*(?:<[^>]*>)?\s*\(([^)]*)\)"
        r"(?:\s*->\s*([\w<>&\[\], ]+))?\s*(?:where|{)",
        re.MULTILINE
    )
    for m in fn_pat.finditer(source):
        line = source[:m.start()].count("\n") + 1
        params = [p.strip() for p in m.group(4).split(",")
                  if p.strip()]
        attrs = {"params": len(params)}
        if m.group(1):
            attrs["visibility"] = "pub"
        if m.group(2):
            attrs["async"] = True
        if m.group(5):
            attrs["return_type"] = m.group(5).strip()
        root.children.append(ASTNode(
            node_type="FnDecl",
            name=m.group(3),
            line=line,
            attributes=attrs,
        ))

    return root


def parse_rust_with_rustc(filepath: str) -> ASTNode:
    """Attempt to use rustc for deeper analysis."""
    try:
        result = subprocess.run(
            ["rustc", "--edition=2021", "-Z", "unpretty=ast-tree",
             filepath],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            root = ASTNode(node_type="Crate", name=filepath)
            root.attributes["raw_ast_lines"] = len(
                result.stdout.split("\n")
            )
            return root
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    with open(filepath) as f:
        return parse_rust_source(f.read(), filepath)


def find_rust_symbols(source: str) -> list:
    """Extract all symbols from Rust source."""
    root = parse_rust_source(source)
    symbols = []
    for node in root.walk():
        if node.node_type.endswith("Decl") and node.name:
            symbols.append({
                "type": node.node_type,
                "name": node.name,
                "line": node.line,
            })
    return symbols


def to_compact(node: ASTNode) -> str:
    """Compact representation."""
    return node.to_compact()
