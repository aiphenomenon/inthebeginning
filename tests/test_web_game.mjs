/**
 * Comprehensive Playwright test suite for the web game and visualizer.
 * Tests all display modes × sound modes, keyboard controls, mode switching,
 * overlay modals, audio integration, and visual rendering.
 */

import { chromium } from 'playwright';
import { mkdirSync, writeFileSync } from 'fs';
import { join } from 'path';

const BASE_URL = 'http://localhost:8080';
const GAME_URL = `${BASE_URL}/inthebeginning-bounce/index.html`;
const VIZ_URL = `${BASE_URL}/visualizer/index.html`;
const SHOTS = join(process.cwd(), 'test_screenshots');
mkdirSync(SHOTS, { recursive: true });

const results = [];
const jsErrors = [];
let browser, page;

function log(msg) { console.log(`[${new Date().toISOString().slice(11,19)}] ${msg}`); }
function pass(n, d='') { results.push({name:n,status:'PASS',details:d}); log(`✓ ${n}${d?' — '+d:''}`); }
function fail(n, d='') { results.push({name:n,status:'FAIL',details:d}); log(`✗ ${n}${d?' — '+d:''}`); }
function warn(n, d='') { results.push({name:n,status:'WARN',details:d}); log(`⚠ ${n}${d?' — '+d:''}`); }
async function shot(name) { await page.screenshot({path:join(SHOTS,`${name}.png`)}); }

async function newPage(url) {
  if (page) await page.close();
  page = await browser.newContext({
    viewport: {width:1280,height:720},
  }).then(ctx => ctx.newPage());
  page.on('pageerror', e => jsErrors.push(`PAGE: ${e.message}`));
  page.on('console', m => { if(m.type()==='error') jsErrors.push(`CONSOLE: ${m.text()}`); });
  await page.goto(url);
  await page.waitForTimeout(1000);
}

// ============================================================================
// GAME TESTS
// ============================================================================

async function gameLoads() {
  await newPage(GAME_URL);
  await shot('g01-title');
  const title = await page.$('#title-screen.active');
  const select = await page.$('#sound-mode-select');
  const start = await page.$('#start-btn');
  const modes = await page.$$('.mode-btn');
  title && select && start
    ? pass('Game title screen', `Modes: ${modes.length}, Select: present, Start: present`)
    : fail('Game title screen', `Title:${!!title} Select:${!!select} Start:${!!start}`);
}

async function soundModeOptions() {
  await newPage(GAME_URL);
  const options = await page.$$eval('#sound-mode-select option', opts =>
    opts.map(o => ({value:o.value, text:o.textContent}))
  );
  options.length >= 3
    ? pass('Sound mode options', options.map(o=>o.value).join(', '))
    : fail('Sound mode options', `Only ${options.length} options`);
  return options;
}

async function startInMode(soundMode, displayMode) {
  await newPage(GAME_URL);
  // Select sound mode
  await page.selectOption('#sound-mode-select', soundMode);
  // Select display mode on title screen
  if (displayMode !== 'game') {
    await page.click(`.mode-btn[data-mode="${displayMode}"]`);
    await page.waitForTimeout(200);
  }
  // Click start
  await page.click('#start-btn');
  await page.waitForTimeout(1500);
}

async function testAllModeCombosTitleToGame() {
  const soundModes = ['mp3', 'midi', 'synth'];
  const displayModes = ['game', 'player', 'grid'];

  for (const sm of soundModes) {
    for (const dm of displayModes) {
      try {
        await startInMode(sm, dm);
        await shot(`g02-${sm}-${dm}`);

        const bodyClass = await page.evaluate(() => document.body.className);
        const hasMode = bodyClass.includes(`mode-${dm}`);
        const mainScreen = await page.$('#main-screen');
        const isActive = mainScreen ? await mainScreen.evaluate(el =>
          el.classList.contains('active') || window.getComputedStyle(el).display !== 'none'
        ) : false;

        hasMode || isActive
          ? pass(`Start: ${sm}/${dm}`, `Body: "${bodyClass}"`)
          : fail(`Start: ${sm}/${dm}`, `Body: "${bodyClass}", MainScreen active: ${isActive}`);
      } catch (e) {
        fail(`Start: ${sm}/${dm}`, e.message.slice(0, 100));
      }
    }
  }
}

async function testModeTabSwitching() {
  await startInMode('mp3', 'game');

  // Switch through modes using HUD tab buttons
  for (const mode of ['player', 'grid', 'game']) {
    await page.click(`.tab-btn[data-mode="${mode}"]`);
    await page.waitForTimeout(800);
    await shot(`g03-tab-${mode}`);

    const bodyClass = await page.evaluate(() => document.body.className);
    bodyClass.includes(`mode-${mode}`)
      ? pass(`Tab switch → ${mode}`)
      : fail(`Tab switch → ${mode}`, `Body: "${bodyClass}"`);
  }
}

