/**
 * Shared Playwright fixtures for inthebeginning bounce E2E tests.
 *
 * Provides: game page fixture, static file server, audio capture helpers,
 * and spectral analysis utilities.
 */

import { test as base, expect } from '@playwright/test';
import { execSync, spawn } from 'child_process';
import { existsSync, readFileSync, mkdirSync, writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = join(__dirname, '..', '..');
const TOOLS_DIR = join(PROJECT_ROOT, 'tools');
const SHOTS_DIR = join(PROJECT_ROOT, 'test_screenshots');
mkdirSync(SHOTS_DIR, { recursive: true });

// ──── Static File Server ────

let serverProcess = null;
let serverPort = 8080;

function startServer() {
  if (serverProcess) return;
  // Serve from deploy/ so relative paths (../../shared/audio/) work correctly
  serverProcess = spawn('python3', [
    '-m', 'http.server', String(serverPort),
    '--directory', join(PROJECT_ROOT, 'deploy'),
    '--bind', '127.0.0.1',
  ], { stdio: 'ignore', detached: false });
  // Give server time to start
  execSync('sleep 1');
}

function stopServer() {
  if (serverProcess) {
    serverProcess.kill();
    serverProcess = null;
  }
}

// ──── PulseAudio Audio Sink ────

function startAudioSink() {
  try {
    execSync(`bash ${join(TOOLS_DIR, 'audio-sink.sh')} --start`, { stdio: 'pipe' });
  } catch (e) {
    console.warn('[fixtures] Audio sink start failed:', e.message);
  }
}

function stopAudioSink() {
  try {
    execSync(`bash ${join(TOOLS_DIR, 'audio-sink.sh')} --stop`, { stdio: 'pipe' });
  } catch (e) {
    // Ignore cleanup errors
  }
}

// ──── Audio Capture + Analysis ────

/**
 * Capture audio from PulseAudio monitor source for the given duration.
 * Returns a WAV file path.
 */
function captureAudio(durationSec = 3, label = 'capture') {
  const outFile = join(SHOTS_DIR, `audio_${label}_${Date.now()}.wav`);
  try {
    execSync(
      `bash ${join(TOOLS_DIR, 'audio-sink.sh')} --capture ${durationSec} ${outFile}`,
      { stdio: 'pipe', timeout: (durationSec + 5) * 1000 }
    );
  } catch (e) {
    console.warn('[fixtures] Audio capture failed:', e.message);
  }
  return outFile;
}

/**
 * Analyze a captured WAV file for audio content.
 * Returns { rms, peak, hasAudio, frames, sampleRate }.
 */
function analyzeAudio(wavPath) {
  if (!existsSync(wavPath)) {
    return { rms: 0, peak: 0, hasAudio: false, frames: 0, sampleRate: 0, error: 'File not found' };
  }
  try {
    const result = execSync(`python3 -c "
import wave, struct, math, json, sys
try:
    f = wave.open('${wavPath}')
    n = f.getnframes()
    ch = f.getnchannels()
    rate = f.getframerate()
    data = f.readframes(n)
    f.close()
    if n == 0:
        print(json.dumps({'rms':0,'peak':0,'hasAudio':False,'frames':0,'sampleRate':rate}))
        sys.exit(0)
    samples = struct.unpack(f'<{n*ch}h', data)
    # Take left channel only for analysis
    left = samples[::ch] if ch > 1 else samples
    fvals = [s / 32768.0 for s in left]
    rms = math.sqrt(sum(v*v for v in fvals) / len(fvals))
    peak = max(abs(v) for v in fvals)
    # Basic spectral analysis: count zero crossings (rough frequency estimate)
    crossings = sum(1 for i in range(1, len(fvals)) if fvals[i-1] * fvals[i] < 0)
    est_freq = crossings * rate / (2 * len(fvals)) if len(fvals) > 1 else 0
    print(json.dumps({
        'rms': round(rms, 6),
        'peak': round(peak, 6),
        'hasAudio': rms > 0.001,
        'frames': n,
        'sampleRate': rate,
        'estFreq': round(est_freq, 1),
        'zeroCrossings': crossings,
    }))
except Exception as e:
    print(json.dumps({'rms':0,'peak':0,'hasAudio':False,'frames':0,'sampleRate':0,'error':str(e)}))
"`, { encoding: 'utf-8', timeout: 10000 }).trim();
    return JSON.parse(result);
  } catch (e) {
    return { rms: 0, peak: 0, hasAudio: false, frames: 0, sampleRate: 0, error: e.message };
  }
}

// ──── Game Page Helpers ────

const GAME_PATH = '/v11/inthebeginning-bounce/index.html';
const VIZ_PATH = '/v5/visualizer/index.html';

/**
 * Start the game in a specific sound mode and display mode.
 * Waits for the main screen to be active.
 */
async function startGame(page, { soundMode = 'mp3', displayMode = 'game', players = 1 } = {}) {
  await page.goto(GAME_PATH);
  await page.waitForTimeout(800);

  // Select sound mode
  await page.selectOption('#sound-mode-select', soundMode);
  await page.waitForTimeout(200);

  // Select display mode on title screen
  if (displayMode === 'player') {
    await page.click('#mode-player');
  } else if (displayMode === 'grid') {
    await page.click('#mode-grid');
  }
  // 'game' is default, no click needed

  // Select player count
  if (players === 2) {
    await page.click('.player-count-btn[data-players="2"]');
  }

  await page.waitForTimeout(200);

  // Click start
  await page.click('#start-btn');
  await page.waitForTimeout(2000);
}

/**
 * Get game state from window._app or DOM inspection.
 */
async function getGameState(page) {
  return page.evaluate(() => {
    // The app stores itself; find it via DOM or global
    const body = document.body;
    const canvas = document.getElementById('main-canvas');
    const score = document.getElementById('hud-score');
    const track = document.getElementById('hud-track');
    const epoch = document.getElementById('hud-epoch');
    const time = document.getElementById('music-time');
    const title = document.getElementById('id3-title');
    const seek = document.getElementById('music-seek');

    return {
      bodyClass: body.className,
      hasCanvas: !!canvas,
      canvasWidth: canvas?.width || 0,
      canvasHeight: canvas?.height || 0,
      score: score?.textContent || '',
      track: track?.textContent || '',
      epoch: epoch?.textContent || '',
      time: time?.textContent || '',
      title: title?.textContent || '',
      seekValue: seek?.value || '0',
      seekMax: seek?.max || '0',
      titleScreenActive: document.getElementById('title-screen')?.classList.contains('active'),
      mainScreenActive: document.getElementById('main-screen')?.classList.contains('active') ||
        window.getComputedStyle(document.getElementById('main-screen') || document.body).display !== 'none',
    };
  });
}

/**
 * Check if canvas has non-blank content (more than 2 unique colors).
 */
async function canvasHasContent(page) {
  return page.evaluate(() => {
    const canvas = document.getElementById('main-canvas');
    if (!canvas) return false;
    const ctx = canvas.getContext('2d');
    const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
    const colors = new Set();
    for (let i = 0; i < data.length; i += 16) {
      colors.add(`${data[i]},${data[i+1]},${data[i+2]}`);
      if (colors.size > 5) return true;
    }
    return colors.size > 2;
  });
}

/**
 * Collect JS errors from the page.
 */
function collectJsErrors(page) {
  const errors = [];
  page.on('pageerror', e => errors.push(`PAGE: ${e.message}`));
  page.on('console', m => {
    if (m.type() === 'error') errors.push(`CONSOLE: ${m.text()}`);
  });
  return errors;
}

// ──── Export Custom Test Fixture ────

export const test = base.extend({
  gamePage: async ({ page }, use) => {
    startServer();
    const errors = collectJsErrors(page);
    page._jsErrors = errors;
    await use(page);
  },
});

export {
  expect,
  startGame,
  getGameState,
  canvasHasContent,
  collectJsErrors,
  startServer,
  stopServer,
  startAudioSink,
  stopAudioSink,
  captureAudio,
  analyzeAudio,
  GAME_PATH,
  VIZ_PATH,
  SHOTS_DIR,
  PROJECT_ROOT,
};
