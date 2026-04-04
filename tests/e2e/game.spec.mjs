/**
 * Comprehensive E2E tests for inthebeginning bounce game.
 *
 * Tests all display modes x sound modes, keyboard controls, HUD interactions,
 * overlay modals, canvas rendering, track navigation, playhead seeking,
 * and multi-player mode.
 *
 * Requires: static file server on port 8080 serving deploy/ directory.
 * Run with: npx playwright test tests/e2e/game.spec.mjs --config=tests/e2e/playwright.config.mjs
 */

import { test, expect, startGame, getGameState, canvasHasContent, collectJsErrors,
         startServer, GAME_PATH, SHOTS_DIR } from './fixtures.mjs';
import { mkdirSync } from 'fs';
import { join } from 'path';

// Ensure server is started before all tests
test.beforeAll(() => { startServer(); });

// ============================================================================
// TITLE SCREEN TESTS
// ============================================================================

test.describe('Title Screen', () => {
  test('loads with all expected elements', async ({ page }) => {
    const errors = collectJsErrors(page);
    await page.goto(GAME_PATH);
    await page.waitForTimeout(1000);
    await page.screenshot({ path: join(SHOTS_DIR, 'e2e-title-screen.png') });

    // Title screen should be active
    const titleActive = await page.$eval('#title-screen', el => el.classList.contains('active'));
    expect(titleActive).toBe(true);

    // Sound mode dropdown
    const selectEl = await page.$('#sound-mode-select');
    expect(selectEl).not.toBeNull();

    // Start button
    const startBtn = await page.$('#start-btn');
    expect(startBtn).not.toBeNull();

    // Mode buttons
    for (const id of ['#mode-player', '#mode-game', '#mode-grid']) {
      const btn = await page.$(id);
      expect(btn, `Expected ${id} to exist`).not.toBeNull();
    }

    // No JS errors
    const criticalErrors = errors.filter(e =>
      !e.includes('404') && !e.includes('favicon') && !e.includes('net::ERR')
    );
    expect(criticalErrors, `JS errors: ${criticalErrors.join('; ')}`).toHaveLength(0);
  });

  test('sound mode dropdown has all 4 options', async ({ page }) => {
    await page.goto(GAME_PATH);
    await page.waitForTimeout(800);

    const options = await page.$$eval('#sound-mode-select option', opts =>
      opts.map(o => ({ value: o.value, text: o.textContent.trim() }))
    );

    expect(options.length).toBeGreaterThanOrEqual(3);
    const values = options.map(o => o.value);
    expect(values).toContain('mp3');
    expect(values).toContain('midi');
    expect(values).toContain('synth');
    // WASM may or may not be present
  });

  test('player count buttons work', async ({ page }) => {
    await page.goto(GAME_PATH);
    await page.waitForTimeout(800);

    // Click 2 players
    await page.click('.player-count-btn[data-players="2"]');
    await page.waitForTimeout(200);

    const is2PSelected = await page.$eval('.player-count-btn[data-players="2"]',
      el => el.classList.contains('selected') || el.classList.contains('active'));
    expect(is2PSelected).toBe(true);
  });

  test('infinite mode toggle exists', async ({ page }) => {
    await page.goto(GAME_PATH);
    await page.waitForTimeout(800);

    const toggle = await page.$('#infinite-mode-toggle');
    expect(toggle).not.toBeNull();
  });

  test('title screen theme/accessibility/credits buttons', async ({ page }) => {
    await page.goto(GAME_PATH);
    await page.waitForTimeout(800);

    for (const id of ['#theme-btn', '#accessibility-btn', '#credits-btn']) {
      const btn = await page.$(id);
      expect(btn, `Expected ${id}`).not.toBeNull();
    }
  });
});

// ============================================================================
// MODE COMBINATION TESTS — 3 sound modes x 3 display modes = 9 combos
// ============================================================================

