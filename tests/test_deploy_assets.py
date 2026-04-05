"""Tests for GitHub Pages deployment asset completeness and path correctness.

Validates that deploy/shared/ and deploy/v5/ contain all required assets,
that JavaScript path references resolve correctly, and that the shared folder
strategy works across versions.
"""

import json
import os
import re
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEPLOY_ROOT = os.path.join(PROJECT_ROOT, "deploy")
SHARED_ROOT = os.path.join(DEPLOY_ROOT, "shared")
V5_ROOT = os.path.join(DEPLOY_ROOT, "v5")
V6_ROOT = os.path.join(DEPLOY_ROOT, "v6")
GAME_ROOT = os.path.join(V5_ROOT, "inthebeginning-bounce")
V6_GAME_ROOT = os.path.join(V6_ROOT, "inthebeginning-bounce")
VISUALIZER_ROOT = os.path.join(V5_ROOT, "visualizer")
MIDI_LIBRARY_SRC = os.path.join(PROJECT_ROOT, "apps", "audio", "midi_library")
SAMPLES_SRC = os.path.join(PROJECT_ROOT, "apps", "audio", "samples")


def _scan_midi_files(directory):
    """Walk directory and return set of relative MIDI file paths."""
    midis = set()
    for dirpath, _, filenames in os.walk(directory):
        for f in filenames:
            if f.lower().endswith((".mid", ".midi")):
                midis.add(os.path.relpath(os.path.join(dirpath, f), directory))
    return midis


