"""Comprehensive integration tests for Cosmic Runner V3.

Validates file structure, audio paths, HTML/CSS/JS content,
build script, MIDI integration, and deployment readiness.
"""
import json
import os
import re
import subprocess
import sys
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V3_DIR = os.path.join(BASE, 'apps', 'cosmic-runner-v3')
AUDIO_DIR = os.path.join(V3_DIR, 'audio')


class TestV3FileStructure(unittest.TestCase):
    """Verify all required files exist in V3."""

    REQUIRED_FILES = [
        'index.html',
        'css/styles.css',
        'js/config.js',
        'js/themes.js',
        'js/app.js',
        'js/game.js',
        'js/player.js',
        'js/music-sync.js',
        'js/background.js',
        'js/characters.js',
        'js/runner.js',
        'js/obstacles.js',
        'js/renderer3d.js',
        'js/blast-effect.js',
        'js/config.js',
        'build.py',
        'DEPLOY.md',
    ]

    def test_all_required_files_exist(self):
        for f in self.REQUIRED_FILES:
            path = os.path.join(V3_DIR, f)
            self.assertTrue(os.path.exists(path), f'Missing: {f}')

    def test_audio_directory_exists(self):
        self.assertTrue(os.path.isdir(AUDIO_DIR))

    def test_server_directory_exists(self):
        self.assertTrue(os.path.isdir(os.path.join(V3_DIR, 'server')))

    def test_test_directory_exists(self):
        self.assertTrue(os.path.isdir(os.path.join(V3_DIR, 'test')))


class TestV3AudioAssets(unittest.TestCase):
    """Verify all audio assets are self-contained in V3."""

    def setUp(self):
        with open(os.path.join(AUDIO_DIR, 'album_notes.json')) as f:
            self.album = json.load(f)

    def test_album_has_12_tracks(self):
        self.assertEqual(len(self.album['tracks']), 12)

    def test_all_mp3s_exist_locally(self):
        for track in self.album['tracks']:
            mp3_path = os.path.join(AUDIO_DIR, track['audio_file'])
            self.assertTrue(os.path.exists(mp3_path),
                            f'Missing MP3: {track["audio_file"]}')

    def test_all_note_jsons_exist_locally(self):
        for track in self.album['tracks']:
            json_path = os.path.join(AUDIO_DIR, track['file'])
            self.assertTrue(os.path.exists(json_path),
                            f'Missing notes: {track["file"]}')

    def test_mp3s_are_nonzero_size(self):
        for track in self.album['tracks']:
            mp3_path = os.path.join(AUDIO_DIR, track['audio_file'])
            size = os.path.getsize(mp3_path)
            self.assertGreater(size, 10000,
                               f'{track["audio_file"]} is too small ({size} bytes)')

    def test_note_jsons_are_valid(self):
        for track in self.album['tracks']:
            json_path = os.path.join(AUDIO_DIR, track['file'])
            with open(json_path) as f:
                data = json.load(f)
            # V3 format has legend + events arrays
            if 'legend' in data:
                self.assertIn('instruments', data['legend'])
                self.assertIsInstance(data['events'], list)
                if data['events']:
                    self.assertIsInstance(data['events'][0], list)

    def test_album_metadata(self):
        self.assertEqual(self.album['n_tracks'], 12)
        self.assertIn('V8 Sessions', self.album['album'])
        self.assertIn('aiphenomenon', self.album['artist'])

    def test_track_durations_positive(self):
        for track in self.album['tracks']:
            self.assertGreater(track['duration'], 0)

    def test_track_event_counts_positive(self):
        for track in self.album['tracks']:
            self.assertGreater(track['n_events'], 0)


