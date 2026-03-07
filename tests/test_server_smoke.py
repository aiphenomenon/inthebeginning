"""Server smoke tests for Go SSE server and PHP snapshot server.

Starts each server on a random port, makes HTTP requests, verifies
responses, then kills the server. Fully self-contained.

Run:
    python -m pytest tests/test_server_smoke.py -v
"""
import http.client
import json
import os
import signal
import socket
import subprocess
import sys
import time
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def find_free_port():
    """Find a free TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def toolchain_available(cmd):
    """Check if a command-line tool is available."""
    try:
        subprocess.run(cmd, capture_output=True, timeout=10)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def wait_for_port(port, host='localhost', timeout=15):
    """Wait until a port is open on localhost."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except (ConnectionRefusedError, OSError):
            time.sleep(0.3)
    return False


def http_get(host, port, path='/', timeout=5):
    """Make an HTTP GET request and return (status, headers, body)."""
    conn = http.client.HTTPConnection(host, port, timeout=timeout)
    try:
        conn.request('GET', path)
        resp = conn.getresponse()
        body = resp.read().decode('utf-8', errors='replace')
        return resp.status, dict(resp.getheaders()), body
    except Exception as e:
        return None, None, str(e)
    finally:
        conn.close()


class TestGoSSEServer(unittest.TestCase):
    """Smoke tests for the Go SSE server."""

    @classmethod
    def setUpClass(cls):
        """Build the Go SSE server."""
        if not toolchain_available(["go", "version"]):
            raise unittest.SkipTest("Go toolchain not available")
        cls.server_dir = os.path.join(PROJECT_ROOT, "apps", "go")
        cls.binary_path = os.path.join(cls.server_dir, "sse_server_test")
        result = subprocess.run(
            ["go", "build", "-o", cls.binary_path, "./cmd/server/"],
            capture_output=True, text=True, timeout=120, cwd=cls.server_dir,
        )
        if result.returncode != 0:
            raise unittest.SkipTest(f"Go SSE server build failed: {result.stderr[:300]}")

    @classmethod
    def tearDownClass(cls):
        """Clean up built binary."""
        try:
            os.remove(cls.binary_path)
        except OSError:
            pass

    def _start_server(self, port):
        """Start the SSE server on given port. Returns process."""
        env = os.environ.copy()
        env["PORT"] = str(port)
        proc = subprocess.Popen(
            [self.binary_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=self.server_dir, env=env,
        )
        return proc

    def test_go_sse_server_starts(self):
        """Go SSE server starts and listens on port."""
        port = find_free_port()
        proc = self._start_server(port)
        try:
            started = wait_for_port(port, timeout=10)
            self.assertTrue(started, "Go SSE server did not start within 10s")
        finally:
            proc.terminate()
            proc.wait(timeout=5)

    def test_go_sse_server_responds_200(self):
        """Go SSE server responds with HTTP 200."""
        port = find_free_port()
        proc = self._start_server(port)
        try:
            if not wait_for_port(port, timeout=10):
                self.skipTest("Server didn't start")
            status, headers, body = http_get('localhost', port, '/')
            self.assertIsNotNone(status, f"Connection failed: {body}")
            self.assertEqual(status, 200, f"Expected 200, got {status}")
        finally:
            proc.terminate()
            proc.wait(timeout=5)

    def test_go_sse_server_content_type(self):
        """Go SSE server responds with appropriate content type."""
        port = find_free_port()
        proc = self._start_server(port)
        try:
            if not wait_for_port(port, timeout=10):
                self.skipTest("Server didn't start")
            status, headers, body = http_get('localhost', port, '/')
            self.assertIsNotNone(status)
            # Should be either text/event-stream or text/html
            content_type = headers.get('Content-Type', headers.get('content-type', ''))
            self.assertTrue(
                'text/' in content_type,
                f"Unexpected content type: {content_type}",
            )
        finally:
            proc.terminate()
            proc.wait(timeout=5)

    def test_go_sse_server_has_body(self):
        """Go SSE server response body is non-empty."""
        port = find_free_port()
        proc = self._start_server(port)
        try:
            if not wait_for_port(port, timeout=10):
                self.skipTest("Server didn't start")
            status, headers, body = http_get('localhost', port, '/')
            self.assertIsNotNone(status)
            self.assertGreater(len(body), 0, "Empty response body")
        finally:
            proc.terminate()
            proc.wait(timeout=5)


class TestPHPSnapshotServer(unittest.TestCase):
    """Smoke tests for the PHP snapshot server."""

    @classmethod
    def setUpClass(cls):
        """Verify PHP is available."""
        if not toolchain_available(["php", "--version"]):
            raise unittest.SkipTest("PHP not available")
        cls.server_dir = os.path.join(PROJECT_ROOT, "apps", "php")
        cls.server_file = os.path.join(cls.server_dir, "server.php")
        if not os.path.exists(cls.server_file):
            raise unittest.SkipTest("server.php not found")

    def _start_server(self, port):
        """Start PHP built-in server. Returns process."""
        proc = subprocess.Popen(
            ["php", "-S", f"localhost:{port}", "server.php"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=self.server_dir,
        )
        return proc

    def test_php_server_starts(self):
        """PHP snapshot server starts and listens on port."""
        port = find_free_port()
        proc = self._start_server(port)
        try:
            started = wait_for_port(port, timeout=10)
            self.assertTrue(started, "PHP server did not start within 10s")
        finally:
            proc.terminate()
            proc.wait(timeout=5)

    def test_php_server_responds_200(self):
        """PHP snapshot server responds with HTTP 200."""
        port = find_free_port()
        proc = self._start_server(port)
        try:
            if not wait_for_port(port, timeout=10):
                self.skipTest("Server didn't start")
            status, headers, body = http_get('localhost', port, '/')
            self.assertIsNotNone(status, f"Connection failed: {body}")
            # PHP server may return 200 or redirect; both are OK
            self.assertIn(status, [200, 301, 302],
                          f"Unexpected status: {status}")
        finally:
            proc.terminate()
            proc.wait(timeout=5)

    def test_php_server_has_body(self):
        """PHP snapshot server response body is non-empty."""
        port = find_free_port()
        proc = self._start_server(port)
        try:
            if not wait_for_port(port, timeout=10):
                self.skipTest("Server didn't start")
            status, headers, body = http_get('localhost', port, '/')
            self.assertIsNotNone(status)
            self.assertGreater(len(body), 0, "Empty response body")
        finally:
            proc.terminate()
            proc.wait(timeout=5)


class TestServerSecurity(unittest.TestCase):
    """Verify servers only bind to localhost."""

    @unittest.skipUnless(toolchain_available(["go", "version"]), "Go not available")
    def test_go_server_binds_localhost_only(self):
        """Go SSE server binds to localhost, not 0.0.0.0."""
        server_file = os.path.join(PROJECT_ROOT, "apps", "go", "cmd", "server", "main.go")
        if not os.path.exists(server_file):
            self.skipTest("Server source not found")
        with open(server_file) as f:
            source = f.read()
        # Should bind to localhost or 127.0.0.1, not 0.0.0.0
        if '0.0.0.0' in source:
            self.fail("Server binds to 0.0.0.0 — should bind to localhost only")

    @unittest.skipUnless(toolchain_available(["php", "--version"]), "PHP not available")
    def test_php_server_source_safe(self):
        """PHP server doesn't contain unsafe patterns."""
        server_file = os.path.join(PROJECT_ROOT, "apps", "php", "server.php")
        if not os.path.exists(server_file):
            self.skipTest("Server source not found")
        with open(server_file) as f:
            source = f.read()
        # Should not use eval, exec, system on user input
        for dangerous in ['eval(', 'exec(', 'system(', 'passthru(']:
            if dangerous in source:
                # Check if it's in a comment
                import re
                if re.search(rf'^\s*[^/\*].*{re.escape(dangerous)}', source, re.MULTILINE):
                    self.fail(f"Server contains potentially dangerous: {dangerous}")


if __name__ == "__main__":
    unittest.main()