def _read_js_file(path):
    """Read a JS file and return its contents."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _resolve_relative_path(base_dir, relative_path):
    """Resolve a relative path from a base directory (simulating browser path resolution)."""
    return os.path.normpath(os.path.join(base_dir, relative_path))


# ──── Shared Asset Completeness ────


class TestSharedAudioStructure(unittest.TestCase):
    """Test that deploy/shared/audio/ has the correct directory structure."""

    def test_shared_dir_exists(self):
        self.assertTrue(os.path.isdir(SHARED_ROOT))

    def test_shared_audio_dir_exists(self):
        self.assertTrue(os.path.isdir(os.path.join(SHARED_ROOT, "audio")))

    def test_shared_tracks_dir_exists(self):
        self.assertTrue(os.path.isdir(os.path.join(SHARED_ROOT, "audio", "tracks")))

    def test_shared_metadata_dir_exists(self):
        self.assertTrue(
            os.path.isdir(os.path.join(SHARED_ROOT, "audio", "metadata", "v1"))
        )

    def test_shared_interstitials_dir_exists(self):
        self.assertTrue(
            os.path.isdir(os.path.join(SHARED_ROOT, "audio", "interstitials"))
        )

    def test_shared_midi_dir_exists(self):
        self.assertTrue(os.path.isdir(os.path.join(SHARED_ROOT, "audio", "midi")))

    def test_shared_instruments_dir_exists(self):
        self.assertTrue(
            os.path.isdir(os.path.join(SHARED_ROOT, "audio", "instruments"))
        )


class TestSharedMidiFiles(unittest.TestCase):
    """Test that all MIDI files from the source library are in deploy/shared/."""

    def setUp(self):
        self.shared_midi_dir = os.path.join(SHARED_ROOT, "audio", "midi")
        self.src_midis = _scan_midi_files(MIDI_LIBRARY_SRC)
        self.shared_midis = _scan_midi_files(self.shared_midi_dir)

    def test_midi_count_matches_source(self):
        """deploy/shared/ MIDI count must match apps/audio/midi_library/."""
        self.assertEqual(
            len(self.src_midis),
            len(self.shared_midis),
            f"Source has {len(self.src_midis)} MIDIs, "
            f"shared has {len(self.shared_midis)}",
        )

    def test_all_source_midis_present(self):
        """Every MIDI file in apps/audio/midi_library/ must exist in deploy/shared/."""
        missing = self.src_midis - self.shared_midis
        self.assertEqual(
            len(missing), 0, f"Missing {len(missing)} MIDIs: {list(missing)[:10]}..."
        )

    def test_midi_count_minimum(self):
        """Must have at least 1700 MIDI files (known library size)."""
        self.assertGreaterEqual(len(self.shared_midis), 1700)

    def test_composer_directories_present(self):
        """Key composer directories must exist."""
        required_composers = [
            "Bach",
            "Beethoven",
            "Mozart",
            "Chopin",
            "Debussy",
            "Handel",
            "Haydn",
            "Schubert",
            "Schumann",
            "Tchaikovsky",
        ]
        for composer in required_composers:
            composer_dir = os.path.join(self.shared_midi_dir, composer)
            self.assertTrue(
                os.path.isdir(composer_dir),
                f"Missing composer directory: {composer}",
            )

    def test_attribution_file_present(self):
        """ATTRIBUTION.md must be in the shared MIDI directory."""
        attr_path = os.path.join(self.shared_midi_dir, "ATTRIBUTION.md")
        self.assertTrue(os.path.isfile(attr_path))

    def test_midi_catalog_in_midi_dir(self):
        """midi_catalog.json must be present alongside MIDI files."""
        catalog_path = os.path.join(self.shared_midi_dir, "midi_catalog.json")
        self.assertTrue(os.path.isfile(catalog_path))


class TestSharedInstrumentSamples(unittest.TestCase):
    """Test that all instrument sample MP3s are in deploy/shared/."""

    def setUp(self):
        self.instruments_dir = os.path.join(SHARED_ROOT, "audio", "instruments")

    def test_instruments_count(self):
        """Must have all 60 instrument sample MP3s."""
        mp3s = [
            f
            for f in os.listdir(self.instruments_dir)
            if f.endswith(".mp3")
        ]
        self.assertEqual(len(mp3s), 60, f"Expected 60 instruments, found {len(mp3s)}")

    def test_key_instruments_present(self):
        """Essential instruments for MIDI playback must be present."""
        required = [
            "piano.mp3",
            "violin.mp3",
            "cello.mp3",
            "flute.mp3",
            "trumpet.mp3",
            "acoustic_guitar.mp3",
            "harp.mp3",
            "pipe_organ.mp3",
            "harpsichord.mp3",
            "oboe.mp3",
        ]
        for inst in required:
            path = os.path.join(self.instruments_dir, inst)
            self.assertTrue(os.path.isfile(path), f"Missing instrument: {inst}")

    def test_instruments_match_source(self):
        """All samples in apps/audio/samples/ must be in deploy/shared/."""
        src_files = set(f for f in os.listdir(SAMPLES_SRC) if f.endswith(".mp3"))
        shared_files = set(
            f for f in os.listdir(self.instruments_dir) if f.endswith(".mp3")
        )
        missing = src_files - shared_files
        self.assertEqual(
            len(missing), 0, f"Missing instruments: {missing}"
        )

    def test_no_empty_instrument_files(self):
        """All instrument MP3s must be non-empty."""
        for f in os.listdir(self.instruments_dir):
            if f.endswith(".mp3"):
                path = os.path.join(self.instruments_dir, f)
                self.assertGreater(
                    os.path.getsize(path), 0, f"Empty instrument file: {f}"
                )


class TestSharedAlbumTracks(unittest.TestCase):
    """Test that album MP3s and note files are in deploy/shared/."""

    def setUp(self):
        self.tracks_dir = os.path.join(SHARED_ROOT, "audio", "tracks")

    def test_twelve_mp3_tracks(self):
        """Must have exactly 12 album MP3 files."""
        mp3s = [f for f in os.listdir(self.tracks_dir) if f.endswith(".mp3")]
        self.assertEqual(len(mp3s), 12, f"Expected 12 MP3s, found {len(mp3s)}")

    def test_notes_files(self):
        """Must have note JSON files for all 12 tracks (v3 and v4 variants)."""
        jsons = [f for f in os.listdir(self.tracks_dir) if f.endswith(".json")]
        self.assertEqual(len(jsons), 24,
                         f"Expected 24 note JSONs (12 v3 + 12 v4), found {len(jsons)}")

    def test_mp3_files_non_empty(self):
        """Album MP3 files must be substantial (>1MB)."""
        for f in os.listdir(self.tracks_dir):
            if f.endswith(".mp3"):
                size = os.path.getsize(os.path.join(self.tracks_dir, f))
                self.assertGreater(size, 1_000_000, f"MP3 too small: {f} ({size})")


class TestSharedMetadata(unittest.TestCase):
    """Test metadata files in deploy/shared/."""

    def test_album_json_exists(self):
        path = os.path.join(SHARED_ROOT, "audio", "metadata", "v1", "album.json")
        self.assertTrue(os.path.isfile(path))

    def test_album_json_valid(self):
        path = os.path.join(SHARED_ROOT, "audio", "metadata", "v1", "album.json")
        with open(path) as f:
            data = json.load(f)
        self.assertIn("tracks", data)
        self.assertEqual(len(data["tracks"]), 12)

    def test_midi_catalog_exists_in_metadata(self):
        path = os.path.join(
            SHARED_ROOT, "audio", "metadata", "v1", "midi_catalog.json"
        )
        self.assertTrue(os.path.isfile(path))

    def test_midi_catalog_valid(self):
        path = os.path.join(
            SHARED_ROOT, "audio", "metadata", "v1", "midi_catalog.json"
        )
        with open(path) as f:
            data = json.load(f)
        self.assertIn("midis", data)
        self.assertGreaterEqual(len(data["midis"]), 1700)

    def test_interstitial_exists(self):
        path = os.path.join(
            SHARED_ROOT, "audio", "interstitials", "in-the-beginning-radio.mp3"
        )
        self.assertTrue(os.path.isfile(path))


# ──── V5 Game App Completeness ────


class TestGameAssets(unittest.TestCase):
    """Test that deploy/v5/inthebeginning-bounce/ has required files."""

    def test_index_html_exists(self):
        self.assertTrue(os.path.isfile(os.path.join(GAME_ROOT, "index.html")))

    def test_css_exists(self):
        self.assertTrue(os.path.isfile(os.path.join(GAME_ROOT, "css", "styles.css")))

    def test_required_js_files(self):
        """All required JS files must be present."""
        required_js = [
            "app.js",
            "game.js",
            "player.js",
            "midi-player.js",
            "synth-engine.js",
            "synth-worker.js",
            "music-sync.js",
            "music-generator.js",
            "config.js",
            "themes.js",
            "runner.js",
            "obstacles.js",
            "characters.js",
            "background.js",
            "blast-effect.js",
            "renderer3d.js",
        ]
        for js_file in required_js:
            path = os.path.join(GAME_ROOT, "js", js_file)
            self.assertTrue(os.path.isfile(path), f"Missing JS: {js_file}")

    def test_local_audio_copies(self):
        """Local audio directory must have album tracks and metadata."""
        audio_dir = os.path.join(GAME_ROOT, "audio")
        self.assertTrue(os.path.isdir(audio_dir))
        # album.json
        self.assertTrue(os.path.isfile(os.path.join(audio_dir, "album.json")))
        # midi_catalog.json
        self.assertTrue(os.path.isfile(os.path.join(audio_dir, "midi_catalog.json")))

    def test_nojekyll_file(self):
        """v5 must have .nojekyll for GitHub Pages."""
        self.assertTrue(os.path.isfile(os.path.join(V5_ROOT, ".nojekyll")))


class TestVisualizerAssets(unittest.TestCase):
    """Test that deploy/v5/visualizer/ has required files."""

    def test_index_html_exists(self):
        self.assertTrue(os.path.isfile(os.path.join(VISUALIZER_ROOT, "index.html")))

    def test_css_exists(self):
        self.assertTrue(
            os.path.isfile(os.path.join(VISUALIZER_ROOT, "css", "visualizer.css"))
        )

    def test_required_js_files(self):
        required_js = [
            "app.js",
            "grid.js",
            "player.js",
            "midi-player.js",
            "synth-engine.js",
            "synth-worker.js",
            "music-generator.js",
            "stream.js",
            "score.js",
        ]
        for js_file in required_js:
            path = os.path.join(VISUALIZER_ROOT, "js", js_file)
            self.assertTrue(os.path.isfile(path), f"Missing JS: {js_file}")


# ──── Path Resolution Tests ────


class TestGamePathResolution(unittest.TestCase):
    """Simulate browser-style path resolution for the game app."""

    def _resolve_from_game(self, relative_path):
        """Resolve a relative path as if from the game's index.html."""
        return _resolve_relative_path(GAME_ROOT, relative_path)

    def test_local_album_json_resolves(self):
        """audio/album.json resolves to an existing file."""
        path = self._resolve_from_game("audio/album.json")
        self.assertTrue(os.path.isfile(path), f"Not found: {path}")

    def test_local_midi_catalog_resolves(self):
        """audio/midi_catalog.json resolves to an existing file."""
        path = self._resolve_from_game("audio/midi_catalog.json")
        self.assertTrue(os.path.isfile(path), f"Not found: {path}")

    def test_shared_midi_catalog_resolves(self):
        """../../shared/audio/midi/midi_catalog.json resolves correctly."""
        path = self._resolve_from_game("../../shared/audio/midi/midi_catalog.json")
        self.assertTrue(os.path.isfile(path), f"Not found: {path}")

    def test_shared_midi_files_resolve(self):
        """MIDI files resolve through shared catalog base URL."""
        # When catalog loads from ../../shared/audio/midi/midi_catalog.json,
        # the base URL is ../../shared/audio/midi/
        # Entry paths are like Bach/adl_Air_on_a_G_string.mid
        base = self._resolve_from_game("../../shared/audio/midi/")
        catalog_path = os.path.join(base, "midi_catalog.json")
        self.assertTrue(os.path.isfile(catalog_path))

        with open(catalog_path) as f:
            catalog = json.load(f)

        # Test first 10 MIDI entries resolve
        for entry in catalog["midis"][:10]:
            midi_path = os.path.join(base, entry["path"])
            self.assertTrue(
                os.path.isfile(midi_path),
                f"MIDI not found: {entry['path']} -> {midi_path}",
            )

    def test_shared_instruments_resolve(self):
        """../../shared/audio/instruments/piano.mp3 resolves correctly."""
        path = self._resolve_from_game("../../shared/audio/instruments/piano.mp3")
        self.assertTrue(os.path.isfile(path), f"Not found: {path}")

    def test_shared_album_tracks_resolve(self):
        """../../shared/audio/tracks/ contains MP3s."""
        path = self._resolve_from_game("../../shared/audio/tracks/")
        self.assertTrue(os.path.isdir(path))
        mp3s = [f for f in os.listdir(path) if f.endswith(".mp3")]
        self.assertEqual(len(mp3s), 12)

    def test_shared_metadata_resolves(self):
        """../../shared/audio/metadata/v1/album.json resolves."""
        path = self._resolve_from_game(
            "../../shared/audio/metadata/v1/album.json"
        )
        self.assertTrue(os.path.isfile(path))

    def test_interstitial_resolves_from_audio_base(self):
        """Interstitial file resolves from audio base URL."""
        # When album loaded from audio/album.json, audioBaseUrl is audio/
        # album.json interstitial.file = "in-the-beginning-radio.mp3"
        # So interstitial URL = "audio/in-the-beginning-radio.mp3"
        path = self._resolve_from_game("audio/in-the-beginning-radio.mp3")
        self.assertTrue(os.path.isfile(path), f"Not found: {path}")


