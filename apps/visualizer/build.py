#!/usr/bin/env python3
"""
Build script for In The Beginning Visualizer — GitHub Pages deployment.

Produces a self-contained dist/ directory with all assets:
- Single-page HTML (all JS/CSS inline or linked)
- Audio assets (MP3s, note JSONs, album index)
- MIDI catalog and MIDI files (optional)
- Web Worker (synth-worker.js must remain a separate file)

Usage:
    python build.py                    # Build with auto-detected assets
    python build.py --mp3-dir ../cosmic-runner-v3/audio
    python build.py --midi-dir ../cosmic-runner-v3/midi
    python build.py --no-midi          # Skip MIDI files (smaller build)
    python build.py --no-mp3           # Skip MP3 files (synth-only build)

Output: dist/
"""

import argparse
import json
import os
import shutil
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def find_assets():
    """Auto-detect asset directories."""
    v3_audio = os.path.join(SCRIPT_DIR, '..', 'cosmic-runner-v3', 'audio')
    v2_audio = os.path.join(SCRIPT_DIR, '..', 'cosmic-runner-v2', 'audio')
    v3_midi = os.path.join(SCRIPT_DIR, '..', 'cosmic-runner-v3', 'midi')
    midi_lib = os.path.join(SCRIPT_DIR, '..', 'audio', 'midi_library')

    mp3_dir = None
    if os.path.isdir(v3_audio):
        mp3_dir = v3_audio
    elif os.path.isdir(v2_audio):
        mp3_dir = v2_audio

    midi_dir = None
    if os.path.isdir(v3_midi):
        midi_dir = v3_midi
    elif os.path.isdir(midi_lib):
        midi_dir = midi_lib

    return mp3_dir, midi_dir


def build(args):
    dist = os.path.join(SCRIPT_DIR, 'dist')
    if os.path.exists(dist):
        shutil.rmtree(dist)
    os.makedirs(dist)

    # Copy HTML
    shutil.copy2(os.path.join(SCRIPT_DIR, 'index.html'), dist)

    # Copy CSS
    css_dir = os.path.join(dist, 'css')
    os.makedirs(css_dir, exist_ok=True)
    shutil.copy2(os.path.join(SCRIPT_DIR, 'css', 'visualizer.css'), css_dir)

    # Copy JS
    js_dir = os.path.join(dist, 'js')
    os.makedirs(js_dir, exist_ok=True)
    for f in os.listdir(os.path.join(SCRIPT_DIR, 'js')):
        if f.endswith('.js'):
            shutil.copy2(os.path.join(SCRIPT_DIR, 'js', f), js_dir)

    # Copy version.json
    ver_file = os.path.join(SCRIPT_DIR, 'version.json')
    if os.path.exists(ver_file):
        shutil.copy2(ver_file, dist)

    mp3_dir, midi_dir = find_assets()
    if args.mp3_dir:
        mp3_dir = args.mp3_dir
    if args.midi_dir:
        midi_dir = args.midi_dir

    copied_mp3 = 0
    copied_midi = 0
    copied_json = 0

    # Copy MP3 assets
    if not args.no_mp3 and mp3_dir and os.path.isdir(mp3_dir):
        audio_dist = os.path.join(dist, 'audio')
        os.makedirs(audio_dist, exist_ok=True)
        for f in sorted(os.listdir(mp3_dir)):
            src = os.path.join(mp3_dir, f)
            if not os.path.isfile(src):
                continue
            if f.endswith('.mp3'):
                shutil.copy2(src, audio_dist)
                copied_mp3 += 1
            elif f.endswith('.json'):
                shutil.copy2(src, audio_dist)
                copied_json += 1
        print(f"  MP3 assets: {copied_mp3} MP3s, {copied_json} JSONs from {mp3_dir}")
    else:
        print("  MP3 assets: skipped")

    # Copy MIDI catalog and files
    if not args.no_midi and midi_dir and os.path.isdir(midi_dir):
        midi_dist = os.path.join(dist, 'midi')
        os.makedirs(midi_dist, exist_ok=True)

        # Copy catalog
        catalog_src = os.path.join(midi_dir, 'midi_catalog.json')
        if os.path.exists(catalog_src):
            shutil.copy2(catalog_src, midi_dist)
        else:
            # Look in audio dir
            for d in [mp3_dir, midi_dir]:
                if d:
                    alt = os.path.join(d, 'midi_catalog.json')
                    if os.path.exists(alt):
                        shutil.copy2(alt, midi_dist)
                        break

        # Copy MIDI files (walk recursively)
        for dirpath, dirnames, filenames in os.walk(midi_dir):
            for f in filenames:
                if f.endswith('.mid') or f.endswith('.midi'):
                    src = os.path.join(dirpath, f)
                    rel = os.path.relpath(src, midi_dir)
                    dst = os.path.join(midi_dist, rel)
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copy2(src, dst)
                    copied_midi += 1

        print(f"  MIDI assets: {copied_midi} files from {midi_dir}")
    else:
        print("  MIDI assets: skipped")

    # Scores directory (for manually loaded scores)
    scores_src = os.path.join(SCRIPT_DIR, 'scores')
    if os.path.isdir(scores_src):
        shutil.copytree(scores_src, os.path.join(dist, 'scores'))
        print(f"  Scores: copied")

    # Summary
    total_size = 0
    for dirpath, _, filenames in os.walk(dist):
        for f in filenames:
            total_size += os.path.getsize(os.path.join(dirpath, f))

    print(f"\nBuild complete: {dist}")
    print(f"  Total size: {total_size / (1024*1024):.1f} MB")
    print(f"  Files: HTML + {len(os.listdir(js_dir))} JS + {copied_mp3} MP3 + {copied_midi} MIDI")
    print(f"\nDeploy: copy dist/ contents to your GitHub Pages repo.")


def main():
    parser = argparse.ArgumentParser(description='Build Visualizer for GitHub Pages')
    parser.add_argument('--mp3-dir', help='Path to MP3 audio directory')
    parser.add_argument('--midi-dir', help='Path to MIDI files directory')
    parser.add_argument('--no-mp3', action='store_true', help='Skip MP3 files')
    parser.add_argument('--no-midi', action='store_true', help='Skip MIDI files')
    args = parser.parse_args()
    build(args)


if __name__ == '__main__':
    main()
