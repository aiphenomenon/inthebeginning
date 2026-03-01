"""Kotlin AST introspection using regex-based parsing.

Provides Kotlin AST analysis using a lightweight regex-based parser
for quick symbol extraction from Kotlin source files.
"""
import re
from ast_dsl.core import ASTNode


def parse_kotlin_source(source: str,
                        filename: str = "<string>") -> ASTNode:
    """Parse Kotlin source into universal AST using lightweight parser."""
    root = ASTNode(node_type="KotlinFile", name=filename)

    # Package declarations
    for m in re.finditer(r"package\s+([\w.]+)", source):
        line = source[:m.start()].count("\n") + 1
        root.children.append(ASTNode(
            node_type="PackageDecl",
            name=m.group(1),
            line=line,
        ))

    # Import declarations
    for m in re.finditer(r"import\s+([\w.*]+)", source):
        line = source[:m.start()].count("\n") + 1
        root.children.append(ASTNode(
            node_type="ImportDecl",
            name=m.group(1),
            line=line,
        ))

    # Type alias declarations
    for m in re.finditer(
        r"(?:public|private|internal|protected)?\s*"
        r"typealias\s+(\w+)\s*=\s*([\w.<>, ]+)", source
    ):
        line = source[:m.start()].count("\n") + 1
        root.children.append(ASTNode(
            node_type="TypeAliasDecl",
            name=m.group(1),
            line=line,
            attributes={"aliased_type": m.group(2).strip()},
        ))

    # Annotation usage
    for m in re.finditer(r"^[ \t]*(@\w+)(?:\([^)]*\))?", source, re.MULTILINE):
        line = source[:m.start()].count("\n") + 1
        root.children.append(ASTNode(
            node_type="AnnotationDecl",
            name=m.group(1),
            line=line,
        ))

    # Class, object, and interface declarations
    cls_pat = re.compile(
        r"(?P<vis>public|private|internal|protected)?\s*"
        r"(?P<abs>abstract\s+)?(?P<open>open\s+)?"
        r"(?P<sealed>sealed\s+)?(?P<data>data\s+)?"
        r"(?P<inner>inner\s+)?(?P<inline>inline\s+|value\s+)?"
        r"(?P<ann>annotation\s+)?(?P<enum>enum\s+)?"
        r"(?P<kind>class|object|interface)\s+(?P<name>\w+)"
        r"(?:<(?P<gen>[^>]+)>)?"
        r"(?:\s*(?::\s*(?P<supers>[^{]+))?)?",
        re.MULTILINE
    )
    for m in cls_pat.finditer(source):
        line = source[:m.start()].count("\n") + 1
        kind = m.group("kind")
        attrs = {}
        if m.group("vis"):
            attrs["visibility"] = m.group("vis")
        if m.group("abs"):
            attrs["abstract"] = True
        if m.group("open"):
            attrs["open"] = True
        if m.group("sealed"):
            attrs["sealed"] = True
        if m.group("data"):
            attrs["data"] = True
        if m.group("inner"):
            attrs["inner"] = True
        if m.group("inline"):
            attrs["inline"] = True
        if m.group("ann"):
            attrs["annotation"] = True
        if m.group("enum"):
            attrs["enum"] = True
        if m.group("gen"):
            attrs["generic_params"] = m.group("gen").strip()
        # Parse superclass and interfaces from supers
        if m.group("supers"):
            supers = [s.strip() for s in m.group("supers").split(",")
                      if s.strip()]
            ifaces = []
            for s in supers:
                clean = re.sub(r"\(.*\)", "", s).strip()
                if not clean:
                    continue
                if "(" in s:
                    attrs["superclass"] = clean
                else:
                    ifaces.append(clean)
            if ifaces:
                attrs["interfaces"] = ifaces

        if kind == "class":
            node_type = "ClassDecl"
        elif kind == "object":
            node_type = "ObjectDecl"
        else:
            node_type = "InterfaceDecl"

        root.children.append(ASTNode(
            node_type=node_type,
            name=m.group("name"),
            line=line,
            attributes=attrs,
        ))

    # Companion object
    for m in re.finditer(r"companion\s+object\s*(\w*)\s*\{", source):
        line = source[:m.start()].count("\n") + 1
        root.children.append(ASTNode(
            node_type="ObjectDecl",
            name=m.group(1) or "Companion",
            line=line,
            attributes={"companion": True},
        ))

    # Constructor declarations
    for m in re.finditer(
        r"(?P<vis>public|private|internal|protected)?\s*"
        r"constructor\s*\((?P<params>[^)]*)\)", source
    ):
        line = source[:m.start()].count("\n") + 1
        params = [p.strip() for p in m.group("params").split(",")
                  if p.strip()]
        attrs = {"param_count": len(params)}
        if m.group("vis"):
            attrs["visibility"] = m.group("vis")
        root.children.append(ASTNode(
            node_type="ConstructorDecl",
            name="constructor",
            line=line,
            attributes=attrs,
        ))

    # Function declarations
    fn_pat = re.compile(
        r"(?P<vis>public|private|internal|protected)?\s*"
        r"(?P<abs>abstract\s+)?(?P<open>open\s+)?"
        r"(?P<suspend>suspend\s+)?(?P<inline>inline\s+)?"
        r"(?P<operator>operator\s+)?(?P<infix>infix\s+)?"
        r"fun\s+(?:(?P<gen><[^>]+>)\s*)?"
        r"(?:(?P<recv>\w+(?:<[^>]+>)?)\.)?"
        r"(?P<name>\w+)\s*\((?P<params>[^)]*)\)"
        r"(?:\s*:\s*(?P<ret>[\w<>., ?]+))?",
        re.MULTILINE
    )
    for m in fn_pat.finditer(source):
        line = source[:m.start()].count("\n") + 1
        params = [p.strip() for p in m.group("params").split(",")
                  if p.strip()]
        attrs = {"param_count": len(params)}
        if m.group("vis"):
            attrs["visibility"] = m.group("vis")
        if m.group("abs"):
            attrs["abstract"] = True
        if m.group("open"):
            attrs["open"] = True
        if m.group("suspend"):
            attrs["suspend"] = True
        if m.group("inline"):
            attrs["inline"] = True
        if m.group("operator"):
            attrs["operator"] = True
        if m.group("infix"):
            attrs["infix"] = True
        if m.group("gen"):
            attrs["generic_params"] = m.group("gen").strip()
        if m.group("recv"):
            attrs["receiver_type"] = m.group("recv")
        if m.group("ret"):
            attrs["return_type"] = m.group("ret").strip()
        root.children.append(ASTNode(
            node_type="FunDecl",
            name=m.group("name"),
            line=line,
            attributes=attrs,
        ))

    # Property declarations (val/var)
    prop_pat = re.compile(
        r"(?P<vis>public|private|internal|protected)?\s*"
        r"(?P<const>const\s+)?(?P<lateinit>lateinit\s+)?"
        r"(?P<kind>val|var)\s+(?P<name>\w+)"
        r"(?:\s*:\s*(?P<type>[\w<>., ?]+))?"
        r"(?:\s*by\s+(?P<delegate>\w+))?"
        r"(?:\s*=\s*(?P<init>[^\n;]+))?",
        re.MULTILINE
    )
    for m in prop_pat.finditer(source):
        line = source[:m.start()].count("\n") + 1
        attrs = {"kind": m.group("kind")}
        if m.group("vis"):
            attrs["visibility"] = m.group("vis")
        if m.group("const"):
            attrs["const"] = True
        if m.group("lateinit"):
            attrs["lateinit"] = True
        if m.group("type"):
            attrs["type"] = m.group("type").strip()
        if m.group("delegate"):
            attrs["delegate"] = m.group("delegate")
        init = m.group("init")
        if init and "lazy" in init:
            attrs["lazy"] = True
        root.children.append(ASTNode(
            node_type="PropertyDecl",
            name=m.group("name"),
            line=line,
            attributes=attrs,
        ))

    return root


def find_kotlin_symbols(source: str) -> list:
    """Extract all symbols from Kotlin source."""
    root = parse_kotlin_source(source)
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
