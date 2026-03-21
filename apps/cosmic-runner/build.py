#!/usr/bin/env python3
"""
Build script for Cosmic Runner.

Bundles all JS and CSS into a single self-contained index.html file
for easy deployment to GitHub Pages or any static hosting.

Usage:
    python build.py

Output:
    dist/index.html  (single file, all JS/CSS inlined)

The bundled file still loads MP3 and JSON audio files from a sibling
'audio/' directory. Copy the album MP3s and JSON files there.
"""

import os
import re
import sys


def read_file(path):
    """Read a file and return its contents."""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def build():
    """Bundle all source files into a single HTML file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(base_dir, 'dist')
    os.makedirs(dist_dir, exist_ok=True)

    # Read the source HTML
    html = read_file(os.path.join(base_dir, 'index.html'))

    # Read and inline CSS
    css_path = os.path.join(base_dir, 'css', 'game.css')
    css_content = read_file(css_path)

    # Replace CSS link with inline style
    css_link = '<link rel="stylesheet" href="css/game.css">'
    html = html.replace(css_link, f'<style>\n{css_content}\n</style>')

    # Read all JS files in order
    js_files = [
        'js/background.js',
        'js/runner.js',
        'js/obstacles.js',
        'js/music-sync.js',
        'js/game.js',
        'js/player.js',
        'js/app.js',
    ]

    js_bundle = []
    for js_file in js_files:
        js_path = os.path.join(base_dir, js_file)
        content = read_file(js_path)
        # Remove Node.js module.exports blocks (not needed in browser bundle)
        # Use DOTALL to match nested braces (e.g., module.exports = { Foo };)
        content = re.sub(
            r"if\s*\(typeof module !== 'undefined' && module\.exports\)\s*\{.*?\}\s*\}",
            '',
            content,
            flags=re.DOTALL
        )
        js_bundle.append(f'// === {js_file} ===')
        js_bundle.append(content)

    js_combined = '\n'.join(js_bundle)

    # Replace individual script tags with single inline script block.
    # Find the first <script src="js/..."> and last one, replace that range.
    first_script = '  <script src="js/background.js"></script>'
    last_script = '  <script src="js/app.js"></script>'
    start_idx = html.find(first_script)
    end_idx = html.find(last_script)
    if start_idx >= 0 and end_idx >= 0:
        end_idx += len(last_script)
        html = html[:start_idx] + f'<script>\n{js_combined}\n</script>' + html[end_idx:]

    # Write the bundled file
    output_path = os.path.join(dist_dir, 'index.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    size_kb = os.path.getsize(output_path) / 1024
    print(f'Built: {output_path} ({size_kb:.1f} KB)')
    print(f'Inlined: {len(js_files)} JS files + 1 CSS file')
    print()
    print('Deployment:')
    print('  1. Copy dist/index.html to your GitHub Pages directory')
    print('  2. Copy audio/ folder (MP3s + album_notes.json) alongside it')
    print('  3. Push to GitHub Pages branch')

    return 0


if __name__ == '__main__':
    sys.exit(build())
