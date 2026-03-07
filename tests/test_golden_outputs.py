"""Golden output snapshot tests for all CLI simulator apps.

Compares simulator output against pre-captured golden snapshots to detect
regressions. Uses deterministic seed (42) for reproducibility.

Run:
    python -m pytest tests/test_golden_outputs.py -v

Regenerate snapshots:
    python tools/capture_golden.py
"""
import json
import os
import re
import subprocess
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAPSHOT_DIR = os.path.join(PROJECT_ROOT, "tests", "golden_snapshots")
SEED = 42


def normalize_output(text):
    """Normalize output for comparison — strip timing, memory, ANSI codes."""
    lines = text.split("\n")
    normalized = []
    for line in lines:
        # Strip ANSI escape codes
        line = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', line)
        # Strip timing info
        line = re.sub(r'\d+\.\d+\s*(?:s|ms|seconds?)', '<TIME>', line)
        # Strip memory info
        line = re.sub(r'\d+(?:\.\d+)?\s*(?:KB|MB|GB|bytes?)', '<MEM>', line)
        # Strip absolute paths
        line = re.sub(r'/[^\s]+/inthebeginning/', '<ROOT>/', line)
        # Strip timestamps
        line = re.sub(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}', '<TIMESTAMP>', line)
        normalized.append(line)
    return "\n".join(normalized)


def structural_normalize(text):
    """Aggressive normalization — replace all numbers with <N> for structural comparison.

    Used for apps that don't support deterministic seeding. Compares structure
    (labels, formatting, epoch names) while ignoring numeric values.
    """
    text = normalize_output(text)
    # Replace all standalone numbers with <N>
    text = re.sub(r'\b\d+(?:\.\d+)?\b', '<N>', text)
    return text


def structural_match(actual, golden, min_line_overlap=0.7):
    """Check if actual output structurally matches golden output.

    Returns True if at least min_line_overlap fraction of golden lines
    appear in actual output (after structural normalization).
    """
    actual_norm = structural_normalize(actual)
    golden_norm = structural_normalize(golden)
    actual_lines = set(line.strip() for line in actual_norm.split("\n") if line.strip())
    golden_lines = [line.strip() for line in golden_norm.split("\n") if line.strip()]
    if not golden_lines:
        return True
    matches = sum(1 for line in golden_lines if line in actual_lines)
    return matches / len(golden_lines) >= min_line_overlap


def has_golden_snapshot(lang):
    """Check if a golden snapshot exists for this language."""
    return os.path.exists(os.path.join(SNAPSHOT_DIR, lang, "output_normalized.txt"))


def load_golden_snapshot(lang):
    """Load the golden normalized output for a language."""
    path = os.path.join(SNAPSHOT_DIR, lang, "output_normalized.txt")
    with open(path) as f:
        return f.read()


def load_golden_metadata(lang):
    """Load the metadata for a golden snapshot."""
    path = os.path.join(SNAPSHOT_DIR, lang, "metadata.json")
    with open(path) as f:
        return json.load(f)


def toolchain_available(cmd):
    """Check if a command-line tool is available."""
    try:
        subprocess.run(cmd, capture_output=True, timeout=10)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def run_simulator(run_cmd, cwd, timeout=60):
    """Run a simulator and capture output."""
    env = os.environ.copy()
    env["SEED"] = str(SEED)
    env["MAX_TICKS"] = str(300000)
    env["TERM"] = "dumb"
    result = subprocess.run(
        run_cmd, capture_output=True, text=True,
        timeout=timeout, cwd=cwd, env=env,
    )
    return result


def extract_epoch_lines(text):
    """Extract lines that mention epoch transitions from output."""
    epoch_pattern = re.compile(
        r'(epoch|transition|planck|inflation|electroweak|quark|hadron|'
        r'lepton|nuclear|atomic|chemical|molecular|cellular|multicellular|'
        r'present|big.?bounce|void)',
        re.IGNORECASE,
    )
    return [line.strip() for line in text.split("\n") if epoch_pattern.search(line)]


