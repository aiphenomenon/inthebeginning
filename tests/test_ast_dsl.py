"""Tests for the AST DSL engine and reactive protocol."""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ast_dsl.core import (
    ASTEngine, ASTNode, ASTQuery, ASTResult, PerformanceMetrics, Language,
)
from ast_dsl.reactive import (
    ReactiveProtocol, AgentState, CueSignal, CueType,
)
from ast_dsl.python_ast import PythonASTAnalyzer


SAMPLE_PYTHON = '''
import os
import math

class Calculator:
    """A simple calculator."""
    def __init__(self):
        self.history = []

    def add(self, a, b):
        result = a + b
        self.history.append(result)
        return result

    def divide(self, a, b):
        if b == 0:
            raise ValueError("Division by zero")
        return a / b

def helper(x):
    for i in range(x):
        if i % 2 == 0:
            print(i)
    return x

def dead_code_example():
    return 42
    x = 1  # Dead code

class SubCalc(Calculator):
    def multiply(self, a, b):
        return a * b
'''


class TestASTNode(unittest.TestCase):
    def test_basic_creation(self):
        node = ASTNode(node_type="Function", name="test", line=1)
        self.assertEqual(node.node_type, "Function")
        self.assertEqual(node.name, "test")
        self.assertEqual(node.line, 1)
        self.assertEqual(node.children, [])
        self.assertEqual(node.attributes, {})

    def test_to_dict(self):
        node = ASTNode(
            node_type="Class", name="Foo", line=10, col=0,
            end_line=20, end_col=5,
            attributes={"bases": ["Bar"]},
            source_text="class Foo(Bar):",
        )
        d = node.to_dict()
        self.assertEqual(d["type"], "Class")
        self.assertEqual(d["name"], "Foo")
        self.assertEqual(d["line"], 10)
        self.assertEqual(d["end_line"], 20)
        self.assertIn("attrs", d)
        self.assertIn("src", d)

    def test_to_dict_no_optional_fields(self):
        node = ASTNode(node_type="Expr", line=1, col=0)
        d = node.to_dict()
        self.assertNotIn("end_line", d)
        self.assertNotIn("attrs", d)
        self.assertNotIn("src", d)
        self.assertNotIn("children", d)

    def test_to_compact(self):
        child = ASTNode(node_type="Arg", name="x", line=5)
        node = ASTNode(
            node_type="Function", name="foo", line=3,
            attributes={"async": True},
            children=[child],
        )
        compact = node.to_compact()
        self.assertIn("Function:foo@3", compact)
        self.assertIn("async=True", compact)
        self.assertIn("Arg:x@5", compact)

    def test_walk(self):
        grandchild = ASTNode(node_type="Leaf", name="l")
        child = ASTNode(node_type="Inner", name="i", children=[grandchild])
        root = ASTNode(node_type="Root", name="r", children=[child])
        nodes = list(root.walk())
        self.assertEqual(len(nodes), 3)
        self.assertEqual(nodes[0].name, "r")
        self.assertEqual(nodes[1].name, "i")
        self.assertEqual(nodes[2].name, "l")

    def test_find(self):
        c1 = ASTNode(node_type="Func", name="a")
        c2 = ASTNode(node_type="Class", name="B")
        c3 = ASTNode(node_type="Func", name="c")
        root = ASTNode(node_type="Module", children=[c1, c2, c3])

        funcs = root.find(node_type="Func")
        self.assertEqual(len(funcs), 2)

        named = root.find(name="B")
        self.assertEqual(len(named), 1)
        self.assertEqual(named[0].node_type, "Class")

    def test_find_both_criteria(self):
        c1 = ASTNode(node_type="Func", name="a")
        c2 = ASTNode(node_type="Func", name="b")
        root = ASTNode(node_type="Mod", children=[c1, c2])
        found = root.find(node_type="Func", name="a")
        self.assertEqual(len(found), 1)


