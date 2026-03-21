#!/usr/bin/env python3
"""Generate a 12-track album from V8 and V18-V8 engine renders.

Renders two 30-minute pieces:
1. RadioEngineV8(seed=42) — original V8 orchestral layering
2. RadioEngineV15_V8Tempo(seed=42) — V15 synthesis + V8 tempo (1.5x-2.5x)

Splits the combined 60 minutes into 12 tracks at low-energy boundaries,
producing per-track MP3s and JSON note metadata files.

Track names use nature words symbolizing universe evolution:
  1. Ember       7. Bloom
  2. Torrent     8. Dusk
  3. Quartz      9. Coral
  4. Tide       10. Moss
  5. Root       11. Thunder
  6. Glacier    12. Horizon
"""
import sys
import os
import wave
import struct
import math
import json
import time as _time
import random
import hashlib
import tempfile

sys.path.insert(0, os.path.dirname(__file__))

from radio_engine import (
    RadioEngineV8, RadioEngineV15, NoteLog, MoodSegment,
    SAMPLE_RATE, EPOCH_ORDER, clamp, wav_to_mp3,
    InstrumentKit,
)

# V15 with V8 tempo (1.5x-2.5x) — same as generate_v18_mp3s.py
class RadioEngineV15_V8Tempo(RadioEngineV15):
    """V15 synthesis with V8's original 1.5x-2.5x tempo range."""

    def _compute_tempo_multiplier(self, sim_state):
        """Original V8 tempo: 1.5x-2.5x range (no density awareness)."""
        if not sim_state:
            return 2.0
        state_str = repr(sorted(sim_state.items()))
        h = hashlib.sha256(state_str.encode()).hexdigest()[:8]
        return 1.5 + 1.0 * (int(h, 16) / 0xFFFFFFFF)


def _log_segment_notes_v8(note_log, engine, mood, sim_state, seg_start_time):
    """Log note events for a V8/V15 engine segment.

    V8 engines don't have _is_noise_instrument, so we use a simplified
    version that captures instrument names directly.

    Args:
        note_log: NoteLog instance.
        engine: RadioEngineV8 or RadioEngineV15 instance.
        mood: MoodSegment for this segment.
        sim_state: Simulation state dict.
        seg_start_time: Start time of this segment in seconds.
    """
    rng = random.Random(mood.rng.random())
    tempo = mood.tempo
    tempo_mult = engine._compute_tempo_multiplier(sim_state)
    effective_tempo = min(tempo * tempo_mult, 360)

    loop_bars = rng.randint(4, 12)
    bars_result = engine.midi_lib.sample_bars_seeded(
        sim_state, loop_bars, effective_tempo, mood.beats_per_bar,
        root=mood.root, scale=mood.scale, rng=rng
    )
    midi_notes, segment_duration, midi_info = bars_result

    if not midi_notes or segment_duration <= 0:
        return

    # Get instrument names (V8 has simpler instrument list)
    instr_names = []
    for instr in engine.instruments[:4]:
        name = instr.get('name', 'unknown')
        instr_names.append(name)
    if not instr_names:
        instr_names = ['synth']

    for t_sec, midi_note, dur_sec, vel in midi_notes:
        abs_time = seg_start_time + t_sec
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


TRACK_NAMES = [
    "Ember", "Torrent", "Quartz", "Tide", "Root", "Glacier",
    "Bloom", "Dusk", "Coral", "Moss", "Thunder", "Horizon",
]

ALBUM_NAME = "In The Beginning Phase 0 — V8 Sessions"
ARTIST = "aiphenomenon (A. Johan Bizzle)"


