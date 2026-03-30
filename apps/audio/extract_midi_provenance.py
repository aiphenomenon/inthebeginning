#!/usr/bin/env python3
"""Extract MIDI provenance for V8 Sessions album.

Re-runs the RadioEngineV8 and RadioEngineV15_V8Tempo segment generation
(without rendering audio) to capture which MIDI file was sampled for each
mood segment. Outputs enhanced per-track JSON files with midi_source and
effects metadata per note event.

Usage:
    python3 apps/audio/extract_midi_provenance.py
"""

import sys
import os
import json
import random
import hashlib

sys.path.insert(0, os.path.dirname(__file__))

from radio_engine import (
    RadioEngineV8, RadioEngineV15, NoteLog, MoodSegment,
    SAMPLE_RATE, EPOCH_ORDER,
)

# V15 with V8 tempo (same as generate_v8_album.py)
class RadioEngineV15_V8Tempo(RadioEngineV15):
    def _compute_tempo_multiplier(self, sim_state):
        if not sim_state:
            return 2.0
        state_str = repr(sorted(sim_state.items()))
        h = hashlib.sha256(state_str.encode()).hexdigest()[:8]
        return 1.5 + 1.0 * (int(h, 16) / 0xFFFFFFFF)


TRACK_NAMES = [
    "Ember", "Torrent", "Quartz", "Tide", "Root", "Glacier",
    "Bloom", "Dusk", "Coral", "Moss", "Thunder", "Horizon",
]

# Track split boundaries (from album.json durations)
TRACK_STARTS = [0.0, 251.75, 545.75, 923.75, 1222.0, 1511.75, 1800.0,
                2051.75, 2345.75, 2723.75, 3022.0, 3311.75]
TRACK_ENDS = [251.75, 545.75, 923.75, 1222.0, 1511.75, 1800.0,
              2051.75, 2345.75, 2723.75, 3022.0, 3311.75, 3600.0]


def extract_provenance(engine_cls, seed, duration, time_offset=0.0):
    """Extract MIDI provenance from engine segments without rendering audio.

    Returns list of dicts: [{
        'start': float,          # absolute start time
        'duration': float,       # segment duration
        'midi_file': str,        # MIDI file path relative to midi_library/
        'midi_composer': str,    # Composer name
        'effects': {             # Active effects for this segment
            'reverb': float,
            'tempo_mult': float,
            'scale': str,
            'root': int,
        },
        'notes': [{              # Note events with provenance
            't': float,
            'note': int,
            'dur': float,
            'vel': float,
            'inst': str,
            'midi_source': str,  # MIDI file from which this note was sampled
        }],
    }]
    """
    engine = engine_cls(seed=seed, total_duration=duration)
    n_segments = len(engine.segments)
    sim_states = engine._generate_sim_states(n_segments)

    segments = []

    for seg_idx in range(n_segments):
        seg_info = engine.segments[seg_idx]
        seg_start = seg_info['start'] + time_offset
        seg_duration = seg_info['duration']
        mood = seg_info.get('mood')

        if not mood:
            continue

        sim_state = sim_states[seg_idx] if seg_idx < len(sim_states) else {}

        # Re-run the MIDI sampling logic
        rng = random.Random(mood.rng.random())
        tempo = mood.tempo
        tempo_mult = engine._compute_tempo_multiplier(sim_state)
        effective_tempo = min(tempo * tempo_mult, 360)

        loop_bars = rng.randint(4, 12)

        try:
            bars_result = engine.midi_lib.sample_bars_seeded(
                sim_state, loop_bars, effective_tempo, mood.beats_per_bar,
                root=mood.root, scale=mood.scale, rng=rng
            )
            midi_notes, segment_duration, midi_info = bars_result
        except Exception as e:
            print(f"  Segment {seg_idx}: sampling failed: {e}")
            continue

        if not midi_notes or segment_duration <= 0:
            continue

        # Extract MIDI source path
        midi_file = midi_info.get('file', '') if midi_info else ''
        midi_composer = ''
        if midi_file:
            parts = midi_file.replace('\\', '/').split('/')
            # Extract composer from path (e.g., "Bach/prelude.mid" -> "Bach")
            if len(parts) >= 2:
                midi_composer = parts[-2]
            elif len(parts) == 1:
                midi_composer = 'Unknown'

        # Get instrument names
        instr_names = []
        for instr in engine.instruments[:4]:
            name = instr.get('name', 'unknown')
            instr_names.append(name)
        if not instr_names:
            instr_names = ['synth']

        # Build note events with provenance
        notes = []
        for t_sec, midi_note, dur_sec, vel in midi_notes:
            abs_time = seg_start + t_sec
            inst_name = instr_names[midi_note % len(instr_names)]
            notes.append({
                't': round(abs_time, 3),
                'note': midi_note,
                'dur': round(dur_sec, 3),
                'vel': round(vel / 127.0 if vel > 1.0 else vel, 3),
                'inst': inst_name,
                'midi_source': midi_file,
            })

        # Get scale name
        scale_name = ''
        if hasattr(mood, 'scale_name'):
            scale_name = mood.scale_name
        elif hasattr(mood, '_scale_name'):
            scale_name = mood._scale_name

        segments.append({
            'start': round(seg_start, 3),
            'duration': round(seg_duration, 3),
            'midi_file': midi_file,
            'midi_composer': midi_composer,
            'effects': {
                'tempo_mult': round(tempo_mult, 2),
                'root': mood.root,
                'scale': scale_name,
                'reverb': round(getattr(engine, '_reverb_wet', 0.3), 2),
            },
            'notes': notes,
        })

    return segments


