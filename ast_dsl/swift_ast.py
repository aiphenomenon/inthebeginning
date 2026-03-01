"""Swift AST introspection using regex-based parsing.

Provides Swift AST analysis using a lightweight regex-based parser
for quick symbol extraction without external dependencies.
"""
import re
from ast_dsl.core import ASTNode

_VISIBILITY = r"(?:(open|public|internal|fileprivate|private)\s+)?"
_STATIC = r"(?:(static|class)\s+)?"


def parse_swift_source(source: str,
                       filename: str = "<string>") -> ASTNode:
    """Parse Swift source into universal AST using lightweight parser."""
    root = ASTNode(node_type="SwiftModule", name=filename)

    # Import declarations
    for m in re.finditer(r"import\s+([\w.]+)", source):
        line = source[:m.start()].count("\n") + 1
        root.children.append(ASTNode(
            node_type="ImportDecl",
            name=m.group(1).strip(),
            line=line,
        ))

    # Struct declarations
    struct_pat = re.compile(
        _VISIBILITY + r"(final\s+)?struct\s+(\w+)(?:<([^>]+)>)?"
        r"(?:\s*:\s*([\w\s,&]+))?\s*\{",
        re.MULTILINE
    )
    for m in struct_pat.finditer(source):
        line = source[:m.start()].count("\n") + 1
        attrs = {}
        if m.group(1):
            attrs["visibility"] = m.group(1)
        if m.group(4):
            attrs["generic_params"] = m.group(4).strip()
        if m.group(5):
            attrs["conformances"] = [c.strip() for c in m.group(5).split(",")]
        root.children.append(ASTNode(
            node_type="StructDecl",
            name=m.group(3),
            line=line,
            attributes=attrs,
        ))

    # Class declarations
    class_pat = re.compile(
        _VISIBILITY + r"(final\s+)?class\s+(\w+)(?:<([^>]+)>)?"
        r"(?:\s*:\s*([\w\s,&]+))?\s*\{",
        re.MULTILINE
    )
    for m in class_pat.finditer(source):
        line = source[:m.start()].count("\n") + 1
        attrs = {}
        if m.group(1):
            attrs["visibility"] = m.group(1)
        if m.group(2):
            attrs["final"] = True
        if m.group(4):
            attrs["generic_params"] = m.group(4).strip()
        if m.group(5):
            attrs["conformances"] = [c.strip() for c in m.group(5).split(",")]
        root.children.append(ASTNode(
            node_type="ClassDecl",
            name=m.group(3),
            line=line,
            attributes=attrs,
        ))

    # Enum declarations
    enum_pat = re.compile(
        _VISIBILITY + r"enum\s+(\w+)(?:<([^>]+)>)?"
        r"(?:\s*:\s*([\w\s,&]+))?\s*\{",
        re.MULTILINE
    )
    for m in enum_pat.finditer(source):
        line = source[:m.start()].count("\n") + 1
        attrs = {}
        if m.group(1):
            attrs["visibility"] = m.group(1)
        if m.group(3):
            attrs["generic_params"] = m.group(3).strip()
        if m.group(4):
            raw = [c.strip() for c in m.group(4).split(",")]
            attrs["conformances"] = raw
        root.children.append(ASTNode(
            node_type="EnumDecl",
            name=m.group(2),
            line=line,
            attributes=attrs,
        ))

    # Protocol declarations
    proto_pat = re.compile(
        _VISIBILITY + r"protocol\s+(\w+)"
        r"(?:\s*:\s*([\w\s,&]+))?\s*\{",
        re.MULTILINE
    )
    for m in proto_pat.finditer(source):
        line = source[:m.start()].count("\n") + 1
        attrs = {}
        if m.group(1):
            attrs["visibility"] = m.group(1)
        if m.group(3):
            attrs["conformances"] = [c.strip() for c in m.group(3).split(",")]
        root.children.append(ASTNode(
            node_type="ProtocolDecl",
            name=m.group(2),
            line=line,
            attributes=attrs,
        ))

    # Extension declarations
    ext_pat = re.compile(
        _VISIBILITY + r"extension\s+(\w+)"
        r"(?:\s*:\s*([\w\s,&]+))?\s*\{",
        re.MULTILINE
    )
    for m in ext_pat.finditer(source):
        line = source[:m.start()].count("\n") + 1
        attrs = {}
        if m.group(1):
            attrs["visibility"] = m.group(1)
        if m.group(3):
            attrs["conformances"] = [c.strip() for c in m.group(3).split(",")]
        root.children.append(ASTNode(
            node_type="ExtensionDecl",
            name=m.group(2),
            line=line,
            attributes=attrs,
        ))

    # Actor declarations
    actor_pat = re.compile(
        _VISIBILITY + r"actor\s+(\w+)(?:<([^>]+)>)?"
        r"(?:\s*:\s*([\w\s,&]+))?\s*\{",
        re.MULTILINE
    )
    for m in actor_pat.finditer(source):
        line = source[:m.start()].count("\n") + 1
        attrs = {}
        if m.group(1):
            attrs["visibility"] = m.group(1)
        if m.group(3):
            attrs["generic_params"] = m.group(3).strip()
        if m.group(4):
            attrs["conformances"] = [c.strip() for c in m.group(4).split(",")]
        root.children.append(ASTNode(
            node_type="ActorDecl",
            name=m.group(2),
            line=line,
            attributes=attrs,
        ))

    # Function declarations
    fn_pat = re.compile(
        _VISIBILITY + _STATIC
        + r"(mutating\s+)?func\s+(\w+)\s*(?:<([^>]*)>)?\s*\(([^)]*)\)"
        r"(?:\s*(async))?"
        r"(?:\s*(throws|rethrows))?"
        r"(?:\s*->\s*([\w<>\[\]:?, ]+))?\s*\{",
        re.MULTILINE
    )
    for m in fn_pat.finditer(source):
        line = source[:m.start()].count("\n") + 1
        params = [p.strip() for p in m.group(6).split(",") if p.strip()]
        attrs = {"param_count": len(params)}
        if m.group(1):
            attrs["visibility"] = m.group(1)
        if m.group(2):
            attrs["static"] = True
        if m.group(3):
            attrs["mutating"] = True
        if m.group(5):
            attrs["generic_params"] = m.group(5).strip()
        if m.group(7):
            attrs["async"] = True
        if m.group(8):
            attrs["throws"] = True
        if m.group(9):
            attrs["return_type"] = m.group(9).strip()
        root.children.append(ASTNode(
            node_type="FuncDecl",
            name=m.group(4),
            line=line,
            attributes=attrs,
        ))

    # Initializer declarations
    init_pat = re.compile(
        _VISIBILITY + r"(convenience\s+)?init\s*(\?)?\s*\(([^)]*)\)",
        re.MULTILINE
    )
    for m in init_pat.finditer(source):
        line = source[:m.start()].count("\n") + 1
        params = [p.strip() for p in m.group(4).split(",") if p.strip()]
        attrs = {"param_count": len(params)}
        if m.group(1):
            attrs["visibility"] = m.group(1)
        if m.group(3):
            attrs["failable"] = True
        root.children.append(ASTNode(
            node_type="InitDecl",
            name="init",
            line=line,
            attributes=attrs,
        ))

    # Property declarations (var / let)
    prop_pat = re.compile(
        _VISIBILITY + _STATIC
        + r"(var|let)\s+(\w+)\s*:\s*([\w<>\[\]:?, ]+)"
        r"(?:\s*\{)?",
        re.MULTILINE
    )
    for m in prop_pat.finditer(source):
        line = source[:m.start()].count("\n") + 1
        attrs = {}
        if m.group(1):
            attrs["visibility"] = m.group(1)
        if m.group(2):
            attrs["static"] = True
        attrs["kind"] = m.group(3)
        # Detect computed properties by trailing brace on same match
        full = m.group(0)
        if full.rstrip().endswith("{") and m.group(3) == "var":
            attrs["computed"] = True
        root.children.append(ASTNode(
            node_type="PropertyDecl",
            name=m.group(4),
            line=line,
            attributes=attrs,
        ))

    # Typealias declarations
    alias_pat = re.compile(
        _VISIBILITY + r"typealias\s+(\w+)\s*=\s*(.+)",
        re.MULTILINE
    )
    for m in alias_pat.finditer(source):
        line = source[:m.start()].count("\n") + 1
        attrs = {"type": m.group(3).strip()}
        if m.group(1):
            attrs["visibility"] = m.group(1)
        root.children.append(ASTNode(
            node_type="TypeAliasDecl",
            name=m.group(2),
            line=line,
            attributes=attrs,
        ))

    # Attribute declarations (@propertyWrapper, @main, etc.)
    for m in re.finditer(r"@(\w+)", source):
        line = source[:m.start()].count("\n") + 1
        root.children.append(ASTNode(
            node_type="AttributeDecl",
            name=m.group(1),
            line=line,
        ))

    return root


def find_swift_symbols(source: str) -> list:
    """Extract all symbols from Swift source."""
    root = parse_swift_source(source)
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
