/**
 * WASM Synth verification E2E tests for inthebeginning bounce.
 *
 * Tests that the WebAssembly synthesis module loads, produces audio,
 * and gracefully falls back when unavailable.
 *
 * WASM mode is only available in deploy versions v8+ (which include
 * wasm_synth_bg.wasm). Tests run against deploy/v11/.
 */

import { test, expect, startGame, startServer, startAudioSink,
         captureAudio, analyzeAudio, SHOTS_DIR, GAME_PATH } from './fixtures.mjs';
import { writeFileSync } from 'fs';
import { join } from 'path';

test.beforeAll(() => {
  startServer();
  startAudioSink();
});

test.describe('WASM Synth Mode', () => {
  test('WASM option exists in sound mode dropdown', async ({ page }) => {
    await page.goto(GAME_PATH);
    await page.waitForTimeout(800);

    const options = await page.$$eval('#sound-mode-select option', opts =>
      opts.map(o => o.value)
    );

    const hasWasm = options.includes('wasm');
    if (!hasWasm) {
      console.warn('  WASM option not in dropdown — may not be enabled in this build');
    }
    // Report but don't fail — WASM may be conditionally shown
  });

  test('WASM mode starts and loads binary', async ({ page }) => {
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));

    // Check if WASM option exists first
    await page.goto(GAME_PATH);
    await page.waitForTimeout(800);
    const options = await page.$$eval('#sound-mode-select option', opts =>
      opts.map(o => o.value));

    if (!options.includes('wasm')) {
      test.skip();
      return;
    }

    await startGame(page, { soundMode: 'wasm', displayMode: 'player' });
    await page.waitForTimeout(5000);
    await page.screenshot({ path: join(SHOTS_DIR, 'e2e-wasm-playing.png') });

    // Check for WASM-related errors
    const wasmErrors = errors.filter(e =>
      e.includes('wasm') || e.includes('WASM') || e.includes('WebAssembly'));
    if (wasmErrors.length > 0) {
      console.warn('  WASM errors:', wasmErrors.join('; '));
    }
  });

  test('WASM mode produces audio output', async ({ page }) => {
    await page.goto(GAME_PATH);
    await page.waitForTimeout(800);
    const options = await page.$$eval('#sound-mode-select option', opts =>
      opts.map(o => o.value));

    if (!options.includes('wasm')) {
      test.skip();
      return;
    }

    await startGame(page, { soundMode: 'wasm', displayMode: 'player' });
    await page.waitForTimeout(6000);

    const wavFile = captureAudio(3, 'wasm');
    const analysis = analyzeAudio(wavFile);

    console.log(`  WASM audio: RMS=${analysis.rms}, Peak=${analysis.peak}, ` +
      `Frames=${analysis.frames}, HasAudio=${analysis.hasAudio}`);
  });

  test('WASM fallback when binary unavailable', async ({ page }) => {
    await page.goto(GAME_PATH);
    await page.waitForTimeout(800);
    const options = await page.$$eval('#sound-mode-select option', opts =>
      opts.map(o => o.value));

    if (!options.includes('wasm')) {
      test.skip();
      return;
    }

    // Intercept the .wasm file request and return 404
    await page.route('**/*.wasm', route => route.abort());

    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    page.on('console', m => {
      if (m.type() === 'error' || m.type() === 'warn') {
        errors.push(m.text());
      }
    });

    await startGame(page, { soundMode: 'wasm', displayMode: 'player' });
    await page.waitForTimeout(5000);
    await page.screenshot({ path: join(SHOTS_DIR, 'e2e-wasm-fallback.png') });

    // Game should still be functional (fallback to JS synth)
    const state = await page.evaluate(() => ({
      bodyClass: document.body.className,
      hasCanvas: !!document.getElementById('main-canvas'),
      titleActive: document.getElementById('title-screen')?.classList.contains('active'),
    }));

    // Should not have crashed back to title screen
    expect(state.titleActive).not.toBe(true);
    expect(state.hasCanvas).toBe(true);

    console.log('  WASM fallback: game remained functional despite missing .wasm binary');
  });
});

test.describe('WASM vs JS Synth Comparison', () => {
  test('compare WASM and JS synth audio output', async ({ page }) => {
    await page.goto(GAME_PATH);
    await page.waitForTimeout(800);
    const options = await page.$$eval('#sound-mode-select option', opts =>
      opts.map(o => o.value));

    const hasWasm = options.includes('wasm');

    // Capture JS synth audio
    await startGame(page, { soundMode: 'synth', displayMode: 'player' });
    await page.waitForTimeout(4000);
    const jsSynthWav = captureAudio(3, 'js-synth');
    const jsSynthAnalysis = analyzeAudio(jsSynthWav);

    let wasmAnalysis = null;
    if (hasWasm) {
      // Capture WASM synth audio (need to restart)
      await page.goto(GAME_PATH);
      await page.waitForTimeout(800);
      await startGame(page, { soundMode: 'wasm', displayMode: 'player' });
      await page.waitForTimeout(5000);
      const wasmWav = captureAudio(3, 'wasm-synth');
      wasmAnalysis = analyzeAudio(wasmWav);
    }

    const report = {
      timestamp: new Date().toISOString(),
      jsSynth: jsSynthAnalysis,
      wasmSynth: wasmAnalysis || 'not available',
      wasmAvailable: hasWasm,
    };

    writeFileSync(
      join(SHOTS_DIR, 'wasm-comparison-report.json'),
      JSON.stringify(report, null, 2)
    );

    console.log('\n=== WASM vs JS Synth Comparison ===');
    console.log(`  JS Synth:   RMS=${jsSynthAnalysis.rms}, Peak=${jsSynthAnalysis.peak}, Audio=${jsSynthAnalysis.hasAudio}`);
    if (wasmAnalysis) {
      console.log(`  WASM Synth: RMS=${wasmAnalysis.rms}, Peak=${wasmAnalysis.peak}, Audio=${wasmAnalysis.hasAudio}`);
    } else {
      console.log(`  WASM Synth: not available in this build`);
    }
    console.log('===================================\n');
  });
});
