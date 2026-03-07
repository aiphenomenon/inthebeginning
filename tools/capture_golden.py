#!/usr/bin/env python3
"""Capture golden output snapshots for all CLI simulator apps.

Runs each simulator with deterministic seed and captures stdout for
use as golden test baselines. Only captures for available toolchains.

Usage:
    python tools/capture_golden.py [--lang LANG] [--ticks N] [--seed N]
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAPSHOT_DIR = os.path.join(PROJECT_ROOT, "tests", "golden_snapshots")

# Each entry: (lang_key, check_cmd, build_cmds, run_cmd, cwd)
# check_cmd: command to verify toolchain is available (None = always available)
# build_cmds: list of shell commands to build before running (empty = interpreted)
# run_cmd: command to run the simulator
# cwd: working directory relative to PROJECT_ROOT
APPS = [
    {
        "lang": "python",
        "check": None,  # always available
        "build": [],
        "run": [sys.executable, "run_demo.py"],
        "cwd": "",
        "timeout": 60,
    },
    {
        "lang": "nodejs",
        "check": ["node", "--version"],
        "build": [],
        "run": ["node", "index.js"],
        "cwd": "apps/nodejs",
        "timeout": 60,
    },
    {
        "lang": "go",
        "check": ["go", "version"],
        "build": ["go build -o simulator_bin ./cmd/simulator/"],
        "run": ["./simulator_bin"],
        "cwd": "apps/go",
        "timeout": 60,
    },
    {
        "lang": "rust",
        "check": ["cargo", "--version"],
        "build": ["cargo build --release"],
        "run": ["./target/release/inthebeginning-rust"],
        "cwd": "apps/rust",
        "timeout": 120,
    },
    {
        "lang": "c",
        "check": ["gcc", "--version"],
        "build": ["make"],
        "run": ["./build/simulator"],
        "cwd": "apps/c",
        "timeout": 60,
    },
    {
        "lang": "cpp",
        "check": ["g++", "--version"],
        "build": ["mkdir -p build", "cd build && cmake .. -DCMAKE_BUILD_TYPE=Release && make"],
        "run": ["./build/simulator"],
        "cwd": "apps/cpp",
        "timeout": 60,
    },
    {
        "lang": "java",
        "check": ["javac", "-version"],
        "build": ["mkdir -p build/classes",
                  "javac -d build/classes src/main/java/com/inthebeginning/simulator/*.java"],
        "run": ["java", "-cp", "build/classes", "com.inthebeginning.simulator.Main"],
        "cwd": "apps/java",
        "timeout": 60,
    },
    {
        "lang": "perl",
        "check": ["perl", "--version"],
        "build": [],
        "run": ["perl", "simulate.pl"],
        "cwd": "apps/perl",
        "timeout": 60,
    },
    {
        "lang": "php",
        "check": ["php", "--version"],
        "build": [],
        "run": ["php", "simulate.php"],
        "cwd": "apps/php",
        "timeout": 60,
    },
    {
        "lang": "typescript",
        "check": ["node", "--version"],
        "build": ["npm run build"],
        "run": ["node", "dist/index.js"],
        "cwd": "apps/typescript",
        "timeout": 60,
    },
]


def is_available(app):
    """Check if the toolchain for this app is available."""
    if app["check"] is None:
        return True
    try:
        subprocess.run(
            app["check"],
            capture_output=True, timeout=10,
            cwd=os.path.join(PROJECT_ROOT, app["cwd"]) if app["cwd"] else PROJECT_ROOT,
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def build_app(app):
    """Build the app if needed. Returns True on success."""
    cwd = os.path.join(PROJECT_ROOT, app["cwd"]) if app["cwd"] else PROJECT_ROOT
    for cmd in app["build"]:
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                timeout=120, cwd=cwd,
            )
            if result.returncode != 0:
                print(f"  BUILD FAILED: {cmd}")
                print(f"  stderr: {result.stderr[:500]}")
                return False
        except subprocess.TimeoutExpired:
            print(f"  BUILD TIMEOUT: {cmd}")
            return False
    return True


def capture_output(app, seed=42, ticks=300000):
    """Run the app and capture its stdout."""
    cwd = os.path.join(PROJECT_ROOT, app["cwd"]) if app["cwd"] else PROJECT_ROOT
    env = os.environ.copy()
    env["SEED"] = str(seed)
    env["MAX_TICKS"] = str(ticks)
    env["TERM"] = "dumb"  # disable terminal colors/control sequences

    try:
        result = subprocess.run(
            app["run"],
            capture_output=True, text=True,
            timeout=app["timeout"], cwd=cwd, env=env,
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "success": result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "TIMEOUT", "returncode": -1, "success": False}
    except FileNotFoundError as e:
        return {"stdout": "", "stderr": str(e), "returncode": -1, "success": False}


def normalize_output(text):
    """Normalize output for comparison — strip timing, memory, ANSI codes."""
    import re
    lines = text.split("\n")
    normalized = []
    for line in lines:
        # Strip ANSI escape codes
        line = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', line)
        # Strip timing info (e.g., "1.234s", "123ms", "0.001 seconds")
        line = re.sub(r'\d+\.\d+\s*(?:s|ms|seconds?)', '<TIME>', line)
        # Strip memory info (e.g., "1234KB", "5.6MB")
        line = re.sub(r'\d+(?:\.\d+)?\s*(?:KB|MB|GB|bytes?)', '<MEM>', line)
        # Strip absolute paths
        line = re.sub(r'/[^\s]+/inthebeginning/', '<ROOT>/', line)
        # Strip timestamps
        line = re.sub(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}', '<TIMESTAMP>', line)
        normalized.append(line)
    return "\n".join(normalized)


def save_snapshot(lang, result, seed, ticks):
    """Save captured output as a golden snapshot."""
    lang_dir = os.path.join(SNAPSHOT_DIR, lang)
    os.makedirs(lang_dir, exist_ok=True)

    # Raw output
    with open(os.path.join(lang_dir, "output.txt"), "w") as f:
        f.write(result["stdout"])

    # Normalized output (for comparison)
    with open(os.path.join(lang_dir, "output_normalized.txt"), "w") as f:
        f.write(normalize_output(result["stdout"]))

    # Metadata
    meta = {
        "lang": lang,
        "seed": seed,
        "ticks": ticks,
        "returncode": result["returncode"],
        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "stdout_lines": len(result["stdout"].split("\n")),
        "stderr_lines": len(result["stderr"].split("\n")) if result["stderr"] else 0,
    }
    with open(os.path.join(lang_dir, "metadata.json"), "w") as f:
        json.dump(meta, f, indent=2)

    if result["stderr"]:
        with open(os.path.join(lang_dir, "stderr.txt"), "w") as f:
            f.write(result["stderr"])


def main():
    parser = argparse.ArgumentParser(description="Capture golden output snapshots")
    parser.add_argument("--lang", help="Only capture for this language")
    parser.add_argument("--ticks", type=int, default=300000, help="Simulation ticks")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--list", action="store_true", help="List available apps")
    args = parser.parse_args()

    apps = APPS
    if args.lang:
        apps = [a for a in apps if a["lang"] == args.lang]
        if not apps:
            print(f"Unknown language: {args.lang}")
            print(f"Available: {', '.join(a['lang'] for a in APPS)}")
            sys.exit(1)

    os.makedirs(SNAPSHOT_DIR, exist_ok=True)

    results = {}
    for app in apps:
        lang = app["lang"]
        print(f"\n{'='*60}")
        print(f"  {lang.upper()}")
        print(f"{'='*60}")

        if not is_available(app):
            print(f"  SKIPPED: toolchain not available")
            results[lang] = "skipped"
            continue

        if app["build"]:
            print(f"  Building...")
            if not build_app(app):
                results[lang] = "build_failed"
                continue

        print(f"  Running (seed={args.seed}, ticks={args.ticks})...")
        result = capture_output(app, seed=args.seed, ticks=args.ticks)

        if result["success"]:
            save_snapshot(lang, result, args.seed, args.ticks)
            print(f"  CAPTURED: {len(result['stdout'])} bytes")
            results[lang] = "captured"
        else:
            print(f"  FAILED: exit code {result['returncode']}")
            if result["stderr"]:
                print(f"  stderr: {result['stderr'][:300]}")
            results[lang] = "failed"

    # Summary
    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    for lang, status in results.items():
        icon = {"captured": "+", "skipped": "-", "failed": "!", "build_failed": "!"}
        print(f"  [{icon.get(status, '?')}] {lang}: {status}")

    # Save summary
    summary_path = os.path.join(SNAPSHOT_DIR, "capture_summary.json")
    with open(summary_path, "w") as f:
        json.dump({
            "seed": args.seed,
            "ticks": args.ticks,
            "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "results": results,
        }, f, indent=2)


if __name__ == "__main__":
    main()