def segments_to_track_notes(all_segments, track_start, track_end):
    """Extract notes and provenance for a specific track time range."""
    track_notes = []
    track_midis = set()
    track_effects = []

    for seg in all_segments:
        seg_end = seg['start'] + seg['duration']
        # Check if segment overlaps with track range
        if seg_end <= track_start or seg['start'] >= track_end:
            continue

        for note in seg['notes']:
            if track_start <= note['t'] < track_end:
                # Adjust time relative to track start
                adjusted = dict(note)
                adjusted['t'] = round(note['t'] - track_start, 3)
                track_notes.append(adjusted)
                if note.get('midi_source'):
                    track_midis.add(note['midi_source'])

        if seg['effects']:
            track_effects.append(seg['effects'])

    track_notes.sort(key=lambda n: n['t'])
    return track_notes, list(track_midis), track_effects


def main():
    print("Extracting MIDI provenance for V8 Sessions album...")
    print()

    # Render 1: RadioEngineV8, seed=42, 30 minutes
    print("=== Render 1: RadioEngineV8 (seed=42, 1800s) ===")
    try:
        segments_v8 = extract_provenance(RadioEngineV8, seed=42, duration=1800, time_offset=0.0)
        print(f"  Extracted {len(segments_v8)} segments, {sum(len(s['notes']) for s in segments_v8)} notes")
    except Exception as e:
        print(f"  ERROR: {e}")
        segments_v8 = []

    # Render 2: RadioEngineV15_V8Tempo, seed=42, 30 minutes
    print("=== Render 2: RadioEngineV15_V8Tempo (seed=42, 1800s) ===")
    try:
        segments_v15 = extract_provenance(RadioEngineV15_V8Tempo, seed=42, duration=1800, time_offset=1800.0)
        print(f"  Extracted {len(segments_v15)} segments, {sum(len(s['notes']) for s in segments_v15)} notes")
    except Exception as e:
        print(f"  ERROR: {e}")
        segments_v15 = []

    all_segments = segments_v8 + segments_v15

    if not all_segments:
        print("\nFailed to extract provenance. Cannot proceed.")
        print("This may require additional engine dependencies or state.")
        sys.exit(1)

    # Split into 12 tracks
    output_dir = os.path.join(os.path.dirname(__file__), 'output', 'v8_album_provenance')
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n=== Splitting into 12 tracks ===")
    track_summary = []

    for i in range(12):
        track_notes, track_midis, track_effects = segments_to_track_notes(
            all_segments, TRACK_STARTS[i], TRACK_ENDS[i]
        )

        track_data = {
            'track_num': i + 1,
            'title': TRACK_NAMES[i],
            'start_time': TRACK_STARTS[i],
            'end_time': TRACK_ENDS[i],
            'duration': round(TRACK_ENDS[i] - TRACK_STARTS[i], 2),
            'note_count': len(track_notes),
            'midi_sources': track_midis,
            'effects_summary': track_effects[:3] if track_effects else [],
            'events': track_notes,
        }

        fname = f"V8_Sessions-{TRACK_NAMES[i]}_provenance.json"
        with open(os.path.join(output_dir, fname), 'w') as f:
            json.dump(track_data, f, indent=2)

        midi_str = ', '.join(track_midis[:3]) if track_midis else 'procedural'
        print(f"  Track {i+1:2d} ({TRACK_NAMES[i]:10s}): {len(track_notes):5d} notes, "
              f"MIDIs: {midi_str}")

        track_summary.append({
            'track': i + 1,
            'title': TRACK_NAMES[i],
            'notes': len(track_notes),
            'midi_sources': track_midis,
        })

    # Save summary
    with open(os.path.join(output_dir, 'provenance_summary.json'), 'w') as f:
        json.dump({
            'album': 'V8 Sessions',
            'engines': ['RadioEngineV8 (seed=42)', 'RadioEngineV15_V8Tempo (seed=42)'],
            'total_segments': len(all_segments),
            'total_notes': sum(len(s['notes']) for s in all_segments),
            'tracks': track_summary,
        }, f, indent=2)

    print(f"\nProvenance data saved to {output_dir}/")
    print("Done!")


if __name__ == '__main__':
    main()
