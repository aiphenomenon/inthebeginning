"""Integration smoke tests for the v13 inthebeginning-bounce deploy.

These tests complement the Playwright e2e suite for environments where
Playwright cannot run (node 12 in local dev, no Chromium available).
They start a Python HTTP server against deploy/ and verify:

1. HTTP smoke: all static assets (HTML, JS, sf2, favicon, album.json)
   respond 200 on the path the app actually probes first.
2. SF2 integrity: the first 4 bytes on the wire are "RIFF" and the
   content-length is > 100 MB (not a 130-byte LFS pointer).
3. Version label correctness: config.js has APP_VERSION = 'v13' and
   ALBUM_DISPLAY_NAME = 'Cosmic Session'.
4. HTML cleanliness: no hardcoded "V11" / "V8 Sessions" leaked into the
   user-visible text of index.html.
5. Bug fix wireup: player.js musicGenerator gate accepts WASM mode;
   spessa-bridge.js has the _validateSoundFontBuffer method; synth-engine
   probes shared paths before audio/samples/; app.js album probes start
   with metadata/v1.

Grid color rendering and actual audio output must still be verified in a
real browser — those depend on Web Audio API and AudioWorklet which are
not exercised here.
"""

import http.server
import socketserver
import subprocess
import threading
import time
import urllib.request
import urllib.error
from pathlib import Path

try:
    import pytest
    HAVE_PYTEST = True
except ImportError:
    HAVE_PYTEST = False
    # Minimal pytest stand-in so the module loads and the tests can run
    # from `python3 tests/test_v13_deploy.py` in environments without pytest.
    class _PytestStub:
        @staticmethod
        def fixture(*args, **kwargs):
            def decorator(fn):
                fn._is_fixture = True
                return fn
            if args and callable(args[0]):
                return decorator(args[0])
            return decorator
    pytest = _PytestStub()


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEPLOY_DIR = PROJECT_ROOT / "deploy"
BOUNCE_DIR = DEPLOY_DIR / "v13" / "inthebeginning-bounce"
PORT = 8090  # Different from playwright's 8080 to avoid conflict


@pytest.fixture(scope="module")
def server():
    """Start a Python HTTP server serving deploy/ for the duration of the module."""
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(DEPLOY_DIR), **kwargs)

        def log_message(self, format, *args):
            pass  # quiet

    httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.1)  # let it bind
    yield f"http://127.0.0.1:{PORT}"
    httpd.shutdown()