class TestASTQuery(unittest.TestCase):
    def test_creation(self):
        q = ASTQuery(action="parse", target="test.py")
        self.assertEqual(q.action, "parse")
        self.assertEqual(q.target, "test.py")
        self.assertEqual(q.language, "python")
        self.assertEqual(q.depth, -1)

    def test_to_dict(self):
        q = ASTQuery(action="find", target="t.py",
                     filters={"name": "foo"})
        d = q.to_dict()
        self.assertEqual(d["action"], "find")
        self.assertIn("filters", d)

    def test_from_dict(self):
        d = {"action": "parse", "target": "x.py", "language": "python",
             "filters": {}, "depth": -1}
        q = ASTQuery.from_dict(d)
        self.assertEqual(q.action, "parse")
        self.assertEqual(q.target, "x.py")

    def test_from_dict_extra_keys(self):
        d = {"action": "parse", "target": "x.py", "extra_key": "ignored"}
        q = ASTQuery.from_dict(d)
        self.assertEqual(q.action, "parse")


class TestPerformanceMetrics(unittest.TestCase):
    def test_defaults(self):
        m = PerformanceMetrics()
        self.assertEqual(m.wall_time_ms, 0.0)
        self.assertEqual(m.peak_memory_kb, 0)

    def test_to_dict(self):
        m = PerformanceMetrics(wall_time_ms=10.5, peak_memory_kb=100)
        d = m.to_dict()
        self.assertEqual(d["wall_time_ms"], 10.5)
        self.assertEqual(d["peak_memory_kb"], 100)


class TestASTResult(unittest.TestCase):
    def test_success(self):
        r = ASTResult(success=True, data="test")
        self.assertTrue(r.success)
        self.assertEqual(r.data, "test")

    def test_to_dict_with_node(self):
        node = ASTNode(node_type="X", name="y")
        r = ASTResult(success=True, data=node, ast_node_count=1,
                      source_hash="abc")
        d = r.to_dict()
        self.assertTrue(d["success"])
        self.assertIn("data", d)
        self.assertEqual(d["data"]["type"], "X")

    def test_to_dict_with_list(self):
        nodes = [ASTNode(node_type="A"), ASTNode(node_type="B")]
        r = ASTResult(success=True, data=nodes)
        d = r.to_dict()
        self.assertEqual(len(d["data"]), 2)

    def test_to_dict_error(self):
        r = ASTResult(success=False, error="fail")
        d = r.to_dict()
        self.assertFalse(d["success"])
        self.assertEqual(d["error"], "fail")

    def test_to_compact_with_node(self):
        node = ASTNode(node_type="F", name="x")
        r = ASTResult(
            success=True, data=node, ast_node_count=5,
            metrics=PerformanceMetrics(peak_memory_kb=10, cpu_user_ms=1.5),
        )
        compact = r.to_compact()
        self.assertIn("ok=True", compact)
        self.assertIn("nodes=5", compact)
        self.assertIn("mem=10kb", compact)

    def test_to_compact_with_list(self):
        nodes = [ASTNode(node_type="A", name="a")]
        r = ASTResult(success=True, data=nodes)
        compact = r.to_compact()
        self.assertIn("results=", compact)

    def test_to_compact_error(self):
        r = ASTResult(success=False, error="bad")
        compact = r.to_compact()
        self.assertIn("err=bad", compact)

    def test_to_dict_with_non_node_data(self):
        r = ASTResult(success=True, data={"key": "val"})
        d = r.to_dict()
        self.assertEqual(d["data"], {"key": "val"})

    def test_to_compact_with_empty_list(self):
        r = ASTResult(success=True, data=[])
        compact = r.to_compact()
        self.assertIn("ok=True", compact)

    def test_to_dict_with_mixed_list(self):
        data = [ASTNode(node_type="A"), "string_item"]
        r = ASTResult(success=True, data=data)
        d = r.to_dict()
        self.assertEqual(len(d["data"]), 2)