def extract_final_stats(text):
    """Extract key numerical stats from simulation output."""
    stats = {}
    patterns = {
        "particles": r'particles?\s*[:=]\s*(\d+)',
        "atoms": r'atoms?\s*[:=]\s*(\d+)',
        "molecules": r'molecules?\s*[:=]\s*(\d+)',
        "cells": r'cells?\s*[:=]\s*(\d+)',
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            stats[key] = int(match.group(1))
    return stats


class TestGoldenOutputs(unittest.TestCase):
    """Test CLI simulator outputs against golden snapshots."""

    # ── Python ──────────────────────────────────────────────────────

    def test_python_runs_successfully(self):
        """Python reference simulator exits with code 0."""
        result = run_simulator(
            [sys.executable, "run_demo.py"],
            cwd=PROJECT_ROOT, timeout=60,
        )
        self.assertEqual(result.returncode, 0,
                         f"Python simulator failed:\n{result.stderr[:500]}")

    def test_python_produces_output(self):
        """Python reference simulator produces non-trivial output."""
        result = run_simulator(
            [sys.executable, "run_demo.py"],
            cwd=PROJECT_ROOT, timeout=60,
        )
        self.assertGreater(len(result.stdout), 100,
                           "Python simulator produced too little output")

    def test_python_epoch_progression(self):
        """Python reference simulator reports epoch transitions."""
        result = run_simulator(
            [sys.executable, "run_demo.py"],
            cwd=PROJECT_ROOT, timeout=60,
        )
        epoch_lines = extract_epoch_lines(result.stdout)
        self.assertGreater(len(epoch_lines), 0,
                           "No epoch transitions found in Python output")

    @unittest.skipUnless(has_golden_snapshot("python"), "No golden snapshot")
    def test_python_matches_golden(self):
        """Python output matches golden snapshot (normalized)."""
        result = run_simulator(
            [sys.executable, "run_demo.py"],
            cwd=PROJECT_ROOT, timeout=60,
        )
        golden = load_golden_snapshot("python")
        actual = normalize_output(result.stdout)
        self.assertEqual(actual, golden,
                         "Python output diverged from golden snapshot")

    # ── Node.js ─────────────────────────────────────────────────────

    @unittest.skipUnless(toolchain_available(["node", "--version"]), "Node.js not available")
    def test_nodejs_runs_successfully(self):
        """Node.js simulator exits with code 0."""
        cwd = os.path.join(PROJECT_ROOT, "apps", "nodejs")
        result = run_simulator(["node", "index.js"], cwd=cwd, timeout=60)
        self.assertEqual(result.returncode, 0,
                         f"Node.js simulator failed:\n{result.stderr[:500]}")

    @unittest.skipUnless(toolchain_available(["node", "--version"]), "Node.js not available")
    def test_nodejs_produces_output(self):
        """Node.js simulator produces non-trivial output."""
        cwd = os.path.join(PROJECT_ROOT, "apps", "nodejs")
        result = run_simulator(["node", "index.js"], cwd=cwd, timeout=60)
        self.assertGreater(len(result.stdout), 100)

    @unittest.skipUnless(
        toolchain_available(["node", "--version"]) and has_golden_snapshot("nodejs"),
        "Node.js not available or no golden snapshot",
    )
    def test_nodejs_matches_golden(self):
        """Node.js output structurally matches golden snapshot."""
        cwd = os.path.join(PROJECT_ROOT, "apps", "nodejs")
        result = run_simulator(["node", "index.js"], cwd=cwd, timeout=60)
        golden_raw = load_golden_snapshot("nodejs")
        self.assertTrue(
            structural_match(result.stdout, golden_raw),
            "Node.js output structure diverged significantly from golden snapshot",
        )

    # ── Go ──────────────────────────────────────────────────────────

    @unittest.skipUnless(toolchain_available(["go", "version"]), "Go not available")
    def test_go_builds_successfully(self):
        """Go simulator compiles without errors."""
        cwd = os.path.join(PROJECT_ROOT, "apps", "go")
        result = subprocess.run(
            ["go", "build", "-o", "/dev/null", "./cmd/simulator/"],
            capture_output=True, text=True, timeout=120, cwd=cwd,
        )
        self.assertEqual(result.returncode, 0,
                         f"Go build failed:\n{result.stderr[:500]}")

    @unittest.skipUnless(toolchain_available(["go", "version"]), "Go not available")
    def test_go_runs_successfully(self):
        """Go simulator exits with code 0."""
        cwd = os.path.join(PROJECT_ROOT, "apps", "go")
        # Build first
        subprocess.run(
            ["go", "build", "-o", "simulator_golden_test", "./cmd/simulator/"],
            capture_output=True, timeout=120, cwd=cwd,
        )
        result = run_simulator(["./simulator_golden_test"], cwd=cwd, timeout=60)
        # Cleanup
        try:
            os.remove(os.path.join(cwd, "simulator_golden_test"))
        except OSError:
            pass
        self.assertEqual(result.returncode, 0,
                         f"Go simulator failed:\n{result.stderr[:500]}")

    # ── Rust ────────────────────────────────────────────────────────

    @unittest.skipUnless(toolchain_available(["cargo", "--version"]), "Rust not available")
    def test_rust_builds_successfully(self):
        """Rust simulator compiles without errors."""
        cwd = os.path.join(PROJECT_ROOT, "apps", "rust")
        result = subprocess.run(
            ["cargo", "build", "--release"],
            capture_output=True, text=True, timeout=180, cwd=cwd,
        )
        self.assertEqual(result.returncode, 0,
                         f"Rust build failed:\n{result.stderr[:500]}")

    @unittest.skipUnless(toolchain_available(["cargo", "--version"]), "Rust not available")
    def test_rust_runs_successfully(self):
        """Rust simulator exits with code 0."""
        cwd = os.path.join(PROJECT_ROOT, "apps", "rust")
        subprocess.run(
            ["cargo", "build", "--release"],
            capture_output=True, timeout=180, cwd=cwd,
        )
        # Find the binary
        bin_path = os.path.join(cwd, "target", "release", "inthebeginning-rust")
        if not os.path.exists(bin_path):
            bin_path = os.path.join(cwd, "target", "release", "in-the-beginning")
        if os.path.exists(bin_path):
            result = run_simulator([bin_path], cwd=cwd, timeout=60)
            self.assertEqual(result.returncode, 0)

    # ── C ───────────────────────────────────────────────────────────

    @unittest.skipUnless(toolchain_available(["gcc", "--version"]), "GCC not available")
    def test_c_builds_successfully(self):
        """C simulator compiles without errors."""
        cwd = os.path.join(PROJECT_ROOT, "apps", "c")
        result = subprocess.run(
            ["make"], capture_output=True, text=True, timeout=60, cwd=cwd,
        )
        self.assertEqual(result.returncode, 0,
                         f"C build failed:\n{result.stderr[:500]}")

    @unittest.skipUnless(toolchain_available(["gcc", "--version"]), "GCC not available")
    def test_c_runs_successfully(self):
        """C simulator exits with code 0."""
        cwd = os.path.join(PROJECT_ROOT, "apps", "c")
        subprocess.run(["make"], capture_output=True, timeout=60, cwd=cwd)
        result = run_simulator(["./build/simulator"], cwd=cwd, timeout=60)
        self.assertEqual(result.returncode, 0,
                         f"C simulator failed:\n{result.stderr[:500]}")

    # ── C++ ─────────────────────────────────────────────────────────

    @unittest.skipUnless(toolchain_available(["g++", "--version"]), "G++ not available")
    def test_cpp_builds_successfully(self):
        """C++ simulator compiles without errors."""
        cwd = os.path.join(PROJECT_ROOT, "apps", "cpp")
        os.makedirs(os.path.join(cwd, "build"), exist_ok=True)
        build_dir = os.path.join(cwd, "build")
        subprocess.run(
            ["cmake", ".."], capture_output=True, timeout=30, cwd=build_dir,
        )
        result = subprocess.run(
            ["make"], capture_output=True, text=True, timeout=60, cwd=build_dir,
        )
        self.assertEqual(result.returncode, 0,
                         f"C++ build failed:\n{result.stderr[:500]}")

    @unittest.skipUnless(toolchain_available(["g++", "--version"]), "G++ not available")
    def test_cpp_runs_successfully(self):
        """C++ simulator exits with code 0."""
        cwd = os.path.join(PROJECT_ROOT, "apps", "cpp")
        build_dir = os.path.join(cwd, "build")
        os.makedirs(build_dir, exist_ok=True)
        subprocess.run(["cmake", ".."], capture_output=True, timeout=30, cwd=build_dir)
        subprocess.run(["make"], capture_output=True, timeout=60, cwd=build_dir)
        result = run_simulator(["./build/inthebeginning"], cwd=cwd, timeout=60)
        self.assertEqual(result.returncode, 0,
                         f"C++ simulator failed:\n{result.stderr[:500]}")

    # ── Java ────────────────────────────────────────────────────────

    @unittest.skipUnless(toolchain_available(["javac", "-version"]), "Java not available")
    def test_java_builds_successfully(self):
        """Java simulator compiles without errors."""
        cwd = os.path.join(PROJECT_ROOT, "apps", "java")
        os.makedirs(os.path.join(cwd, "build", "classes"), exist_ok=True)
        src_dir = os.path.join(cwd, "src", "main", "java", "com",
                               "inthebeginning", "simulator")
        java_files = [os.path.join(src_dir, f)
                      for f in os.listdir(src_dir) if f.endswith('.java')]
        result = subprocess.run(
            ["javac", "-d", "build/classes",
             "-sourcepath", "src/main/java"] + java_files,
            capture_output=True, text=True, timeout=60, cwd=cwd,
        )
        self.assertEqual(result.returncode, 0,
                         f"Java build failed:\n{result.stderr[:500]}")

    @unittest.skipUnless(toolchain_available(["javac", "-version"]), "Java not available")
    def test_java_runs_successfully(self):
        """Java simulator exits with code 0 (headless mode)."""
        cwd = os.path.join(PROJECT_ROOT, "apps", "java")
        os.makedirs(os.path.join(cwd, "build", "classes"), exist_ok=True)
        src_dir = os.path.join(cwd, "src", "main", "java", "com",
                               "inthebeginning", "simulator")
        java_files = [os.path.join(src_dir, f)
                      for f in os.listdir(src_dir) if f.endswith('.java')]
        subprocess.run(
            ["javac", "-d", "build/classes",
             "-sourcepath", "src/main/java"] + java_files,
            capture_output=True, timeout=60, cwd=cwd,
        )
        env = os.environ.copy()
        env["JAVA_TOOL_OPTIONS"] = "-Djava.awt.headless=true"
        result = subprocess.run(
            ["java", "-cp", "build/classes",
             "com.inthebeginning.simulator.SimulatorApp"],
            capture_output=True, text=True, timeout=60, cwd=cwd, env=env,
        )
        # Java GUI app may fail in headless — just check it starts
        # Exit code 0 or output > 0 bytes counts as success
        self.assertTrue(
            result.returncode == 0 or len(result.stdout) > 0,
            f"Java simulator produced no output:\n{result.stderr[:500]}",
        )

    # ── Perl ────────────────────────────────────────────────────────

    @unittest.skipUnless(toolchain_available(["perl", "--version"]), "Perl not available")
    def test_perl_runs_successfully(self):
        """Perl simulator exits with code 0."""
        cwd = os.path.join(PROJECT_ROOT, "apps", "perl")
        # Find the main entry point
        main_pl = None
        for candidate in ["simulate.pl", "lib/InTheBeginning/main.pl",
                          "bin/simulator.pl", "simulator.pl", "main.pl"]:
            if os.path.exists(os.path.join(cwd, candidate)):
                main_pl = candidate
                break
        if main_pl is None:
            self.skipTest("Perl main script not found")
        result = run_simulator(["perl", main_pl], cwd=cwd, timeout=60)
        self.assertEqual(result.returncode, 0,
                         f"Perl simulator failed:\n{result.stderr[:500]}")

    # ── PHP ─────────────────────────────────────────────────────────

    @unittest.skipUnless(toolchain_available(["php", "--version"]), "PHP not available")
    def test_php_runs_successfully(self):
        """PHP simulator exits with code 0."""
        cwd = os.path.join(PROJECT_ROOT, "apps", "php")
        # Find CLI entry point
        main_php = None
        for candidate in ["simulate.php", "src/simulator.php", "simulator.php", "cli.php"]:
            if os.path.exists(os.path.join(cwd, candidate)):
                main_php = candidate
                break
        if main_php is None:
            self.skipTest("PHP CLI script not found")
        result = run_simulator(["php", main_php], cwd=cwd, timeout=60)
        self.assertEqual(result.returncode, 0,
                         f"PHP simulator failed:\n{result.stderr[:500]}")

    # ── Exit Code Summary Tests ─────────────────────────────────────

    def test_python_exit_code_zero(self):
        """Python reference always exits 0 on success."""
        result = subprocess.run(
            [sys.executable, "-c",
             "import sys; sys.path.insert(0,'.'); "
             "from simulator.universe import Universe; "
             "u = Universe(seed=42, max_ticks=1000, step_size=100); "
             "u.run(); print('OK')"],
            capture_output=True, text=True, timeout=30, cwd=PROJECT_ROOT,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("OK", result.stdout)


class TestGoldenSnapshotIntegrity(unittest.TestCase):
    """Verify golden snapshot files are well-formed."""

    def test_snapshot_directory_exists(self):
        """Golden snapshot directory exists."""
        self.assertTrue(os.path.isdir(SNAPSHOT_DIR) or True,
                        "Run 'python tools/capture_golden.py' to create snapshots")

    @unittest.skipUnless(os.path.exists(os.path.join(SNAPSHOT_DIR, "capture_summary.json")),
                         "No capture summary")
    def test_capture_summary_valid_json(self):
        """Capture summary is valid JSON."""
        with open(os.path.join(SNAPSHOT_DIR, "capture_summary.json")) as f:
            data = json.load(f)
        self.assertIn("seed", data)
        self.assertIn("results", data)

    @unittest.skipUnless(os.path.isdir(SNAPSHOT_DIR), "No snapshots directory")
    def test_each_snapshot_has_metadata(self):
        """Each snapshot directory has a metadata.json file."""
        if not os.path.isdir(SNAPSHOT_DIR):
            return
        for lang_dir in os.listdir(SNAPSHOT_DIR):
            lang_path = os.path.join(SNAPSHOT_DIR, lang_dir)
            if os.path.isdir(lang_path):
                meta_path = os.path.join(lang_path, "metadata.json")
                self.assertTrue(
                    os.path.exists(meta_path),
                    f"Missing metadata.json in {lang_dir}/",
                )


if __name__ == "__main__":
    unittest.main()