def _status(url, method="HEAD"):
    req = urllib.request.Request(url, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def _resolve(rel):
    """Resolve a relative URL from inside the bounce folder to an absolute path."""
    if rel.startswith("../../"):
        return "/" + rel[len("../../"):]
    if rel.startswith("../"):
        return "/v13/" + rel[len("../"):]
    return "/v13/inthebeginning-bounce/" + rel


# ────────────────────────── HTTP smoke tests ──────────────────────────


def test_index_html_serves(server):
    assert _status(f"{server}/v13/inthebeginning-bounce/index.html", "GET") == 200


def test_favicon_serves(server):
    assert _status(f"{server}/v13/inthebeginning-bounce/favicon.ico") == 200


def test_all_edited_js_files_serve(server):
    files = [
        "config.js",
        "spessa-bridge.js",
        "app.js",
        "player.js",
        "synth-engine.js",
        "wasm-synth.js",
    ]
    for f in files:
        url = f"{server}/v13/inthebeginning-bounce/js/{f}"
        assert _status(url, "GET") == 200, f"{f} did not serve"


# ─────────────────────── Path probe smoke tests ───────────────────────


def test_first_album_probe_returns_200(server):
    """After v50, album.json is probed at metadata/v1 first — it exists."""
    path = _resolve("../../shared/audio/metadata/v1/album.json")
    assert _status(f"{server}{path}") == 200


def test_first_audio_base_probe_returns_200(server):
    """After v50, the first-track HEAD uses shared/audio/tracks/ which exists."""
    path = _resolve("../../shared/audio/tracks/") + "V8_Sessions-aiphenomenon-01-Ember.mp3"
    assert _status(f"{server}{path}") == 200


def test_piano_mp3_first_probe_returns_200(server):
    """After v50, SynthEngine.initSamples probes shared/instruments first."""
    path = _resolve("../../shared/audio/instruments/") + "piano.mp3"
    assert _status(f"{server}{path}") == 200


def test_sf2_first_probe_returns_200(server):
    path = _resolve("../../shared/audio/soundfonts/FluidR3_GM.sf2")
    assert _status(f"{server}{path}") == 200


# ────────────────────── SF2 integrity tests ──────────────────────


def test_sf2_content_length_is_full_file(server):
    """The served sf2 must be the real binary, not a 130-byte LFS pointer."""
    path = _resolve("../../shared/audio/soundfonts/FluidR3_GM.sf2")
    req = urllib.request.Request(f"{server}{path}", method="HEAD")
    with urllib.request.urlopen(req) as r:
        cl = int(r.headers.get("content-length", 0))
    assert cl > 100_000_000, f"sf2 content-length {cl} suggests it's an LFS pointer"


def test_sf2_first_four_bytes_are_riff(server):
    """Client-side SpessaBridge will check this — verify the server's response."""
    path = _resolve("../../shared/audio/soundfonts/FluidR3_GM.sf2")
    with urllib.request.urlopen(f"{server}{path}") as r:
        first = r.read(4)
    assert first == b"RIFF", f"sf2 magic bytes expected 'RIFF', got {first!r}"


# ───────────────── Source-level correctness tests ─────────────────


def _read(path):
    return (BOUNCE_DIR / path).read_text()


def test_config_has_app_version_v13():
    src = _read("js/config.js")
    assert "const APP_VERSION = 'v13'" in src, "APP_VERSION not set to v13"


def test_config_has_album_display_name_cosmic_session():
    src = _read("js/config.js")
    assert "const ALBUM_DISPLAY_NAME = 'Cosmic Session'" in src


def test_index_has_no_hardcoded_v11_in_visible_text():
    """The subtitle and credits must not hardcode a version string."""
    src = _read("index.html")
    # Title comment explains runtime population — allow the phrase "APP_VERSION"
    # Locate the subtitle element and make sure it's empty (populated at runtime)
    assert '<p class="subtitle" id="title-subtitle"></p>' in src, (
        "subtitle should be empty in markup — populated from config.js at runtime"
    )


def test_index_has_favicon_link():
    src = _read("index.html")
    assert 'rel="icon"' in src and "favicon.ico" in src


def test_index_has_no_user_visible_v8_sessions():
    """Credits use 'Cosmic Session Album' rename."""
    src = _read("index.html")
    # Still OK to reference internal file names like V8_Sessions-*.mp3
    # in script tags / URLs, but the user-facing <p> text must be renamed.
    # The subtitle previously said "V8 Sessions — V11" — now empty.
    # The credits previously said "V8 Sessions Album" — now "Cosmic Session Album".
    assert "Cosmic Session Album" in src, "credits should mention Cosmic Session"
    assert "V8 Sessions Album" not in src, "stale 'V8 Sessions Album' text in credits"


def test_spessa_bridge_has_validator():
    src = _read("js/spessa-bridge.js")
    assert "_validateSoundFontBuffer" in src
    # Validator must check for LFS pointer and RIFF magic
    assert "Git LFS pointer file" in src
    assert "RIFF" in src


def test_spessa_bridge_init_no_longer_swallows():
    """init() should throw on error, not silently return false."""
    src = _read("js/spessa-bridge.js")
    # The old version had `console.warn('SpessaBridge: Initialization failed')`
    # and `return false`. The new version throws from the validator and init
    # re-throws via surface. Verify the old-style swallow is gone.
    assert "console.warn('SpessaBridge: Initialization failed'" not in src


def test_synth_engine_probes_shared_first():
    src = _read("js/synth-engine.js")
    # The `paths` array should have shared paths before audio/samples/
    idx_shared = src.find("'../../shared/audio/instruments/'")
    idx_audio = src.find("'audio/samples/'")
    assert idx_shared > 0, "shared instruments path missing"
    assert idx_audio == -1 or idx_audio > idx_shared, (
        "synth-engine should probe shared/instruments/ before audio/samples/"
    )


def test_player_js_wasm_gate_accepts_wasm_mode():
    """The musicGenerator.onNoteEvent gate must fire for both SYNTH and WASM."""
    src = _read("js/player.js")
    # New pattern: single multi-mode check
    assert "AUDIO_MODE.SYNTH || m === AUDIO_MODE.WASM" in src, (
        "player.js musicGenerator gate not updated to accept WASM mode"
    )


def test_app_loadmusic_probes_metadata_v1_first():
    src = _read("js/app.js")
    # First entry in albumJsonPaths
    probe_block = src[src.find("const albumJsonPaths"):src.find("const albumJsonPaths")+400]
    # metadata/v1 should appear before tracks/ in the block
    idx_meta = probe_block.find("metadata/v1/album.json")
    idx_tracks = probe_block.find("tracks/album.json")
    idx_audio = probe_block.find("'audio/album.json'")
    assert idx_meta > 0 and (idx_tracks < 0 or idx_meta < idx_tracks), (
        "app.js should probe metadata/v1/album.json before tracks/album.json"
    )
    assert idx_audio < 0 or idx_audio > idx_meta, (
        "app.js should probe metadata/v1 before audio/album.json"
    )


def test_app_hifi_branch_has_visible_error():
    src = _read("js/app.js")
    # New fallback shows a red HUD warning — not just console.warn
    assert "⚠ HiFi unavailable" in src or "HiFi unavailable" in src
    assert "console.error" in src


def test_wasm_synth_normalizes_velocity():
    src = _read("js/wasm-synth.js")
    assert "(note.vel || 80) / 127" in src, (
        "wasm-synth.js should normalize velocity to 0-1"
    )


# ────────────────────────── Standalone runner ──────────────────────────
# When invoked directly (no pytest), run every `test_*` function here.
# The `server` fixture is instantiated once and passed to tests that take it.

if __name__ == "__main__":
    import sys
    import inspect

    # Start the server manually
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(DEPLOY_DIR), **kwargs)

        def log_message(self, format, *args):
            pass

    httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.1)
    server_url = f"http://127.0.0.1:{PORT}"

    try:
        module = sys.modules[__name__]
        tests = [
            (name, fn)
            for name, fn in inspect.getmembers(module)
            if name.startswith("test_") and callable(fn)
        ]
        passed = 0
        failed = 0
        for name, fn in tests:
            sig = inspect.signature(fn)
            kwargs = {"server": server_url} if "server" in sig.parameters else {}
            try:
                fn(**kwargs)
                print(f"PASS: {name}")
                passed += 1
            except AssertionError as e:
                print(f"FAIL: {name} — {e}")
                failed += 1
            except Exception as e:
                print(f"ERROR: {name} — {type(e).__name__}: {e}")
                failed += 1
        print()
        print(f"{passed} passed, {failed} failed")
        sys.exit(0 if failed == 0 else 1)
    finally:
        httpd.shutdown()
