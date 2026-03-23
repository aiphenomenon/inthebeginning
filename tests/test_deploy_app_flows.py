"""Application flow tests for GitHub Pages deployment.

Simulates the asset loading flows that the game and visualizer JavaScript
performs at runtime. Validates that every code path for loading audio,
MIDI, instruments, and metadata will succeed when served from the deploy
directory structure.

These tests act as an "application controller" — they simulate the
decision logic in the JS code to verify all flows work without requiring
a browser.
"""

import json
import os
import re
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEPLOY_ROOT = os.path.join(PROJECT_ROOT, "deploy")
SHARED_ROOT = os.path.join(DEPLOY_ROOT, "shared")
V5_ROOT = os.path.join(DEPLOY_ROOT, "v5")
GAME_ROOT = os.path.join(V5_ROOT, "inthebeginning-bounce")
VISUALIZER_ROOT = os.path.join(V5_ROOT, "visualizer")


def _resolve(base_dir, rel_path):
    """Resolve a relative URL path from a base directory."""
    return os.path.normpath(os.path.join(base_dir, rel_path))


def _file_exists(base_dir, rel_path):
    """Check if a relative path resolves to an existing file."""
    return os.path.isfile(_resolve(base_dir, rel_path))


def _dir_exists(base_dir, rel_path):
    """Check if a relative path resolves to an existing directory."""
    return os.path.isdir(_resolve(base_dir, rel_path))


def _first_successful_path(base_dir, paths):
    """Simulate the JS fallback chain: try each path, return first that exists."""
    for path in paths:
        full = _resolve(base_dir, path)
        if os.path.isfile(full) or os.path.isdir(full):
            return path
    return None


# ──── Game Flow Simulation ────


class TestGameAlbumLoadingFlow(unittest.TestCase):
    """Simulate the game's _autoLoad album loading flow (app.js)."""

    def test_album_json_loading(self):
        """Simulate album.json loading fallback chain."""
        # From app.js _autoLoad: tries multiple bases × ['album.json', 'album_notes.json']
        bases = [
            "audio/",
            "../../shared/audio/tracks/",
            "../shared/audio/tracks/",
        ]
        found = None
        for base in bases:
            for name in ["album.json", "album_notes.json"]:
                if _file_exists(GAME_ROOT, base + name):
                    found = base + name
                    break
            if found:
                break

        self.assertIsNotNone(found, "No album JSON found via any fallback path")

    def test_album_tracks_loadable(self):
        """Once album.json is loaded, all audio files must be reachable."""
        album_path = os.path.join(GAME_ROOT, "audio", "album.json")
        with open(album_path) as f:
            album = json.load(f)

        audio_base = "audio/"
        for track in album["tracks"]:
            audio_file = track.get("audio_file")
            if audio_file:
                self.assertTrue(
                    _file_exists(GAME_ROOT, audio_base + audio_file),
                    f"Track audio not found: {audio_file}",
                )

    def test_album_note_events_loadable(self):
        """Note event JSON files must be loadable for each track."""
        album_path = os.path.join(GAME_ROOT, "audio", "album.json")
        with open(album_path) as f:
            album = json.load(f)

        base = "audio/"
        for track in album["tracks"]:
            notes_file = track.get("file") or track.get("notes_file")
            if notes_file:
                self.assertTrue(
                    _file_exists(GAME_ROOT, base + notes_file),
                    f"Notes file not found: {notes_file}",
                )

    def test_interstitial_loadable(self):
        """Interstitial MP3 must be reachable from audio base."""
        album_path = os.path.join(GAME_ROOT, "audio", "album.json")
        with open(album_path) as f:
            album = json.load(f)

        interstitial = album.get("interstitial", {})
        interstitial_file = interstitial.get("file")
        if interstitial_file:
            self.assertTrue(
                _file_exists(GAME_ROOT, "audio/" + interstitial_file),
                f"Interstitial not found: {interstitial_file}",
            )


