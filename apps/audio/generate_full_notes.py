#!/usr/bin/env python3
"""Generate full-track note data for Cosmic Runner V3 visualization.

The V2 note JSONs only captured partial note data (sparse coverage).
This script generates dense note events covering the full duration of
each track by re-running the engine's segment/mood analysis without
the expensive audio synthesis step.

Output format uses a compressed legend-based structure to reduce JSON
file size while covering the entire track duration.
"""

import json
import math
import os
import random
import sys

# Add project root to path
BASE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, BASE)

from radio_engine import (
    RadioEngineV8, RadioEngineV15, NoteLog, MoodSegment,
    InstrumentKit, EPOCH_ORDER, TIME_SIGNATURES
)
from generate_v8_album import RadioEngineV15_V8Tempo

SAMPLE_RATE = 44100

TRACK_NAMES = [
    "Ember", "Torrent", "Quartz", "Tide", "Root", "Glacier",
    "Bloom", "Dusk", "Coral", "Moss", "Thunder", "Horizon",
]


def clamp(v, lo, hi):
    """Clamp value between lo and hi."""
    return max(lo, min(hi, v))


def generate_dense_notes(engine_cls, seed, duration):
    """Generate dense note events covering the full duration.

    Instead of rendering audio (expensive), we replay the engine's
    segment/mood structure and extract MIDI notes from each segment,
    then tile them to fill the full segment duration.

    Args:
        engine_cls: RadioEngineV8 or RadioEngineV15_V8Tempo.
        seed: Random seed.
        duration: Total duration in seconds.

    Returns:
        NoteLog with dense events covering the full duration.
    """
    engine = engine_cls(seed=seed, total_duration=duration)
    note_log = NoteLog()

    n_segments = len(engine.segments)
    sim_states = engine._generate_sim_states(n_segments)

    # Patch MoodSegment init like the render does
    orig, patched = engine._patch_mood_init()
    MoodSegment.__init__ = patched

    try:
        for seg_idx in range(n_segments):
            seg_info = engine.segments[seg_idx]
            seg_start = seg_info['start']
            seg_duration = seg_info['duration']

            time_pos = seg_start
            epoch_idx = int(time_pos / engine.total_duration * 12.999)
            epoch_idx = clamp(epoch_idx, 0, 12)
            epoch = EPOCH_ORDER[epoch_idx]
            sim_state = sim_states[min(seg_idx, len(sim_states) - 1)]

            mood = MoodSegment(
                seg_idx, epoch, epoch_idx, sim_state,
                engine.seed + seg_idx * 31337
            )

            # Get the MIDI notes for this segment
            rng = random.Random(mood.rng.random())
            tempo = mood.tempo
            try:
                tempo_mult = engine._compute_tempo_multiplier(sim_state)
            except Exception:
                tempo_mult = 2.0
            effective_tempo = min(tempo * tempo_mult, 360)

            loop_bars = rng.randint(4, 12)
            bars_result = engine.midi_lib.sample_bars_seeded(
                sim_state, loop_bars, effective_tempo, mood.beats_per_bar,
                root=mood.root, scale=mood.scale, rng=rng
            )
            midi_notes, pattern_duration, midi_info = bars_result

            if not midi_notes or pattern_duration <= 0:
                continue

            # Get instrument names
            selected = engine._select_instruments(mood)
            instr_names = []
            for instr in selected[:8]:
                name = instr.get('name', 'unknown')
                instr_names.append(name)
            if not instr_names:
                instr_names = ['synth']

            # Tile the pattern to fill the full segment duration
            n_repeats = max(1, math.ceil(seg_duration / pattern_duration))
            for rep in range(n_repeats):
                offset = rep * pattern_duration
                if offset >= seg_duration:
                    break

                for t_sec, midi_note, dur_sec, vel in midi_notes:
                    abs_time = seg_start + offset + t_sec
                    # Clip to segment boundary
                    if abs_time >= seg_start + seg_duration:
                        break
                    if abs_time + dur_sec > seg_start + seg_duration:
                        dur_sec = seg_start + seg_duration - abs_time

                    inst_name = instr_names[midi_note % len(instr_names)]
                    note_log.log_note(
                        time=abs_time,
                        duration=dur_sec,
                        midi_note=midi_note,
                        instrument_name=inst_name,
                        velocity=vel / 127.0 if vel > 1.0 else vel,
                        bend=0.0,
                        channel=midi_note % 16,
                    )
    finally:
        MoodSegment.__init__ = orig

    # Sort by time
    note_log.events.sort(key=lambda e: e['t'])
    return note_log


def extract_track_notes(note_log, start_time, end_time):
    """Extract events for a time range, rebased to track start."""
    events = []
    for ev in note_log.events:
        t = ev['t']
        dur = ev.get('dur', 0)
        if t + dur > start_time and t < end_time:
            new_ev = dict(ev)
            new_ev['t'] = round(max(0, t - start_time), 3)
            if t < start_time:
                clipped = start_time - t
                new_ev['dur'] = round(dur - clipped, 3)
            if t + dur > end_time:
                new_ev['dur'] = round(end_time - max(t, start_time), 3)
            events.append(new_ev)
    return events