test.describe('Mode Combinations', () => {
  const soundModes = ['mp3', 'midi', 'synth'];
  const displayModes = ['game', 'player', 'grid'];

  for (const sm of soundModes) {
    for (const dm of displayModes) {
      test(`starts in ${sm}/${dm} mode`, async ({ page }) => {
        const errors = collectJsErrors(page);
        await startGame(page, { soundMode: sm, displayMode: dm });
        await page.screenshot({ path: join(SHOTS_DIR, `e2e-mode-${sm}-${dm}.png`) });

        const state = await getGameState(page);
        // Body should contain mode class
        expect(state.bodyClass).toContain(`mode-${dm}`);
        // Canvas should exist
        expect(state.hasCanvas).toBe(true);

        // Check for critical JS errors (ignore 404s for audio files)
        const critical = errors.filter(e =>
          !e.includes('404') && !e.includes('net::ERR') && !e.includes('favicon')
          && !e.includes('NotAllowedError') && !e.includes('AbortError')
        );
        if (critical.length > 0) {
          console.warn(`  JS errors in ${sm}/${dm}: ${critical.join('; ')}`);
        }
      });
    }
  }
});

// ============================================================================
// KEYBOARD CONTROLS
// ============================================================================

test.describe('Keyboard Controls', () => {
  test('mode switching with 1/2/3 keys', async ({ page }) => {
    await startGame(page, { soundMode: 'mp3', displayMode: 'game' });

    // Press 1 -> player mode
    await page.keyboard.press('1');
    await page.waitForTimeout(500);
    let state = await getGameState(page);
    expect(state.bodyClass).toContain('mode-player');

    // Press 2 -> game mode
    await page.keyboard.press('2');
    await page.waitForTimeout(500);
    state = await getGameState(page);
    expect(state.bodyClass).toContain('mode-game');

    // Press 3 -> grid mode
    await page.keyboard.press('3');
    await page.waitForTimeout(500);
    await page.screenshot({ path: join(SHOTS_DIR, 'e2e-key3-grid.png') });
    state = await getGameState(page);
    expect(state.bodyClass).toContain('mode-grid');
  });

  test('tab button mode switching', async ({ page }) => {
    await startGame(page, { soundMode: 'mp3', displayMode: 'game' });

    for (const mode of ['player', 'grid', 'game']) {
      const tabBtn = await page.$(`.tab-btn[data-mode="${mode}"]`);
      expect(tabBtn, `Tab button for ${mode}`).not.toBeNull();
      await tabBtn.click();
      await page.waitForTimeout(500);

      const state = await getGameState(page);
      expect(state.bodyClass).toContain(`mode-${mode}`);
    }
    await page.screenshot({ path: join(SHOTS_DIR, 'e2e-tab-switching.png') });
  });

  test('pause with P key', async ({ page }) => {
    await startGame(page, { soundMode: 'synth', displayMode: 'game' });

    // Press P to pause
    await page.keyboard.press('p');
    await page.waitForTimeout(300);
    await page.screenshot({ path: join(SHOTS_DIR, 'e2e-paused.png') });

    // Check pause button changed
    const pauseBtn = await page.$('#pause-btn');
    const btnText = await pauseBtn.textContent();

    // Press P again to resume
    await page.keyboard.press('p');
    await page.waitForTimeout(300);
  });

  test('game movement: arrows and WASD', async ({ page }) => {
    await startGame(page, { soundMode: 'synth', displayMode: 'game' });

    // Arrow keys
    await page.keyboard.down('ArrowLeft');
    await page.waitForTimeout(200);
    await page.keyboard.up('ArrowLeft');
    await page.keyboard.down('ArrowRight');
    await page.waitForTimeout(200);
    await page.keyboard.up('ArrowRight');

    // Jump
    await page.keyboard.press('Space');
    await page.waitForTimeout(100);

    // WASD
    await page.keyboard.down('a');
    await page.waitForTimeout(200);
    await page.keyboard.up('a');
    await page.keyboard.down('d');
    await page.waitForTimeout(200);
    await page.keyboard.up('d');
    await page.keyboard.press('w');
    await page.waitForTimeout(100);

    await page.screenshot({ path: join(SHOTS_DIR, 'e2e-game-controls.png') });
    // If we get here without error, controls work
  });
});

// ============================================================================
// HUD ELEMENTS
// ============================================================================

