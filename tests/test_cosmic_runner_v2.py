"""Tests for Cosmic Runner V2 and V8 Sessions album generation.

Covers:
- Album generation script (track splitting, note extraction)
- Cosmic Runner V2 HTML/CSS/JS structure
- Build script (single-file bundling)
- Music sync note info display
"""
import json
import os
import re
import subprocess
import sys
import unittest

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNNER_DIR = os.path.join(BASE_DIR, 'apps', 'cosmic-runner-v2')
ALBUM_DIR = os.path.join(BASE_DIR, 'apps', 'audio', 'output', 'v8_album')
AUDIO_DIR = os.path.join(BASE_DIR, 'apps', 'audio')

sys.path.insert(0, AUDIO_DIR)


class TestCosmicRunnerV2Structure(unittest.TestCase):
    """Test that Cosmic Runner V2 has the correct file structure."""

    def test_index_html_exists(self):
        path = os.path.join(RUNNER_DIR, 'index.html')
        self.assertTrue(os.path.exists(path), 'index.html missing')

    def test_css_exists(self):
        path = os.path.join(RUNNER_DIR, 'css', 'styles.css')
        self.assertTrue(os.path.exists(path), 'styles.css missing')

    def test_js_files_exist(self):
        expected = ['app.js', 'background.js', 'game.js', 'music-sync.js',
                    'obstacles.js', 'player.js', 'runner.js']
        for f in expected:
            path = os.path.join(RUNNER_DIR, 'js', f)
            self.assertTrue(os.path.exists(path), f'{f} missing')

    def test_readme_exists(self):
        path = os.path.join(RUNNER_DIR, 'README.md')
        self.assertTrue(os.path.exists(path), 'README.md missing')

    def test_build_script_exists(self):
        path = os.path.join(RUNNER_DIR, 'build.py')
        self.assertTrue(os.path.exists(path), 'build.py missing')


class TestCosmicRunnerV2HTML(unittest.TestCase):
    """Test Cosmic Runner V2 HTML content."""

    @classmethod
    def setUpClass(cls):
        path = os.path.join(RUNNER_DIR, 'index.html')
        with open(path, 'r') as f:
            cls.html = f.read()

    def test_title(self):
        self.assertIn('V8 Sessions', self.html)

    def test_three_mode_buttons(self):
        self.assertIn('data-mode="player"', self.html)
        self.assertIn('data-mode="game"', self.html)
        self.assertIn('data-mode="grid"', self.html)

    def test_mode_tabs(self):
        self.assertIn('mode-tabs', self.html)

    def test_note_info_panel(self):
        self.assertIn('note-info', self.html)
        self.assertIn('note-info-content', self.html)

    def test_canvas(self):
        self.assertIn('main-canvas', self.html)

    def test_music_controls(self):
        self.assertIn('play-btn', self.html)
        self.assertIn('prev-btn', self.html)
        self.assertIn('next-btn', self.html)
        self.assertIn('music-seek', self.html)

    def test_no_external_dependencies(self):
        # No CDN links or external scripts
        self.assertNotIn('cdn.', self.html)
        self.assertNotIn('https://', self.html)


class TestCosmicRunnerV2CSS(unittest.TestCase):
    """Test Cosmic Runner V2 CSS content."""

    @classmethod
    def setUpClass(cls):
        path = os.path.join(RUNNER_DIR, 'css', 'styles.css')
        with open(path, 'r') as f:
            cls.css = f.read()

    def test_mode_specific_styles(self):
        self.assertIn('mode-player', self.css)
        self.assertIn('mode-grid', self.css)

    def test_mode_tabs_styling(self):
        self.assertIn('.mode-tabs', self.css)
        self.assertIn('.tab-btn', self.css)

    def test_note_info_styling(self):
        self.assertIn('.note-info', self.css)
        self.assertIn('.note-tag', self.css)

    def test_responsive(self):
        self.assertIn('@media', self.css)


class TestCosmicRunnerV2JS(unittest.TestCase):
    """Test Cosmic Runner V2 JavaScript content."""

    def _read_js(self, name):
        path = os.path.join(RUNNER_DIR, 'js', name)
        with open(path, 'r') as f:
            return f.read()

    def test_app_has_mode_switching(self):
        js = self._read_js('app.js')
        self.assertIn('_switchMode', js)
        self.assertIn("'player'", js)
        self.assertIn("'game'", js)
        self.assertIn("'grid'", js)

    def test_app_has_note_info(self):
        js = self._read_js('app.js')
        self.assertIn('_updateNoteInfo', js)
        self.assertIn('noteInfoContent', js)

    def test_app_keyboard_mode_switching(self):
        js = self._read_js('app.js')
        self.assertIn('Digit1', js)
        self.assertIn('Digit2', js)
        self.assertIn('Digit3', js)

    def test_game_supports_modes(self):
        js = self._read_js('game.js')
        self.assertIn('setMode', js)
        self.assertIn("'grid'", js)
        self.assertIn("'player'", js)

    def test_background_has_adjustable_opacity(self):
        js = self._read_js('background.js')
        self.assertIn('setGridOpacity', js)
        self.assertIn('showStars', js)

    def test_music_sync_has_note_info(self):
        js = self._read_js('music-sync.js')
        self.assertIn('getNoteInfo', js)
        self.assertIn('midiToNoteName', js)
        self.assertIn('NOTE_NAMES', js)

    def test_music_sync_loads_album_title(self):
        js = self._read_js('music-sync.js')
        self.assertIn('title:', js)
        self.assertIn('audioFile:', js)