def render_engine_to_wav(engine_cls, seed, duration, wav_path, label):
    """Render an engine directly to a WAV file with NoteLog.

    Streams to disk to conserve memory.

    Args:
        engine_cls: Engine class (RadioEngineV8 or RadioEngineV15_V8Tempo).
        seed: Random seed.
        duration: Duration in seconds.
        wav_path: Output WAV file path.
        label: Label for progress messages.

    Returns:
        NoteLog with recorded events.
    """
    ct_now = _time.strftime('%Y-%m-%d %H:%M CT', _time.localtime())
    print(f"[{ct_now}] Rendering {label} (seed={seed}, {duration}s)...")

    engine = engine_cls(seed=seed, total_duration=duration)
    note_log = NoteLog()

    n_segments = len(engine.segments)
    sim_states = engine._generate_sim_states(n_segments)

    orig, patched = engine._patch_mood_init()
    MoodSegment.__init__ = patched

    try:
        with wave.open(wav_path, 'wb') as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)

            total_samples = int(duration * SAMPLE_RATE)
            morph_samples = int(engine.MORPH_DURATION * SAMPLE_RATE)
            fade_in_samples = int(engine.FADE_IN_DURATION * SAMPLE_RATE)
            fade_out_samples = int(engine.FADE_OUT_DURATION * SAMPLE_RATE)

            max_seg_samples = int(220 * SAMPLE_RATE)
            buf_len = max_seg_samples + morph_samples * 2
            buf_left = [0.0] * buf_len
            buf_right = [0.0] * buf_len
            buf_global_start = 0
            samples_written = 0
            _tanh = math.tanh

            for seg_idx in range(n_segments):
                seg_info = engine.segments[seg_idx]
                seg_global_start = int(seg_info['start'] * SAMPLE_RATE)
                seg_duration_s = seg_info['duration']
                segment_samples = int(seg_duration_s * SAMPLE_RATE)
                if seg_global_start >= total_samples:
                    break

                time_pos = seg_info['start']
                epoch_idx = int(time_pos / engine.total_duration * 12.999)
                epoch_idx = clamp(epoch_idx, 0, 12)
                epoch = EPOCH_ORDER[epoch_idx]
                sim_state = sim_states[min(seg_idx, len(sim_states) - 1)]

                mood = MoodSegment(
                    seg_idx, epoch, epoch_idx, sim_state,
                    engine.seed + seg_idx * 31337
                )
                selected = engine._select_instruments(mood)
                kits = InstrumentKit.build_kits(
                    selected, mood.scale, mood.root, mood.n_kits, mood.rng
                )
                seg_left, seg_right = engine._render_segment(
                    mood, kits, segment_samples, sim_state
                )

                # Log notes
                _log_segment_notes_v8(note_log, engine, mood, sim_state,
                                      seg_info['start'])

                if mood.dampen:
                    seg_left = engine.smoother.apply_lowpass(seg_left, 5000)
                    seg_right = engine.smoother.apply_lowpass(seg_right, 5000)
                    seg_left = engine.smoother.apply_gentle_compression(seg_left)
                    seg_right = engine.smoother.apply_gentle_compression(seg_right)

                seg_end_global = min(seg_global_start + len(seg_left),
                                     total_samples)
                seg_len = seg_end_global - seg_global_start

                for i in range(seg_len):
                    global_i = seg_global_start + i
                    buf_i = global_i - buf_global_start
                    while buf_i >= len(buf_left):
                        buf_left.append(0.0)
                        buf_right.append(0.0)

                    fade = 1.0
                    if i < morph_samples and seg_idx > 0:
                        fade = 0.5 - 0.5 * math.cos(
                            math.pi * i / morph_samples)
                    remaining = seg_len - i
                    if remaining < morph_samples and seg_idx < n_segments - 1:
                        fade *= 0.5 + 0.5 * math.cos(
                            math.pi * (1 - remaining / morph_samples))

                    if global_i < fade_in_samples:
                        fade *= global_i / fade_in_samples
                    elif global_i >= total_samples - fade_out_samples:
                        fade *= (total_samples - global_i) / fade_out_samples

                    buf_left[buf_i] += seg_left[i] * fade
                    buf_right[buf_i] += seg_right[i] * fade

                # Flush completed audio to disk
                if seg_idx < n_segments - 1:
                    next_seg_start = int(
                        engine.segments[seg_idx + 1]['start'] * SAMPLE_RATE)
                    flush_up_to = next_seg_start - morph_samples
                else:
                    flush_up_to = total_samples

                flush_end = min(flush_up_to, total_samples)
                flush_count = flush_end - samples_written
                if flush_count > 0:
                    data = bytearray(flush_count * 4)
                    for j in range(flush_count):
                        buf_j = (samples_written + j) - buf_global_start
                        lv = (buf_left[buf_j]
                              if 0 <= buf_j < len(buf_left) else 0.0)
                        rv = (buf_right[buf_j]
                              if 0 <= buf_j < len(buf_right) else 0.0)
                        lv = max(-1.0, min(1.0, _tanh(lv)))
                        rv = max(-1.0, min(1.0, _tanh(rv)))
                        ls = max(-32767, min(32767, int(lv * 32767)))
                        rs = max(-32767, min(32767, int(rv * 32767)))
                        struct.pack_into('<hh', data, j * 4, ls, rs)
                    wf.writeframes(data)
                    samples_written += flush_count

                # Reclaim buffer
                if flush_count > 0:
                    keep_from = samples_written - buf_global_start
                    if keep_from > 0:
                        buf_left = buf_left[keep_from:] + [0.0] * keep_from
                        buf_right = buf_right[keep_from:] + [0.0] * keep_from
                        buf_global_start = samples_written

                ct_now = _time.strftime('%Y-%m-%d %H:%M CT', _time.localtime())
                elapsed = seg_info['start'] + seg_duration_s
                print(f"  [{ct_now}] Segment {seg_idx+1}/{n_segments} "
                      f"({elapsed:.0f}s / {duration:.0f}s rendered)")

            # Flush remaining
            remaining_count = total_samples - samples_written
            if remaining_count > 0:
                data = bytearray(remaining_count * 4)
                for j in range(remaining_count):
                    buf_j = (samples_written + j) - buf_global_start
                    lv = (buf_left[buf_j]
                          if 0 <= buf_j < len(buf_left) else 0.0)
                    rv = (buf_right[buf_j]
                          if 0 <= buf_j < len(buf_right) else 0.0)
                    lv = max(-1.0, min(1.0, _tanh(lv)))
                    rv = max(-1.0, min(1.0, _tanh(rv)))
                    ls = max(-32767, min(32767, int(lv * 32767)))
                    rs = max(-32767, min(32767, int(rv * 32767)))
                    struct.pack_into('<hh', data, j * 4, ls, rs)
                wf.writeframes(data)

    finally:
        MoodSegment.__init__ = orig

    ct_now = _time.strftime('%Y-%m-%d %H:%M CT', _time.localtime())
    n_events = note_log.to_dict()['n_events']
    print(f"[{ct_now}] {label} done: {n_events} note events, WAV: {wav_path}")
    return note_log