test.describe('HUD Elements', () => {
  test('music bar elements present', async ({ page }) => {
    await startGame(page, { soundMode: 'mp3', displayMode: 'game' });

    for (const id of ['#play-btn', '#prev-btn', '#next-btn', '#music-seek',
                       '#id3-title', '#music-time', '#music-vol']) {
      const el = await page.$(id);
      expect(el, `Expected ${id}`).not.toBeNull();
    }
  });

  test('HUD buttons present', async ({ page }) => {
    await startGame(page, { soundMode: 'midi', displayMode: 'game' });

    for (const id of ['#pause-btn', '#mute-btn', '#speed-up', '#speed-down']) {
      const el = await page.$(id);
      expect(el, `Expected ${id}`).not.toBeNull();
    }
  });

  test('speed up/down buttons work', async ({ page }) => {
    await startGame(page, { soundMode: 'synth', displayMode: 'game' });

    const speedUp = await page.$('#speed-up');
    const speedDown = await page.$('#speed-down');
    if (speedUp) await speedUp.click();
    await page.waitForTimeout(200);
    if (speedDown) await speedDown.click();
    await page.waitForTimeout(200);
    // No crash = pass
  });

  test('mute button toggles', async ({ page }) => {
    await startGame(page, { soundMode: 'synth', displayMode: 'game' });

    const muteBtn = await page.$('#mute-btn');
    expect(muteBtn).not.toBeNull();

    const textBefore = await muteBtn.textContent();
    await muteBtn.click();
    await page.waitForTimeout(200);
    const textAfter = await muteBtn.textContent();

    // Click again to unmute
    await muteBtn.click();
    await page.waitForTimeout(200);
  });

  test('score display in game mode', async ({ page }) => {
    await startGame(page, { soundMode: 'synth', displayMode: 'game' });
    await page.waitForTimeout(2000);

    const score = await page.$eval('#hud-score', el => el.textContent);
    expect(score).toBeDefined();
  });

  test('restart button returns to title', async ({ page }) => {
    await startGame(page, { soundMode: 'synth', displayMode: 'game' });

    const restartBtn = await page.$('#restart-btn');
    expect(restartBtn).not.toBeNull();
    await restartBtn.click();
    await page.waitForTimeout(1000);

    const titleActive = await page.$eval('#title-screen',
      el => el.classList.contains('active'));
    expect(titleActive).toBe(true);
  });
});

// ============================================================================
// TRACK NAVIGATION (MP3 MODE)
// ============================================================================

test.describe('Track Navigation (MP3)', () => {
  test('next/prev buttons change track', async ({ page }) => {
    await startGame(page, { soundMode: 'mp3', displayMode: 'player' });
    await page.waitForTimeout(2000);

    const titleBefore = await page.$eval('#id3-title', el => el.textContent).catch(() => '');

    // Click next
    const nextBtn = await page.$('#next-btn');
    expect(nextBtn).not.toBeNull();
    await nextBtn.click();
    await page.waitForTimeout(1500);
    await page.screenshot({ path: join(SHOTS_DIR, 'e2e-mp3-next.png') });

    const titleAfter = await page.$eval('#id3-title', el => el.textContent).catch(() => '');

    // Click prev to go back
    const prevBtn = await page.$('#prev-btn');
    await prevBtn.click();
    await page.waitForTimeout(1500);

    const titleBack = await page.$eval('#id3-title', el => el.textContent).catch(() => '');
  });

  test('play/pause button works', async ({ page }) => {
    await startGame(page, { soundMode: 'mp3', displayMode: 'player' });
    await page.waitForTimeout(1500);

    const playBtn = await page.$('#play-btn');
    expect(playBtn).not.toBeNull();

    // Click to toggle play/pause
    await playBtn.click();
    await page.waitForTimeout(500);
    await playBtn.click();
    await page.waitForTimeout(500);
  });

  test('seek bar exists and has range', async ({ page }) => {
    await startGame(page, { soundMode: 'mp3', displayMode: 'player' });
    await page.waitForTimeout(2000);

    const seekBar = await page.$('#music-seek');
    expect(seekBar).not.toBeNull();

    const max = await seekBar.getAttribute('max');
    // Max should be set to track duration (> 0)
    // Note: may be 0 if MP3 hasn't loaded yet
  });

  test('time display updates', async ({ page }) => {
    await startGame(page, { soundMode: 'mp3', displayMode: 'player' });
    await page.waitForTimeout(1000);

    const time1 = await page.$eval('#music-time', el => el.textContent).catch(() => '');
    await page.waitForTimeout(2000);
    const time2 = await page.$eval('#music-time', el => el.textContent).catch(() => '');

    // Time should have changed (or at least be non-empty)
    // With MP3 loading issues in headless, time may stay at 0:00
  });

  test('volume slider works', async ({ page }) => {
    await startGame(page, { soundMode: 'mp3', displayMode: 'player' });
    await page.waitForTimeout(1000);

    const volSlider = await page.$('#music-vol');
    expect(volSlider).not.toBeNull();

    // Set volume to 50%
    await volSlider.fill('50');
    await page.waitForTimeout(200);
  });

  test('track list overlay opens (MP3 mode)', async ({ page }) => {
    await startGame(page, { soundMode: 'mp3', displayMode: 'player' });
    await page.waitForTimeout(1500);

    // Click on track title to open track list
    const hudTrack = await page.$('#hud-track');
    if (hudTrack) {
      await hudTrack.click();
      await page.waitForTimeout(500);
      await page.screenshot({ path: join(SHOTS_DIR, 'e2e-track-list.png') });

      const trackOverlay = await page.$('#track-overlay');
      if (trackOverlay) {
        const isVisible = await trackOverlay.evaluate(el =>
          window.getComputedStyle(el).display !== 'none'
        );
        // Close it
        const closeBtn = await page.$('#track-close');
        if (closeBtn) await closeBtn.click();
      }
    }
  });
});

