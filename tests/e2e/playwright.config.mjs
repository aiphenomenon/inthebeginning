/**
 * Playwright configuration for inthebeginning bounce E2E tests.
 *
 * Tests run against the deploy/v11/ static file server, which has the latest
 * game code plus shared audio assets at the correct relative paths.
 *
 * Audio capture requires:
 *   1. PulseAudio virtual sink: bash tools/audio-sink.sh --start
 *   2. Xvfb display for headful mode (set DISPLAY=:99 and E2E_AUDIO=1)
 *
 * Headless mode (default): all tests pass except audio capture (browser
 * doesn't output real audio in headless).
 *
 * Headful mode (E2E_AUDIO=1): real audio captured from PulseAudio monitor.
 * Requires Xvfb: Xvfb :99 -screen 0 1280x720x24 & export DISPLAY=:99
 */

import { defineConfig } from '@playwright/test';
import { execSync } from 'child_process';

// Discover PulseAudio socket path for Chromium audio routing.
let pulseServer = process.env.PULSE_SERVER || '';
if (!pulseServer) {
  try {
    const info = execSync('pactl info 2>/dev/null', { encoding: 'utf-8' });
    const match = info.match(/Server String:\s*(.+)/);
    if (match) pulseServer = match[1].trim();
  } catch (e) { /* PulseAudio may not be running */ }
}

// Headful mode for real audio output: set E2E_AUDIO=1 and DISPLAY=:99
const wantAudio = process.env.E2E_AUDIO === '1';
const hasDisplay = !!process.env.DISPLAY;
const useHeadful = wantAudio && hasDisplay;

export default defineConfig({
  testDir: '.',
  testMatch: '*.spec.mjs',
  timeout: 45_000,
  retries: 0,
  workers: 1,  // Sequential — audio capture and game state are shared resources

  use: {
    baseURL: 'http://localhost:8080',
    viewport: { width: 1280, height: 720 },
    screenshot: 'on',
    video: 'off',
    trace: 'off',
    headless: !useHeadful,
    launchOptions: {
      args: [
        '--no-sandbox',
        '--disable-gpu',
        '--autoplay-policy=no-user-gesture-required',
        '--disable-web-security',
      ],
      env: {
        ...process.env,
        ...(pulseServer ? { PULSE_SERVER: pulseServer } : {}),
      },
    },
  },

  outputDir: '../../test_screenshots/e2e-results',

  reporter: [
    ['list'],
    ['json', { outputFile: '../../test_screenshots/e2e-results/results.json' }],
    ['html', { open: 'never', outputFolder: '../../test_screenshots/e2e-report' }],
  ],
});
