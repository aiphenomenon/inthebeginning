"""C/C++ AST introspection using pycparser and clang.

Provides C and C++ AST parsing via pycparser (pure C) and falls back
to clang's AST dump for C++ code. Outputs universal AST format.
"""
import json
import os
import subprocess
import tempfile
from ast_dsl.core import ASTNode


def parse_c_source(source: str, filename: str = "<string>") -> ASTNode:
    """Parse C source code using pycparser."""
    try:
        import pycparser
    except ImportError:
        return ASTNode(node_type="Error",
                       name="pycparser not installed")

    # Write to temp file if needed
    if not os.path.isfile(filename):
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False)
        tmp.write(source)
        tmp.close()
        filename = tmp.name

    try:
        parser = pycparser.CParser()
        tree = parser.parse(source, filename=filename)
        return _convert_pycparser_node(tree)
    except pycparser.plyparser.ParseError as e:
        return ASTNode(node_type="ParseError", name=str(e))


def _convert_pycparser_node(node) -> ASTNode:
    """Convert pycparser AST node to universal format."""
    node_type = type(node).__name__
    name = ""
    attrs = {}
    children = []

    if hasattr(node, "name") and node.name:
        name = node.name
    if hasattr(node, "declname") and node.declname:
        name = node.declname

    coord = getattr(node, "coord", None)
    line = coord.line if coord else 0
    col = coord.column if coord else 0

    # Extract type-specific attributes
    if node_type == "FuncDecl":
        if hasattr(node, "args") and node.args:
            attrs["param_count"] = len(node.args.params) if node.args.params else 0
    elif node_type == "Decl":
        if hasattr(node, "quals"):
            attrs["quals"] = node.quals
        if hasattr(node, "storage"):
            attrs["storage"] = node.storage

    # Recurse into children
    for child_name, child in node.children():
        children.append(_convert_pycparser_node(child))

    return ASTNode(
        node_type=node_type,
        name=name,
        children=children,
        attributes=attrs,
        line=line,
        col=col,
    )


def parse_cpp_with_clang(source: str,
                         filename: str = "<string>") -> ASTNode:
    """Parse C++ source using clang -ast-dump."""
    if not os.path.isfile(filename):
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".cpp",
                                          delete=False)
        tmp.write(source)
        tmp.close()
        filename = tmp.name

    try:
        result = subprocess.run(
            ["clang", "-Xclang", "-ast-dump", "-fsyntax-only",
             "-fno-color-diagnostics", filename],
            capture_output=True, text=True, timeout=30
        )
        return _parse_clang_dump(result.stdout)
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return ASTNode(node_type="Error", name=str(e))


def _parse_clang_dump(dump: str) -> ASTNode:
    """Parse clang -ast-dump output into universal AST."""
    lines = dump.strip().split("\n")
    if not lines:
        return ASTNode(node_type="Empty")

    root = ASTNode(node_type="TranslationUnit")
    stack = [(root, -1)]

    for line in lines:
        stripped = line.lstrip("| `\\-")
        depth = (len(line) - len(line.lstrip("| `"))) // 2

        parts = stripped.split(" ", 2)
        node_type = parts[0] if parts else "Unknown"

        name = ""
        attrs = {}
        line_num = 0

        for part in parts[1:]:
            if part.startswith("<") and ":" in part:
                # Location info
                loc = part.strip("<>").split(":")
                if len(loc) >= 2:
                    try:
                        line_num = int(loc[1])
                    except ValueError:
                        pass
            elif not part.startswith("<") and not part.startswith("0x"):
                if not name:
                    name = part.strip("'\"")

        node = ASTNode(
            node_type=node_type,
            name=name,
            attributes=attrs,
            line=line_num,
        )

        while stack and stack[-1][1] >= depth:
            stack.pop()

        if stack:
            stack[-1][0].children.append(node)

        stack.append((node, depth))

    return root


def find_c_symbols(source: str) -> list:
    """Find all function and type declarations in C source."""
    root = parse_c_source(source)
    symbols = []
    for node in root.walk():
        if node.node_type in ("FuncDecl", "FuncDef", "Struct",
                              "Union", "Enum", "Typedef"):
            symbols.append({
                "type": node.node_type,
                "name": node.name,
                "line": node.line,
            })
    return symbols


def to_compact(node: ASTNode) -> str:
    """Compact representation of C AST."""
    return node.to_compact()