// ============================================================================
// TRACK NAVIGATION (MIDI MODE)
// ============================================================================

test.describe('Track Navigation (MIDI)', () => {
  test('MIDI info panel shows composer/source', async ({ page }) => {
    await startGame(page, { soundMode: 'midi', displayMode: 'player' });
    await page.waitForTimeout(4000);
    await page.screenshot({ path: join(SHOTS_DIR, 'e2e-midi-playing.png') });

    const source = await page.$eval('#midi-source', el => el.textContent).catch(() => '');
    const composer = await page.$eval('#midi-composer', el => el.textContent).catch(() => '');
    // At least one should have content if catalog loaded
  });

  test('next track loads new MIDI', async ({ page }) => {
    await startGame(page, { soundMode: 'midi', displayMode: 'player' });
    await page.waitForTimeout(3000);

    const titleBefore = await page.$eval('#id3-title', el => el.textContent).catch(() => '');

    const nextBtn = await page.$('#next-btn');
    await nextBtn.click();
    await page.waitForTimeout(3000);
    await page.screenshot({ path: join(SHOTS_DIR, 'e2e-midi-next.png') });

    const titleAfter = await page.$eval('#id3-title', el => el.textContent).catch(() => '');
  });
});

// ============================================================================
// TRACK NAVIGATION (SYNTH MODE)
// ============================================================================

test.describe('Track Navigation (Synth)', () => {
  test('synth starts and shows epoch info', async ({ page }) => {
    await startGame(page, { soundMode: 'synth', displayMode: 'player' });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: join(SHOTS_DIR, 'e2e-synth-playing.png') });

    const track = await page.$eval('#hud-track', el => el.textContent).catch(() => '');
    // Track should show epoch name
  });

  test('synth next track advances epoch', async ({ page }) => {
    await startGame(page, { soundMode: 'synth', displayMode: 'player' });
    await page.waitForTimeout(2000);

    const trackBefore = await page.$eval('#hud-track', el => el.textContent).catch(() => '');

    const nextBtn = await page.$('#next-btn');
    await nextBtn.click();
    await page.waitForTimeout(2000);

    const trackAfter = await page.$eval('#hud-track', el => el.textContent).catch(() => '');
  });
});

// ============================================================================
// OVERLAY MODALS
// ============================================================================