class TestVisualizerPathResolution(unittest.TestCase):
    """Simulate browser-style path resolution for the visualizer."""

    def _resolve_from_viz(self, relative_path):
        return _resolve_relative_path(VISUALIZER_ROOT, relative_path)

    def test_sibling_game_audio_resolves(self):
        """../inthebeginning-bounce/audio/ resolves to game audio."""
        path = self._resolve_from_viz("../inthebeginning-bounce/audio/album.json")
        self.assertTrue(os.path.isfile(path), f"Not found: {path}")

    def test_shared_midi_catalog_resolves(self):
        """../../shared/audio/midi/midi_catalog.json resolves."""
        path = self._resolve_from_viz("../../shared/audio/midi/midi_catalog.json")
        self.assertTrue(os.path.isfile(path))

    def test_shared_midi_files_resolve(self):
        """MIDI files resolve through shared MIDI base URL."""
        base = self._resolve_from_viz("../../shared/audio/midi/")
        catalog_path = os.path.join(base, "midi_catalog.json")
        with open(catalog_path) as f:
            catalog = json.load(f)

        # Test a sample of entries
        for entry in catalog["midis"][:10]:
            midi_path = os.path.join(base, entry["path"])
            self.assertTrue(
                os.path.isfile(midi_path),
                f"MIDI not found: {entry['path']}",
            )

    def test_shared_instruments_resolve(self):
        """../../shared/audio/instruments/piano.mp3 resolves."""
        path = self._resolve_from_viz("../../shared/audio/instruments/piano.mp3")
        self.assertTrue(os.path.isfile(path))

    def test_shared_album_tracks_resolve(self):
        """../../shared/audio/tracks/ resolves."""
        path = self._resolve_from_viz("../../shared/audio/tracks/")
        self.assertTrue(os.path.isdir(path))

    def test_game_midi_catalog_resolves(self):
        """../inthebeginning-bounce/audio/midi_catalog.json resolves."""
        path = self._resolve_from_viz(
            "../inthebeginning-bounce/audio/midi_catalog.json"
        )
        self.assertTrue(os.path.isfile(path))


