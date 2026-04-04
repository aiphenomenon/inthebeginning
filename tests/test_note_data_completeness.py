"""Tests for MP3 album note data completeness.

Validates that note JSON files for all 12 tracks have:
- Valid JSON with expected fields
- Full duration coverage (no gaps at end)
- Reasonable event density
- Consistent data between v3 and v4 formats
"""

import json
import glob
import os
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARED_TRACKS = os.path.join(PROJECT_ROOT, 'deploy', 'shared', 'audio', 'tracks')
V11_AUDIO = os.path.join(PROJECT_ROOT, 'deploy', 'v11', 'inthebeginning-bounce', 'audio')

TRACK_NAMES = [
    "Ember", "Torrent", "Quartz", "Tide", "Root", "Glacier",
    "Bloom", "Dusk", "Coral", "Moss", "Thunder", "Horizon",
]

PREFIX = "V8_Sessions-aiphenomenon"

# Expected durations from album.json (seconds)
EXPECTED_DURATIONS = {
    1: 251.75, 2: 294.0, 3: 378.0, 4: 298.25, 5: 289.75, 6: 288.0,
    7: 252.0, 8: 294.0, 9: 378.0, 10: 298.25, 11: 289.75, 12: 288.25,
}

# Minimum events per second (sanity check — at least 2 events/sec avg)
MIN_EVENTS_PER_SECOND = 2.0


class TestV3NoteFiles:
    """Test v3 compressed note files in deploy/shared."""

    def _load_v3(self, track_num):
        name = TRACK_NAMES[track_num - 1]
        path = os.path.join(SHARED_TRACKS, f"{PREFIX}-{track_num:02d}-{name}_notes_v3.json")
        assert os.path.exists(path), f"v3 file missing: {path}"
        return json.load(open(path))

    @pytest.mark.parametrize("track_num", range(1, 13))
    def test_v3_valid_json_structure(self, track_num):
        """Each v3 file has legend, events, and track metadata."""
        data = self._load_v3(track_num)
        assert 'legend' in data, "Missing legend"
        assert 'events' in data, "Missing events"
        assert 'instruments' in data['legend'], "Missing legend.instruments"
        assert 'fields' in data['legend'], "Missing legend.fields"
        assert isinstance(data['events'], list), "events must be array"
        assert len(data['events']) > 0, "events array is empty"

    @pytest.mark.parametrize("track_num", range(1, 13))
    def test_v3_event_format(self, track_num):
        """Each event is an array of [t, dur, note, inst_idx, vel, ch]."""
        data = self._load_v3(track_num)
        for i, ev in enumerate(data['events'][:10]):
            assert isinstance(ev, list), f"Event {i} not an array"
            assert len(ev) >= 6, f"Event {i} has {len(ev)} fields, need >=6"
            assert isinstance(ev[0], (int, float)), f"Event {i}: t not numeric"
            assert isinstance(ev[1], (int, float)), f"Event {i}: dur not numeric"
            assert isinstance(ev[2], int), f"Event {i}: note not int"

    @pytest.mark.parametrize("track_num", range(1, 13))
    def test_v3_full_duration_coverage(self, track_num):
        """Notes span at least 95% of the track duration."""
        data = self._load_v3(track_num)
        expected_dur = EXPECTED_DURATIONS[track_num]
        events = data['events']
        last_end = max(ev[0] + ev[1] for ev in events)
        coverage = last_end / expected_dur
        assert coverage >= 0.95, (
            f"Track {track_num}: coverage {coverage:.1%}, "
            f"last_end={last_end:.1f}s vs expected={expected_dur:.1f}s"
        )

    @pytest.mark.parametrize("track_num", range(1, 13))
    def test_v3_event_density(self, track_num):
        """At least MIN_EVENTS_PER_SECOND average density."""
        data = self._load_v3(track_num)
        expected_dur = EXPECTED_DURATIONS[track_num]
        density = len(data['events']) / expected_dur
        assert density >= MIN_EVENTS_PER_SECOND, (
            f"Track {track_num}: {density:.1f} events/sec < {MIN_EVENTS_PER_SECOND}"
        )