class TestV3AudioPathsSelfContained(unittest.TestCase):
    """Ensure V3 doesn't reference files outside its own directory."""

    def test_app_js_no_cross_directory_audio_refs(self):
        with open(os.path.join(V3_DIR, 'js', 'app.js')) as f:
            content = f.read()
        # Should NOT reference ../cosmic-runner-v2/
        self.assertNotIn('../cosmic-runner-v2/', content,
                         'app.js still references V2 audio directory')
        # Should use local audio/ path
        self.assertIn("'audio/album_notes.json'", content)

    def test_no_js_files_reference_parent_dirs_for_audio(self):
        js_dir = os.path.join(V3_DIR, 'js')
        for f in os.listdir(js_dir):
            if not f.endswith('.js'):
                continue
            with open(os.path.join(js_dir, f)) as fp:
                content = fp.read()
            self.assertNotIn('../cosmic-runner-v2/', content,
                             f'{f} references V2 directory')
            self.assertNotIn('../cosmic-runner/', content,
                             f'{f} references V1 directory')


class TestV3HTMLContent(unittest.TestCase):
    """Verify HTML contains required elements."""

    def setUp(self):
        with open(os.path.join(V3_DIR, 'index.html')) as f:
            self.html = f.read()

    def test_has_title(self):
        self.assertIn('Cosmic Runner V3', self.html)

    def test_has_mode_buttons(self):
        self.assertIn('data-mode="player"', self.html)
        self.assertIn('data-mode="game"', self.html)
        self.assertIn('data-mode="grid"', self.html)

    def test_has_midi_mode_toggle(self):
        self.assertIn('midi-mode-toggle', self.html)

    def test_has_infinite_mode_toggle(self):
        self.assertIn('infinite-mode-toggle', self.html)

    def test_has_midi_provenance_panel(self):
        self.assertIn('midi-info', self.html)
        self.assertIn('midi-composer', self.html)
        self.assertIn('midi-piece', self.html)
        self.assertIn('midi-era', self.html)

    def test_has_midi_controls(self):
        self.assertIn('midi-controls', self.html)
        self.assertIn('midi-skip', self.html)
        self.assertIn('midi-mutate', self.html)

    def test_has_player_controls(self):
        self.assertIn('play-btn', self.html)
        self.assertIn('prev-btn', self.html)
        self.assertIn('next-btn', self.html)
        self.assertIn('music-seek', self.html)
        self.assertIn('music-vol', self.html)

    def test_has_midi_player_script(self):
        self.assertIn('midi-player.js', self.html)

    def test_has_canvas(self):
        self.assertIn('main-canvas', self.html)
        self.assertIn('blast-canvas', self.html)

    def test_has_accessibility_settings(self):
        self.assertIn('game-3d-toggle', self.html)
        self.assertIn('note-display-toggle', self.html)

    def test_has_2player_option(self):
        self.assertIn('data-players="2"', self.html)

    def test_script_order(self):
        # config.js must come before app.js
        config_pos = self.html.find('config.js')
        app_pos = self.html.find('js/app.js')
        self.assertGreater(app_pos, config_pos)

    def test_no_external_cdn_refs(self):
        # Should not load any external CDN scripts
        self.assertNotIn('cdn.', self.html)
        self.assertNotIn('unpkg.com', self.html)
        self.assertNotIn('jsdelivr', self.html)


class TestV3CSSContent(unittest.TestCase):
    """Verify CSS contains required styles."""

    def setUp(self):
        with open(os.path.join(V3_DIR, 'css', 'styles.css')) as f:
            self.css = f.read()

    def test_has_midi_info_styles(self):
        self.assertIn('.midi-info', self.css)
        self.assertIn('.midi-info-composer', self.css)

    def test_has_midi_controls_styles(self):
        self.assertIn('.midi-controls', self.css)
        self.assertIn('.midi-mutation-name', self.css)

    def test_has_audio_mode_styles(self):
        self.assertIn('.audio-mode-select', self.css)
        self.assertIn('.toggle-label', self.css)

    def test_has_responsive_breakpoints(self):
        self.assertIn('@media', self.css)

    def test_has_mode_specific_styles(self):
        self.assertIn('mode-player', self.css)
        self.assertIn('mode-grid', self.css)


