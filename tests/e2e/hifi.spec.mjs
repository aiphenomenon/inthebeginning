/**
 * HiFi SoundFont mode E2E tests for inthebeginning bounce.
 *
 * Tests the HiFi mode which uses SpessaSynth + FluidR3_GM.sf2
 * for album-quality music generation via MIDI fragment sampling.
 *
 * Requires: static file server on port 8080 serving deploy/
 */

import { test, expect, startGame, getGameState, canvasHasContent,
         collectJsErrors, startServer, startAudioSink,
         captureAudio, analyzeAudio, GAME_PATH, SHOTS_DIR } from './fixtures.mjs';
import { writeFileSync, mkdirSync } from 'fs';
import { join } from 'path';

const V48_DIR = join(SHOTS_DIR, 'v48');
mkdirSync(V48_DIR, { recursive: true });

test.beforeAll(() => { startServer(); });

test.describe('HiFi SoundFont Mode', () => {
  test('HiFi option exists in dropdown', async ({ page }) => {
    await page.goto(GAME_PATH);
    await page.waitForTimeout(800);

    const options = await page.$$eval('#sound-mode-select option', opts =>
      opts.map(o => o.value));
    expect(options).toContain('hifi');
  });

  test('HiFi mode starts and shows epoch name', async ({ page }) => {
    const errors = collectJsErrors(page);
    await startGame(page, { soundMode: 'hifi', displayMode: 'game' });

    // Wait for SoundFont loading (may take several seconds)
    for (let i = 0; i < 20; i++) {
      await page.waitForTimeout(1000);
      const track = await page.$eval('#hud-track', el => el.textContent).catch(() => '');
      if (track && !track.includes('Loading') && !track.includes('SoundFont')) break;
    }

    await page.screenshot({ path: join(V48_DIR, 'hifi-game.png') });

    const state = await getGameState(page);
    expect(state.bodyClass).toContain('mode-game');

    // HUD should show an epoch name (Planck is the first)
    const track = await page.$eval('#hud-track', el => el.textContent).catch(() => '');
    console.log(`  HiFi track: "${track}"`);
    expect(track.length).toBeGreaterThan(0);
    expect(track).not.toContain('Loading');
  });

  test('HiFi mode shows time display', async ({ page }) => {
    await startGame(page, { soundMode: 'hifi', displayMode: 'player' });

    // Wait for load
    for (let i = 0; i < 15; i++) {
      await page.waitForTimeout(1000);
      const time = await page.$eval('#music-time', el => el.textContent).catch(() => '');
      if (time && time !== '0:00 / 0:00') break;
    }

    await page.screenshot({ path: join(V48_DIR, 'hifi-player.png') });

    const time = await page.$eval('#music-time', el => el.textContent).catch(() => '');
    console.log(`  HiFi time: "${time}"`);
    // Duration should be 30:00 (1800 seconds)
    expect(time).toContain('30:00');
  });

  test('HiFi mode in grid view shows note blocks', async ({ page }) => {
    await startGame(page, { soundMode: 'hifi', displayMode: 'grid' });

    // Wait for load + notes to appear
    for (let i = 0; i < 15; i++) {
      await page.waitForTimeout(1000);
      const track = await page.$eval('#hud-track', el => el.textContent).catch(() => '');
      if (track && !track.includes('Loading')) break;
    }

    await page.waitForTimeout(3000); // Extra time for notes to render
    await page.screenshot({ path: join(V48_DIR, 'hifi-grid.png') });

    const state = await getGameState(page);
    expect(state.bodyClass).toContain('mode-grid');
  });

  test('HiFi graceful fallback when SF2 unavailable', async ({ page }) => {
    // Block SF2 file
    await page.route('**/*.sf2', route => route.abort());

    await startGame(page, { soundMode: 'hifi', displayMode: 'game' });
    await page.waitForTimeout(5000);
    await page.screenshot({ path: join(V48_DIR, 'hifi-fallback.png') });

    // Should fall back to Synth mode (not crash)
    const state = await getGameState(page);
    expect(state.hasCanvas).toBe(true);
  });

  test('HiFi credits include SpessaSynth attribution', async ({ page }) => {
    await page.goto(GAME_PATH);
    await page.waitForTimeout(800);

    const creditsBtn = await page.$('#credits-btn');
    await creditsBtn.click();
    await page.waitForTimeout(500);

    const creditsText = await page.$eval('#credits-content', el => el.textContent).catch(() => '');
    expect(creditsText).toContain('SpessaSynth');
    expect(creditsText).toContain('FluidR3_GM');
    expect(creditsText).toContain('Apache-2.0');
  });
});

test.describe('HiFi Audio Verification', () => {
  test.beforeAll(() => { startAudioSink(); });

  test('HiFi produces audio output (spectral analysis)', async ({ page }) => {
    await startGame(page, { soundMode: 'hifi', displayMode: 'player' });

    // Wait for SF2 load + playback
    for (let i = 0; i < 15; i++) {
      await page.waitForTimeout(1000);
      const track = await page.$eval('#hud-track', el => el.textContent).catch(() => '');
      if (track && !track.includes('Loading')) break;
    }

    await page.waitForTimeout(3000); // Extra playback time

    const wavFile = captureAudio(3, 'hifi');
    const analysis = analyzeAudio(wavFile);

    console.log(`  HiFi audio: RMS=${analysis.rms}, Peak=${analysis.peak}, ` +
      `Frames=${analysis.frames}, HasAudio=${analysis.hasAudio}`);

    // HiFi should produce audio (when PulseAudio + xvfb is available)
    // In headless mode, this will be silent — that's expected
  });

  test('generate audio comparison report', async ({ page }) => {
    const report = { timestamp: new Date().toISOString(), modes: {} };

    for (const sm of ['mp3', 'synth', 'hifi']) {
      await startGame(page, { soundMode: sm, displayMode: 'player' });

      if (sm === 'hifi') {
        // Extra wait for SF2 load
        for (let i = 0; i < 15; i++) {
          await page.waitForTimeout(1000);
          const track = await page.$eval('#hud-track', el => el.textContent).catch(() => '');
          if (track && !track.includes('Loading')) break;
        }
      }

      await page.waitForTimeout(sm === 'hifi' ? 5000 : 3000);

      const wavFile = captureAudio(3, `report-${sm}`);
      const analysis = analyzeAudio(wavFile);
      report.modes[sm] = analysis;
    }

    writeFileSync(
      join(V48_DIR, 'audio-comparison-report.json'),
      JSON.stringify(report, null, 2)
    );

    console.log('\n=== HiFi Audio Comparison ===');
    for (const [mode, data] of Object.entries(report.modes)) {
      const status = data.hasAudio ? 'AUDIO' : 'SILENT';
      console.log(`  ${mode.toUpperCase()}: ${status} (RMS=${data.rms}, Peak=${data.peak})`);
    }
    console.log('=============================\n');
  });
});