def find_split_points_wav(wav_path, n_tracks, sr=SAMPLE_RATE):
    """Find optimal split points in a WAV file at low-energy boundaries.

    Reads the WAV file and scans for quietest 0.5s windows near each
    target split point.

    Args:
        wav_path: Path to the WAV file.
        n_tracks: Number of tracks to split into.
        sr: Sample rate.

    Returns:
        List of (start_sample, end_sample) tuples for each track.
    """
    with wave.open(wav_path, 'rb') as wf:
        total_samples = wf.getnframes()
        raw = wf.readframes(total_samples)

    target_track_len = total_samples // n_tracks
    min_track_len = int(3 * 60 * sr)  # 3 minutes
    window_samples = int(0.5 * sr)
    search_radius = int(60 * sr)

    split_points = [0]

    for i in range(1, n_tracks):
        target = i * target_track_len
        best_pos = target
        best_energy = float('inf')

        search_start = max(split_points[-1] + min_track_len,
                          target - search_radius)
        search_end = min(total_samples - min_track_len * (n_tracks - i),
                        target + search_radius)

        if search_start >= search_end:
            search_start = split_points[-1] + min_track_len
            search_end = min(total_samples, search_start + search_radius * 2)

        step = sr // 4
        for pos in range(search_start, search_end, step):
            end_pos = min(pos + window_samples, total_samples)
            energy = 0.0
            count = end_pos - pos
            for j in range(pos, end_pos):
                offset = j * 4
                if offset + 4 <= len(raw):
                    ls, rs = struct.unpack_from('<hh', raw, offset)
                    lv = ls / 32767.0
                    rv = rs / 32767.0
                    energy += lv * lv + rv * rv
            if count > 0:
                energy /= count
            if energy < best_energy:
                best_energy = energy
                best_pos = pos

        split_points.append(best_pos)

    split_points.append(total_samples)

    tracks = []
    for i in range(n_tracks):
        tracks.append((split_points[i], split_points[i + 1]))

    return tracks


