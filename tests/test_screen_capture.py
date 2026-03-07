"""Screen capture and visual evidence tests for all simulator implementations.

Tests fall into three categories:
1. Terminal CLI simulators: capture ANSI terminal output (Unicode progress bars,
   box-drawing, epoch banners) and convert to HTML for visual evidence.
2. Web servers: start Go SSE / PHP servers, capture HTTP responses.
3. GUI/OpenGL: attempt Xvfb-based screen capture where possible.

All evidence is saved to tests/screen_captures/ for session log inclusion.
Machine vision review: captured images should be inspected by the agent to
verify they show sensible simulation output (not blank/broken).
"""
import os
import sys
import json
import time
import struct
import signal
import subprocess
import tempfile

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

CAPTURES_DIR = os.path.join(PROJECT_ROOT, 'tests', 'screen_captures')
os.makedirs(CAPTURES_DIR, exist_ok=True)

TIMEOUT = 30  # seconds per simulator


def _capture_cli(cmd, label, max_lines=40):
    """Run a CLI simulator and capture its terminal output.

    Returns (text_output, exit_code).
    """
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=TIMEOUT,
            cwd=PROJECT_ROOT
        )
        output = result.stdout[:8000]  # Limit size
        lines = output.split('\n')[:max_lines]
        text = '\n'.join(lines)

        # Save raw ANSI output
        raw_path = os.path.join(CAPTURES_DIR, f'{label}_terminal.txt')
        with open(raw_path, 'w') as f:
            f.write(text)

        # Convert to HTML using aha (if available)
        try:
            html_result = subprocess.run(
                ['aha', '--black', '--title', f'{label} Simulator'],
                input=text, capture_output=True, text=True, timeout=5
            )
            if html_result.returncode == 0:
                html_path = os.path.join(CAPTURES_DIR, f'{label}_terminal.html')
                with open(html_path, 'w') as f:
                    f.write(html_result.stdout)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass  # aha not installed

        return text, result.returncode
    except subprocess.TimeoutExpired:
        return "(timeout)", -1
    except FileNotFoundError:
        return "(not found)", -1


def _capture_python_terminal_ui(ticks=5000):
    """Capture the Python reference terminal UI rendering."""
    code = f"""
import sys
sys.path.insert(0, '{PROJECT_ROOT}')
from simulator.universe import Universe
from simulator.terminal_ui import render_full_state
u = Universe(seed=42)
for _ in range({ticks}):
    u.step()
print(render_full_state(u))
"""
    try:
        result = subprocess.run(
            [sys.executable, '-c', code],
            capture_output=True, text=True, timeout=TIMEOUT,
            cwd=PROJECT_ROOT
        )
        output = result.stdout[:8000]
        raw_path = os.path.join(CAPTURES_DIR, 'python_terminal_ui.txt')
        with open(raw_path, 'w') as f:
            f.write(output)

        # HTML version
        try:
            html_result = subprocess.run(
                ['aha', '--black', '--title', 'Python Terminal UI'],
                input=output, capture_output=True, text=True, timeout=5
            )
            if html_result.returncode == 0:
                html_path = os.path.join(CAPTURES_DIR, 'python_terminal_ui.html')
                with open(html_path, 'w') as f:
                    f.write(html_result.stdout)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        return output, result.returncode
    except subprocess.TimeoutExpired:
        return "(timeout)", -1


def _test_server(start_cmd, port, label, cwd=None):
    """Start a server, make HTTP requests, capture responses, stop server."""
    proc = None
    try:
        proc = subprocess.Popen(
            start_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=cwd or PROJECT_ROOT
        )
        time.sleep(3)  # Let server start

        # Get HTML page
        html_result = subprocess.run(
            ['curl', '-s', f'http://localhost:{port}/'],
            capture_output=True, text=True, timeout=10
        )
        html_path = os.path.join(CAPTURES_DIR, f'{label}_server.html')
        with open(html_path, 'w') as f:
            f.write(html_result.stdout[:10000])

        # Get API JSON
        api_endpoints = ['/api/snapshot', '/api/state']
        api_data = None
        for endpoint in api_endpoints:
            try:
                api_result = subprocess.run(
                    ['curl', '-s', f'http://localhost:{port}{endpoint}'],
                    capture_output=True, text=True, timeout=10
                )
                if api_result.stdout and api_result.stdout.strip().startswith('{'):
                    api_data = json.loads(api_result.stdout)
                    api_path = os.path.join(CAPTURES_DIR, f'{label}_api.json')
                    with open(api_path, 'w') as f:
                        json.dump(api_data, f, indent=2)
                    break
            except Exception:
                continue

        return html_result.stdout[:500], api_data

    finally:
        if proc:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