def compress_notes(events):
    """Compress note events using a legend-based format.

    Instead of repeating instrument name strings in every event,
    create a legend mapping index -> instrument name, and replace
    the string in each event with the index.

    Output format:
    {
        "legend": {"instruments": {"0": "piano_v0_additive_0", ...}},
        "events": [[t, dur, note, inst_idx, vel, ch], ...]
    }

    This reduces JSON size by ~60% compared to the verbose format.
    """
    # Build instrument legend
    instruments = {}
    inst_to_idx = {}
    idx = 0
    for ev in events:
        inst = ev.get('inst', 'unknown')
        if inst not in inst_to_idx:
            inst_to_idx[inst] = idx
            instruments[str(idx)] = inst
            idx += 1

    # Convert events to compact arrays
    compact_events = []
    for ev in events:
        inst_idx = inst_to_idx.get(ev.get('inst', 'unknown'), 0)
        compact_events.append([
            ev['t'],
            ev['dur'],
            ev['note'],
            inst_idx,
            ev['vel'],
            ev['ch'],
        ])

    return {
        'legend': {
            'instruments': instruments,
            'fields': ['t', 'dur', 'note', 'inst', 'vel', 'ch'],
        },
        'events': compact_events,
    }


def main():
    """Generate full-track note data for all 12 tracks."""
    output_dir = os.path.join(BASE, 'output', 'v8_album')
    v3_audio_dir = os.path.join(
        PROJECT_ROOT, 'apps', 'cosmic-runner-v3', 'audio')
    os.makedirs(v3_audio_dir, exist_ok=True)

    prefix = "V8_Sessions-aiphenomenon"

    print("=== Generating Full-Track Note Data ===")
    print(f"Output: {v3_audio_dir}")
    print()

    # Generate dense notes for both engines
    print("Generating V8 engine notes (1800s)...")
    v8_notes = generate_dense_notes(RadioEngineV8, seed=42, duration=1800.0)
    print(f"  V8: {len(v8_notes.events)} events")

    print("Generating V18 engine notes (1800s)...")
    v18_notes = generate_dense_notes(
        RadioEngineV15_V8Tempo, seed=42, duration=1800.0)
    print(f"  V18: {len(v18_notes.events)} events")

    # Combine (V18 events shifted by V8 duration)
    combined = NoteLog()
    combined.events = list(v8_notes.events)
    for ev in v18_notes.events:
        shifted = dict(ev)
        shifted['t'] = round(ev['t'] + 1800.0, 3)
        combined.events.append(shifted)
    combined.events.sort(key=lambda e: e['t'])

    print(f"Combined: {len(combined.events)} total events")
    print()

    # Load track timing from album_notes.json
    album_path = os.path.join(output_dir, 'album_notes.json')
    with open(album_path) as f:
        album = json.load(f)

    tracks_meta = []
    for i, track_info in enumerate(album['tracks']):
        track_num = track_info['track_num']
        title = track_info['title']
        duration = track_info['duration']
        start_time = track_info['start_time']
        end_time = start_time + duration

        # Extract and compress notes for this track
        track_events = extract_track_notes(combined, start_time, end_time)
        compressed = compress_notes(track_events)

        # Add track metadata
        compressed['track_num'] = track_num
        compressed['title'] = title
        compressed['duration'] = duration
        compressed['start_time'] = start_time
        compressed['n_events'] = len(track_events)

        # Compute coverage stats
        if track_events:
            first_t = track_events[0]['t']
            last_t = track_events[-1]['t'] + track_events[-1].get('dur', 0)
            coverage_pct = round(
                (last_t - first_t) / duration * 100, 1) if duration > 0 else 0
        else:
            first_t = 0
            last_t = 0
            coverage_pct = 0

        safe_name = title.replace(' ', '_')
        notes_name = f"{prefix}-{track_num:02d}-{safe_name}_notes_v3.json"
        notes_path = os.path.join(v3_audio_dir, notes_name)

        with open(notes_path, 'w') as f:
            json.dump(compressed, f, separators=(',', ':'))

        file_size = os.path.getsize(notes_path)
        print(f"  Track {track_num:2d} ({title:10s}): "
              f"{len(track_events):5d} events, "
              f"coverage {first_t:.0f}s-{last_t:.0f}s "
              f"({coverage_pct}%), "
              f"{file_size / 1024:.1f} KB")

        tracks_meta.append({
            'track_num': track_num,
            'title': title,
            'file': notes_name,
            'audio_file': track_info['audio_file'],
            'duration': duration,
            'start_time': start_time,
            'n_events': len(track_events),
        })

    # Write album index for v3
    album_v3 = {
        'album': album['album'],
        'artist': album['artist'],
        'n_tracks': len(tracks_meta),
        'total_duration': album['total_duration'],
        'total_events': sum(t['n_events'] for t in tracks_meta),
        'format': 'compressed_v3',
        'legend_note': (
            'Each track JSON uses a legend-based compressed format. '
            'Events are arrays: [t, dur, note, inst_idx, vel, ch]. '
            'inst_idx maps to legend.instruments.'
        ),
        'tracks': tracks_meta,
    }

    album_v3_path = os.path.join(v3_audio_dir, 'album_notes.json')
    with open(album_v3_path, 'w') as f:
        json.dump(album_v3, f, indent=2)

    total_events = sum(t['n_events'] for t in tracks_meta)
    print(f"\nTotal: {total_events} events across {len(tracks_meta)} tracks")
    print(f"Album index: {album_v3_path}")


if __name__ == '__main__':
    main()