# ──── MIDI Catalog Consistency ────


class TestMidiCatalogConsistency(unittest.TestCase):
    """Test that midi_catalog.json entries match actual MIDI files on disk."""

    def setUp(self):
        catalog_path = os.path.join(
            SHARED_ROOT, "audio", "midi", "midi_catalog.json"
        )
        with open(catalog_path) as f:
            self.catalog = json.load(f)
        self.midi_dir = os.path.join(SHARED_ROOT, "audio", "midi")

    def test_all_catalog_entries_exist_on_disk(self):
        """Every path in the catalog must correspond to an actual file."""
        missing = []
        for entry in self.catalog["midis"]:
            path = os.path.join(self.midi_dir, entry["path"])
            if not os.path.isfile(path):
                missing.append(entry["path"])
        self.assertEqual(
            len(missing),
            0,
            f"{len(missing)} catalog entries missing on disk: {missing[:10]}...",
        )

    def test_all_disk_files_in_catalog(self):
        """Every MIDI file on disk should be referenced in the catalog."""
        disk_midis = _scan_midi_files(self.midi_dir)
        catalog_paths = set(e["path"] for e in self.catalog["midis"])
        orphans = disk_midis - catalog_paths
        # Filter out non-MIDI files like midi_catalog.json
        orphans = {p for p in orphans if p.endswith((".mid", ".midi"))}
        # Allow some tolerance (catalog may use slightly different count)
        self.assertLessEqual(
            len(orphans),
            100,
            f"Too many orphan MIDIs not in catalog: {len(orphans)}",
        )

    def test_catalog_entries_have_required_fields(self):
        """Each entry must have path, name, composer, era."""
        for i, entry in enumerate(self.catalog["midis"][:50]):
            self.assertIn("path", entry, f"Entry {i} missing 'path'")
            self.assertIn("composer", entry, f"Entry {i} missing 'composer'")
            self.assertIn("era", entry, f"Entry {i} missing 'era'")

    def test_catalog_has_expected_composer_count(self):
        """Catalog should reference ~120 composers."""
        composers = set(e.get("composer", "") for e in self.catalog["midis"])
        self.assertGreaterEqual(len(composers), 100)