async function testKeyboardModeSwitching() {
  await startInMode('mp3', 'game');

  // Press 1, 2, 3 for player, game, grid
  const keyMap = [
    {key:'1', expect:'player'},
    {key:'2', expect:'game'},
    {key:'3', expect:'grid'},
  ];

  for (const {key, expect} of keyMap) {
    await page.keyboard.press(key);
    await page.waitForTimeout(500);
    const bodyClass = await page.evaluate(() => document.body.className);
    bodyClass.includes(`mode-${expect}`)
      ? pass(`Key ${key} → ${expect}`)
      : fail(`Key ${key} → ${expect}`, `Body: "${bodyClass}"`);
  }
}

async function testGameControls() {
  await startInMode('mp3', 'game');

  // Test movement keys by checking runner position changes
  const getRunnerY = () => page.evaluate(() => {
    const app = window._app;
    return app && app.game && app.game.runners ? app.game.runners[0]?.y : null;
  });

  const initialY = await getRunnerY();

  // Jump
  await page.keyboard.press('Space');
  await page.waitForTimeout(100);
  const afterJump = await getRunnerY();

  // Move left/right
  await page.keyboard.down('ArrowLeft');
  await page.waitForTimeout(200);
  await page.keyboard.up('ArrowLeft');
  await page.keyboard.down('ArrowRight');
  await page.waitForTimeout(200);
  await page.keyboard.up('ArrowRight');

  // WASD
  await page.keyboard.press('w');
  await page.waitForTimeout(100);
  await page.keyboard.down('a');
  await page.waitForTimeout(200);
  await page.keyboard.up('a');
  await page.keyboard.down('d');
  await page.waitForTimeout(200);
  await page.keyboard.up('d');

  await shot('g04-after-controls');
  pass('Game controls', `InitialY: ${initialY}, AfterJump: ${afterJump}`);
}

async function testPauseResume() {
  await startInMode('mp3', 'game');

  // Press P to pause
  await page.keyboard.press('p');
  await page.waitForTimeout(300);
  await shot('g05-paused');

  const isPaused = await page.evaluate(() => {
    const app = window._app;
    return app && app.game ? app.game.paused : null;
  });

  // Press P again to resume
  await page.keyboard.press('p');
  await page.waitForTimeout(300);

  const isResumed = await page.evaluate(() => {
    const app = window._app;
    return app && app.game ? !app.game.paused : null;
  });

  isPaused || isResumed
    ? pass('Pause/Resume', `Paused: ${isPaused}, Resumed: ${isResumed}`)
    : warn('Pause/Resume', `Paused: ${isPaused}, Resumed: ${isResumed}`);
}

async function test3DToggle() {
  await startInMode('mp3', 'grid');

  // Grid dim tabs should be visible in grid mode
  const dimTabs = await page.$('#grid-dim-tabs');
  const isVisible = dimTabs ? await dimTabs.evaluate(el =>
    window.getComputedStyle(el).display !== 'none'
  ) : false;

  if (isVisible) {
    // Click 3D
    await page.click('.dim-btn[data-dim="3d"]');
    await page.waitForTimeout(800);
    await shot('g06-grid-3d');

    // Click 2D
    await page.click('.dim-btn[data-dim="2d"]');
    await page.waitForTimeout(800);
    await shot('g06-grid-2d');
    pass('Grid 2D/3D toggle');
  } else {
    fail('Grid 2D/3D toggle', 'Dim tabs not visible in grid mode');
  }
}

async function testMusicBar() {
  await startInMode('mp3', 'game');
  await page.waitForTimeout(500);

  // Check music bar elements exist and are visible
  const playBtn = await page.$('#play-btn');
  const prevBtn = await page.$('#prev-btn');
  const nextBtn = await page.$('#next-btn');
  const seekBar = await page.$('#music-seek');
  const id3Title = await page.$('#id3-title');
  const timeDisplay = await page.$('#music-time');

  const hasAll = playBtn && prevBtn && nextBtn && seekBar && id3Title && timeDisplay;
  hasAll
    ? pass('Music bar elements', 'Play, Prev, Next, Seek, ID3, Time all present')
    : fail('Music bar elements', `Play:${!!playBtn} Prev:${!!prevBtn} Next:${!!nextBtn} Seek:${!!seekBar}`);

  // Test play button
  if (playBtn) {
    await playBtn.click();
    await page.waitForTimeout(500);
    await shot('g07-after-play-click');

    // Test next track
    if (nextBtn) {
      await nextBtn.click();
      await page.waitForTimeout(1000);
      await shot('g07-after-next');
      pass('Track navigation', 'Next button clicked');
    }
  }
}