def extract_track_from_wav(src_wav, start, end, out_wav, sr=SAMPLE_RATE):
    """Extract a slice from a WAV file with fade-in/out.

    Args:
        src_wav: Source WAV path.
        start: Start sample index.
        end: End sample index.
        out_wav: Output WAV path.
        sr: Sample rate.
    """
    fade_len = int(0.1 * sr)
    track_len = end - start

    with wave.open(src_wav, 'rb') as rf:
        rf.setpos(start)
        raw = rf.readframes(track_len)

    with wave.open(out_wav, 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)

        data = bytearray(track_len * 4)
        for i in range(track_len):
            offset = i * 4
            if offset + 4 <= len(raw):
                ls, rs = struct.unpack_from('<hh', raw, offset)
            else:
                ls, rs = 0, 0

            # Fade in/out
            if i < fade_len:
                fade = i / fade_len
                ls = int(ls * fade)
                rs = int(rs * fade)
            elif i > track_len - fade_len:
                fade = (track_len - i) / fade_len
                ls = int(ls * fade)
                rs = int(rs * fade)

            struct.pack_into('<hh', data, i * 4, ls, rs)

        wf.writeframes(data)


def extract_track_notes(note_log, start_time, end_time, track_offset=0.0):
    """Extract and rebase note events for a time range.

    Args:
        note_log: NoteLog with all events.
        start_time: Track start time in seconds.
        end_time: Track end time in seconds.
        track_offset: Time offset to subtract (usually start_time).

    Returns:
        List of event dicts with times rebased to track start.
    """
    events = []
    for ev in note_log.events:
        t = ev['t']
        dur = ev.get('dur', 0)
        # Include events that overlap with the track range
        if t + dur > start_time and t < end_time:
            new_ev = dict(ev)
            new_ev['t'] = round(max(0, t - track_offset), 3)
            # Clip duration to track boundary
            if t < start_time:
                clipped = start_time - t
                new_ev['dur'] = round(dur - clipped, 3)
            if t + dur > end_time:
                new_ev['dur'] = round(end_time - max(t, start_time), 3)
            events.append(new_ev)
    return events


def concatenate_wavs(wav1_path, wav2_path, output_path, sr=SAMPLE_RATE):
    """Concatenate two WAV files into one.

    Args:
        wav1_path: First WAV file.
        wav2_path: Second WAV file.
        output_path: Output WAV file.
        sr: Sample rate.

    Returns:
        Total number of frames in the output.
    """
    with wave.open(output_path, 'wb') as out:
        out.setnchannels(2)
        out.setsampwidth(2)
        out.setframerate(sr)

        for path in [wav1_path, wav2_path]:
            with wave.open(path, 'rb') as rf:
                chunk_size = 44100 * 4  # Read 1 second at a time
                while True:
                    raw = rf.readframes(44100)
                    if not raw:
                        break
                    out.writeframes(raw)

    with wave.open(output_path, 'rb') as wf:
        return wf.getnframes()