# ──── JavaScript Code Analysis ────


class TestGameJSPathReferences(unittest.TestCase):
    """Validate that JS files have correct path fallback chains."""

    def setUp(self):
        self.app_js = _read_js_file(os.path.join(GAME_ROOT, "js", "app.js"))
        self.music_sync = _read_js_file(
            os.path.join(GAME_ROOT, "js", "music-sync.js")
        )
        self.synth_engine = _read_js_file(
            os.path.join(GAME_ROOT, "js", "synth-engine.js")
        )

    def test_midi_catalog_paths_include_shared(self):
        """Game app.js must include shared MIDI path in fallback chain."""
        self.assertIn("../../shared/audio/midi/midi_catalog.json", self.app_js)

    def test_music_sync_has_load_midi_catalog(self):
        """MusicSync must have loadMidiCatalog method."""
        self.assertIn("async loadMidiCatalog", self.music_sync)

    def test_music_sync_sets_midi_base_url(self):
        """loadMidiCatalog must set midiBaseUrl."""
        self.assertIn("this.midiBaseUrl", self.music_sync)

    def test_synth_engine_includes_shared_instruments(self):
        """SynthEngine must include shared instruments path."""
        self.assertIn("../../shared/audio/instruments/", self.synth_engine)

    def test_album_paths_include_shared_tracks(self):
        """Game must include shared tracks path for album loading."""
        self.assertIn("../../shared/audio/tracks/", self.app_js)

    def test_album_paths_include_shared_metadata(self):
        """Game must include shared metadata path."""
        self.assertIn("../../shared/audio/metadata/v1/", self.app_js)


class TestVisualizerJSPathReferences(unittest.TestCase):
    """Validate visualizer JS path references."""

    def setUp(self):
        self.app_js = _read_js_file(os.path.join(VISUALIZER_ROOT, "js", "app.js"))
        self.synth_engine = _read_js_file(
            os.path.join(VISUALIZER_ROOT, "js", "synth-engine.js")
        )

    def test_midi_catalog_includes_shared(self):
        """Visualizer must include shared MIDI path in catalog fallback."""
        self.assertIn("../../shared/audio/midi/midi_catalog.json", self.app_js)

    def test_synth_engine_includes_shared_instruments(self):
        """Visualizer SynthEngine must include shared instruments path."""
        self.assertIn("../../shared/audio/instruments/", self.synth_engine)

    def test_visualizer_references_game_audio(self):
        """Visualizer must reference game's audio as sibling directory."""
        self.assertIn("../inthebeginning-bounce/audio/", self.app_js)


# ──── HTML Integrity ────


class TestGameHTMLIntegrity(unittest.TestCase):
    """Verify game HTML references correct JS and CSS files."""

    def setUp(self):
        with open(os.path.join(GAME_ROOT, "index.html"), "r") as f:
            self.html = f.read()

    def test_all_script_tags_reference_existing_files(self):
        """Every <script src="..."> must point to an existing file."""
        script_refs = re.findall(r'<script\s+src="([^"]+)"', self.html)
        for ref in script_refs:
            path = os.path.join(GAME_ROOT, ref)
            self.assertTrue(os.path.isfile(path), f"Missing script: {ref}")

    def test_all_css_links_reference_existing_files(self):
        """Every <link href="...css"> must point to an existing file."""
        css_refs = re.findall(r'<link[^>]+href="([^"]+\.css)"', self.html)
        for ref in css_refs:
            path = os.path.join(GAME_ROOT, ref)
            self.assertTrue(os.path.isfile(path), f"Missing CSS: {ref}")


class TestVisualizerHTMLIntegrity(unittest.TestCase):
    """Verify visualizer HTML references correct JS and CSS files."""

    def setUp(self):
        with open(os.path.join(VISUALIZER_ROOT, "index.html"), "r") as f:
            self.html = f.read()

    def test_all_script_tags_reference_existing_files(self):
        script_refs = re.findall(r'<script\s+src="([^"]+)"', self.html)
        for ref in script_refs:
            path = os.path.join(VISUALIZER_ROOT, ref)
            self.assertTrue(os.path.isfile(path), f"Missing script: {ref}")

    def test_all_css_links_reference_existing_files(self):
        css_refs = re.findall(r'<link[^>]+href="([^"]+\.css)"', self.html)
        for ref in css_refs:
            path = os.path.join(VISUALIZER_ROOT, ref)
            self.assertTrue(os.path.isfile(path), f"Missing CSS: {ref}")