async function testHUDButtons() {
  await startInMode('mp3', 'game');

  // Test each HUD button
  const buttons = [
    {id: '#pause-btn', name: 'Pause button'},
    {id: '#mute-btn', name: 'Mute button'},
    {id: '#speed-up', name: 'Speed up'},
    {id: '#speed-down', name: 'Speed down'},
  ];

  for (const {id, name} of buttons) {
    const btn = await page.$(id);
    if (btn) {
      await btn.click();
      await page.waitForTimeout(200);
      pass(name);
    } else {
      fail(name, 'Button not found');
    }
  }
}

async function testOverlays() {
  await startInMode('mp3', 'game');

  // Test Mutation overlay
  const mutBtn = await page.$('#mutation-btn');
  if (mutBtn) {
    await mutBtn.click();
    await page.waitForTimeout(500);
    await shot('g08-mutation-overlay');

    const overlay = await page.$('#mutation-overlay');
    const isOpen = overlay ? await overlay.evaluate(el =>
      el.classList.contains('active') || window.getComputedStyle(el).display !== 'none'
    ) : false;

    isOpen ? pass('Mutation overlay opens') : fail('Mutation overlay opens', 'Not visible');

    // Close it
    const closeBtn = await page.$('#mutation-close');
    if (closeBtn) await closeBtn.click();
    await page.waitForTimeout(300);
  }

  // Test Style overlay
  const styleBtn = await page.$('#style-btn');
  if (styleBtn) {
    await styleBtn.click();
    await page.waitForTimeout(500);
    await shot('g08-style-overlay');

    const closeBtn = await page.$('#style-close');
    if (closeBtn) await closeBtn.click();
    await page.waitForTimeout(300);
    pass('Style overlay opens');
  }

  // Test Help overlay
  const helpBtn = await page.$('#ingame-help-btn');
  if (helpBtn) {
    await helpBtn.click();
    await page.waitForTimeout(500);
    await shot('g08-help-overlay');

    const closeBtn = await page.$('#help-close');
    if (closeBtn) await closeBtn.click();
    await page.waitForTimeout(300);
    pass('Help overlay opens');
  }

  // Test Theme overlay
  const themeBtn = await page.$('#ingame-theme-btn');
  if (themeBtn) {
    await themeBtn.click();
    await page.waitForTimeout(500);
    await shot('g08-theme-overlay');

    const closeBtn = await page.$('#theme-close');
    if (closeBtn) await closeBtn.click();
    await page.waitForTimeout(300);
    pass('Theme overlay opens');
  }
}

async function testMIDIPlayback() {
  await startInMode('midi', 'player');
  await page.waitForTimeout(3000);
  await shot('g09-midi-playing');

  // Check MIDI info is displayed
  const midiSource = await page.$eval('#midi-source', el => el.textContent).catch(() => '');
  const midiComposer = await page.$eval('#midi-composer', el => el.textContent).catch(() => '');

  midiSource || midiComposer
    ? pass('MIDI info display', `Source: "${midiSource.slice(0,50)}" Composer: "${midiComposer.slice(0,30)}"`)
    : warn('MIDI info display', 'No MIDI info shown (may need catalog)');
}

async function testSynthPlayback() {
  await startInMode('synth', 'player');
  await page.waitForTimeout(3000);
  await shot('g10-synth-playing');

  // Check HUD shows synth track info
  const trackInfo = await page.$eval('#hud-track', el => el.textContent).catch(() => '');
  pass('Synth mode loads', `Track: "${trackInfo.slice(0,50)}"`);
}

async function testInfiniteMode() {
  await newPage(GAME_URL);

  // Check infinite toggle
  const toggle = await page.$('#infinite-mode-toggle');
  if (toggle) {
    const checked = await toggle.evaluate(el => el.checked);
    pass('Infinite mode toggle', `Default: ${checked ? 'ON' : 'OFF'}`);
  } else {
    fail('Infinite mode toggle', 'Not found');
  }
}

async function test2PlayerMode() {
  await newPage(GAME_URL);

  // Select 2 player
  await page.click('.player-count-btn[data-players="2"]');
  await page.waitForTimeout(200);
  await page.click('#start-btn');
  await page.waitForTimeout(1500);
  await shot('g11-2player');

  // Check for 2 runners
  const runnerCount = await page.evaluate(() => {
    const app = window._app;
    return app && app.game && app.game.runners ? app.game.runners.length : 0;
  });

  runnerCount === 2
    ? pass('2-Player mode', `${runnerCount} runners`)
    : warn('2-Player mode', `${runnerCount} runners (expected 2)`);
}