class TestV3ConfigJS(unittest.TestCase):
    """Verify config.js constants."""

    def setUp(self):
        with open(os.path.join(V3_DIR, 'js', 'config.js')) as f:
            self.content = f.read()

    def test_has_12_track_colors(self):
        # Count color entries
        matches = re.findall(r"name:\s*'(\w+)'", self.content)
        track_names = [m for m in matches if m in
                       ['Ember', 'Torrent', 'Quartz', 'Tide', 'Root', 'Glacier',
                        'Bloom', 'Dusk', 'Coral', 'Moss', 'Thunder', 'Horizon']]
        self.assertEqual(len(track_names), 12)

    def test_has_12_epoch_names(self):
        self.assertIn('Quantum Fluctuation', self.content)
        self.assertIn('Emergence of Life', self.content)

    def test_has_midi_mutations(self):
        self.assertIn('MIDI_MUTATIONS', self.content)
        # Should have 16 mutations
        mutation_matches = re.findall(r"name:\s*'[^']+'", self.content)
        mutation_names = [m for m in mutation_matches if 'Original' in m or
                          'Celestial' in m or 'Photon' in m]
        self.assertGreater(len(mutation_names), 0)

    def test_has_grid_size(self):
        self.assertIn('GRID_SIZE', self.content)
        self.assertIn('64', self.content)

    def test_has_spacetime_scale(self):
        self.assertIn('SPACETIME_SCALE', self.content)
        self.assertIn('1.38e10', self.content)


class TestV3MusicSync(unittest.TestCase):
    """Verify music-sync.js features."""

    def setUp(self):
        with open(os.path.join(V3_DIR, 'js', 'music-sync.js')) as f:
            self.content = f.read()

    def test_has_midi_catalog_loading(self):
        self.assertIn('loadMidiCatalog', self.content)

    def test_has_random_midi_selection(self):
        self.assertIn('getRandomMidi', self.content)

    def test_has_midi_display_info(self):
        self.assertIn('getMidiDisplayInfo', self.content)

    def test_has_xss_prevention(self):
        self.assertIn('sanitize', self.content)
        # Should strip HTML tags
        self.assertIn('<>', self.content)

    def test_has_album_loading(self):
        self.assertIn('loadAlbum', self.content)

    def test_has_binary_search(self):
        # Binary search for event lookup
        self.assertIn('>>> 1', self.content)

    def test_has_note_names(self):
        self.assertIn('NOTE_NAMES', self.content)
        self.assertIn("'C#'", self.content)


class TestV3AppJS(unittest.TestCase):
    """Verify app.js MIDI integration."""

    def setUp(self):
        with open(os.path.join(V3_DIR, 'js', 'app.js')) as f:
            self.content = f.read()

    def test_has_midi_mode_toggle(self):
        self.assertIn('midi-mode-toggle', self.content)

    def test_has_infinite_mode(self):
        self.assertIn('infiniteMode', self.content)

    def test_has_midi_start_stop(self):
        self.assertIn('_startMidiMode', self.content)
        self.assertIn('_stopMidiMode', self.content)

    def test_has_midi_skip(self):
        self.assertIn('_nextMidi', self.content)

    def test_has_mutation_cycling(self):
        self.assertIn('_cycleMutation', self.content)

    def test_has_provenance_display(self):
        self.assertIn('_showMidiInfo', self.content)
        self.assertIn('midi-composer', self.content)

    def test_has_media_session_api(self):
        self.assertIn('mediaSession', self.content)

    def test_has_local_audio_path(self):
        self.assertIn("'audio/album_notes.json'", self.content)
        self.assertIn("'audio/'", self.content)

    def test_has_midi_catalog_loading(self):
        self.assertIn("'audio/midi_catalog.json'", self.content)


class TestV3MidiCatalogIntegration(unittest.TestCase):
    """Verify MIDI catalog is properly integrated."""

    def test_catalog_exists_in_v3_audio(self):
        path = os.path.join(AUDIO_DIR, 'midi_catalog.json')
        self.assertTrue(os.path.exists(path))

    def test_catalog_has_midi_entries(self):
        with open(os.path.join(AUDIO_DIR, 'midi_catalog.json')) as f:
            data = json.load(f)
        self.assertGreater(len(data.get('midis', [])), 1000)

    def test_catalog_paths_are_relative(self):
        with open(os.path.join(AUDIO_DIR, 'midi_catalog.json')) as f:
            data = json.load(f)
        for midi in data['midis'][:50]:
            self.assertNotIn('/', midi['path'][:1],
                             'MIDI path should be relative, not absolute')
            self.assertFalse(midi['path'].startswith('..'),
                             'MIDI path should not use parent directory refs')