class TestCosmicRunnerV2Build(unittest.TestCase):
    """Test Cosmic Runner V2 build script."""

    def test_build_produces_dist(self):
        result = subprocess.run(
            [sys.executable, 'build.py'],
            cwd=RUNNER_DIR,
            capture_output=True, text=True, timeout=30
        )
        self.assertEqual(result.returncode, 0, result.stderr)

        dist_path = os.path.join(RUNNER_DIR, 'dist', 'index.html')
        self.assertTrue(os.path.exists(dist_path))

        with open(dist_path, 'r') as f:
            content = f.read()

        # Should contain inlined CSS
        self.assertIn('<style>', content)
        # Should contain inlined JS
        self.assertIn('<script>', content)
        # Should NOT have external script/link refs
        self.assertNotIn('src="js/', content)
        self.assertNotIn('href="css/', content)
        # Should still have three-mode support
        self.assertIn('_switchMode', content)
        self.assertIn('data-mode="grid"', content)

    def test_dist_size_reasonable(self):
        dist_path = os.path.join(RUNNER_DIR, 'dist', 'index.html')
        if os.path.exists(dist_path):
            size = os.path.getsize(dist_path)
            # Should be between 20KB and 200KB
            self.assertGreater(size, 20_000)
            self.assertLess(size, 200_000)


class TestV8AlbumGenerationScript(unittest.TestCase):
    """Test the V8 album generation script structure."""

    def test_script_importable(self):
        from generate_v8_album import (
            TRACK_NAMES, ALBUM_NAME, ARTIST,
            RadioEngineV15_V8Tempo,
            find_split_points_wav,
            extract_track_notes,
            extract_track_from_wav,
        )

    def test_track_names(self):
        from generate_v8_album import TRACK_NAMES
        self.assertEqual(len(TRACK_NAMES), 12)
        # All should be single-word nature names
        for name in TRACK_NAMES:
            self.assertFalse(' ' in name, f'Track name has space: {name}')

    def test_extract_track_notes(self):
        from generate_v8_album import extract_track_notes
        from radio_engine import NoteLog

        log = NoteLog()
        log.log_note(5.0, 1.0, 60, 'piano', 0.8, channel=0)
        log.log_note(10.0, 2.0, 64, 'violin', 0.6, channel=1)
        log.log_note(15.0, 1.5, 67, 'flute', 0.7, channel=2)

        # Extract events from t=8 to t=13
        events = extract_track_notes(log, 8.0, 13.0, track_offset=8.0)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['note'], 64)
        self.assertAlmostEqual(events[0]['t'], 2.0, places=2)

    def test_v15_v8_tempo_range(self):
        from generate_v8_album import RadioEngineV15_V8Tempo
        engine = RadioEngineV15_V8Tempo(seed=42, total_duration=10.0)
        state = {'particles': 100, 'atoms': 50}
        mult = engine._compute_tempo_multiplier(state)
        self.assertGreaterEqual(mult, 1.5)
        self.assertLessEqual(mult, 2.5)


class TestV8AlbumOutput(unittest.TestCase):
    """Test V8 album output files (if they exist)."""

    def test_album_notes_json(self):
        path = os.path.join(ALBUM_DIR, 'album_notes.json')
        if not os.path.exists(path):
            self.skipTest('Album not yet generated')

        with open(path, 'r') as f:
            data = json.load(f)

        self.assertEqual(data['n_tracks'], 12)
        self.assertIn('V8 Sessions', data['album'])
        self.assertEqual(len(data['tracks']), 12)

        for track in data['tracks']:
            self.assertIn('title', track)
            self.assertIn('file', track)
            self.assertIn('audio_file', track)
            self.assertIn('duration', track)
            self.assertGreater(track['duration'], 60)  # At least 1 minute
            self.assertLess(track['duration'], 600)    # At most 10 minutes

    def test_track_mp3s_exist(self):
        path = os.path.join(ALBUM_DIR, 'album_notes.json')
        if not os.path.exists(path):
            self.skipTest('Album not yet generated')

        with open(path, 'r') as f:
            data = json.load(f)

        for track in data['tracks']:
            mp3_path = os.path.join(ALBUM_DIR, track['audio_file'])
            self.assertTrue(os.path.exists(mp3_path),
                          f'Missing: {track["audio_file"]}')
            self.assertGreater(os.path.getsize(mp3_path), 100_000,
                             f'Too small: {track["audio_file"]}')

    def test_track_notes_json_exist(self):
        path = os.path.join(ALBUM_DIR, 'album_notes.json')
        if not os.path.exists(path):
            self.skipTest('Album not yet generated')

        with open(path, 'r') as f:
            data = json.load(f)

        for track in data['tracks']:
            notes_path = os.path.join(ALBUM_DIR, track['file'])
            self.assertTrue(os.path.exists(notes_path),
                          f'Missing: {track["file"]}')

            with open(notes_path, 'r') as f:
                notes_data = json.load(f)
            self.assertIn('events', notes_data)
            self.assertGreater(len(notes_data['events']), 0,
                             f'No events in {track["file"]}')


if __name__ == '__main__':
    unittest.main()
