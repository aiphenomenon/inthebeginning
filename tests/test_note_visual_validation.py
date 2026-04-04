"""Playwright visual validation of note data rendering.

Serves the v11 game, loads MP3 mode, seeks to multiple positions across
tracks, and screenshots the grid to verify note visualization is present
at beginning, middle, and end of tracks.

Run: python3 tests/test_note_visual_validation.py
"""

import json
import os
import subprocess
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME_DIR = os.path.join(PROJECT_ROOT, 'deploy', 'v11', 'inthebeginning-bounce')
SCREENSHOT_DIR = os.path.join(PROJECT_ROOT, 'test_screenshots', 'v43')
ALBUM_JSON = os.path.join(GAME_DIR, 'audio', 'album.json')

# Test 4 representative tracks at 5 positions each
TEST_TRACKS = [1, 4, 8, 12]  # beginning, mid-early, mid-late, end
POSITIONS_PER_TRACK = 5  # 0%, 25%, 50%, 75%, 90% of duration


def main():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    # Load album metadata
    album = json.load(open(ALBUM_JSON))
    tracks = {t['track_num']: t for t in album['tracks']}

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright not available as Python module, using npx")
        # Fall back to npx approach
        run_with_npx(tracks)
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1280, 'height': 720})

        for track_num in TEST_TRACKS:
            track = tracks[track_num]
            duration = track['duration']
            title = track['title']
            print(f"\n=== Track {track_num}: {title} ({duration:.0f}s) ===")

            for pct_idx, pct in enumerate([0.05, 0.25, 0.50, 0.75, 0.90]):
                seek_time = duration * pct
                print(f"  Seeking to {seek_time:.0f}s ({pct:.0%})...")

                # Load game fresh for each position
                page.goto('http://localhost:8765/index.html')
                page.wait_for_load_state('networkidle')
                time.sleep(1)

                # Start game in MP3 mode, grid display
                page.evaluate(f"""() => {{
                    // Click through to start
                    if (window.app && window.app.startGame) {{
                        window.app.startGame('mp3', 'grid');
                    }}
                }}""")
                time.sleep(2)

                # Seek to position and wait for rendering
                page.evaluate(f"""() => {{
                    if (window.app && window.app.musicSync) {{
                        // Set track and seek
                        const audio = document.querySelector('audio');
                        if (audio) {{
                            audio.currentTime = {seek_time};
                        }}
                    }}
                    // Try alternative seek methods
                    if (window.app && window.app.seekTo) {{
                        window.app.seekTo({seek_time});
                    }}
                }}""")
                time.sleep(1.5)

                fname = f"track{track_num:02d}-{title}-{int(pct*100)}pct.png"
                path = os.path.join(SCREENSHOT_DIR, fname)
                page.screenshot(path=path)
                size = os.path.getsize(path)
                print(f"    Screenshot: {fname} ({size/1024:.1f} KB)")

        browser.close()

    print(f"\n=== Screenshots saved to {SCREENSHOT_DIR}/ ===")
    print(f"Total: {len(TEST_TRACKS) * POSITIONS_PER_TRACK} screenshots")


def run_with_npx(tracks):
    """Fallback using npx playwright for screenshot capture."""
    # Write a JS script for playwright to execute
    js_path = os.path.join(PROJECT_ROOT, 'tests', '_note_visual_test.js')
    screenshots = []

    for track_num in TEST_TRACKS:
        track = tracks[track_num]
        duration = track['duration']
        title = track['title']

        for pct in [0.05, 0.25, 0.50, 0.75, 0.90]:
            seek_time = duration * pct
            fname = f"track{track_num:02d}-{title}-{int(pct*100)}pct.png"
            screenshots.append({
                'track': track_num,
                'title': title,
                'seekTime': seek_time,
                'pct': pct,
                'filename': fname,
            })

    script = """
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  const screenshots = SCREENSHOTS_PLACEHOLDER;
  const outDir = 'OUT_DIR_PLACEHOLDER';

  for (const shot of screenshots) {
    console.log(`Track ${shot.track} (${shot.title}): seeking to ${shot.seekTime.toFixed(0)}s (${(shot.pct*100).toFixed(0)}%)...`);

    await page.goto('http://localhost:8765/index.html');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1500);

    // Try to start game
    await page.evaluate(() => {
      if (window.app && window.app.startGame) {
        window.app.startGame('mp3', 'grid');
      }
    });
    await page.waitForTimeout(2000);

    // Seek
    await page.evaluate((seekTime) => {
      const audio = document.querySelector('audio');
      if (audio) audio.currentTime = seekTime;
      if (window.app && window.app.seekTo) window.app.seekTo(seekTime);
    }, shot.seekTime);
    await page.waitForTimeout(1500);

    await page.screenshot({ path: outDir + '/' + shot.filename });
    console.log(`  -> ${shot.filename}`);
  }

  await browser.close();
  console.log(`\\nDone: ${screenshots.length} screenshots`);
})();
""".replace('SCREENSHOTS_PLACEHOLDER', json.dumps(screenshots)).replace('OUT_DIR_PLACEHOLDER', SCREENSHOT_DIR)

    with open(js_path, 'w') as f:
        f.write(script)

    print(f"Running Playwright via node...")
    result = subprocess.run(
        ['node', js_path],
        capture_output=True, text=True, timeout=120
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr[:500])

    # Cleanup
    os.unlink(js_path)


if __name__ == '__main__':
    main()