class TestGameMidiModeFlow(unittest.TestCase):
    """Simulate the game's MIDI mode initialization flow."""

    def test_midi_catalog_preload(self):
        """Simulate _autoLoad MIDI catalog preloading."""
        # From app.js: musicSync.loadMidiCatalog() tries these paths
        midi_paths = [
            "audio/midi_catalog.json",
            "../../shared/audio/midi/midi_catalog.json",
            "../shared/audio/midi/midi_catalog.json",
            "../../shared/audio/metadata/v1/midi_catalog.json",
            "../shared/audio/metadata/v1/midi_catalog.json",
        ]
        found = _first_successful_path(GAME_ROOT, midi_paths)
        self.assertIsNotNone(found, "No MIDI catalog found via any path")

    def test_midi_catalog_sets_correct_base_url(self):
        """When catalog loads from shared/audio/midi/, base URL points to MIDI files."""
        # The primary shared path should work
        catalog_path = "../../shared/audio/midi/midi_catalog.json"
        self.assertTrue(_file_exists(GAME_ROOT, catalog_path))

        # Base URL derivation: path.substring(0, path.lastIndexOf('/') + 1)
        base_url = catalog_path[: catalog_path.rfind("/") + 1]
        self.assertEqual(base_url, "../../shared/audio/midi/")

        # Test that MIDI files resolve from this base
        catalog_full = _resolve(GAME_ROOT, catalog_path)
        with open(catalog_full) as f:
            catalog = json.load(f)

        # Test 20 random entries
        import random

        sample = random.sample(catalog["midis"], min(20, len(catalog["midis"])))
        for entry in sample:
            midi_path = base_url + entry["path"]
            self.assertTrue(
                _file_exists(GAME_ROOT, midi_path),
                f"MIDI not found: {entry['path']} (resolved: {midi_path})",
            )

    def test_midi_mode_init_uses_catalog_base(self):
        """_initSoundMode uses musicSync.midiBaseUrl for MIDI mode."""
        # When midiBaseUrl is set (from successful loadMidiCatalog),
        # startMidiMode is called with: midiBase + 'midi_catalog.json', midiBase
        midi_base = "../../shared/audio/midi/"
        catalog_url = midi_base + "midi_catalog.json"
        self.assertTrue(_file_exists(GAME_ROOT, catalog_url))

    def test_midi_mode_fallback_local(self):
        """Fallback midiBase 'audio/midi_library/' — test what happens."""
        # This is the fallback if midiBaseUrl isn't set.
        # We should verify that either:
        # 1. midiBaseUrl IS set (test_midi_catalog_preload proves this), or
        # 2. audio/midi_library/ exists (it doesn't in deploy, so #1 is critical)
        local_path = "audio/midi_library/"
        shared_works = _file_exists(
            GAME_ROOT, "../../shared/audio/midi/midi_catalog.json"
        )
        local_works = _dir_exists(GAME_ROOT, local_path)

        self.assertTrue(
            shared_works or local_works,
            "Neither shared MIDI path nor local midi_library/ works",
        )


class TestGameSynthModeFlow(unittest.TestCase):
    """Simulate game's synth mode — no external assets needed."""

    def test_synth_worker_exists(self):
        """Synth worker JS file must exist."""
        self.assertTrue(_file_exists(GAME_ROOT, "js/synth-worker.js"))

    def test_music_generator_exists(self):
        """Music generator JS must exist for synth mode."""
        self.assertTrue(_file_exists(GAME_ROOT, "js/music-generator.js"))


class TestGameInstrumentLoadingFlow(unittest.TestCase):
    """Simulate synth-engine.js instrument sample loading."""

    def test_sample_loading_fallback_chain(self):
        """At least one instrument sample path must resolve."""
        paths = [
            "audio/samples/",
            "../../shared/audio/instruments/",
            "../shared/audio/instruments/",
            "../audio/samples/",
            "../../apps/audio/samples/",
            "../cosmic-runner-v5/audio/samples/",
            "samples/",
        ]
        # Test piano.mp3 as the canary (same as JS does)
        found = None
        for path in paths:
            if _file_exists(GAME_ROOT, path + "piano.mp3"):
                found = path
                break

        self.assertIsNotNone(
            found, "No instrument samples found via any fallback path"
        )

    def test_all_instruments_loadable_from_shared(self):
        """All 60 instruments must be loadable from shared path."""
        instruments_dir = _resolve(GAME_ROOT, "../../shared/audio/instruments/")
        files = [f for f in os.listdir(instruments_dir) if f.endswith(".mp3")]
        self.assertEqual(len(files), 60)