class TestV3BuildScript(unittest.TestCase):
    """Verify build.py works correctly."""

    def test_build_script_exists(self):
        self.assertTrue(os.path.exists(os.path.join(V3_DIR, 'build.py')))

    def test_build_script_is_valid_python(self):
        result = subprocess.run(
            [sys.executable, '-c',
             f"import py_compile; py_compile.compile('{os.path.join(V3_DIR, 'build.py')}', doraise=True)"],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0, f'Syntax error: {result.stderr}')

    def test_build_produces_output(self):
        result = subprocess.run(
            [sys.executable, os.path.join(V3_DIR, 'build.py')],
            capture_output=True, text=True, cwd=V3_DIR
        )
        self.assertEqual(result.returncode, 0, f'Build failed: {result.stderr}')
        self.assertTrue(os.path.exists(os.path.join(V3_DIR, 'dist', 'index.html')))

    def test_built_html_contains_inlined_js(self):
        dist_html = os.path.join(V3_DIR, 'dist', 'index.html')
        if not os.path.exists(dist_html):
            self.skipTest('Build output not available')
        with open(dist_html) as f:
            content = f.read()
        # Should contain inlined config
        self.assertIn('GRID_SIZE', content)
        self.assertIn('TRACK_COLORS', content)
        self.assertIn('CosmicRunnerApp', content)

    def test_built_audio_copied(self):
        dist_audio = os.path.join(V3_DIR, 'dist', 'audio')
        if not os.path.exists(dist_audio):
            self.skipTest('Build output not available')
        mp3_count = len([f for f in os.listdir(dist_audio) if f.endswith('.mp3')])
        self.assertEqual(mp3_count, 12)


class TestV3DeployGuide(unittest.TestCase):
    """Verify DEPLOY.md is comprehensive."""

    def setUp(self):
        with open(os.path.join(V3_DIR, 'DEPLOY.md')) as f:
            self.content = f.read()

    def test_has_quick_start(self):
        self.assertIn('Quick Start', self.content)

    def test_has_build_command(self):
        self.assertIn('python3 build.py', self.content)

    def test_has_directory_structure(self):
        self.assertIn('.nojekyll', self.content)
        self.assertIn('index.html', self.content)

    def test_has_github_pages_setup(self):
        self.assertIn('GitHub Pages', self.content)
        self.assertIn('Settings', self.content)

    def test_has_midi_mode_docs(self):
        self.assertIn('MIDI Mode', self.content)
        self.assertIn('1,854', self.content)

    def test_has_provenance_info(self):
        self.assertIn('Provenance', self.content)
        self.assertIn('CC-BY', self.content)

    def test_has_troubleshooting(self):
        self.assertIn('Troubleshooting', self.content)

    def test_has_file_sizes(self):
        self.assertIn('File Size', self.content)


class TestV3ServerJS(unittest.TestCase):
    """Verify radio server is valid."""

    def test_radio_server_exists(self):
        self.assertTrue(os.path.exists(
            os.path.join(V3_DIR, 'server', 'radio.js')))

    def test_server_uses_no_npm_deps(self):
        with open(os.path.join(V3_DIR, 'server', 'radio.js')) as f:
            content = f.read()
        # Should only require Node.js builtins
        requires = re.findall(r"require\('([^']+)'\)", content)
        builtins = {'http', 'fs', 'path', 'url', 'os', 'events', 'stream',
                    'crypto', 'net', 'child_process', 'util', 'querystring'}
        for req in requires:
            self.assertIn(req, builtins,
                          f'Server requires non-builtin module: {req}')


if __name__ == '__main__':
    unittest.main()