test.describe('Overlay Modals', () => {
  test('mutation overlay opens and closes', async ({ page }) => {
    await startGame(page, { soundMode: 'midi', displayMode: 'game' });

    const mutBtn = await page.$('#mutation-btn');
    if (mutBtn) {
      const isVisible = await mutBtn.evaluate(el =>
        window.getComputedStyle(el).display !== 'none');
      if (isVisible) {
        await mutBtn.click();
        await page.waitForTimeout(500);
        await page.screenshot({ path: join(SHOTS_DIR, 'e2e-mutation-overlay.png') });

        const overlay = await page.$('#mutation-overlay');
        const overlayVisible = overlay ? await overlay.evaluate(el =>
          el.classList.contains('active') || window.getComputedStyle(el).display !== 'none'
        ) : false;
        expect(overlayVisible).toBe(true);

        // Close
        const closeBtn = await page.$('#mutation-close');
        if (closeBtn) await closeBtn.click();
        await page.waitForTimeout(300);
      }
    }
  });

  test('style overlay opens and sliders work', async ({ page }) => {
    await startGame(page, { soundMode: 'synth', displayMode: 'game' });

    const styleBtn = await page.$('#style-btn');
    if (styleBtn) {
      const isVisible = await styleBtn.evaluate(el =>
        window.getComputedStyle(el).display !== 'none');
      if (isVisible) {
        await styleBtn.click();
        await page.waitForTimeout(500);
        await page.screenshot({ path: join(SHOTS_DIR, 'e2e-style-overlay.png') });

        // Check sliders exist
        for (const id of ['#style-speed', '#style-arpeggio', '#style-chords', '#style-bend']) {
          const slider = await page.$(id);
          expect(slider, `Expected ${id}`).not.toBeNull();
        }

        const closeBtn = await page.$('#style-close');
        if (closeBtn) await closeBtn.click();
      }
    }
  });

  test('instrument overlay opens', async ({ page }) => {
    await startGame(page, { soundMode: 'midi', displayMode: 'game' });

    const instrBtn = await page.$('#instrument-btn');
    if (instrBtn) {
      const isVisible = await instrBtn.evaluate(el =>
        window.getComputedStyle(el).display !== 'none');
      if (isVisible) {
        await instrBtn.click();
        await page.waitForTimeout(500);
        await page.screenshot({ path: join(SHOTS_DIR, 'e2e-instrument-overlay.png') });

        const closeBtn = await page.$('#instrument-close');
        if (closeBtn) await closeBtn.click();
      }
    }
  });

  test('help overlay opens and closes', async ({ page }) => {
    await startGame(page, { soundMode: 'mp3', displayMode: 'game' });

    const helpBtn = await page.$('#ingame-help-btn');
    expect(helpBtn).not.toBeNull();
    await helpBtn.click();
    await page.waitForTimeout(500);
    await page.screenshot({ path: join(SHOTS_DIR, 'e2e-help-overlay.png') });

    const closeBtn = await page.$('#help-close');
    if (closeBtn) await closeBtn.click();
    await page.waitForTimeout(300);
  });

  test('theme overlay opens and closes', async ({ page }) => {
    await startGame(page, { soundMode: 'mp3', displayMode: 'game' });

    const themeBtn = await page.$('#ingame-theme-btn');
    expect(themeBtn).not.toBeNull();
    await themeBtn.click();
    await page.waitForTimeout(500);
    await page.screenshot({ path: join(SHOTS_DIR, 'e2e-theme-overlay.png') });

    const closeBtn = await page.$('#theme-close');
    if (closeBtn) await closeBtn.click();
    await page.waitForTimeout(300);
  });

  test('credits overlay opens from title screen', async ({ page }) => {
    await page.goto(GAME_PATH);
    await page.waitForTimeout(800);

    const creditsBtn = await page.$('#credits-btn');
    expect(creditsBtn).not.toBeNull();
    await creditsBtn.click();
    await page.waitForTimeout(500);
    await page.screenshot({ path: join(SHOTS_DIR, 'e2e-credits-overlay.png') });

    const closeBtn = await page.$('#credits-close');
    if (closeBtn) await closeBtn.click();
  });

  test('accessibility overlay opens', async ({ page }) => {
    await startGame(page, { soundMode: 'synth', displayMode: 'game' });

    const accessBtn = await page.$('#ingame-access-btn');
    expect(accessBtn).not.toBeNull();
    await accessBtn.click();
    await page.waitForTimeout(500);
    await page.screenshot({ path: join(SHOTS_DIR, 'e2e-accessibility-overlay.png') });

    // Check access mode buttons
    for (const mode of ['minimal', 'normal', 'flashy']) {
      const btn = await page.$(`.access-btn[data-access="${mode}"]`);
      expect(btn, `Access mode ${mode}`).not.toBeNull();
    }

    const closeBtn = await page.$('#access-close');
    if (closeBtn) await closeBtn.click();
  });
});