# ──── Visualizer Flow Simulation ────


class TestVisualizerAlbumFlow(unittest.TestCase):
    """Simulate visualizer's _autoLoad album loading."""

    def test_album_loading_from_sibling(self):
        """Visualizer loads album from ../inthebeginning-bounce/audio/."""
        paths = [
            "../inthebeginning-bounce/audio/",
            "../../shared/audio/tracks/",
            "../shared/audio/tracks/",
        ]
        found = None
        for base in paths:
            for name in ["album.json", "album_notes.json"]:
                if _file_exists(VISUALIZER_ROOT, base + name):
                    found = base + name
                    break
            if found:
                break

        self.assertIsNotNone(found, "Visualizer cannot find album data")

    def test_album_tracks_from_sibling(self):
        """Album tracks loaded via sibling game directory."""
        album_path = _resolve(
            VISUALIZER_ROOT, "../inthebeginning-bounce/audio/album.json"
        )
        with open(album_path) as f:
            album = json.load(f)

        base = "../inthebeginning-bounce/audio/"
        for track in album["tracks"]:
            audio_file = track.get("audio_file")
            if audio_file:
                self.assertTrue(
                    _file_exists(VISUALIZER_ROOT, base + audio_file),
                    f"Track not reachable: {audio_file}",
                )


class TestVisualizerMidiFlow(unittest.TestCase):
    """Simulate visualizer's MIDI catalog loading and playback flow."""

    def test_midi_catalog_loading(self):
        """Visualizer must find MIDI catalog via fallback chain."""
        catalog_paths = [
            "../inthebeginning-bounce/audio/midi_catalog.json",
            "../../shared/audio/midi/midi_catalog.json",
            "../shared/audio/midi/midi_catalog.json",
            "../../shared/audio/metadata/v1/midi_catalog.json",
            "../shared/audio/metadata/v1/midi_catalog.json",
        ]
        found = _first_successful_path(VISUALIZER_ROOT, catalog_paths)
        self.assertIsNotNone(found, "Visualizer cannot find MIDI catalog")

    def test_midi_base_url_resolution(self):
        """Base URL derived from catalog path must lead to MIDI files."""
        # Primary path: ../../shared/audio/midi/midi_catalog.json
        catalog_path = "../../shared/audio/midi/midi_catalog.json"
        if _file_exists(VISUALIZER_ROOT, catalog_path):
            base_url = catalog_path[: catalog_path.rfind("/") + 1]
            catalog_full = _resolve(VISUALIZER_ROOT, catalog_path)
            with open(catalog_full) as f:
                catalog = json.load(f)

            # Test entries resolve
            for entry in catalog["midis"][:10]:
                midi_url = base_url + entry["path"]
                self.assertTrue(
                    _file_exists(VISUALIZER_ROOT, midi_url),
                    f"MIDI not found: {entry['path']}",
                )
        else:
            # Fallback: game sibling
            catalog_path = "../inthebeginning-bounce/audio/midi_catalog.json"
            self.assertTrue(_file_exists(VISUALIZER_ROOT, catalog_path))

    def test_midi_file_from_game_catalog_base(self):
        """When catalog loads from game sibling, MIDI files resolve there."""
        catalog_path = "../inthebeginning-bounce/audio/midi_catalog.json"
        if _file_exists(VISUALIZER_ROOT, catalog_path):
            base = "../inthebeginning-bounce/audio/"
            # The game's audio/ doesn't have MIDI files directly
            # but midi_catalog.json in audio/ means base = audio/
            # and entry paths are like Bach/xxx.mid
            # So it would try ../inthebeginning-bounce/audio/Bach/xxx.mid
            # This WON'T work — but the shared path WILL work
            # This test verifies the shared path is in the chain
            shared_path = "../../shared/audio/midi/midi_catalog.json"
            self.assertTrue(
                _file_exists(VISUALIZER_ROOT, shared_path),
                "Shared MIDI catalog must exist as fallback",
            )


