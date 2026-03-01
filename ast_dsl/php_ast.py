"""PHP AST introspection using php -l and token_get_all.

Provides PHP AST analysis by invoking PHP's tokenizer or using
regex-based lightweight parsing for symbol extraction.
"""
import json
import os
import re
import subprocess
import tempfile
from ast_dsl.core import ASTNode


def parse_php_source(source: str,
                     filename: str = "<string>") -> ASTNode:
    """Parse PHP source into universal AST using regex parser."""
    root = ASTNode(node_type="PHPFile", name=filename)

    # Namespace declarations
    for m in re.finditer(r"namespace\s+([\w\\]+)\s*;", source):
        line = source[:m.start()].count("\n") + 1
        root.children.append(ASTNode(
            node_type="NamespaceDecl",
            name=m.group(1),
            line=line,
        ))

    # Use declarations
    for m in re.finditer(r"use\s+([\w\\]+)(?:\s+as\s+(\w+))?\s*;",
                         source):
        line = source[:m.start()].count("\n") + 1
        attrs = {}
        if m.group(2):
            attrs["alias"] = m.group(2)
        root.children.append(ASTNode(
            node_type="UseDecl",
            name=m.group(1),
            line=line,
            attributes=attrs,
        ))

    # Class declarations
    class_pat = re.compile(
        r"(abstract\s+|final\s+)?(class|interface|trait|enum)\s+(\w+)"
        r"(?:\s+extends\s+(\w+))?"
        r"(?:\s+implements\s+([\w,\s\\]+))?"
        r"\s*\{",
        re.MULTILINE
    )
    for m in class_pat.finditer(source):
        line = source[:m.start()].count("\n") + 1
        attrs = {}
        if m.group(1):
            attrs["modifier"] = m.group(1).strip()
        if m.group(4):
            attrs["extends"] = m.group(4)
        if m.group(5):
            attrs["implements"] = [
                s.strip() for s in m.group(5).split(",")
            ]
        root.children.append(ASTNode(
            node_type=m.group(2).capitalize() + "Decl",
            name=m.group(3),
            line=line,
            attributes=attrs,
        ))

    # Function declarations
    fn_pat = re.compile(
        r"(public|private|protected|static|\s)*"
        r"function\s+(\w+)\s*\(([^)]*)\)"
        r"(?:\s*:\s*([\w?|\\]+))?\s*\{",
        re.MULTILINE
    )
    for m in fn_pat.finditer(source):
        line = source[:m.start()].count("\n") + 1
        params = [p.strip() for p in m.group(3).split(",")
                  if p.strip()]
        attrs = {"params": len(params)}
        if m.group(4):
            attrs["return_type"] = m.group(4)
        root.children.append(ASTNode(
            node_type="FunctionDecl",
            name=m.group(2),
            line=line,
            attributes=attrs,
        ))

    return root


def parse_php_with_tokenizer(filepath: str) -> ASTNode:
    """Use PHP's token_get_all for deeper analysis."""
    php_code = '''<?php
$source = file_get_contents($argv[1]);
$tokens = token_get_all($source);
$result = [];
foreach ($tokens as $token) {
    if (is_array($token)) {
        $result[] = [
            "type" => token_name($token[0]),
            "value" => $token[1],
            "line" => $token[2]
        ];
    }
}
echo json_encode($result);
'''
    try:
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".php",
                                          delete=False)
        tmp.write(php_code)
        tmp.close()

        result = subprocess.run(
            ["php", tmp.name, filepath],
            capture_output=True, text=True, timeout=30
        )
        os.unlink(tmp.name)

        if result.returncode == 0:
            tokens = json.loads(result.stdout)
            root = ASTNode(node_type="PHPFile", name=filepath)

            # Build AST from tokens
            i = 0
            while i < len(tokens):
                tok = tokens[i]
                if tok["type"] in ("T_CLASS", "T_INTERFACE", "T_TRAIT"):
                    if i + 2 < len(tokens):
                        root.children.append(ASTNode(
                            node_type=tok["type"].replace("T_", "") + "Decl",
                            name=tokens[i + 2]["value"],
                            line=tok["line"],
                        ))
                elif tok["type"] == "T_FUNCTION":
                    if i + 2 < len(tokens):
                        root.children.append(ASTNode(
                            node_type="FunctionDecl",
                            name=tokens[i + 2]["value"],
                            line=tok["line"],
                        ))
                i += 1

            return root

    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        pass

    with open(filepath) as f:
        return parse_php_source(f.read(), filepath)


def find_php_symbols(source: str) -> list:
    """Extract all symbols from PHP source."""
    root = parse_php_source(source)
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