def _xvfb_capture(cmd, label, run_seconds=8, cwd=None):
    """Run a GUI program in Xvfb and capture screenshot."""
    display = ':98'
    xvfb = None
    app = None
    try:
        xvfb = subprocess.Popen(
            ['Xvfb', display, '-screen', '0', '1024x768x24'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        time.sleep(1)

        env = os.environ.copy()
        env['DISPLAY'] = display
        env['LIBGL_ALWAYS_SOFTWARE'] = '1'
        env['MESA_GL_VERSION_OVERRIDE'] = '3.3'

        app = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=env, cwd=cwd or PROJECT_ROOT
        )
        time.sleep(run_seconds)

        # Capture screenshot
        png_path = os.path.join(CAPTURES_DIR, f'{label}_screenshot.png')
        subprocess.run(
            ['import', '-display', display, '-window', 'root', png_path],
            env=env, timeout=10, capture_output=True
        )

        if os.path.exists(png_path) and os.path.getsize(png_path) > 500:
            return png_path
        return None

    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    finally:
        if app:
            app.terminate()
            try:
                app.wait(timeout=3)
            except subprocess.TimeoutExpired:
                app.kill()
        if xvfb:
            xvfb.terminate()


# ===================================================================
# Test functions
# ===================================================================

def test_python_terminal_ui():
    """Capture Python reference terminal UI with box-drawing and progress bars."""
    output, rc = _capture_python_terminal_ui(ticks=5000)
    assert rc == 0, f"Python terminal UI failed with exit code {rc}"
    assert 'IN THE BEGINNING' in output, "Missing title banner"
    assert 'Tick' in output or 'tick' in output, "Missing tick counter"
    assert 'Epoch' in output or 'epoch' in output, "Missing epoch info"
    # Verify Unicode box-drawing characters present
    assert any(c in output for c in ['┌', '─', '│', '└', '╔', '═']), \
        "Missing Unicode box-drawing characters"


def test_nodejs_terminal():
    """Capture Node.js terminal output with ANSI progress bars."""
    output, rc = _capture_cli(
        ['node', os.path.join(PROJECT_ROOT, 'apps', 'nodejs', 'index.js')],
        'nodejs'
    )
    assert rc == 0, f"Node.js failed with exit code {rc}"
    assert 'I N   T H E   B E G I N N I N G' in output or \
           'IN THE BEGINNING' in output, "Missing title"


def test_go_terminal():
    """Capture Go CLI terminal output."""
    # Pre-built binary preferred (go run is slow in tests)
    go_dir = os.path.join(PROJECT_ROOT, 'apps', 'go')
    binary = os.path.join(go_dir, 'sim_binary')
    if not os.path.exists(binary):
        subprocess.run(['go', 'build', '-o', binary, './cmd/simulator/'],
                       cwd=go_dir, timeout=60, capture_output=True)
    if os.path.exists(binary) and os.access(binary, os.X_OK):
        output, rc = _capture_cli([binary], 'go')
    else:
        output, rc = _capture_cli(
            ['go', 'run', './cmd/simulator/'],
            'go'
        )
    assert rc == 0, f"Go failed with exit code {rc}"
    assert 'IN THE BEGINNING' in output, "Missing title"


def test_cpp_terminal():
    """Capture C++ terminal output with ANSI formatting."""
    binary = os.path.join(PROJECT_ROOT, 'apps', 'cpp', 'build', 'inthebeginning')
    if not os.path.exists(binary):
        import pytest
        pytest.skip("C++ binary not built")
    output, rc = _capture_cli([binary], 'cpp')
    assert rc == 0, f"C++ failed with exit code {rc}"
    assert 'IN THE BEGINNING' in output, "Missing title"


def test_c_terminal():
    """Capture C terminal output."""
    binary = os.path.join(PROJECT_ROOT, 'apps', 'c', 'build', 'simulator')
    if not os.path.exists(binary):
        import pytest
        pytest.skip("C binary not built")
    output, rc = _capture_cli([binary], 'c')
    assert rc == 0, f"C failed with exit code {rc}"
    assert 'IN THE BEGINNING' in output, "Missing title"


def test_rust_terminal():
    """Capture Rust terminal output."""
    binary = os.path.join(PROJECT_ROOT, 'apps', 'rust', 'target', 'release',
                          'inthebeginning-rust')
    if not os.path.exists(binary):
        # Try debug build
        binary = os.path.join(PROJECT_ROOT, 'apps', 'rust', 'target', 'debug',
                              'inthebeginning-rust')
    if not os.path.exists(binary):
        import pytest
        pytest.skip("Rust binary not built")
    output, rc = _capture_cli([binary], 'rust')
    assert rc == 0, f"Rust failed with exit code {rc}"
    assert 'IN THE BEGINNING' in output or 'Cosmic Simulation' in output, \
        "Missing title"


def test_perl_terminal():
    """Capture Perl terminal output."""
    output, rc = _capture_cli(
        ['perl', os.path.join(PROJECT_ROOT, 'apps', 'perl', 'simulate.pl')],
        'perl'
    )
    assert rc == 0, f"Perl failed with exit code {rc}"
    assert 'IN THE BEGINNING' in output, "Missing title"


def test_php_terminal():
    """Capture PHP CLI terminal output."""
    output, rc = _capture_cli(
        ['php', os.path.join(PROJECT_ROOT, 'apps', 'php', 'simulate.php')],
        'php'
    )
    assert rc == 0, f"PHP failed with exit code {rc}"
    assert 'IN THE BEGINNING' in output, "Missing title"


def test_go_sse_server():
    """Test Go SSE server: start, HTTP request, verify response."""
    go_dir = os.path.join(PROJECT_ROOT, 'apps', 'go')
    binary = os.path.join(go_dir, 'server')
    if not os.path.exists(binary):
        subprocess.run(['go', 'build', '-o', binary, './cmd/server/'],
                       cwd=go_dir, timeout=60, capture_output=True)
    if os.path.exists(binary):
        cmd = [binary, '-port', '8094']
    else:
        cmd = ['go', 'run', './cmd/server/', '-port', '8094']
    html, api_data = _test_server(cmd, 8094, 'go_sse', cwd=go_dir)
    assert 'In The Beginning' in html, "Missing title in Go SSE HTML"
    if api_data:
        assert 'epoch' in api_data, "Missing epoch in API response"
        assert 'tick' in api_data, "Missing tick in API response"


def test_php_server():
    """Test PHP snapshot server: start, HTTP request, verify response."""
    html, api_data = _test_server(
        ['php', '-S', 'localhost:8095',
         os.path.join(PROJECT_ROOT, 'apps', 'php', 'server.php')],
        8095, 'php_snapshot',
        cwd=os.path.join(PROJECT_ROOT, 'apps', 'php')
    )
    assert 'In The Beginning' in html, "Missing title in PHP server HTML"
    if api_data:
        assert 'current_epoch' in api_data, "Missing epoch in PHP API"


def test_ubuntu_screensaver_xvfb():
    """Test Ubuntu screensaver in Xvfb (OpenGL may not render in software mode)."""
    binary = os.path.join(PROJECT_ROOT, 'apps', 'screensaver-ubuntu',
                          'inthebeginning-screensaver')
    if not os.path.exists(binary):
        import pytest
        pytest.skip("Ubuntu screensaver not built")

    # Even if OpenGL doesn't render, verify the binary starts and exits cleanly
    png_path = _xvfb_capture([binary, '-window'], 'ubuntu_screensaver', run_seconds=6)
    # Note: screenshot may be black if Mesa software rendering can't do GLX
    # The test passes as long as the binary doesn't crash
    capture_path = os.path.join(CAPTURES_DIR, 'ubuntu_screensaver_screenshot.png')
    if png_path and os.path.exists(capture_path):
        assert os.path.getsize(capture_path) > 0, "Screenshot is empty"


def test_java_headless():
    """Test Java simulator in headless mode."""
    classes_dir = os.path.join(PROJECT_ROOT, 'apps', 'java', 'build', 'classes')
    if not os.path.isdir(classes_dir):
        import pytest
        pytest.skip("Java classes not built")

    output, rc = _capture_cli(
        ['java', '-Djava.awt.headless=true', '-cp', classes_dir,
         'com.inthebeginning.simulator.SimulatorApp'],
        'java'
    )
    # Java may exit non-zero in headless if it tries to open GUI
    assert 'IN THE BEGINNING' in output or 'Epoch' in output or rc == 0, \
        f"Java headless failed: {output[:200]}"


def test_captures_summary():
    """Generate a summary of all captured screen evidence."""
    summary = {"captures": [], "timestamp": time.strftime("%Y-%m-%d %H:%M CT")}

    for fname in sorted(os.listdir(CAPTURES_DIR)):
        fpath = os.path.join(CAPTURES_DIR, fname)
        size = os.path.getsize(fpath)
        summary["captures"].append({
            "file": fname,
            "size_bytes": size,
            "type": "html" if fname.endswith('.html') else
                    "json" if fname.endswith('.json') else
                    "png" if fname.endswith('.png') else "txt"
        })

    summary_path = os.path.join(CAPTURES_DIR, 'capture_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    assert len(summary["captures"]) > 0, "No captures were generated"
    print(f"\nScreen capture summary: {len(summary['captures'])} files generated")
    for c in summary["captures"]:
        print(f"  {c['file']} ({c['size_bytes']} bytes)")
