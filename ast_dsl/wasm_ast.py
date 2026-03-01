"""WebAssembly Text Format (WAT) AST introspection using regex-based parsing.

Provides WAT AST analysis by parsing S-expression based WAT source
into a universal AST representation for symbol extraction and analysis.
"""
import re
from ast_dsl.core import ASTNode


def parse_wasm_source(source: str,
                      filename: str = "<string>") -> ASTNode:
    """Parse WAT source into universal AST using lightweight parser."""
    root = ASTNode(node_type="WasmModule", name=filename)

    # Type declarations
    for m in re.finditer(r"\(type\s+(\$[\w.]+)\s", source):
        line = source[:m.start()].count("\n") + 1
        root.children.append(ASTNode(
            node_type="TypeDecl",
            name=m.group(1).lstrip("$"),
            line=line,
        ))

    # Import declarations
    import_pat = re.compile(
        r'\(import\s+"([^"]+)"\s+"([^"]+)"\s+\((\w+)',
        re.MULTILINE
    )
    for m in import_pat.finditer(source):
        line = source[:m.start()].count("\n") + 1
        attrs = {
            "import_module": m.group(1).lstrip("$"),
            "import_name": m.group(2),
            "kind": m.group(3),
        }
        root.children.append(ASTNode(
            node_type="ImportDecl",
            name=f"{m.group(1)}.{m.group(2)}",
            line=line,
            attributes=attrs,
        ))

    # Function declarations (top-level only, not refs inside other exprs)
    func_pat = re.compile(
        r"\(func\s+(\$[\w.]+)"
        r"((?:\s+\((?:param|result|local)[^)]*\))*)",
        re.MULTILINE
    )
    for m in func_pat.finditer(source):
        # Skip func references nested inside import/export/elem
        preceding = source[max(0, m.start() - 80):m.start()]
        if re.search(
            r'\((import\s+"[^"]*"\s+"[^"]*"|export\s+"[^"]*"|elem)\s*$',
            preceding
        ):
            continue
        line = source[:m.start()].count("\n") + 1
        signature = m.group(2)
        params = re.findall(r"\(param\b", signature)
        results = re.findall(r"\(result\s+(\w+)\)", signature)
        attrs = {"param_count": len(params)}
        if results:
            attrs["result_type"] = results[0]
        root.children.append(ASTNode(
            node_type="FuncDecl",
            name=m.group(1).lstrip("$"),
            line=line,
            attributes=attrs,
        ))

    # Export declarations
    export_pat = re.compile(
        r'\(export\s+"([^"]+)"\s+\((\w+)',
        re.MULTILINE
    )
    for m in export_pat.finditer(source):
        line = source[:m.start()].count("\n") + 1
        attrs = {
            "export_name": m.group(1).lstrip("$"),
            "kind": m.group(2),
        }
        root.children.append(ASTNode(
            node_type="ExportDecl",
            name=m.group(1).lstrip("$"),
            line=line,
            attributes=attrs,
        ))

    # Memory declarations (skip those inside imports)
    for m in re.finditer(r"\(memory\s+(?:(\$[\w.]+)\s+)?(\d+)", source):
        preceding = source[max(0, m.start() - 80):m.start()]
        if re.search(r'\(import\s+"[^"]*"\s+"[^"]*"\s*$', preceding):
            continue
        line = source[:m.start()].count("\n") + 1
        attrs = {"initial_pages": int(m.group(2))}
        name = m.group(1) or ""
        root.children.append(ASTNode(
            node_type="MemoryDecl",
            name=name,
            line=line,
            attributes=attrs,
        ))

    # Table declarations (skip those inside imports)
    for m in re.finditer(r"\(table\s+(?:(\$[\w.]+)\s+)?(\d+)\s+(\w+)",
                         source):
        preceding = source[max(0, m.start() - 80):m.start()]
        if re.search(r'\(import\s+"[^"]*"\s+"[^"]*"\s*$', preceding):
            continue
        line = source[:m.start()].count("\n") + 1
        attrs = {
            "initial_size": int(m.group(2)),
            "element_type": m.group(3),
        }
        name = m.group(1) or ""
        root.children.append(ASTNode(
            node_type="TableDecl",
            name=name,
            line=line,
            attributes=attrs,
        ))

    # Global declarations
    global_pat = re.compile(
        r"\(global\s+(\$[\w.]+)\s+\(?(mut\s+)?(\w+)\)?",
        re.MULTILINE
    )
    for m in global_pat.finditer(source):
        line = source[:m.start()].count("\n") + 1
        attrs = {"value_type": m.group(3)}
        if m.group(2):
            attrs["mutable"] = True
        root.children.append(ASTNode(
            node_type="GlobalDecl",
            name=m.group(1).lstrip("$"),
            line=line,
            attributes=attrs,
        ))

    # Data segments
    for m in re.finditer(r"\(data\b", source):
        line = source[:m.start()].count("\n") + 1
        root.children.append(ASTNode(
            node_type="DataSegment",
            name="",
            line=line,
        ))

    # Element segments
    for m in re.finditer(r"\(elem\b", source):
        line = source[:m.start()].count("\n") + 1
        root.children.append(ASTNode(
            node_type="ElemSegment",
            name="",
            line=line,
        ))

    # Start function
    for m in re.finditer(r"\(start\s+(\$[\w.]+)\)", source):
        line = source[:m.start()].count("\n") + 1
        root.children.append(ASTNode(
            node_type="StartDecl",
            name=m.group(1).lstrip("$"),
            line=line,
        ))

    return root


def find_wasm_symbols(source: str) -> list:
    """Extract all symbols from WAT source."""
    root = parse_wasm_source(source)
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
