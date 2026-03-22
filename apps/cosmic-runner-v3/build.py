#!/usr/bin/env python3
"""Build script for Cosmic Runner V3.

Bundles all JS and CSS into a single self-contained index.html file
for easy deployment to GitHub Pages or any static hosting.

Also organizes MIDI library files for web access when --with-midi is used.

Usage:
    python build.py              # Bundle HTML only
    python build.py --with-midi  # Bundle HTML + copy MIDI library
    python build.py --full       # Bundle HTML + MIDI + verify all assets

Output:
    dist/index.html     (single file, all JS/CSS inlined)
    dist/audio/          (album MP3s + JSON note files)
    dist/midi/           (MIDI library organized by composer, if --with-midi)
"""

import json
import os
import re
import shutil
import sys


def read_file(path):
    """Read a file and return its contents."""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def build_html(base_dir, dist_dir):
    """Bundle all source files into a single HTML file."""
    html = read_file(os.path.join(base_dir, 'index.html'))

    # Read and inline CSS
    css_path = os.path.join(base_dir, 'css', 'styles.css')
    css_content = read_file(css_path)

    css_link = '<link rel="stylesheet" href="css/styles.css">'
    html = html.replace(css_link, f'<style>\n{css_content}\n</style>')

    # JS files in dependency order
    js_files = [
        'js/config.js',
        'js/themes.js',
        'js/background.js',
        'js/runner.js',
        'js/obstacles.js',
        'js/blast-effect.js',
        'js/characters.js',
        'js/renderer3d.js',
        'js/music-sync.js',
        'js/game.js',
        'js/player.js',
        'js/midi-player.js',
        'js/app.js',
    ]

    js_bundle = []
    inlined_count = 0
    for js_file in js_files:
        js_path = os.path.join(base_dir, js_file)
        if not os.path.exists(js_path):
            print(f'  Warning: {js_file} not found, skipping')
            continue
        content = read_file(js_path)
        # Remove Node.js module.exports blocks
        content = re.sub(
            r"if\s*\(typeof module !== 'undefined' && module\.exports\)\s*\{[^}]*\}",
            '',
            content,
            flags=re.DOTALL
        )
        js_bundle.append(f'// === {js_file} ===')
        js_bundle.append(content)
        inlined_count += 1

    js_combined = '\n'.join(js_bundle)

    # Replace individual script tags with single inline script block
    first_script = '  <script src="js/config.js"></script>'
    last_script = '  <script src="js/app.js"></script>'
    start_idx = html.find(first_script)
    end_idx = html.find(last_script)
    if start_idx >= 0 and end_idx >= 0:
        end_idx += len(last_script)
        html = html[:start_idx] + f'<script>\n{js_combined}\n</script>' + html[end_idx:]

    output_path = os.path.join(dist_dir, 'index.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    size_kb = os.path.getsize(output_path) / 1024
    print(f'Built: dist/index.html ({size_kb:.1f} KB, {inlined_count} JS files + 1 CSS inlined)')
    return output_path


def copy_audio(base_dir, dist_dir):
    """Copy album audio files (MP3s + JSON) to dist/audio/."""
    src_audio = os.path.join(base_dir, 'audio')
    dst_audio = os.path.join(dist_dir, 'audio')
    os.makedirs(dst_audio, exist_ok=True)

    copied = 0
    for f in sorted(os.listdir(src_audio)):
        if f.endswith('.mp3') or f.endswith('.json'):
            shutil.copy2(os.path.join(src_audio, f), os.path.join(dst_audio, f))
            copied += 1

    print(f'Copied: {copied} audio files to dist/audio/')
    return copied


def copy_midi_library(base_dir, dist_dir):
    """Copy MIDI library to dist/midi/ for web access."""
    # Find the MIDI library relative to project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    midi_src = os.path.join(project_root, 'apps', 'audio', 'midi_library')

    if not os.path.isdir(midi_src):
        print(f'Warning: MIDI library not found at {midi_src}')
        return 0

    dst_midi = os.path.join(dist_dir, 'midi')
    os.makedirs(dst_midi, exist_ok=True)

    copied = 0
    for dirpath, dirnames, filenames in os.walk(midi_src):
        # Skip hidden dirs
        dirnames[:] = [d for d in dirnames if not d.startswith('.')]

        for f in sorted(filenames):
            if f.endswith('.mid') or f.endswith('.midi'):
                rel = os.path.relpath(dirpath, midi_src)
                dst_subdir = os.path.join(dst_midi, rel)
                os.makedirs(dst_subdir, exist_ok=True)
                shutil.copy2(os.path.join(dirpath, f), os.path.join(dst_subdir, f))
                copied += 1

    # Copy ATTRIBUTION.md
    attr_src = os.path.join(midi_src, 'ATTRIBUTION.md')
    if os.path.exists(attr_src):
        shutil.copy2(attr_src, os.path.join(dst_midi, 'ATTRIBUTION.md'))

    # Copy midi_catalog.json if it exists in audio/
    catalog_src = os.path.join(base_dir, 'audio', 'midi_catalog.json')
    if os.path.exists(catalog_src):
        shutil.copy2(catalog_src, os.path.join(dst_midi, 'midi_catalog.json'))
        # Also keep in dist/audio/ for the app
        shutil.copy2(catalog_src, os.path.join(dist_dir, 'audio', 'midi_catalog.json'))

    print(f'Copied: {copied} MIDI files to dist/midi/')
    return copied


def verify_assets(dist_dir):
    """Verify all required assets are present."""
    errors = []
    audio_dir = os.path.join(dist_dir, 'audio')

    # Check album_notes.json
    album_path = os.path.join(audio_dir, 'album_notes.json')
    if not os.path.exists(album_path):
        errors.append('Missing: audio/album_notes.json')
    else:
        with open(album_path) as f:
            album = json.load(f)
        for track in album.get('tracks', []):
            mp3 = os.path.join(audio_dir, track['audio_file'])
            if not os.path.exists(mp3):
                errors.append(f'Missing MP3: {track["audio_file"]}')
            notes = os.path.join(audio_dir, track['file'])
            if not os.path.exists(notes):
                errors.append(f'Missing notes: {track["file"]}')

    # Check index.html
    if not os.path.exists(os.path.join(dist_dir, 'index.html')):
        errors.append('Missing: index.html')

    if errors:
        print('\nVerification FAILED:')
        for e in errors:
            print(f'  - {e}')
        return False
    else:
        print('\nVerification OK: all required assets present')
        return True


def build():
    """Main build entry point."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(base_dir, 'dist')

    with_midi = '--with-midi' in sys.argv or '--full' in sys.argv
    full_verify = '--full' in sys.argv

    # Clean dist
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    os.makedirs(dist_dir, exist_ok=True)

    print('=== Cosmic Runner V3 Build ===\n')

    # Bundle HTML
    build_html(base_dir, dist_dir)

    # Copy audio
    copy_audio(base_dir, dist_dir)

    # Copy MIDI library
    if with_midi:
        copy_midi_library(base_dir, dist_dir)
    else:
        print('Skipping MIDI library (use --with-midi to include)')

    # Verify
    if full_verify:
        ok = verify_assets(dist_dir)
        if not ok:
            return 1

    print('\n=== Deployment Instructions ===')
    print()
    print('To deploy to GitHub Pages:')
    print('  1. Copy dist/ contents to your GitHub Pages repo')
    print('  2. Structure:')
    print('       your-pages-repo/')
    print('         cosmic-runner/')
    print('           index.html')
    print('           audio/')
    print('             album_notes.json + *.mp3 + *_notes_v3.json')
    if with_midi:
        print('           midi/')
        print('             Bach/ Beethoven/ ... (MIDI files by composer)')
        print('             midi_catalog.json')
        print('             ATTRIBUTION.md')
    print('  3. Add .nojekyll file to repo root')
    print('  4. Push to main branch')
    print()
    print('See DEPLOY.md for detailed instructions.')

    return 0


if __name__ == '__main__':
    sys.exit(build())
