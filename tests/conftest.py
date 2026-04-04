"""
Shared pytest fixtures and configuration for inthebeginning test suite.

Registers custom markers for test categorization and provides fixtures
for PulseAudio audio sink lifecycle and browser E2E test integration.
"""

import os
import subprocess
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.join(PROJECT_ROOT, 'tools')


def pytest_configure(config):
    """Register custom markers for test categorization."""
    config.addinivalue_line("markers", "unit: Fast unit tests (<5s)")
    config.addinivalue_line("markers", "integration: Integration tests (~30s)")
    config.addinivalue_line("markers", "e2e: Browser end-to-end tests (~2-5min)")
    config.addinivalue_line("markers", "screen: Screenshot comparison tests")
    config.addinivalue_line("markers", "audio: Audio capture and analysis tests")
    config.addinivalue_line("markers", "wasm: WASM-specific tests")
    config.addinivalue_line("markers", "slow: Tests that take >30s")


@pytest.fixture(scope="session")
def audio_sink():
    """Start PulseAudio virtual audio sink for the test session."""
    sink_script = os.path.join(TOOLS_DIR, 'audio-sink.sh')
    if not os.path.exists(sink_script):
        pytest.skip("audio-sink.sh not found")

    try:
        subprocess.run(
            ['bash', sink_script, '--start'],
            capture_output=True, timeout=10
        )
        yield
    finally:
        subprocess.run(
            ['bash', sink_script, '--stop'],
            capture_output=True, timeout=10
        )


@pytest.fixture(scope="session")
def static_server():
    """Start a static file server for the deploy directory."""
    deploy_dir = os.path.join(PROJECT_ROOT, 'deploy')
    proc = subprocess.Popen(
        ['python3', '-m', 'http.server', '8080',
         '--directory', deploy_dir, '--bind', '127.0.0.1'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    import time
    time.sleep(1)
    yield proc
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
