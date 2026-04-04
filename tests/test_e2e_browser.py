"""
Python pytest wrapper for Playwright browser E2E tests.

Invokes `npx playwright test` and maps results to pytest assertions.
This allows the browser E2E tests to appear in the standard pytest report
alongside all other Python tests.

Usage:
    # Headless (no audio capture):
    python3 -m pytest tests/test_e2e_browser.py -v

    # With real audio capture (requires PulseAudio + Xvfb):
    python3 -m pytest tests/test_e2e_browser.py -v -k audio
"""

import json
import os
import subprocess
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E2E_DIR = os.path.join(PROJECT_ROOT, 'tests', 'e2e')
RESULTS_FILE = os.path.join(PROJECT_ROOT, 'test_screenshots', 'e2e-results', 'results.json')


def _check_playwright():
    """Check if Playwright is available."""
    try:
        result = subprocess.run(
            ['npx', 'playwright', '--version'],
            capture_output=True, text=True, timeout=15, cwd=PROJECT_ROOT,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def _check_server():
    """Check if the static file server is running on port 8080."""
    import urllib.request
    try:
        urllib.request.urlopen('http://localhost:8080/v11/inthebeginning-bounce/index.html', timeout=3)
        return True
    except Exception:
        return False


def _run_playwright(spec_file, grep=None, audio=False):
    """Run a Playwright test spec and return parsed results."""
    os.makedirs(os.path.dirname(RESULTS_FILE), exist_ok=True)

    cmd = ['npx', 'playwright', 'test', spec_file,
           '--config=tests/e2e/playwright.config.mjs',
           '--reporter=json']
    if grep:
        cmd.extend(['-g', grep])

    env = os.environ.copy()
    if audio:
        env['E2E_AUDIO'] = '1'

    wrapper = cmd
    if audio:
        wrapper = ['xvfb-run', '-a', '-s', '-screen 0 1280x720x24', '--'] + cmd

    result = subprocess.run(
        wrapper, capture_output=True, text=True,
        timeout=300, cwd=PROJECT_ROOT, env=env,
    )

    # Parse JSON output
    try:
        data = json.loads(result.stdout)
        suites = data.get('suites', [])
        tests = []
        _extract_tests(suites, tests)
        return tests
    except (json.JSONDecodeError, KeyError):
        return [{'title': 'playwright-run', 'status': 'failed',
                 'error': result.stderr[:500] or result.stdout[:500] or 'Unknown error'}]


def _extract_tests(suites, tests):
    """Recursively extract test results from Playwright JSON report."""
    for suite in suites:
        for spec in suite.get('specs', []):
            for test in spec.get('tests', []):
                for result in test.get('results', []):
                    tests.append({
                        'title': spec.get('title', 'unknown'),
                        'status': result.get('status', 'unknown'),
                        'duration': result.get('duration', 0),
                        'error': result.get('error', {}).get('message', '') if result.get('error') else '',
                    })
        # Recurse into child suites
        _extract_tests(suite.get('suites', []), tests)


# ──── Pytest Test Functions ────

@pytest.mark.e2e
class TestBrowserE2E:
    """Browser E2E tests via Playwright (headless)."""

    @classmethod
    def setup_class(cls):
        if not _check_playwright():
            pytest.skip("Playwright not available")
        if not _check_server():
            pytest.skip("Static file server not running on port 8080")

    def test_game_e2e(self):
        """Run all game E2E tests (headless)."""
        results = _run_playwright('tests/e2e/game.spec.mjs')
        passed = sum(1 for t in results if t['status'] == 'passed')
        failed = [t for t in results if t['status'] != 'passed']

        if failed:
            failures = '; '.join(f"{t['title']}: {t['error'][:100]}" for t in failed[:5])
            pytest.fail(f"{len(failed)} tests failed: {failures}")

        assert passed > 0, "No tests ran"

    def test_wasm_e2e(self):
        """Run WASM verification tests (headless)."""
        results = _run_playwright('tests/e2e/wasm.spec.mjs')
        passed = sum(1 for t in results if t['status'] == 'passed')
        failed = [t for t in results if t['status'] != 'passed']

        if failed:
            failures = '; '.join(f"{t['title']}: {t['error'][:100]}" for t in failed[:5])
            pytest.fail(f"{len(failed)} tests failed: {failures}")


@pytest.mark.e2e
@pytest.mark.audio
class TestBrowserAudio:
    """Browser audio E2E tests via Playwright (headful + PulseAudio)."""

    @classmethod
    def setup_class(cls):
        if not _check_playwright():
            pytest.skip("Playwright not available")
        if not _check_server():
            pytest.skip("Static file server not running on port 8080")
        # Check PulseAudio
        try:
            result = subprocess.run(
                ['pactl', 'info'], capture_output=True, timeout=5)
            if result.returncode != 0:
                pytest.skip("PulseAudio not running")
        except FileNotFoundError:
            pytest.skip("PulseAudio not installed")

    def test_audio_e2e(self):
        """Run audio verification tests (headful + PulseAudio + Xvfb)."""
        results = _run_playwright('tests/e2e/audio.spec.mjs', audio=True)
        passed = sum(1 for t in results if t['status'] == 'passed')
        failed = [t for t in results if t['status'] != 'passed']

        if failed:
            failures = '; '.join(f"{t['title']}: {t['error'][:100]}" for t in failed[:5])
            pytest.fail(f"{len(failed)} tests failed: {failures}")

        assert passed > 0, "No audio tests ran"