class TestASTEngine(unittest.TestCase):
    def setUp(self):
        self.engine = ASTEngine()
        self.tmpfile = tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        )
        self.tmpfile.write(SAMPLE_PYTHON)
        self.tmpfile.close()

    def tearDown(self):
        os.unlink(self.tmpfile.name)

    def test_parse_file(self):
        result = self.engine.parse_file(self.tmpfile.name)
        self.assertTrue(result.success)
        self.assertGreater(result.ast_node_count, 0)
        self.assertGreater(result.metrics.wall_time_ms, 0)

    def test_parse_string(self):
        q = ASTQuery(action="parse", target="x = 1", language="python")
        result = self.engine.execute(q)
        self.assertTrue(result.success)

    def test_find_symbols(self):
        result = self.engine.find_symbols(self.tmpfile.name)
        self.assertTrue(result.success)
        symbols = result.data
        self.assertIsInstance(symbols, list)
        names = [s["name"] for s in symbols]
        self.assertIn("Calculator", names)
        self.assertIn("add", names)
        self.assertIn("helper", names)

    def test_get_dependencies(self):
        result = self.engine.get_dependencies(self.tmpfile.name)
        self.assertTrue(result.success)
        deps = result.data
        modules = [d["module"] for d in deps]
        self.assertIn("os", modules)
        self.assertIn("math", modules)

    def test_code_metrics(self):
        q = ASTQuery(action="metrics", target=self.tmpfile.name)
        result = self.engine.execute(q)
        self.assertTrue(result.success)
        self.assertGreater(result.data["total_nodes"], 0)
        self.assertGreater(result.data["functions"], 0)
        self.assertGreater(result.data["classes"], 0)

    def test_find_with_filters(self):
        q = ASTQuery(
            action="find", target=self.tmpfile.name,
            filters={"node_type": "FunctionDef"},
        )
        result = self.engine.execute(q)
        self.assertTrue(result.success)

    def test_callers(self):
        q = ASTQuery(
            action="callers", target=self.tmpfile.name,
            filters={"name": "append"},
        )
        result = self.engine.execute(q)
        self.assertTrue(result.success)

    def test_transform_rename(self):
        q = ASTQuery(
            action="transform", target=self.tmpfile.name,
            filters={"transform": "rename", "old_name": "add",
                     "new_name": "sum_values"},
        )
        result = self.engine.execute(q)
        self.assertTrue(result.success)

    def test_coverage_map(self):
        q = ASTQuery(action="coverage_map", target=self.tmpfile.name)
        result = self.engine.execute(q)
        self.assertTrue(result.success)
        self.assertIsInstance(result.data, list)
        func_names = [p["function"] for p in result.data]
        self.assertIn("add", func_names)

    def test_unknown_action(self):
        q = ASTQuery(action="nonexistent", target=self.tmpfile.name)
        result = self.engine.execute(q)
        self.assertFalse(result.success)
        self.assertIn("Unknown action", result.error)

    def test_unknown_language(self):
        q = ASTQuery(action="parse", target=self.tmpfile.name,
                     language="brainfuck")
        result = self.engine.execute(q)
        self.assertFalse(result.success)

    def test_parse_caching(self):
        tree1 = self.engine._get_python_ast(self.tmpfile.name)
        tree2 = self.engine._get_python_ast(self.tmpfile.name)
        self.assertIs(tree1, tree2)

    def test_source_hash(self):
        result = self.engine.parse_file(self.tmpfile.name)
        self.assertTrue(len(result.source_hash) > 0)

    def test_token_approximation(self):
        result = self.engine.parse_file(self.tmpfile.name)
        self.assertGreater(result.metrics.prompt_tokens_approx, 0)
        self.assertGreater(result.metrics.result_tokens_approx, 0)