class TestV4NoteFiles:
    """Test v4 note files with MIDI provenance in deploy/v11."""

    def _load_v4(self, track_num):
        name = TRACK_NAMES[track_num - 1]
        path = os.path.join(V11_AUDIO, f"{PREFIX}-{track_num:02d}-{name}_notes_v4.json")
        assert os.path.exists(path), f"v4 file missing: {path}"
        return json.load(open(path))

    @pytest.mark.parametrize("track_num", range(1, 13))
    def test_v4_valid_json_structure(self, track_num):
        """Each v4 file has track_num, title, duration, events."""
        data = self._load_v4(track_num)
        assert 'track_num' in data
        assert 'title' in data
        assert 'duration' in data
        assert 'events' in data
        assert isinstance(data['events'], list)
        assert len(data['events']) > 0

    @pytest.mark.parametrize("track_num", range(1, 13))
    def test_v4_event_format(self, track_num):
        """Each v4 event has t, note, dur, vel, inst fields."""
        data = self._load_v4(track_num)
        for i, ev in enumerate(data['events'][:10]):
            assert isinstance(ev, dict), f"Event {i} not a dict"
            assert 't' in ev, f"Event {i}: missing t"
            assert 'note' in ev, f"Event {i}: missing note"
            assert 'dur' in ev, f"Event {i}: missing dur"
            assert 'vel' in ev, f"Event {i}: missing vel"
            assert 'inst' in ev, f"Event {i}: missing inst"

    @pytest.mark.parametrize("track_num", range(1, 13))
    def test_v4_full_duration_coverage(self, track_num):
        """V4 notes span at least 95% of the track duration."""
        data = self._load_v4(track_num)
        expected_dur = EXPECTED_DURATIONS[track_num]
        events = data['events']
        last_end = max(ev['t'] + ev.get('dur', 0) for ev in events)
        coverage = last_end / expected_dur
        assert coverage >= 0.95, (
            f"Track {track_num}: v4 coverage {coverage:.1%}, "
            f"last_end={last_end:.1f}s vs expected={expected_dur:.1f}s"
        )

    @pytest.mark.parametrize("track_num", range(1, 13))
    def test_v4_event_density(self, track_num):
        """At least MIN_EVENTS_PER_SECOND average density."""
        data = self._load_v4(track_num)
        expected_dur = EXPECTED_DURATIONS[track_num]
        density = len(data['events']) / expected_dur
        assert density >= MIN_EVENTS_PER_SECOND, (
            f"Track {track_num}: v4 {density:.1f} events/sec < {MIN_EVENTS_PER_SECOND}"
        )


class TestV3V4Consistency:
    """Test that v3 and v4 have comparable coverage."""

    @pytest.mark.parametrize("track_num", range(1, 13))
    def test_both_formats_cover_full_duration(self, track_num):
        """Both v3 and v4 should cover the full track duration."""
        name = TRACK_NAMES[track_num - 1]
        expected_dur = EXPECTED_DURATIONS[track_num]

        v3_path = os.path.join(SHARED_TRACKS, f"{PREFIX}-{track_num:02d}-{name}_notes_v3.json")
        v4_path = os.path.join(V11_AUDIO, f"{PREFIX}-{track_num:02d}-{name}_notes_v4.json")

        v3 = json.load(open(v3_path))
        v4 = json.load(open(v4_path))

        v3_last = max(ev[0] + ev[1] for ev in v3['events'])
        v4_last = max(ev['t'] + ev.get('dur', 0) for ev in v4['events'])

        assert v3_last / expected_dur >= 0.95, f"v3 coverage too low: {v3_last:.1f}s"
        assert v4_last / expected_dur >= 0.95, f"v4 coverage too low: {v4_last:.1f}s"


class TestAlbumJson:
    """Test album.json metadata consistency."""

    def test_album_json_exists(self):
        path = os.path.join(V11_AUDIO, 'album.json')
        assert os.path.exists(path)

    def test_album_has_12_tracks(self):
        data = json.load(open(os.path.join(V11_AUDIO, 'album.json')))
        assert data['n_tracks'] == 12
        assert len(data['tracks']) == 12

    def test_album_references_existing_files(self):
        data = json.load(open(os.path.join(V11_AUDIO, 'album.json')))
        for track in data['tracks']:
            notes_file = track.get('notes_file', '')
            assert notes_file, f"Track {track['track_num']}: no notes_file"
            path = os.path.join(V11_AUDIO, notes_file)
            assert os.path.exists(path), f"Missing: {notes_file}"

            v4_file = track.get('notes_file_v4', '')
            if v4_file:
                v4_path = os.path.join(V11_AUDIO, v4_file)
                assert os.path.exists(v4_path), f"Missing v4: {v4_file}"

    def test_album_total_events_match(self):
        data = json.load(open(os.path.join(V11_AUDIO, 'album.json')))
        claimed_total = data.get('total_events', 0)
        actual_total = sum(t.get('n_events', 0) for t in data['tracks'])
        assert claimed_total == actual_total, (
            f"album.json claims {claimed_total} events but tracks sum to {actual_total}"
        )
