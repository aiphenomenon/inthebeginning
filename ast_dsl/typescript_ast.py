"""TypeScript AST introspection using regex-based parsing.

Provides TypeScript AST analysis using a lightweight regex-based parser
for quick symbol extraction without external dependencies.
"""
import re
from ast_dsl.core import ASTNode


def parse_typescript_source(source: str,
                            filename: str = "<string>") -> ASTNode:
    """Parse TypeScript source into universal AST using lightweight parser."""
    root = ASTNode(node_type="TSModule", name=filename)

    # Decorator declarations
    for m in re.finditer(r"@(\w+)(?:\([^)]*\))?", source):
        line = source[:m.start()].count("\n") + 1
        root.children.append(ASTNode(
            node_type="DecoratorDecl",
            name=m.group(1),
            line=line,
        ))

    # Import declarations
    import_pat = re.compile(
        r"import\s+(?:(\{[^}]+\})|(\w+)|\*\s+as\s+(\w+))"
        r"\s+from\s+['\"]([^'\"]+)['\"]",
        re.MULTILINE
    )
    for m in import_pat.finditer(source):
        line = source[:m.start()].count("\n") + 1
        name = m.group(4)
        attrs = {}
        if m.group(1):
            names = [n.strip() for n in m.group(1).strip("{}").split(",")
                     if n.strip()]
            attrs["names"] = names
        elif m.group(2):
            attrs["default"] = m.group(2)
        elif m.group(3):
            attrs["namespace"] = m.group(3)
        root.children.append(ASTNode(
            node_type="ImportDecl",
            name=name,
            line=line,
            attributes=attrs,
        ))

    # Export declarations
    for m in re.finditer(
        r"export\s+(?:default\s+)?(?:(?:async\s+)?function|class|interface"
        r"|type|enum|const|let|var|namespace)\s+(\w+)",
        source
    ):
        line = source[:m.start()].count("\n") + 1
        attrs = {}
        if "default" in m.group(0):
            attrs["default"] = True
        root.children.append(ASTNode(
            node_type="ExportDecl",
            name=m.group(1),
            line=line,
            attributes=attrs,
        ))

    # Interface declarations
    iface_pat = re.compile(
        r"(?:export\s+)?interface\s+(\w+)(?:<([^>]+)>)?"
        r"(?:\s+extends\s+([\w,\s]+))?\s*\{",
        re.MULTILINE
    )
    for m in iface_pat.finditer(source):
        line = source[:m.start()].count("\n") + 1
        attrs = {}
        if m.group(2):
            attrs["generic_params"] = m.group(2).strip()
        if m.group(3):
            attrs["extends"] = m.group(3).strip()
        root.children.append(ASTNode(
            node_type="InterfaceDecl",
            name=m.group(1),
            line=line,
            attributes=attrs,
        ))

    # Type alias declarations
    for m in re.finditer(
        r"(?:export\s+)?type\s+(\w+)(?:<([^>]+)>)?\s*=", source
    ):
        line = source[:m.start()].count("\n") + 1
        attrs = {}
        if m.group(2):
            attrs["generic_params"] = m.group(2).strip()
        root.children.append(ASTNode(
            node_type="TypeAliasDecl",
            name=m.group(1),
            line=line,
            attributes=attrs,
        ))

    # Enum declarations
    for m in re.finditer(
        r"(?:export\s+)?(?:const\s+)?enum\s+(\w+)\s*\{", source
    ):
        line = source[:m.start()].count("\n") + 1
        root.children.append(ASTNode(
            node_type="EnumDecl",
            name=m.group(1),
            line=line,
        ))

    # Class declarations
    class_pat = re.compile(
        r"(?:export\s+)?(?:(abstract)\s+)?class\s+(\w+)(?:<([^>]+)>)?"
        r"(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w,\s]+))?\s*\{",
        re.MULTILINE
    )
    for m in class_pat.finditer(source):
        line = source[:m.start()].count("\n") + 1
        attrs = {}
        if m.group(1):
            attrs["abstract"] = True
        if m.group(3):
            attrs["generic_params"] = m.group(3).strip()
        if m.group(4):
            attrs["extends"] = m.group(4)
        if m.group(5):
            attrs["implements"] = m.group(5).strip()
        root.children.append(ASTNode(
            node_type="ClassDecl",
            name=m.group(2),
            line=line,
            attributes=attrs,
        ))

    # Function declarations
    fn_pat = re.compile(
        r"(?:export\s+)?(?:declare\s+)?(async\s+)?function\s+(\w+)"
        r"(?:<([^>]*)>)?\s*\(([^)]*)\)(?:\s*:\s*([\w<>\[\]|&\s,]+))?\s*\{?",
        re.MULTILINE
    )
    for m in fn_pat.finditer(source):
        line = source[:m.start()].count("\n") + 1
        params = [p.strip() for p in m.group(4).split(",")
                  if p.strip()]
        attrs = {"param_count": len(params)}
        if m.group(1):
            attrs["async"] = True
        if m.group(3):
            attrs["generic_params"] = m.group(3).strip()
        if m.group(5):
            attrs["return_type"] = m.group(5).strip()
        root.children.append(ASTNode(
            node_type="FunctionDecl",
            name=m.group(2),
            line=line,
            attributes=attrs,
        ))

    # Variable declarations
    var_pat = re.compile(
        r"(?:export\s+)?(const|let|var)\s+(\w+)"
        r"(?:\s*:\s*([\w<>\[\]|&\s,]+))?\s*=",
        re.MULTILINE
    )
    for m in var_pat.finditer(source):
        line = source[:m.start()].count("\n") + 1
        attrs = {"kind": m.group(1)}
        if m.group(3):
            attrs["type_annotation"] = m.group(3).strip()
        root.children.append(ASTNode(
            node_type="VarDecl",
            name=m.group(2),
            line=line,
            attributes=attrs,
        ))

    # Method declarations inside classes
    method_pat = re.compile(
        r"(?:(public|private|protected)\s+)?"
        r"(?:(abstract|static)\s+)?"
        r"(async\s+)?(\w+)\s*(?:<([^>]*)>)?\s*\(([^)]*)\)"
        r"(?:\s*:\s*([\w<>\[\]|&\s,]+))?\s*[{;]",
        re.MULTILINE
    )
    for m in method_pat.finditer(source):
        line = source[:m.start()].count("\n") + 1
        name = m.group(4)
        if name in ("if", "for", "while", "switch", "catch", "function",
                     "class", "interface", "type", "enum", "import",
                     "export", "return", "const", "let", "var"):
            continue
        params = [p.strip() for p in m.group(6).split(",")
                  if p.strip()]
        attrs = {"param_count": len(params)}
        if m.group(1):
            attrs["visibility"] = m.group(1)
        if m.group(2):
            attrs[m.group(2)] = True
        if m.group(3):
            attrs["async"] = True
        if m.group(5):
            attrs["generic_params"] = m.group(5).strip()
        if m.group(7):
            attrs["return_type"] = m.group(7).strip()
        root.children.append(ASTNode(
            node_type="MethodDecl",
            name=name,
            line=line,
            attributes=attrs,
        ))

    # Namespace declarations
    for m in re.finditer(
        r"(?:export\s+)?namespace\s+(\w+)\s*\{", source
    ):
        line = source[:m.start()].count("\n") + 1
        root.children.append(ASTNode(
            node_type="NamespaceDecl",
            name=m.group(1),
            line=line,
        ))

    return root


def find_typescript_symbols(source: str) -> list:
    """Extract all symbols from TypeScript source."""
    root = parse_typescript_source(source)
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