class TestPythonASTAnalyzer(unittest.TestCase):
    def test_analyze_scopes(self):
        analyzer = PythonASTAnalyzer()
        scopes = analyzer.analyze_scopes(SAMPLE_PYTHON)
        self.assertIn("global", scopes)
        self.assertIn("add", scopes)
        self.assertIn("result", scopes["add"]["writes"])

    def test_extract_control_flow(self):
        analyzer = PythonASTAnalyzer()
        edges = analyzer.extract_control_flow(SAMPLE_PYTHON)
        self.assertGreater(len(edges), 0)
        types = [e["type"] for e in edges]
        self.assertIn("branch", types)
        self.assertIn("loop", types)

    def test_find_dead_code(self):
        analyzer = PythonASTAnalyzer()
        dead = analyzer.find_dead_code(SAMPLE_PYTHON)
        self.assertGreater(len(dead), 0)

    def test_generate_test_stubs(self):
        analyzer = PythonASTAnalyzer()
        stubs = analyzer.generate_test_stubs(SAMPLE_PYTHON, "calc")
        self.assertIn("import unittest", stubs)
        self.assertIn("TestCalculator", stubs)
        self.assertIn("test_add", stubs)

    def test_control_flow_return(self):
        src = "def f():\n    return 1\n"
        analyzer = PythonASTAnalyzer()
        edges = analyzer.extract_control_flow(src)
        types = [e["type"] for e in edges]
        self.assertIn("return", types)

    def test_control_flow_raise(self):
        src = "def f():\n    raise ValueError()\n"
        analyzer = PythonASTAnalyzer()
        edges = analyzer.extract_control_flow(src)
        types = [e["type"] for e in edges]
        self.assertIn("raise", types)

    def test_control_flow_while(self):
        src = "def f():\n    while True:\n        pass\n"
        analyzer = PythonASTAnalyzer()
        edges = analyzer.extract_control_flow(src)
        types = [e["type"] for e in edges]
        self.assertIn("loop", types)

    def test_control_flow_try(self):
        src = "def f():\n    try:\n        pass\n    except:\n        pass\n"
        analyzer = PythonASTAnalyzer()
        edges = analyzer.extract_control_flow(src)
        types = [e["type"] for e in edges]
        self.assertIn("try", types)

    def test_dead_code_in_if(self):
        src = "def f():\n    if True:\n        return 1\n        x = 2\n    else:\n        raise ValueError()\n        y = 3\n"
        analyzer = PythonASTAnalyzer()
        dead = analyzer.find_dead_code(src)
        self.assertGreaterEqual(len(dead), 2)