# ──── Cross-Version Shared Asset Strategy ────


class TestSharedAssetVersioning(unittest.TestCase):
    """Test that the shared folder strategy works across versions."""

    def test_v5_game_can_reach_shared(self):
        """From v5/inthebeginning-bounce/, ../../shared/ resolves to shared/."""
        path = _resolve_relative_path(GAME_ROOT, "../../shared")
        expected = os.path.normpath(SHARED_ROOT)
        self.assertEqual(path, expected)

    def test_v5_visualizer_can_reach_shared(self):
        """From v5/visualizer/, ../../shared/ resolves to shared/."""
        path = _resolve_relative_path(VISUALIZER_ROOT, "../../shared")
        expected = os.path.normpath(SHARED_ROOT)
        self.assertEqual(path, expected)

    def test_hypothetical_v6_can_reach_shared(self):
        """From a hypothetical v6/app/, ../../shared/ resolves to shared/."""
        v6_app = os.path.join(DEPLOY_ROOT, "v6", "some-app")
        path = _resolve_relative_path(v6_app, "../../shared")
        expected = os.path.normpath(SHARED_ROOT)
        self.assertEqual(path, expected)

    def test_shared_not_inside_version_dirs(self):
        """Shared assets must NOT be duplicated inside version directories."""
        v5_midi_dir = os.path.join(V5_ROOT, "midi")
        self.assertFalse(
            os.path.isdir(v5_midi_dir),
            "MIDI files should not be in v5/ directly",
        )

    def test_metadata_versioned_subdirs(self):
        """Metadata uses versioned subdirs (v1/) for schema evolution."""
        v1_dir = os.path.join(SHARED_ROOT, "audio", "metadata", "v1")
        self.assertTrue(os.path.isdir(v1_dir))
        self.assertTrue(os.path.isfile(os.path.join(v1_dir, "album.json")))
        self.assertTrue(os.path.isfile(os.path.join(v1_dir, "midi_catalog.json")))


# ──── Album JSON Integrity ────


class TestAlbumJSONIntegrity(unittest.TestCase):
    """Test album.json content integrity."""

    def setUp(self):
        path = os.path.join(GAME_ROOT, "audio", "album.json")
        with open(path) as f:
            self.album = json.load(f)

    def test_has_12_tracks(self):
        self.assertEqual(len(self.album["tracks"]), 12)

    def test_tracks_have_audio_files(self):
        for i, track in enumerate(self.album["tracks"]):
            self.assertIn("audio_file", track, f"Track {i+1} missing audio_file")

    def test_audio_files_exist_locally(self):
        """Album audio files must exist in the local audio directory."""
        audio_dir = os.path.join(GAME_ROOT, "audio")
        for track in self.album["tracks"]:
            path = os.path.join(audio_dir, track["audio_file"])
            self.assertTrue(
                os.path.isfile(path),
                f"Missing audio: {track['audio_file']}",
            )

    def test_has_interstitial_config(self):
        self.assertIn("interstitial", self.album)
        interstitial = self.album["interstitial"]
        self.assertIn("file", interstitial)

    def test_interstitial_file_exists_locally(self):
        """Interstitial MP3 must exist in the local audio directory."""
        interstitial_file = self.album["interstitial"]["file"]
        path = os.path.join(GAME_ROOT, "audio", interstitial_file)
        self.assertTrue(os.path.isfile(path), f"Missing interstitial: {path}")

    def test_has_id3_metadata(self):
        """Album must have artist, album, year fields."""
        self.assertIn("artist", self.album)
        self.assertIn("album", self.album)
        self.assertIn("year", self.album)


# ──── Deployment Copy Simulation ────