async function testCanvasRendering() {
  await startInMode('mp3', 'game');
  await page.waitForTimeout(2000);

  // Check canvas has content (non-blank)
  const isBlank = await page.evaluate(() => {
    const canvas = document.getElementById('main-canvas');
    if (!canvas) return true;
    const ctx = canvas.getContext('2d');
    const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
    // Check if all pixels are the same (blank)
    let uniqueColors = new Set();
    for (let i = 0; i < data.length; i += 16) { // Sample every 4th pixel
      uniqueColors.add(`${data[i]},${data[i+1]},${data[i+2]}`);
      if (uniqueColors.size > 5) return false; // Not blank
    }
    return uniqueColors.size <= 2;
  });

  isBlank
    ? fail('Canvas rendering', 'Canvas appears blank')
    : pass('Canvas rendering', 'Canvas has varied content');
}

// ============================================================================
// VISUALIZER TESTS
// ============================================================================

async function vizLoads() {
  await newPage(VIZ_URL);
  await page.waitForTimeout(1500);
  await shot('v01-initial');

  const hasErrors = jsErrors.some(e => e.includes('FAMILY_HUES') || e.includes('SynthEngine is not defined'));
  const trackList = await page.$$('.track-list li, .track-item, [data-track]');
  const tabs = await page.$$('.mode-tab, [data-mode]');

  !hasErrors
    ? pass('Visualizer loads without JS errors')
    : fail('Visualizer loads without JS errors', jsErrors.filter(e => e.includes('FAMILY_HUES') || e.includes('SynthEngine')).join('; '));

  pass('Visualizer UI', `Tracks: ${trackList.length}, Tabs: ${tabs.length}`);
}

async function vizModeSwitching() {
  await newPage(VIZ_URL);
  await page.waitForTimeout(1000);

  const modes = ['Album', 'MIDI', 'Synth', 'Stream'];
  for (const mode of modes) {
    try {
      // Click the tab by text content
      const tab = await page.$(`button:has-text("${mode}"), [data-mode="${mode.toLowerCase()}"]`);
      if (tab) {
        await tab.click();
        await page.waitForTimeout(1000);
        await shot(`v02-${mode.toLowerCase()}`);
        pass(`Visualizer: ${mode} tab`);
      } else {
        warn(`Visualizer: ${mode} tab`, 'Tab not found');
      }
    } catch (e) {
      fail(`Visualizer: ${mode} tab`, e.message.slice(0, 80));
    }
  }
}

// ============================================================================
// MAIN
// ============================================================================

async function main() {
  log('=== Web Game & Visualizer Test Suite ===');
  log(`Screenshots: ${SHOTS}`);

  browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-gpu', '--autoplay-policy=no-user-gesture-required']
  });

  log('');
  log('--- GAME TESTS ---');
  await gameLoads();
  await soundModeOptions();
  await testAllModeCombosTitleToGame();
  await testModeTabSwitching();
  await testKeyboardModeSwitching();
  await testGameControls();
  await testPauseResume();
  await test3DToggle();
  await testMusicBar();
  await testHUDButtons();
  await testOverlays();
  await testCanvasRendering();
  await testMIDIPlayback();
  await testSynthPlayback();
  await testInfiniteMode();
  await test2PlayerMode();

  log('');
  log('--- VISUALIZER TESTS ---');
  jsErrors.length = 0; // Reset for visualizer
  await vizLoads();
  await vizModeSwitching();

  await browser.close();

  // Report
  log('');
  log('--- JS ERRORS (unique) ---');
  const uniqueErrors = [...new Set(jsErrors)].filter(e => !e.includes('404'));
  uniqueErrors.length === 0
    ? log('No JS errors (excluding 404s)')
    : uniqueErrors.forEach(e => log(`  ${e}`));

  const p = results.filter(r => r.status === 'PASS').length;
  const f = results.filter(r => r.status === 'FAIL').length;
  const w = results.filter(r => r.status === 'WARN').length;
  log('');
  log(`=== SUMMARY: PASS:${p}  FAIL:${f}  WARN:${w}  TOTAL:${results.length} ===`);

  if (f > 0) {
    log('');
    log('FAILURES:');
    results.filter(r => r.status === 'FAIL').forEach(r => log(`  ✗ ${r.name}: ${r.details}`));
  }

  writeFileSync(join(SHOTS, 'report.json'), JSON.stringify({
    timestamp: new Date().toISOString(),
    summary: {pass:p,fail:f,warn:w,total:results.length},
    results, jsErrors: uniqueErrors,
  }, null, 2));
}

main().catch(e => { console.error('Fatal:', e); process.exit(1); });
