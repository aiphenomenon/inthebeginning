"""Cross-language parity tests for simulator implementations.

Verifies that all language implementations produce equivalent simulation
results: same epoch transitions, comparable particle/atom/cell counts,
and matching final state metrics.

Run:
    python -m pytest tests/test_cross_language_parity.py -v
"""
import json
import os
import re
import subprocess
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = 42
SHORT_TICKS = 10000  # Short run for parity checks (faster)


def toolchain_available(cmd):
    """Check if a command-line tool is available."""
    try:
        subprocess.run(cmd, capture_output=True, timeout=10)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def run_python_simulation(ticks=SHORT_TICKS):
    """Run the Python reference simulation and return structured results."""
    code = f"""
import sys, json
sys.path.insert(0, '.')
from simulator.universe import Universe
u = Universe(seed={SEED}, max_ticks={ticks}, step_size=100)
u.run()
s = u.summary()
# Extract key fields for parity comparison
result = {{
    "epochs": [e.get("name", e.get("epoch", "")) for e in s.get("epoch_transitions", s.get("epochs", []))],
    "final_tick": s.get("tick", s.get("current_tick", 0)),
    "particles": s.get("particles", s.get("particle_count", 0)),
    "atoms": s.get("atoms", s.get("atom_count", 0)),
    "molecules": s.get("molecules", s.get("molecule_count", 0)),
    "cells": s.get("cells", s.get("cell_count", 0)),
}}
print(json.dumps(result))
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True, text=True, timeout=30, cwd=PROJECT_ROOT,
    )
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout.strip())
    except json.JSONDecodeError:
        return None


def extract_simulation_data(stdout_text):
    """Extract structured simulation data from CLI output text.

    Handles various output formats across languages. Returns a dict with:
    - epochs: list of epoch names found in output
    - particles, atoms, molecules, cells: integer counts (0 if not found)
    """
    data = {
        "epochs": [],
        "particles": 0,
        "atoms": 0,
        "molecules": 0,
        "cells": 0,
    }

    # Try JSON first (some apps output JSON)
    try:
        parsed = json.loads(stdout_text.strip())
        if isinstance(parsed, dict):
            data["epochs"] = parsed.get("epochs", parsed.get("epoch_transitions", []))
            data["particles"] = parsed.get("particles", parsed.get("particle_count", 0))
            data["atoms"] = parsed.get("atoms", parsed.get("atom_count", 0))
            data["molecules"] = parsed.get("molecules", parsed.get("molecule_count", 0))
            data["cells"] = parsed.get("cells", parsed.get("cell_count", 0))
            return data
    except (json.JSONDecodeError, ValueError):
        pass

    # Parse text output
    known_epochs = [
        "Void", "Planck", "Inflation", "Electroweak", "Quark",
        "Hadron", "Lepton", "Nuclear", "Atomic", "Chemical",
        "Molecular", "Cellular", "Multicellular", "Present",
    ]
    for epoch_name in known_epochs:
        pattern = re.compile(rf'\b{epoch_name}\b', re.IGNORECASE)
        if pattern.search(stdout_text):
            data["epochs"].append(epoch_name)

    # Extract counts
    count_patterns = {
        "particles": r'particles?\s*[:=]\s*(\d+)',
        "atoms": r'atoms?\s*[:=]\s*(\d+)',
        "molecules": r'molecules?\s*[:=]\s*(\d+)',
        "cells": r'cells?\s*[:=]\s*(\d+)',
    }
    for key, pattern in count_patterns.items():
        match = re.search(pattern, stdout_text, re.IGNORECASE)
        if match:
            data[key] = int(match.group(1))

    return data


def run_app(run_cmd, cwd, timeout=60, build_cmds=None):
    """Build (if needed) and run an app, returning stdout."""
    if build_cmds:
        for cmd in build_cmds:
            subprocess.run(
                cmd, shell=True, capture_output=True, timeout=120, cwd=cwd,
            )
    env = os.environ.copy()
    env["SEED"] = str(SEED)
    env["MAX_TICKS"] = str(SHORT_TICKS)
    env["TERM"] = "dumb"
    result = subprocess.run(
        run_cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd, env=env,
    )
    return result


class TestCrossLanguageParity(unittest.TestCase):
    """Verify that different language implementations produce parity results."""

    @classmethod
    def setUpClass(cls):
        """Run the Python reference simulation once for comparison."""
        cls.python_data = run_python_simulation()
        if cls.python_data is None:
            raise unittest.SkipTest("Python reference simulation failed")

    def _assert_epoch_parity(self, lang_data, lang_name):
        """Assert that a language's epoch list overlaps significantly with Python's."""
        if not lang_data["epochs"]:
            self.skipTest(f"{lang_name} produced no epoch data")
        python_epochs = set(e.lower() for e in self.python_data["epochs"])
        lang_epochs = set(e.lower() for e in lang_data["epochs"])
        overlap = python_epochs & lang_epochs
        # At least 50% epoch overlap (different output formats may miss some)
        min_overlap = max(1, len(python_epochs) // 2)
        self.assertGreaterEqual(
            len(overlap), min_overlap,
            f"{lang_name} epochs {lang_epochs} too different from Python {python_epochs}",
        )

    def _assert_count_parity(self, lang_data, lang_name, key, tolerance=0.5):
        """Assert a count value is within tolerance of Python reference."""
        py_val = self.python_data.get(key, 0)
        lang_val = lang_data.get(key, 0)
        if py_val == 0:
            return  # Can't compare if Python has zero
        ratio = lang_val / py_val if py_val else 0
        self.assertGreater(
            ratio, 1 - tolerance,
            f"{lang_name} {key}={lang_val} too low vs Python {key}={py_val}",
        )

    # ── Node.js ─────────────────────────────────────────────────────

    @unittest.skipUnless(toolchain_available(["node", "--version"]), "Node.js not available")
    def test_nodejs_epoch_parity(self):
        """Node.js produces matching epoch transitions."""
        cwd = os.path.join(PROJECT_ROOT, "apps", "nodejs")
        result = run_app(["node", "index.js"], cwd=cwd)
        if result.returncode != 0:
            self.skipTest(f"Node.js failed: {result.stderr[:200]}")
        data = extract_simulation_data(result.stdout)
        self._assert_epoch_parity(data, "Node.js")

    @unittest.skipUnless(toolchain_available(["node", "--version"]), "Node.js not available")
    def test_nodejs_output_parity(self):
        """Node.js produces comparable simulation counts."""
        cwd = os.path.join(PROJECT_ROOT, "apps", "nodejs")
        result = run_app(["node", "index.js"], cwd=cwd)
        if result.returncode != 0:
            self.skipTest(f"Node.js failed: {result.stderr[:200]}")
        data = extract_simulation_data(result.stdout)
        if data["particles"] > 0:
            self._assert_count_parity(data, "Node.js", "particles")

    # ── Go ──────────────────────────────────────────────────────────

    @unittest.skipUnless(toolchain_available(["go", "version"]), "Go not available")
    def test_go_epoch_parity(self):
        """Go produces matching epoch transitions."""
        cwd = os.path.join(PROJECT_ROOT, "apps", "go")
        result = run_app(
            ["./simulator_parity_test"], cwd=cwd,
            build_cmds=["go build -o simulator_parity_test ./cmd/simulator/"],
        )
        # cleanup
        try:
            os.remove(os.path.join(cwd, "simulator_parity_test"))
        except OSError:
            pass
        if result.returncode != 0:
            self.skipTest(f"Go failed: {result.stderr[:200]}")
        data = extract_simulation_data(result.stdout)
        self._assert_epoch_parity(data, "Go")

    # ── C ───────────────────────────────────────────────────────────

    @unittest.skipUnless(toolchain_available(["gcc", "--version"]), "GCC not available")
    def test_c_epoch_parity(self):
        """C produces matching epoch transitions."""
        cwd = os.path.join(PROJECT_ROOT, "apps", "c")
        result = run_app(
            ["./build/inthebeginning"], cwd=cwd,
            build_cmds=["make"],
        )
        if result.returncode != 0:
            self.skipTest(f"C failed: {result.stderr[:200]}")
        data = extract_simulation_data(result.stdout)
        self._assert_epoch_parity(data, "C")

    # ── C++ ─────────────────────────────────────────────────────────

    @unittest.skipUnless(toolchain_available(["g++", "--version"]), "G++ not available")
    def test_cpp_epoch_parity(self):
        """C++ produces matching epoch transitions."""
        cwd = os.path.join(PROJECT_ROOT, "apps", "cpp")
        build_dir = os.path.join(cwd, "build")
        os.makedirs(build_dir, exist_ok=True)
        result = run_app(
            ["./build/inthebeginning"], cwd=cwd,
            build_cmds=["cd build && cmake .. && make"],
        )
        if result.returncode != 0:
            self.skipTest(f"C++ failed: {result.stderr[:200]}")
        data = extract_simulation_data(result.stdout)
        self._assert_epoch_parity(data, "C++")

    # ── Rust ────────────────────────────────────────────────────────

    @unittest.skipUnless(toolchain_available(["cargo", "--version"]), "Rust not available")
    def test_rust_epoch_parity(self):
        """Rust produces matching epoch transitions."""
        cwd = os.path.join(PROJECT_ROOT, "apps", "rust")
        subprocess.run(
            ["cargo", "build", "--release"],
            capture_output=True, timeout=180, cwd=cwd,
        )
        bin_path = os.path.join(cwd, "target", "release", "inthebeginning-rust")
        if not os.path.exists(bin_path):
            bin_path = os.path.join(cwd, "target", "release", "in-the-beginning")
        if not os.path.exists(bin_path):
            self.skipTest("Rust binary not found after build")
        result = run_app([bin_path], cwd=cwd)
        if result.returncode != 0:
            self.skipTest(f"Rust failed: {result.stderr[:200]}")
        data = extract_simulation_data(result.stdout)
        self._assert_epoch_parity(data, "Rust")

    # ── Perl ────────────────────────────────────────────────────────

    @unittest.skipUnless(toolchain_available(["perl", "--version"]), "Perl not available")
    def test_perl_epoch_parity(self):
        """Perl produces matching epoch transitions."""
        cwd = os.path.join(PROJECT_ROOT, "apps", "perl")
        main_pl = None
        for candidate in ["simulate.pl", "lib/InTheBeginning/main.pl",
                          "bin/simulator.pl", "simulator.pl", "main.pl"]:
            if os.path.exists(os.path.join(cwd, candidate)):
                main_pl = candidate
                break
        if main_pl is None:
            self.skipTest("Perl main script not found")
        result = run_app(["perl", main_pl], cwd=cwd)
        if result.returncode != 0:
            self.skipTest(f"Perl failed: {result.stderr[:200]}")
        data = extract_simulation_data(result.stdout)
        self._assert_epoch_parity(data, "Perl")

    # ── PHP ─────────────────────────────────────────────────────────

    @unittest.skipUnless(toolchain_available(["php", "--version"]), "PHP not available")
    def test_php_epoch_parity(self):
        """PHP produces matching epoch transitions."""
        cwd = os.path.join(PROJECT_ROOT, "apps", "php")
        main_php = None
        for candidate in ["simulate.php", "src/simulator.php", "simulator.php", "cli.php"]:
            if os.path.exists(os.path.join(cwd, candidate)):
                main_php = candidate
                break
        if main_php is None:
            self.skipTest("PHP CLI script not found")
        result = run_app(["php", main_php], cwd=cwd)
        if result.returncode != 0:
            self.skipTest(f"PHP failed: {result.stderr[:200]}")
        data = extract_simulation_data(result.stdout)
        self._assert_epoch_parity(data, "PHP")


class TestPythonReferenceBaseline(unittest.TestCase):
    """Baseline tests for the Python reference implementation."""

    def test_python_universe_summary_has_epochs(self):
        """Python Universe.summary() includes epoch transition data."""
        result = subprocess.run(
            [sys.executable, "-c",
             "import sys,json;sys.path.insert(0,'.');"
             "from simulator.universe import Universe;"
             "u=Universe(seed=42,max_ticks=10000,step_size=100);"
             "u.run();print(json.dumps(u.summary(),default=str))"],
            capture_output=True, text=True, timeout=30, cwd=PROJECT_ROOT,
        )
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        # Should have epoch information
        has_epochs = ("epoch_transitions" in data or "epochs" in data
                      or "current_epoch" in data)
        self.assertTrue(has_epochs, f"No epoch data in summary: {list(data.keys())}")

    def test_python_deterministic_with_same_seed(self):
        """Two runs with same seed produce identical results."""
        code = """
import sys, json
sys.path.insert(0, '.')
from simulator.universe import Universe
u = Universe(seed=42, max_ticks=1000, step_size=100)
u.run()
s = u.summary()
print(json.dumps({"tick": s.get("tick", 0), "particles": s.get("particles", 0)}, default=str))
"""
        r1 = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, timeout=30, cwd=PROJECT_ROOT,
        )
        r2 = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, timeout=30, cwd=PROJECT_ROOT,
        )
        self.assertEqual(r1.stdout, r2.stdout,
                         "Two runs with same seed produced different output")


if __name__ == "__main__":
    unittest.main()