class TestReactiveProtocol(unittest.TestCase):
    def setUp(self):
        self.protocol = ReactiveProtocol(session_id="test-session")
        self.tmpfile = tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        )
        self.tmpfile.write(SAMPLE_PYTHON)
        self.tmpfile.close()

    def tearDown(self):
        os.unlink(self.tmpfile.name)

    def test_query_parse(self):
        result = self.protocol.run_query(
            "parse", self.tmpfile.name
        )
        self.assertEqual(result.cue_type, CueType.RESULT)
        self.assertIsInstance(result.payload, dict)
        self.assertTrue(result.payload.get("success"))

    def test_query_symbols(self):
        result = self.protocol.run_query(
            "symbols", self.tmpfile.name
        )
        self.assertTrue(result.payload.get("success"))
        self.assertGreater(len(self.protocol.state.discovered_symbols), 0)

    def test_query_dependencies(self):
        result = self.protocol.run_query(
            "dependencies", self.tmpfile.name
        )
        self.assertTrue(result.payload.get("success"))
        self.assertGreater(len(self.protocol.state.discovered_deps), 0)

    def test_refine_cue(self):
        cue = CueSignal(
            cue_type=CueType.REFINE,
            payload=ASTQuery(
                action="find", target=self.tmpfile.name,
                filters={"node_type": "ClassDef"},
            ).to_dict(),
            sequence_id=10,
        )
        result = self.protocol.process_cue(cue)
        self.assertEqual(result.cue_type, CueType.RESULT)

    def test_transform_cue(self):
        cue = CueSignal(
            cue_type=CueType.TRANSFORM,
            payload=ASTQuery(
                action="transform", target=self.tmpfile.name,
                filters={"transform": "rename", "old_name": "add",
                         "new_name": "sum"},
            ).to_dict(),
            sequence_id=20,
        )
        result = self.protocol.process_cue(cue)
        self.assertEqual(result.cue_type, CueType.RESULT)
        self.assertGreater(len(self.protocol.state.pending_transforms), 0)

    def test_synthesize_cue(self):
        self.protocol.run_query("symbols", self.tmpfile.name)
        cue = CueSignal(
            cue_type=CueType.SYNTHESIZE,
            sequence_id=30,
        )
        result = self.protocol.process_cue(cue)
        self.assertIn("state", result.payload)
        self.assertIn("all_symbols", result.payload)

    def test_complete_cue(self):
        cue = CueSignal(cue_type=CueType.COMPLETE, sequence_id=40)
        result = self.protocol.process_cue(cue)
        self.assertEqual(result.cue_type, CueType.COMPLETE)

    def test_invalid_query_payload(self):
        cue = CueSignal(
            cue_type=CueType.QUERY,
            payload="not a dict",
            sequence_id=50,
        )
        result = self.protocol.process_cue(cue)
        self.assertIn("error", result.payload)

    def test_invalid_transform_payload(self):
        cue = CueSignal(
            cue_type=CueType.TRANSFORM,
            payload="not a dict",
            sequence_id=60,
        )
        result = self.protocol.process_cue(cue)
        self.assertIn("error", result.payload)

    def test_session_log(self):
        self.protocol.run_query("symbols", self.tmpfile.name)
        log = self.protocol.get_session_log()
        parsed = json.loads(log)
        self.assertIn("session", parsed)
        self.assertIn("history", parsed)

    def test_agent_state(self):
        state = self.protocol.state
        self.assertEqual(state.session_id, "test-session")
        d = state.to_dict()
        self.assertIn("session_id", d)
        compact = state.to_compact()
        self.assertIn("test-ses", compact)

    def test_create_query_cue(self):
        cue = self.protocol.create_query_cue("parse", "test.py")
        self.assertEqual(cue.cue_type, CueType.QUERY)

    def test_cue_signal_serialization(self):
        cue = CueSignal(
            cue_type=CueType.QUERY,
            payload={"action": "parse"},
            sequence_id=1,
            parent_id=0,
        )
        d = cue.to_dict()
        self.assertEqual(d["cue_type"], "query")
        compact = cue.to_compact()
        self.assertIn("cue:query#1", compact)

        # Round-trip
        restored = CueSignal.from_dict(d)
        self.assertEqual(restored.cue_type, CueType.QUERY)

    def test_cue_compact_long_payload(self):
        cue = CueSignal(
            cue_type=CueType.RESULT,
            payload={"x": "y" * 600},
            sequence_id=1,
        )
        compact = cue.to_compact()
        self.assertIn("...", compact)

    def test_cue_compact_string_payload(self):
        cue = CueSignal(
            cue_type=CueType.RESULT,
            payload="hello world",
            sequence_id=1,
        )
        compact = cue.to_compact()
        self.assertIn("hello", compact)

    def test_cue_with_parent(self):
        cue = CueSignal(
            cue_type=CueType.REFINE,
            sequence_id=5,
            parent_id=3,
        )
        compact = cue.to_compact()
        self.assertIn("<-#3", compact)

    def test_query_with_ast_query_payload(self):
        query = ASTQuery(action="symbols", target=self.tmpfile.name)
        cue = CueSignal(
            cue_type=CueType.QUERY,
            payload=query,
            sequence_id=70,
        )
        result = self.protocol.process_cue(cue)
        self.assertTrue(result.payload.get("success"))


class TestLanguageEnum(unittest.TestCase):
    def test_all_languages(self):
        langs = list(Language)
        self.assertGreater(len(langs), 5)
        self.assertIn(Language.PYTHON, langs)
        self.assertIn(Language.JAVASCRIPT, langs)
        self.assertIn(Language.GO, langs)


if __name__ == "__main__":
    unittest.main()