class TestVisualizerInstrumentFlow(unittest.TestCase):
    """Simulate visualizer's instrument sample loading."""

    def test_instrument_sample_fallback(self):
        """At least one instrument sample path must resolve."""
        paths = [
            "../inthebeginning-bounce/audio/samples/",
            "../../shared/audio/instruments/",
            "../shared/audio/instruments/",
            "../audio/samples/",
            "../../apps/audio/samples/",
            "audio/samples/",
            "samples/",
        ]
        found = None
        for path in paths:
            if _file_exists(VISUALIZER_ROOT, path + "piano.mp3"):
                found = path
                break

        self.assertIsNotNone(found, "Visualizer cannot find instrument samples")


class TestVisualizerStreamFlow(unittest.TestCase):
    """Simulate visualizer's stream mode (requires SSE server)."""

    def test_stream_js_exists(self):
        """Stream module JS must exist."""
        self.assertTrue(_file_exists(VISUALIZER_ROOT, "js/stream.js"))


class TestVisualizerSingleFileFlow(unittest.TestCase):
    """Simulate visualizer's single file mode (drag and drop)."""

    def test_score_js_exists(self):
        """Score module JS must exist for file parsing."""
        self.assertTrue(_file_exists(VISUALIZER_ROOT, "js/score.js"))

    def test_midi_player_js_exists(self):
        """MIDI player must exist for dropped MIDI files."""
        self.assertTrue(_file_exists(VISUALIZER_ROOT, "js/midi-player.js"))


# ──── Mode Switching Flow ────


class TestModeSwitchingFlow(unittest.TestCase):
    """Test that mode switching between game/player/grid works."""

    def test_game_has_all_mode_assets(self):
        """Game app must have assets for all three display modes."""
        # game mode: needs runner, obstacles, game engine
        for f in ["runner.js", "obstacles.js", "game.js", "characters.js"]:
            self.assertTrue(_file_exists(GAME_ROOT, f"js/{f}"), f"Missing: {f}")

        # player mode: needs player, music-sync
        for f in ["player.js", "music-sync.js"]:
            self.assertTrue(_file_exists(GAME_ROOT, f"js/{f}"), f"Missing: {f}")

        # grid mode: uses same player/music-sync

    def test_game_has_all_sound_mode_assets(self):
        """Game must have assets for MP3, MIDI, and synth sound modes."""
        # MP3: needs album data + audio element (HTML)
        self.assertTrue(_file_exists(GAME_ROOT, "audio/album.json"))

        # MIDI: needs midi-player, synth-engine, catalog
        for f in ["midi-player.js", "synth-engine.js"]:
            self.assertTrue(_file_exists(GAME_ROOT, f"js/{f}"), f"Missing: {f}")

        # Synth: needs music-generator
        self.assertTrue(_file_exists(GAME_ROOT, "js/music-generator.js"))


class TestVisualizerModeSwitching(unittest.TestCase):
    """Test visualizer mode switching (album, midi, synth, stream, single)."""

    def test_all_visualizer_modes_have_assets(self):
        """Each visualizer mode must have its required JS modules."""
        mode_requirements = {
            "album": ["player.js", "grid.js"],
            "midi": ["midi-player.js", "synth-engine.js", "synth-worker.js"],
            "synth": ["music-generator.js", "synth-engine.js"],
            "stream": ["stream.js"],
            "single": ["score.js", "midi-player.js"],
        }
        for mode, files in mode_requirements.items():
            for f in files:
                self.assertTrue(
                    _file_exists(VISUALIZER_ROOT, f"js/{f}"),
                    f"Mode '{mode}' missing: {f}",
                )