def main():
    """Generate the 12-track V8 Sessions album."""
    base = os.path.dirname(__file__)
    output_dir = os.path.join(base, 'output', 'v8_album')
    os.makedirs(output_dir, exist_ok=True)

    ct_now = _time.strftime('%Y-%m-%d %H:%M CT', _time.localtime())
    print(f"[{ct_now}] === Generating {ALBUM_NAME} ===")
    print(f"[{ct_now}] Output: {output_dir}")
    print(f"[{ct_now}] Tracks: {len(TRACK_NAMES)}")
    print()

    t0 = _time.time()

    # Paths for intermediate WAV files
    v8_wav = os.path.join(output_dir, '_v8_raw.wav')
    v18_wav = os.path.join(output_dir, '_v18_raw.wav')
    combined_wav = os.path.join(output_dir, '_combined.wav')

    # Render both engines to disk
    v8_notes = render_engine_to_wav(
        RadioEngineV8, seed=42, duration=1800.0,
        wav_path=v8_wav, label="V8 (orchestral)")

    v18_notes = render_engine_to_wav(
        RadioEngineV15_V8Tempo, seed=42, duration=1800.0,
        wav_path=v18_wav, label="V18-V8 (V15 synth + V8 tempo)")

    # Combine note logs (shift V18 times by V8 duration)
    v8_duration = 1800.0
    combined_notes = NoteLog()
    combined_notes.events = list(v8_notes.events)
    for ev in v18_notes.events:
        shifted = dict(ev)
        shifted['t'] = round(ev['t'] + v8_duration, 3)
        combined_notes.events.append(shifted)

    # Concatenate WAV files
    ct_now = _time.strftime('%Y-%m-%d %H:%M CT', _time.localtime())
    print(f"\n[{ct_now}] Concatenating WAV files...")
    total_frames = concatenate_wavs(v8_wav, v18_wav, combined_wav)
    total_duration = total_frames / SAMPLE_RATE
    print(f"[{ct_now}] Combined: {total_duration:.1f}s "
          f"({total_duration/60:.1f} min), "
          f"{len(combined_notes.events)} note events")

    # Clean up intermediate WAVs
    os.remove(v8_wav)
    os.remove(v18_wav)

    # Find split points
    ct_now = _time.strftime('%Y-%m-%d %H:%M CT', _time.localtime())
    print(f"[{ct_now}] Finding optimal split points for 12 tracks...")
    track_ranges = find_split_points_wav(combined_wav, 12)

    # Generate each track
    album_tracks = []
    prefix = "V8_Sessions-aiphenomenon"

    for i, (start, end) in enumerate(track_ranges):
        name = TRACK_NAMES[i]
        track_num = i + 1
        start_time = start / SAMPLE_RATE
        end_time = end / SAMPLE_RATE
        track_duration = end_time - start_time

        ct_now = _time.strftime('%Y-%m-%d %H:%M CT', _time.localtime())
        print(f"\n[{ct_now}] Track {track_num:02d}: {name} "
              f"({track_duration:.1f}s = {track_duration/60:.1f} min)")

        # File names
        safe_name = name.replace(' ', '_')
        mp3_name = f"{prefix}-{track_num:02d}-{safe_name}.mp3"
        notes_name = f"{prefix}-{track_num:02d}-{safe_name}_notes.json"
        wav_path = os.path.join(output_dir, f"track_{track_num:02d}.wav")
        mp3_path = os.path.join(output_dir, mp3_name)
        notes_path = os.path.join(output_dir, notes_name)

        # Extract track from combined WAV
        extract_track_from_wav(combined_wav, start, end, wav_path)

        # Convert to MP3
        wav_to_mp3(wav_path, mp3_path)
        os.remove(wav_path)

        mp3_size = os.path.getsize(mp3_path)
        print(f"  MP3: {mp3_name} ({mp3_size:,} bytes)")

        # Extract and save note events
        track_events = extract_track_notes(
            combined_notes, start_time, end_time, track_offset=start_time)

        notes_data = {
            'track_num': track_num,
            'title': name,
            'duration': round(track_duration, 3),
            'start_time': round(start_time, 3),
            'n_events': len(track_events),
            'events': track_events,
        }
        with open(notes_path, 'w') as f:
            json.dump(notes_data, f, separators=(',', ':'))

        print(f"  Notes: {notes_name} ({len(track_events)} events)")

        album_tracks.append({
            'track_num': track_num,
            'title': name,
            'file': notes_name,
            'audio_file': mp3_name,
            'duration': round(track_duration, 3),
            'start_time': round(start_time, 3),
            'n_events': len(track_events),
        })

    # Clean up combined WAV
    if os.path.exists(combined_wav):
        os.remove(combined_wav)

    # Write album_notes.json (index file)
    album_data = {
        'album': ALBUM_NAME,
        'artist': ARTIST,
        'n_tracks': len(album_tracks),
        'total_duration': round(total_duration, 3),
        'total_events': len(combined_notes.events),
        'seed_v8': 42,
        'seed_v18': 42,
        'engines': ['RadioEngineV8', 'RadioEngineV15_V8Tempo'],
        'tracks': album_tracks,
    }
    album_path = os.path.join(output_dir, 'album_notes.json')
    with open(album_path, 'w') as f:
        json.dump(album_data, f, indent=2)

    elapsed = _time.time() - t0
    ct_now = _time.strftime('%Y-%m-%d %H:%M CT', _time.localtime())
    print(f"\n[{ct_now}] === Album generation complete ===")
    print(f"  Tracks: {len(album_tracks)}")
    print(f"  Total duration: {total_duration:.1f}s ({total_duration/60:.1f} min)")
    print(f"  Total events: {len(combined_notes.events)}")
    print(f"  Elapsed: {elapsed:.1f}s ({elapsed/60:.1f} min)")
    print(f"  Output: {output_dir}")


if __name__ == '__main__':
    main()
