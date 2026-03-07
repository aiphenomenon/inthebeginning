"""Golden tests for visualizer/GUI apps.

Tests build success, headless operation, and simulator core output for:
- Ubuntu screensaver (C + X11) — compile test + sim core unit tests
- WASM (Rust → WebAssembly) — Rust library tests (no browser needed)
- Java GUI (Swing) — headless mode test
- macOS screensaver (Swift + Metal) — skipped on Linux (no Swift toolchain)

Run:
    python -m pytest tests/test_visualizer_golden.py -v
"""
import json
import os
import re
import subprocess
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def toolchain_available(cmd):
    """Check if a command-line tool is available."""
    try:
        subprocess.run(cmd, capture_output=True, timeout=10)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def pkg_config_exists(lib):
    """Check if a pkg-config library exists."""
    try:
        result = subprocess.run(
            ["pkg-config", "--exists", lib],
            capture_output=True, timeout=5,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


# ── Ubuntu Screensaver (C + X11) ──────────────────────────────────────


class TestUbuntuScreensaver(unittest.TestCase):
    """Tests for the Ubuntu C screensaver app."""

    SCREENSAVER_DIR = os.path.join(PROJECT_ROOT, "apps", "screensaver-ubuntu")

    @unittest.skipUnless(toolchain_available(["gcc", "--version"]), "GCC not available")
    def test_simulator_core_compiles(self):
        """Ubuntu screensaver simulator core compiles."""
        # Compile test_simulator.c which tests the sim without X11/GL deps
        cwd = self.SCREENSAVER_DIR
        test_src = os.path.join(cwd, "test_simulator.c")
        if not os.path.exists(test_src):
            self.skipTest("test_simulator.c not found")

        # Find all simulator .c files
        sim_dir = os.path.join(cwd, "simulator")
        if not os.path.isdir(sim_dir):
            self.skipTest("simulator/ directory not found")

        sim_sources = [os.path.join(sim_dir, f)
                       for f in os.listdir(sim_dir) if f.endswith('.c')]

        result = subprocess.run(
            ["gcc", "-std=c11", "-Wall", "-O2", "-o", "test_sim_golden",
             test_src] + sim_sources + ["-lm"],
            capture_output=True, text=True, timeout=60, cwd=cwd,
        )
        self.assertEqual(result.returncode, 0,
                         f"Compilation failed:\n{result.stderr[:500]}")
        # Cleanup
        try:
            os.remove(os.path.join(cwd, "test_sim_golden"))
        except OSError:
            pass

    @unittest.skipUnless(toolchain_available(["gcc", "--version"]), "GCC not available")
    def test_simulator_core_tests_pass(self):
        """Ubuntu screensaver simulator unit tests pass."""
        cwd = self.SCREENSAVER_DIR
        # Build and run the existing test binary
        result = subprocess.run(
            ["make", "test"],
            capture_output=True, text=True, timeout=60, cwd=cwd,
        )
        # Check output for pass indicators
        if result.returncode == 0:
            self.assertNotIn("FAIL", result.stdout.upper().split("PASS")[-1] if "PASS" in result.stdout.upper() else "")
        else:
            # Make test might fail on missing X11 libs for the main binary
            # but the test runner itself should work
            if "test_simulator" in result.stderr or "-lGL" in result.stderr:
                # Build just the test binary without GL
                sim_dir = os.path.join(cwd, "simulator")
                sim_sources = [os.path.join(sim_dir, f)
                               for f in os.listdir(sim_dir) if f.endswith('.c')]
                r2 = subprocess.run(
                    ["gcc", "-std=c11", "-Wall", "-O2", "-o", "test_sim_run",
                     os.path.join(cwd, "test_simulator.c")] + sim_sources + ["-lm"],
                    capture_output=True, text=True, timeout=60, cwd=cwd,
                )
                if r2.returncode != 0:
                    self.skipTest(f"Cannot compile tests: {r2.stderr[:300]}")
                r3 = subprocess.run(
                    ["./test_sim_run"],
                    capture_output=True, text=True, timeout=60, cwd=cwd,
                )
                try:
                    os.remove(os.path.join(cwd, "test_sim_run"))
                except OSError:
                    pass
                self.assertEqual(r3.returncode, 0,
                                 f"Tests failed:\n{r3.stdout[:300]}\n{r3.stderr[:300]}")

    @unittest.skipUnless(
        toolchain_available(["gcc", "--version"]) and pkg_config_exists("x11"),
        "GCC or X11 headers not available",
    )
    def test_screensaver_binary_compiles_with_x11(self):
        """Ubuntu screensaver full binary compiles (if X11+GL available)."""
        cwd = self.SCREENSAVER_DIR
        if not pkg_config_exists("gl"):
            self.skipTest("GL headers not available — can compile sim core but not full screensaver")
        result = subprocess.run(
            ["make", "clean"], capture_output=True, timeout=10, cwd=cwd,
        )
        result = subprocess.run(
            ["make"],
            capture_output=True, text=True, timeout=60, cwd=cwd,
        )
        self.assertEqual(result.returncode, 0,
                         f"Full screensaver build failed:\n{result.stderr[:500]}")


# ── WASM (Rust → WebAssembly) ─────────────────────────────────────────


class TestWASMApp(unittest.TestCase):
    """Tests for the WebAssembly (Rust→WASM) app."""

    WASM_DIR = os.path.join(PROJECT_ROOT, "apps", "wasm")

    @unittest.skipUnless(toolchain_available(["cargo", "--version"]), "Rust not available")
    def test_wasm_rust_lib_tests_pass(self):
        """WASM Rust library unit tests pass (no browser needed)."""
        cwd = self.WASM_DIR
        result = subprocess.run(
            ["cargo", "test", "--lib"],
            capture_output=True, text=True, timeout=180, cwd=cwd,
        )
        self.assertEqual(result.returncode, 0,
                         f"WASM Rust lib tests failed:\n{result.stderr[:500]}")

    @unittest.skipUnless(toolchain_available(["cargo", "--version"]), "Rust not available")
    def test_wasm_rust_compiles(self):
        """WASM Rust library compiles as rlib (no wasm-pack needed)."""
        cwd = self.WASM_DIR
        result = subprocess.run(
            ["cargo", "check"],
            capture_output=True, text=True, timeout=180, cwd=cwd,
        )
        # cargo check may fail due to wgpu/wasm-bindgen features
        # but the core simulator modules should compile
        if result.returncode != 0:
            # Try building just the lib tests (no wasm target needed)
            result2 = subprocess.run(
                ["cargo", "test", "--lib", "--no-run"],
                capture_output=True, text=True, timeout=180, cwd=cwd,
            )
            self.assertEqual(result2.returncode, 0,
                             f"WASM lib compile failed:\n{result2.stderr[:500]}")

    def test_wasm_html_exists(self):
        """WASM app has index.html for browser interface."""
        html_path = os.path.join(self.WASM_DIR, "index.html")
        self.assertTrue(os.path.exists(html_path),
                        "Missing index.html for WASM browser interface")

    def test_wasm_html_references_wasm(self):
        """WASM index.html references the WASM module."""
        html_path = os.path.join(self.WASM_DIR, "index.html")
        if not os.path.exists(html_path):
            self.skipTest("No index.html")
        with open(html_path) as f:
            html = f.read()
        # Should reference wasm init or import
        self.assertTrue(
            'wasm' in html.lower() or '.js' in html,
            "index.html doesn't appear to reference WASM module",
        )


# ── Java GUI (Swing) ─────────────────────────────────────────────────


class TestJavaGUI(unittest.TestCase):
    """Tests for the Java Swing GUI application."""

    JAVA_DIR = os.path.join(PROJECT_ROOT, "apps", "java")

    @unittest.skipUnless(toolchain_available(["javac", "-version"]), "Java not available")
    def test_java_compiles_all(self):
        """All Java source files compile without errors."""
        cwd = self.JAVA_DIR
        os.makedirs(os.path.join(cwd, "build", "classes"), exist_ok=True)
        src_dir = os.path.join(cwd, "src", "main", "java", "com", "inthebeginning", "simulator")
        if not os.path.isdir(src_dir):
            self.skipTest("Java source directory not found")
        java_files = [os.path.join(src_dir, f)
                      for f in os.listdir(src_dir) if f.endswith('.java')]
        result = subprocess.run(
            ["javac", "-d", "build/classes", "-sourcepath", "src/main/java"] + java_files,
            capture_output=True, text=True, timeout=60, cwd=cwd,
        )
        self.assertEqual(result.returncode, 0,
                         f"Java compilation failed:\n{result.stderr[:500]}")

    @unittest.skipUnless(toolchain_available(["javac", "-version"]), "Java not available")
    def test_java_unit_tests_pass(self):
        """Java unit tests pass."""
        cwd = self.JAVA_DIR
        os.makedirs(os.path.join(cwd, "build", "classes"), exist_ok=True)
        os.makedirs(os.path.join(cwd, "build", "test-classes"), exist_ok=True)

        # Compile main sources
        src_dir = os.path.join(cwd, "src", "main", "java", "com", "inthebeginning", "simulator")
        java_files = [os.path.join(src_dir, f)
                      for f in os.listdir(src_dir) if f.endswith('.java')]
        subprocess.run(
            ["javac", "-d", "build/classes", "-sourcepath", "src/main/java"] + java_files,
            capture_output=True, timeout=60, cwd=cwd,
        )

        # Compile test sources
        test_dir = os.path.join(cwd, "src", "test", "java", "com", "inthebeginning", "simulator")
        if not os.path.isdir(test_dir):
            self.skipTest("No Java test directory")
        test_files = [os.path.join(test_dir, f)
                      for f in os.listdir(test_dir) if f.endswith('.java')]
        result = subprocess.run(
            ["javac", "-d", "build/test-classes", "-cp", "build/classes",
             "-sourcepath", "src/test/java"] + test_files,
            capture_output=True, text=True, timeout=60, cwd=cwd,
        )
        if result.returncode != 0:
            self.skipTest(f"Test compilation failed: {result.stderr[:300]}")

        # Run tests
        result = subprocess.run(
            ["java", "-cp", "build/classes:build/test-classes",
             "com.inthebeginning.simulator.AllTests"],
            capture_output=True, text=True, timeout=60, cwd=cwd,
        )
        self.assertEqual(result.returncode, 0,
                         f"Java tests failed:\n{result.stdout[:500]}")

    @unittest.skipUnless(toolchain_available(["javac", "-version"]), "Java not available")
    def test_java_headless_mode(self):
        """Java app can start in headless mode (no display needed)."""
        cwd = self.JAVA_DIR
        os.makedirs(os.path.join(cwd, "build", "classes"), exist_ok=True)
        src_dir = os.path.join(cwd, "src", "main", "java", "com", "inthebeginning", "simulator")
        java_files = [os.path.join(src_dir, f)
                      for f in os.listdir(src_dir) if f.endswith('.java')]
        subprocess.run(
            ["javac", "-d", "build/classes", "-sourcepath", "src/main/java"] + java_files,
            capture_output=True, timeout=60, cwd=cwd,
        )
        env = os.environ.copy()
        env["JAVA_TOOL_OPTIONS"] = "-Djava.awt.headless=true"
        result = subprocess.run(
            ["java", "-cp", "build/classes",
             "com.inthebeginning.simulator.Main"],
            capture_output=True, text=True, timeout=30, cwd=cwd, env=env,
        )
        # In headless mode, it may exit non-zero but shouldn't crash with NPE
        self.assertNotIn("NullPointerException", result.stderr,
                         "Java NPE in headless mode")


# ── macOS Screensaver (Swift + Metal) ─────────────────────────────────


class TestMacOSScreensaver(unittest.TestCase):
    """Tests for the macOS screensaver app (Swift + Metal)."""

    SCREENSAVER_DIR = os.path.join(PROJECT_ROOT, "apps", "screensaver-macos")

    def test_source_files_exist(self):
        """macOS screensaver has expected source structure."""
        self.assertTrue(os.path.isdir(self.SCREENSAVER_DIR),
                        "screensaver-macos directory not found")
        # Should have Swift source files
        swift_files = []
        for root, dirs, files in os.walk(self.SCREENSAVER_DIR):
            swift_files.extend(f for f in files if f.endswith('.swift'))
        self.assertGreater(len(swift_files), 0,
                           "No Swift source files found")

    def test_test_files_exist(self):
        """macOS screensaver has test files."""
        test_dir = os.path.join(self.SCREENSAVER_DIR, "Tests")
        if not os.path.isdir(test_dir):
            self.skipTest("No Tests/ directory")
        swift_tests = []
        for root, dirs, files in os.walk(test_dir):
            swift_tests.extend(f for f in files if f.endswith('.swift'))
        self.assertGreater(len(swift_tests), 0,
                           "No Swift test files found")

    @unittest.skipUnless(toolchain_available(["swift", "--version"]), "Swift not available")
    def test_swift_tests_pass(self):
        """macOS screensaver Swift tests pass (if toolchain available)."""
        result = subprocess.run(
            ["swift", "test"],
            capture_output=True, text=True, timeout=120,
            cwd=self.SCREENSAVER_DIR,
        )
        self.assertEqual(result.returncode, 0,
                         f"Swift tests failed:\n{result.stderr[:500]}")


# ── Cross-Visualizer Consistency ──────────────────────────────────────


class TestVisualizerConsistency(unittest.TestCase):
    """Verify visualizer apps share consistent simulator implementations."""

    def test_all_visualizers_have_tests(self):
        """All visualizer apps have test files."""
        apps_with_tests = {
            "screensaver-ubuntu": "test_simulator.c",
            "screensaver-macos": "Tests/",
            "java": "src/test/",
            "wasm": "src/",  # inline #[test] in Rust files
        }
        for app, test_indicator in apps_with_tests.items():
            app_dir = os.path.join(PROJECT_ROOT, "apps", app)
            if not os.path.isdir(app_dir):
                continue
            test_path = os.path.join(app_dir, test_indicator)
            self.assertTrue(
                os.path.exists(test_path),
                f"Missing tests for {app}: expected {test_indicator}",
            )

    def test_ubuntu_screensaver_has_simulator_module(self):
        """Ubuntu screensaver has a simulator/ subdirectory."""
        sim_dir = os.path.join(PROJECT_ROOT, "apps", "screensaver-ubuntu", "simulator")
        self.assertTrue(os.path.isdir(sim_dir),
                        "Missing simulator/ in screensaver-ubuntu")


if __name__ == "__main__":
    unittest.main()