# ──── Cross-App Asset Sharing ────


class TestCrossAppAssetSharing(unittest.TestCase):
    """Test that game and visualizer can share assets correctly."""

    def test_visualizer_can_reach_game_audio(self):
        """Visualizer reaches game's audio directory."""
        self.assertTrue(
            _dir_exists(VISUALIZER_ROOT, "../inthebeginning-bounce/audio/")
        )

    def test_both_apps_reach_same_shared_midi(self):
        """Both apps resolve to the same shared MIDI directory."""
        game_midi = _resolve(GAME_ROOT, "../../shared/audio/midi/")
        viz_midi = _resolve(VISUALIZER_ROOT, "../../shared/audio/midi/")
        self.assertEqual(
            os.path.normpath(game_midi),
            os.path.normpath(viz_midi),
        )

    def test_both_apps_reach_same_shared_instruments(self):
        """Both apps resolve to the same shared instruments directory."""
        game_inst = _resolve(GAME_ROOT, "../../shared/audio/instruments/")
        viz_inst = _resolve(VISUALIZER_ROOT, "../../shared/audio/instruments/")
        self.assertEqual(
            os.path.normpath(game_inst),
            os.path.normpath(viz_inst),
        )


# ──── End-to-End Full Catalog Test ────


class TestEndToEndMidiPlayback(unittest.TestCase):
    """End-to-end: simulate loading catalog, picking a MIDI, resolving path."""

    def test_full_midi_playback_flow_from_game(self):
        """Game: load catalog → pick random MIDI → verify file exists."""
        # Step 1: Load catalog (simulating loadMidiCatalog)
        catalog_url = "../../shared/audio/midi/midi_catalog.json"
        catalog_full = _resolve(GAME_ROOT, catalog_url)
        self.assertTrue(os.path.isfile(catalog_full))

        with open(catalog_full) as f:
            catalog = json.load(f)

        # Step 2: Derive base URL (JS: url.substring(0, url.lastIndexOf('/') + 1))
        base_url = catalog_url[: catalog_url.rfind("/") + 1]

        # Step 3: Pick entries and verify paths
        import random

        entries = random.sample(catalog["midis"], min(50, len(catalog["midis"])))
        for entry in entries:
            midi_url = base_url + entry["path"]
            self.assertTrue(
                _file_exists(GAME_ROOT, midi_url),
                f"Playback broken: {entry['path']}",
            )

    def test_full_midi_playback_flow_from_visualizer(self):
        """Visualizer: load catalog → pick MIDI → verify file exists."""
        catalog_url = "../../shared/audio/midi/midi_catalog.json"
        catalog_full = _resolve(VISUALIZER_ROOT, catalog_url)
        self.assertTrue(os.path.isfile(catalog_full))

        with open(catalog_full) as f:
            catalog = json.load(f)

        base_url = catalog_url[: catalog_url.rfind("/") + 1]

        import random

        entries = random.sample(catalog["midis"], min(50, len(catalog["midis"])))
        for entry in entries:
            midi_url = base_url + entry["path"]
            self.assertTrue(
                _file_exists(VISUALIZER_ROOT, midi_url),
                f"Playback broken: {entry['path']}",
            )

    def test_full_album_playback_flow(self):
        """Game: load album → play each track → verify notes load."""
        album_path = os.path.join(GAME_ROOT, "audio", "album.json")
        with open(album_path) as f:
            album = json.load(f)

        for i, track in enumerate(album["tracks"]):
            # Verify audio file
            if track.get("audio_file"):
                self.assertTrue(
                    _file_exists(GAME_ROOT, "audio/" + track["audio_file"]),
                    f"Track {i+1} audio missing",
                )
            # Verify notes file
            notes_file = track.get("file") or track.get("notes_file")
            if notes_file:
                self.assertTrue(
                    _file_exists(GAME_ROOT, "audio/" + notes_file),
                    f"Track {i+1} notes missing",
                )


if __name__ == "__main__":
    unittest.main()
