"""Python-specific AST introspection with deep analysis.

Leverages Python's built-in ast module for full AST access including
type inference, scope analysis, and control flow extraction.
"""
import ast
import sys
import os
from ast_dsl.core import ASTEngine, ASTNode, ASTQuery, ASTResult, Language


class PythonASTAnalyzer:
    """Deep Python AST analysis beyond basic parsing."""

    def __init__(self, engine: ASTEngine = None):
        self.engine = engine or ASTEngine()

    def analyze_scopes(self, source: str) -> dict:
        """Analyze variable scopes in Python source."""
        tree = ast.parse(source)
        scopes = {"global": {"reads": set(), "writes": set()}}

        class ScopeVisitor(ast.NodeVisitor):
            def __init__(self):
                self.current_scope = "global"

            def visit_FunctionDef(self, node):
                old = self.current_scope
                self.current_scope = node.name
                scopes[node.name] = {"reads": set(), "writes": set()}
                self.generic_visit(node)
                self.current_scope = old

            visit_AsyncFunctionDef = visit_FunctionDef

            def visit_Name(self, node):
                scope = scopes[self.current_scope]
                if isinstance(node.ctx, ast.Store):
                    scope["writes"].add(node.id)
                elif isinstance(node.ctx, ast.Load):
                    scope["reads"].add(node.id)
                self.generic_visit(node)

        ScopeVisitor().visit(tree)
        return {k: {"reads": sorted(v["reads"]), "writes": sorted(v["writes"])}
                for k, v in scopes.items()}

    def extract_control_flow(self, source: str) -> list:
        """Extract control flow graph edges."""
        tree = ast.parse(source)
        edges = []

        class CFGVisitor(ast.NodeVisitor):
            def __init__(self):
                self.current_func = "<module>"

            def visit_FunctionDef(self, node):
                old = self.current_func
                self.current_func = node.name
                self.generic_visit(node)
                self.current_func = old

            visit_AsyncFunctionDef = visit_FunctionDef

            def visit_If(self, node):
                edges.append({
                    "func": self.current_func,
                    "type": "branch",
                    "line": node.lineno,
                    "true_line": node.body[0].lineno if node.body else None,
                    "false_line": (node.orelse[0].lineno
                                  if node.orelse else None),
                })
                self.generic_visit(node)

            def visit_For(self, node):
                edges.append({
                    "func": self.current_func,
                    "type": "loop",
                    "line": node.lineno,
                    "body_line": node.body[0].lineno if node.body else None,
                })
                self.generic_visit(node)

            def visit_While(self, node):
                edges.append({
                    "func": self.current_func,
                    "type": "loop",
                    "line": node.lineno,
                    "body_line": node.body[0].lineno if node.body else None,
                })
                self.generic_visit(node)

            def visit_Return(self, node):
                edges.append({
                    "func": self.current_func,
                    "type": "return",
                    "line": node.lineno,
                })
                self.generic_visit(node)

            def visit_Raise(self, node):
                edges.append({
                    "func": self.current_func,
                    "type": "raise",
                    "line": node.lineno,
                })
                self.generic_visit(node)

            def visit_Try(self, node):
                edges.append({
                    "func": self.current_func,
                    "type": "try",
                    "line": node.lineno,
                    "handlers": len(node.handlers),
                })
                self.generic_visit(node)

        CFGVisitor().visit(tree)
        return edges

    def find_dead_code(self, source: str) -> list:
        """Find potentially dead code (unreachable after return/raise)."""
        tree = ast.parse(source)
        dead = []

        class DeadCodeVisitor(ast.NodeVisitor):
            def _check_body(self, body):
                for i, stmt in enumerate(body):
                    if isinstance(stmt, (ast.Return, ast.Raise)):
                        remaining = body[i + 1:]
                        for r in remaining:
                            dead.append({
                                "line": r.lineno,
                                "type": type(r).__name__,
                                "after": type(stmt).__name__,
                            })
                        break

            def visit_FunctionDef(self, node):
                self._check_body(node.body)
                self.generic_visit(node)

            visit_AsyncFunctionDef = visit_FunctionDef

            def visit_If(self, node):
                self._check_body(node.body)
                self._check_body(node.orelse)
                self.generic_visit(node)

        DeadCodeVisitor().visit(tree)
        return dead

    def generate_test_stubs(self, source: str, module_name: str = "mod") -> str:
        """Generate test stubs for all functions in source."""
        tree = ast.parse(source)
        stubs = [f'"""Auto-generated test stubs for {module_name}."""']
        stubs.append("import unittest")
        stubs.append(f"from {module_name} import *\n")

        class StubGen(ast.NodeVisitor):
            def __init__(self):
                self.current_class = None

            def visit_ClassDef(self, node):
                old = self.current_class
                self.current_class = node.name
                stubs.append(f"\nclass Test{node.name}(unittest.TestCase):")
                self.generic_visit(node)
                self.current_class = old

            def visit_FunctionDef(self, node):
                if node.name.startswith("_") and node.name != "__init__":
                    return
                args = [a.arg for a in node.args.args if a.arg != "self"]
                if self.current_class:
                    test_name = f"test_{node.name}"
                    stubs.append(f"    def {test_name}(self):")
                    stubs.append(f"        # TODO: test {node.name}"
                                f"({', '.join(args)})")
                    stubs.append(f"        pass\n")
                else:
                    stubs.append(f"\nclass TestModule(unittest.TestCase):")
                    stubs.append(f"    def test_{node.name}(self):")
                    stubs.append(f"        # TODO: test {node.name}"
                                f"({', '.join(args)})")
                    stubs.append(f"        pass\n")

            visit_AsyncFunctionDef = visit_FunctionDef

        StubGen().visit(tree)
        stubs.append('\nif __name__ == "__main__":')
        stubs.append("    unittest.main()")
        return "\n".join(stubs)