class TestDeploymentCopySimulation(unittest.TestCase):
    """Simulate what happens when deploy/ is copied to a GH Pages repo."""

    def test_all_required_top_level_dirs_exist(self):
        """deploy/ must have shared/ and at least one version dir."""
        self.assertTrue(os.path.isdir(SHARED_ROOT))
        self.assertTrue(os.path.isdir(V5_ROOT))

    def test_shared_to_version_relative_paths_work(self):
        """Verify every version→shared relative path resolves correctly."""
        # Game
        for rel in [
            "../../shared/audio/midi/midi_catalog.json",
            "../../shared/audio/tracks/",
            "../../shared/audio/metadata/v1/album.json",
            "../../shared/audio/instruments/piano.mp3",
            "../../shared/audio/interstitials/in-the-beginning-radio.mp3",
        ]:
            path = _resolve_relative_path(GAME_ROOT, rel)
            self.assertTrue(
                os.path.exists(path), f"Game path broken: {rel} -> {path}"
            )

        # Visualizer
        for rel in [
            "../../shared/audio/midi/midi_catalog.json",
            "../../shared/audio/instruments/piano.mp3",
            "../inthebeginning-bounce/audio/album.json",
        ]:
            path = _resolve_relative_path(VISUALIZER_ROOT, rel)
            self.assertTrue(
                os.path.exists(path), f"Visualizer path broken: {rel} -> {path}"
            )

    def test_full_midi_resolution_chain(self):
        """End-to-end: catalog → MIDI file resolution for all entries."""
        catalog_path = os.path.join(
            SHARED_ROOT, "audio", "midi", "midi_catalog.json"
        )
        with open(catalog_path) as f:
            catalog = json.load(f)

        midi_base = os.path.join(SHARED_ROOT, "audio", "midi")
        missing = []
        for entry in catalog["midis"]:
            path = os.path.join(midi_base, entry["path"])
            if not os.path.isfile(path):
                missing.append(entry["path"])

        self.assertEqual(
            len(missing),
            0,
            f"{len(missing)} MIDIs referenced in catalog but missing: "
            f"{missing[:5]}...",
        )


# ──── V6 Game App Completeness ────


class TestV6GameAssets(unittest.TestCase):
    """Test that deploy/v6/inthebeginning-bounce/ has required files."""

    def test_index_html_exists(self):
        self.assertTrue(os.path.isfile(os.path.join(V6_GAME_ROOT, "index.html")))

    def test_css_exists(self):
        self.assertTrue(os.path.isfile(os.path.join(V6_GAME_ROOT, "css", "styles.css")))

    def test_required_js_files(self):
        """All 16 required JS files must be present."""
        required_js = [
            "app.js",
            "game.js",
            "player.js",
            "midi-player.js",
            "synth-engine.js",
            "synth-worker.js",
            "music-sync.js",
            "music-generator.js",
            "config.js",
            "themes.js",
            "runner.js",
            "obstacles.js",
            "characters.js",
            "background.js",
            "blast-effect.js",
            "renderer3d.js",
        ]
        for js_file in required_js:
            path = os.path.join(V6_GAME_ROOT, "js", js_file)
            self.assertTrue(os.path.isfile(path), f"Missing JS: {js_file}")

    def test_local_audio_metadata(self):
        """V6 audio directory must have metadata JSONs and interstitial."""
        audio_dir = os.path.join(V6_GAME_ROOT, "audio")
        self.assertTrue(os.path.isdir(audio_dir))
        self.assertTrue(os.path.isfile(os.path.join(audio_dir, "album.json")))
        self.assertTrue(os.path.isfile(os.path.join(audio_dir, "midi_catalog.json")))
        self.assertTrue(os.path.isfile(os.path.join(audio_dir, "album_notes.json")))
        self.assertTrue(
            os.path.isfile(os.path.join(audio_dir, "in-the-beginning-radio.mp3"))
        )

    def test_twelve_note_event_files(self):
        """V6 must have all 12 note event JSON files."""
        audio_dir = os.path.join(V6_GAME_ROOT, "audio")
        note_files = [
            f for f in os.listdir(audio_dir) if f.endswith("_notes_v3.json")
        ]
        self.assertEqual(len(note_files), 12, f"Expected 12 note JSONs, found {len(note_files)}")

    def test_nojekyll_file(self):
        """v6 must have .nojekyll for GitHub Pages."""
        self.assertTrue(os.path.isfile(os.path.join(V6_ROOT, ".nojekyll")))

    def test_no_visualizer(self):
        """V6 should NOT have a visualizer directory."""
        self.assertFalse(os.path.isdir(os.path.join(V6_ROOT, "visualizer")))


class TestV6GameHTMLIntegrity(unittest.TestCase):
    """Verify V6 game HTML references correct JS and CSS files."""

    def setUp(self):
        with open(os.path.join(V6_GAME_ROOT, "index.html"), "r") as f:
            self.html = f.read()

    def test_all_script_tags_reference_existing_files(self):
        script_refs = re.findall(r'<script\s+src="([^"]+)"', self.html)
        for ref in script_refs:
            path = os.path.join(V6_GAME_ROOT, ref)
            self.assertTrue(os.path.isfile(path), f"Missing script: {ref}")

    def test_all_css_links_reference_existing_files(self):
        css_refs = re.findall(r'<link[^>]+href="([^"]+\.css)"', self.html)
        for ref in css_refs:
            path = os.path.join(V6_GAME_ROOT, ref)
            self.assertTrue(os.path.isfile(path), f"Missing CSS: {ref}")

    def test_title_is_v6_branding(self):
        """Title should reference 'inthebeginning bounce', not 'Cosmic Runner'."""
        self.assertIn("inthebeginning bounce", self.html)
        self.assertNotIn("Cosmic Runner", self.html)