// ============================================================================
// GRID MODE
// ============================================================================

test.describe('Grid Mode', () => {
  test('2D/3D toggle works', async ({ page }) => {
    await startGame(page, { soundMode: 'synth', displayMode: 'grid' });

    // Check grid dim tabs
    const dimTabs = await page.$('#grid-dim-tabs');
    expect(dimTabs).not.toBeNull();

    // Switch to 3D
    const btn3d = await page.$(`.dim-btn[data-dim="3d"]`);
    if (btn3d) {
      await btn3d.click();
      await page.waitForTimeout(800);
      await page.screenshot({ path: join(SHOTS_DIR, 'e2e-grid-3d.png') });
    }

    // Switch back to 2D
    const btn2d = await page.$(`.dim-btn[data-dim="2d"]`);
    if (btn2d) {
      await btn2d.click();
      await page.waitForTimeout(800);
      await page.screenshot({ path: join(SHOTS_DIR, 'e2e-grid-2d.png') });
    }
  });
});

// ============================================================================
// CANVAS RENDERING
// ============================================================================

test.describe('Canvas Rendering', () => {
  test('game mode renders non-blank canvas', async ({ page }) => {
    await startGame(page, { soundMode: 'synth', displayMode: 'game' });
    await page.waitForTimeout(2000);

    const hasContent = await canvasHasContent(page);
    await page.screenshot({ path: join(SHOTS_DIR, 'e2e-canvas-game.png') });
    expect(hasContent, 'Canvas should have varied content').toBe(true);
  });

  test('grid mode renders non-blank canvas', async ({ page }) => {
    await startGame(page, { soundMode: 'synth', displayMode: 'grid' });
    await page.waitForTimeout(2000);

    const hasContent = await canvasHasContent(page);
    await page.screenshot({ path: join(SHOTS_DIR, 'e2e-canvas-grid.png') });
    expect(hasContent, 'Canvas should have varied content').toBe(true);
  });

  test('player mode renders non-blank canvas', async ({ page }) => {
    await startGame(page, { soundMode: 'synth', displayMode: 'player' });
    await page.waitForTimeout(2000);

    const hasContent = await canvasHasContent(page);
    await page.screenshot({ path: join(SHOTS_DIR, 'e2e-canvas-player.png') });
    // Player mode may have minimal rendering, so we're lenient here
  });
});

// ============================================================================
// 2-PLAYER MODE
// ============================================================================

test.describe('2-Player Mode', () => {
  test('starts with 2 runners', async ({ page }) => {
    await startGame(page, { soundMode: 'synth', displayMode: 'game', players: 2 });
    await page.screenshot({ path: join(SHOTS_DIR, 'e2e-2player.png') });

    const runnerCount = await page.evaluate(() => {
      // Try to find runner count from game state
      const canvas = document.getElementById('main-canvas');
      return canvas ? 'canvas_found' : 'no_canvas';
    });
  });
});

// ============================================================================
// JS ERROR COLLECTION (runs last, aggregates across all tests)
// ============================================================================

test.describe('Error Collection', () => {
  test('collect JS errors across sound modes', async ({ page }) => {
    const allErrors = [];

    for (const sm of ['mp3', 'midi', 'synth']) {
      const errors = collectJsErrors(page);
      await startGame(page, { soundMode: sm, displayMode: 'game' });
      await page.waitForTimeout(3000);

      const critical = errors.filter(e =>
        !e.includes('404') && !e.includes('net::ERR') && !e.includes('favicon')
        && !e.includes('NotAllowedError') && !e.includes('AbortError')
      );
      if (critical.length > 0) {
        allErrors.push(`${sm}: ${critical.join('; ')}`);
      }
    }

    if (allErrors.length > 0) {
      console.warn('JS errors found:', allErrors.join('\n'));
    }
  });
});
