"""Perl AST introspection using B::Deparse and regex-based parsing.

Provides Perl AST analysis via perl -MO=Deparse or regex-based
lightweight parsing for symbol extraction.
"""
import os
import re
import subprocess
import tempfile
from ast_dsl.core import ASTNode


def parse_perl_source(source: str,
                      filename: str = "<string>") -> ASTNode:
    """Parse Perl source into universal AST using regex parser."""
    root = ASTNode(node_type="PerlScript", name=filename)

    # Use/require declarations
    for m in re.finditer(r"(use|require)\s+([\w:]+)(?:\s+([^;]+))?;",
                         source):
        line = source[:m.start()].count("\n") + 1
        attrs = {}
        if m.group(3):
            attrs["args"] = m.group(3).strip()
        root.children.append(ASTNode(
            node_type="UseDecl" if m.group(1) == "use" else "RequireDecl",
            name=m.group(2),
            line=line,
            attributes=attrs,
        ))

    # Package declarations
    for m in re.finditer(r"package\s+([\w:]+)\s*;", source):
        line = source[:m.start()].count("\n") + 1
        root.children.append(ASTNode(
            node_type="PackageDecl",
            name=m.group(1),
            line=line,
        ))

    # Subroutine declarations
    sub_pat = re.compile(r"sub\s+(\w+)\s*(?:\(([^)]*)\))?\s*\{",
                         re.MULTILINE)
    for m in sub_pat.finditer(source):
        line = source[:m.start()].count("\n") + 1
        attrs = {}
        if m.group(2):
            attrs["prototype"] = m.group(2)
        root.children.append(ASTNode(
            node_type="SubDecl",
            name=m.group(1),
            line=line,
            attributes=attrs,
        ))

    # Method calls (arrow notation)
    for m in re.finditer(r"->(\w+)\s*\(", source):
        line = source[:m.start()].count("\n") + 1
        root.children.append(ASTNode(
            node_type="MethodCall",
            name=m.group(1),
            line=line,
        ))

    # Variable declarations (my, our, local)
    for m in re.finditer(r"(my|our|local)\s+([\$@%]\w+)", source):
        line = source[:m.start()].count("\n") + 1
        root.children.append(ASTNode(
            node_type="VarDecl",
            name=m.group(2),
            line=line,
            attributes={"scope": m.group(1)},
        ))

    return root


def parse_perl_with_deparse(filepath: str) -> ASTNode:
    """Use perl -MO=Deparse for deeper analysis."""
    try:
        result = subprocess.run(
            ["perl", "-MO=Deparse", filepath],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            root = ASTNode(node_type="PerlScript", name=filepath)
            root.attributes["deparsed_lines"] = len(
                result.stdout.split("\n")
            )
            # Also do regex parse for symbols
            with open(filepath) as f:
                source = f.read()
            regex_root = parse_perl_source(source, filepath)
            root.children = regex_root.children
            return root
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    with open(filepath) as f:
        return parse_perl_source(f.read(), filepath)


def find_perl_symbols(source: str) -> list:
    """Extract all symbols from Perl source."""
    root = parse_perl_source(source)
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
