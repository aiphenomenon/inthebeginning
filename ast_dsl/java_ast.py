"""Java AST introspection using javac and javap.

Parses Java source by invoking javac for compilation then javap for
class analysis. Also provides a regex-based lightweight parser for
quick symbol extraction without requiring compilation.
"""
import os
import re
import subprocess
import tempfile
from ast_dsl.core import ASTNode


def parse_java_source(source: str,
                      filename: str = "<string>") -> ASTNode:
    """Parse Java source into universal AST using lightweight parser."""
    root = ASTNode(node_type="CompilationUnit", name=filename)

    # Package declaration
    pkg_match = re.search(r"package\s+([\w.]+)\s*;", source)
    if pkg_match:
        root.children.append(ASTNode(
            node_type="PackageDecl",
            name=pkg_match.group(1),
            line=source[:pkg_match.start()].count("\n") + 1,
        ))

    # Import declarations
    for m in re.finditer(r"import\s+(static\s+)?([\w.*]+)\s*;", source):
        line = source[:m.start()].count("\n") + 1
        attrs = {}
        if m.group(1):
            attrs["static"] = True
        root.children.append(ASTNode(
            node_type="ImportDecl",
            name=m.group(2),
            line=line,
            attributes=attrs,
        ))

    # Class/interface/enum declarations
    class_pat = re.compile(
        r"(public|private|protected|abstract|final|static|\s)*"
        r"(class|interface|enum|record)\s+(\w+)"
        r"(?:\s+extends\s+(\w+))?"
        r"(?:\s+implements\s+([\w,\s]+))?"
        r"\s*\{",
        re.MULTILINE
    )
    for m in class_pat.finditer(source):
        line = source[:m.start()].count("\n") + 1
        attrs = {}
        if m.group(4):
            attrs["extends"] = m.group(4)
        if m.group(5):
            attrs["implements"] = [
                s.strip() for s in m.group(5).split(",")
            ]
        class_node = ASTNode(
            node_type=m.group(2).capitalize() + "Decl",
            name=m.group(3),
            line=line,
            attributes=attrs,
        )

        # Find methods within class scope
        # (simplified - doesn't handle nested braces perfectly)
        method_pat = re.compile(
            r"(public|private|protected|static|final|abstract|synchronized|\s)*"
            r"([\w<>\[\]]+)\s+(\w+)\s*\(([^)]*)\)",
            re.MULTILINE
        )
        class_body_start = m.end()
        for mm in method_pat.finditer(source[class_body_start:]):
            mline = source[:class_body_start + mm.start()].count("\n") + 1
            params = [p.strip() for p in mm.group(4).split(",")
                      if p.strip()]
            method_attrs = {
                "return_type": mm.group(2),
                "params": len(params),
            }
            class_node.children.append(ASTNode(
                node_type="MethodDecl",
                name=mm.group(3),
                line=mline,
                attributes=method_attrs,
            ))

        root.children.append(class_node)

    return root


def parse_java_with_javac(filepath: str) -> ASTNode:
    """Parse Java file using javac -Xprint for detailed AST."""
    try:
        result = subprocess.run(
            ["javac", "-Xprint", filepath],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return _parse_javac_output(result.stdout, filepath)
        # Fall back to lightweight parser
        with open(filepath) as f:
            return parse_java_source(f.read(), filepath)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        with open(filepath) as f:
            return parse_java_source(f.read(), filepath)


def _parse_javac_output(output: str, filename: str) -> ASTNode:
    """Parse javac -Xprint output."""
    root = ASTNode(node_type="CompilationUnit", name=filename)
    lines = output.strip().split("\n")
    for i, line in enumerate(lines):
        stripped = line.strip()
        if "class " in stripped or "interface " in stripped:
            parts = stripped.split()
            for j, p in enumerate(parts):
                if p in ("class", "interface", "enum"):
                    if j + 1 < len(parts):
                        root.children.append(ASTNode(
                            node_type=p.capitalize() + "Decl",
                            name=parts[j + 1].rstrip("{"),
                            line=i + 1,
                        ))
                    break
    return root


def find_java_symbols(source: str) -> list:
    """Extract all symbols from Java source."""
    root = parse_java_source(source)
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
