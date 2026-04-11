# V50 Plan — HiFi SoundFont Wireup Fixes + v13 Deploy

## Date
2026-04-11

## Context
User reported the HiFi mode build shipped in v48/v12 has several runtime bugs
when deployed to GitHub Pages. In addition, several pre-existing rough edges
(version label drift, "V8 Sessions" terminology, start-screen preload 404,
missing favicon) should be cleaned up while we're in the file.

This session:
- Is session **v50** (session_logs/v50-session.md, journal v50-journal.json)
- Produces **deploy/v13/** (next deploy version after v12)
- Canonical source remains `apps/inthebeginning-bounce/` (verified bit-identical
  to `deploy/v12/inthebeginning-bounce/` at start of session)

## Bug diagnoses

### Bug 1: `SF parsing error: Invalid chunk header! Expected "riff" got "vers"`

**Root cause**: GitHub Pages is serving the LFS *pointer text* for
`FluidR3_GM.sf2` rather than the resolved 142 MB binary. An LFS pointer file
starts with the literal ASCII `version https://git-lfs.github.com/spec/v1\noid
sha256:...\nsize ...`. The first four bytes are **"vers"**, which matches the
error message exactly. SpessaSynth's SF2 parser expects "RIFF".

This is a server-side configuration issue on the user's Pages repo (LFS needs
to be fully enabled / bandwidth-allowed), but the client has **no defense
against it** — it happily hands the pointer text to SpessaSynth and gets a
cryptic error.

Files: `deploy/v12/inthebeginning-bounce/js/spessa-bridge.js` — `_fetchWithProgress`
and `init` swallow all errors via broad try/catch and never inspect the buffer.

**Fix**:
1. In `_fetchWithProgress`, after download, inspect the first 4 bytes of the
   buffer. If they're not `RIFF`, return a **typed error** (not null) with a
   clear message: "LFS pointer detected — the .sf2 at {url} is a 130-byte LFS
   pointer file, not the real soundfont. Check your GitHub Pages LFS config or
   copy the file outside LFS."
2. Also check content-length: if it's < 1 MB, the server is definitely not
   returning the real file.
3. In `init`, log the actual error instead of just `e.message`, and re-throw
   to the caller so app.js can surface it.
4. In `app.js _initSoundMode` case `'hifi'`, use a **GET** probe that reads
   the first 4 bytes rather than a HEAD — HEAD passes for pointer files
   (they're served as regular 130-byte text).

### Bug 2: HiFi silently falls back to synth (user can't tell)

**Root cause**: `app.js:826-836` catches the failure and transparently swaps
the mode to `AUDIO_MODE.SYNTH`, setting `hudTrack.textContent = 'SoundFont
unavailable — using Synth'`. The user reported hearing audio and thought it
was HiFi; it was actually the Synth fallback.

**Fix**: Don't swallow the fall-back. Keep the automatic fallback (better UX
than a dead page) but make it obvious:
- Print `console.error` with the actual error (not `console.warn` with
  `e.message` only)
- Set `hudTrack.textContent` to a **red** error state: "⚠ HiFi failed — see
  console (playing synth)"
- Add a persistent toast/notification that stays visible for ~8 seconds
  overlaying the HUD so the user can't miss it

Critically: the user's concern is **"exceptions were being trapped"**. The
fix removes the silent `catch (e) { /* try next path */ }` patterns in the
HiFi branch and replaces them with catches that log the actual error with
enough context to debug.

### Bug 3: `synth-engine.js:491` complains about piano.mp3 404

**Root cause**: `SynthEngine.initSamples()` (line 473) probes a list of paths
in order, starting with `audio/samples/` (which doesn't exist in the deployed
structure — only `../../shared/audio/instruments/` exists). The first HEAD
fetch fails with 404 → browser logs the error → user sees the scary "piano.mp3
not found" message in devtools even though the bank eventually succeeds via
the shared path.

**Fix**: Reorder the probe list so the known-good shared path comes first.
Remove `audio/samples/` entirely since it's never used in the deploy layout.
Keep `../audio/samples/` and `../cosmic-runner-v5/...` as legacy fallbacks for
local dev. This removes the 404 noise without changing behavior.

### Bug 4: Grid colors missing in HiFi and WASM modes

**Root cause (hypothesized — needs runtime confirmation)**: Event wiring looks
correct on paper:
- HiFi: `hifiGenerator.onNoteEvent` → `player.onNoteEvent` → `app._onNoteEvent`
  → `game.setMusicEvents` → `background.updateFromMusic`
- WASM: `wasmSynth.onNoteEvent` → same gated at `mode === AUDIO_MODE.WASM` in
  `player.js:112`

Two suspects:
1. **WASM**: `wasm-synth.js:700-706` emits events with `vel: note.vel || 80`
   — raw 0-127 instead of the normalized 0-1 that `background.js:89` expects.
   But `vel > 0.3` still triggers, so colors *should* appear (at max
   intensity). This is inconsistent with hifi-generator.js:1022 which
   divides by 127. **Fix**: normalize WASM vel to 0-1.
2. **HiFi**: when the SF2 fails to load (Bug 1), the fallback calls
   `player.setMode(AUDIO_MODE.SYNTH)` but the game's initial mode was HIFI
   and the fallback doesn't update the hifiGenerator's emission loop. So
   event emission only starts *if* HiFi actually loaded. If HiFi appeared to
   play because of the Synth fallback, then in Synth mode, `musicGenerator`
   should emit fine via its own `onNoteEvent`. So the fact that the user
   sees grid colors in Synth mode but not in "HiFi" (actually Synth
   fallback) is weird — unless the fallback isn't actually being hit.

The fix for Bug 1 should restore real HiFi operation; once that's in place,
we'll test at runtime and see if grid colors appear. If not, debug from
there with actual devtools output captured via Playwright.

The WASM fix (normalize vel) is independent and should be applied regardless.

### Bug 5: Start-screen 404 `audio/V8_Sessions-aiphenomenon-01-Ember.mp3`

**Root cause**: `app.js:630-640` (`_loadMusic`) probes `audioBases = ['audio/',
'../../shared/audio/tracks/', '../shared/audio/tracks/']` with HEAD fetches
to find the right base URL. The first candidate (`audio/`) 404s, leaving
browser console noise, then the shared path is discovered.

This is preload — it runs during `app.init()`, before the user picks a mode.

**Fix**: Reorder `audioBases` so shared paths are first for deployed builds.
Remove `audio/` entirely since the inthebeginning-bounce deploy never has an
`audio/tracks/` subfolder. Same rationale as Bug 3.

### Bug 6: Start screen shows "v11" — should be v13 and must not drift

**Root cause**: `index.html:6` and `index.html:14` hardcode `V11`. No single
source of truth.

**Fix**:
1. Add `APP_VERSION = 'v13'` constant to `config.js`.
2. Remove the hardcoded `V11` text from `index.html` (leave placeholders).
3. In `app.js` initialization, set `document.title` and the subtitle element
   text from `APP_VERSION`.
4. Add a **steering entry** in CLAUDE.md documenting the version source of
   truth and the one-line change needed when cutting a new version.

### Bug 7: "V8 Sessions" user-facing text

**Root cause**: `index.html:14` ("V8 Sessions — V11") and `index.html:223`
("V8 Sessions Album"). Internal file names (`V8_Sessions-*.mp3`) stay as-is
since they're part of the album provenance metadata the user committed.

**Fix**: Update the two visible occurrences:
- Subtitle: "Cosmic Session — v13"
- Credits: "**Cosmic Session Album** — 12 tracks generated by RadioEngineV8"

Keep file names, `audio_file` fields in album.json, and the engine name
`RadioEngineV8` unchanged — these are internal references, not user-facing.

### Bug 8: Missing favicon

**Fix**: Generate `favicon.ico` containing the alien emoji (👽 U+1F47D) at
32×32 using a tiny Python script (stdlib only per steering — PIL is allowed
because it's for tooling, not the simulator). Alternative: render the emoji
to a PNG via a data URI if Python can't handle emoji fonts. Add the favicon
link to `index.html` head.

Note: The simulator "no dependencies" rule applies to the simulator apps.
This is a build-time artifact generator and can use PIL if available;
otherwise fall back to a pre-made minimal `.ico` binary.

## Implementation sequence

1. **Plan file + stage v13 copy** (this document, then
   `cp -r deploy/v12 deploy/v13`). Commit plan alone first.
2. **Edit `apps/inthebeginning-bounce/`** (canonical source):
   - `config.js`: add `APP_VERSION`
   - `index.html`: remove hardcoded V11 and V8 Sessions, add favicon link
   - `app.js`: set title/subtitle from `APP_VERSION`, reorder probe lists
     (sf2, audio bases), remove silent catches, add visible HiFi error, fix
     path probe to GET+magic-byte check
   - `spessa-bridge.js`: add magic-byte validation and typed errors
   - `synth-engine.js`: reorder sample probe paths, remove `audio/samples/`
   - `wasm-synth.js`: normalize note event velocity to 0-1
3. **Copy to `deploy/v13/`** via `cp -r apps/inthebeginning-bounce/
   deploy/v13/inthebeginning-bounce/`.
4. **Generate favicon.ico** and place in both `apps/inthebeginning-bounce/`
   and `deploy/v13/inthebeginning-bounce/`.
5. **Update tests**: `tests/e2e/fixtures.mjs` GAME_PATH → `/v13/...`.
   Add targeted grid-color tests (inspect canvas pixel histogram in grid mode
   after each sound mode).
6. **Run E2E tests** headful via xvfb + PulseAudio. Capture screenshots
   inline into a new test report at `session_logs/v50-test-report.md`.
7. **Verify no silent fallbacks**: grep for `catch (e) { /* try next */ }`
   and confirm all remaining ones in the HiFi path now log the error.
8. **Update WORKLOG.md**: mark fixed items, record v13 cut.
9. **Session log** `session_logs/v50-session.md` + journal
   `v50-journal.json` (schema-compliant, from `.tool_capture.jsonl`).
10. **Cross-link** session log ↔ test report.
11. **Commit + push** v13 cut.
12. **Compress v49-journal.json** per cut protocol (all prior journals
    compressed; only latest stays uncompressed).
13. **Print GitHub Pages copy instructions** for v13.

## Testing strategy

- **Unit**: `python -m pytest tests/ -v --tb=short` (reference) — no change
  expected.
- **E2E game** (headless, `tests/e2e/game.spec.mjs`) — should still pass
  with `GAME_PATH` pointing at v13.
- **E2E HiFi** (`tests/e2e/hifi.spec.mjs`) — the key suite. Add assertions:
  - SF2 magic byte check (inject a bad file via page.route → expect clear
    error, not cryptic "vers" message)
  - Grid-mode HiFi: canvas pixel histogram has non-bg colors after 3 seconds
- **E2E WASM** (`tests/e2e/wasm.spec.mjs`) — add grid-color assertion for
  WASM mode.
- **Audio capture** via PulseAudio: confirm HiFi mode produces real audio,
  not just silence. This is the only way to verify we're actually running
  through SpessaSynth.
- **Manual** of version label, Cosmic Session rename, favicon display via
  screenshot capture.

## Non-goals

- Fixing the server-side LFS-on-GitHub-Pages issue (out of scope; client
  defends with clear error).
- Rewriting the radio_engine or hifi-generator algorithms.
- Touching other apps/ implementations (Go, Rust, etc.) — this is a
  web-only session.
- Renaming internal file names like `V8_Sessions-*.mp3` or the album.json
  `audio_file` fields. Only user-facing text changes.

## Rollback

If runtime tests show the HiFi fix still doesn't work on GitHub Pages due
to LFS, the client-side fix remains valuable (replaces a cryptic error
with an actionable one) and the v13 cut is still useful for the other six
bug fixes. We'll document the remaining LFS-serving limitation in
WORKLOG and KNOWN_ISSUES.

## Version management going forward

After this session, `APP_VERSION` in `config.js` becomes the single source
of truth for the version label shown to the user. CLAUDE.md will document:
> When cutting a new deploy version: (1) bump `APP_VERSION` in
> `apps/inthebeginning-bounce/js/config.js`, (2) `cp -r
> apps/inthebeginning-bounce deploy/vN/inthebeginning-bounce`,
> (3) update `tests/e2e/fixtures.mjs` GAME_PATH.