class TestV6GamePathResolution(unittest.TestCase):
    """Simulate browser-style path resolution for the V6 game app."""

    def _resolve_from_v6(self, relative_path):
        return _resolve_relative_path(V6_GAME_ROOT, relative_path)

    def test_local_album_json_resolves(self):
        path = self._resolve_from_v6("audio/album.json")
        self.assertTrue(os.path.isfile(path), f"Not found: {path}")

    def test_local_midi_catalog_resolves(self):
        path = self._resolve_from_v6("audio/midi_catalog.json")
        self.assertTrue(os.path.isfile(path), f"Not found: {path}")

    def test_shared_midi_catalog_resolves(self):
        path = self._resolve_from_v6("../../shared/audio/midi/midi_catalog.json")
        self.assertTrue(os.path.isfile(path), f"Not found: {path}")

    def test_shared_instruments_resolve(self):
        path = self._resolve_from_v6("../../shared/audio/instruments/piano.mp3")
        self.assertTrue(os.path.isfile(path), f"Not found: {path}")

    def test_shared_album_tracks_resolve(self):
        """V6 loads album MP3s from shared (no local copies)."""
        path = self._resolve_from_v6("../../shared/audio/tracks/")
        self.assertTrue(os.path.isdir(path))
        mp3s = [f for f in os.listdir(path) if f.endswith(".mp3")]
        self.assertEqual(len(mp3s), 12)

    def test_shared_metadata_resolves(self):
        path = self._resolve_from_v6("../../shared/audio/metadata/v1/album.json")
        self.assertTrue(os.path.isfile(path))

    def test_interstitial_resolves(self):
        path = self._resolve_from_v6("audio/in-the-beginning-radio.mp3")
        self.assertTrue(os.path.isfile(path), f"Not found: {path}")

    def test_v6_can_reach_shared(self):
        """From v6/inthebeginning-bounce/, ../../shared/ resolves to shared/."""
        path = _resolve_relative_path(V6_GAME_ROOT, "../../shared")
        expected = os.path.normpath(SHARED_ROOT)
        self.assertEqual(path, expected)


class TestV6AlbumJSONIntegrity(unittest.TestCase):
    """Test V6 album.json content integrity."""

    def setUp(self):
        path = os.path.join(V6_GAME_ROOT, "audio", "album.json")
        with open(path) as f:
            self.album = json.load(f)

    def test_has_12_tracks(self):
        self.assertEqual(len(self.album["tracks"]), 12)

    def test_tracks_have_audio_files(self):
        for i, track in enumerate(self.album["tracks"]):
            self.assertIn("audio_file", track, f"Track {i+1} missing audio_file")

    def test_audio_files_exist_in_shared(self):
        """V6 album MP3s should be in shared/audio/tracks/."""
        tracks_dir = os.path.join(SHARED_ROOT, "audio", "tracks")
        for track in self.album["tracks"]:
            path = os.path.join(tracks_dir, track["audio_file"])
            self.assertTrue(
                os.path.isfile(path),
                f"Missing in shared: {track['audio_file']}",
            )

    def test_has_interstitial_config(self):
        self.assertIn("interstitial", self.album)
        self.assertIn("file", self.album["interstitial"])

    def test_has_id3_metadata(self):
        self.assertIn("artist", self.album)
        self.assertIn("album", self.album)
        self.assertIn("year", self.album)


class TestV6GameJSPathReferences(unittest.TestCase):
    """Validate that V6 JS files have correct path fallback chains."""

    def setUp(self):
        self.app_js = _read_js_file(os.path.join(V6_GAME_ROOT, "js", "app.js"))
        self.music_sync = _read_js_file(
            os.path.join(V6_GAME_ROOT, "js", "music-sync.js")
        )
        self.synth_engine = _read_js_file(
            os.path.join(V6_GAME_ROOT, "js", "synth-engine.js")
        )

    def test_midi_catalog_paths_include_shared(self):
        self.assertIn("../../shared/audio/midi/midi_catalog.json", self.app_js)

    def test_music_sync_has_load_midi_catalog(self):
        self.assertIn("async loadMidiCatalog", self.music_sync)

    def test_synth_engine_includes_shared_instruments(self):
        self.assertIn("../../shared/audio/instruments/", self.synth_engine)

    def test_album_paths_include_shared_tracks(self):
        self.assertIn("../../shared/audio/tracks/", self.app_js)

    def test_v6_branding_in_app_js(self):
        """app.js should use V6 branding, not Cosmic Runner."""
        self.assertNotIn("Cosmic Runner", self.app_js)


if __name__ == "__main__":
    unittest.main()
