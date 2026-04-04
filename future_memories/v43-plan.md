# V43 Plan — MP3 Album JSON Note Data Completeness

## Date: 2026-04-04

## Problem
MP3 Album JSON note data reportedly "cuts off ~8s" — the visualization data
for MP3 tracks is incomplete, meaning grid colors and note boxes stop
displaying partway through tracks.

## Investigation
1. Git archaeology: find when/how note JSON was generated, what tool produced it
2. Examine the actual JSON files for all 12 tracks — check duration coverage
3. Compare JSON duration vs MP3 duration for each track
4. Identify the gap/truncation point

## Fix
- Regenerate note data if the generation tool exists
- Or fix the generation tool if it's truncating
- Ensure all 12 tracks have note data spanning their full duration

## Validation
- Mathematical estimate: expected JSON size based on track durations and note density
- Full JSON scan: well-formed, expected fields, duration coverage
- Playwright visual tests at 15 equidistant intervals across all 12 tracks
- Screenshot evidence in grid mode and game mode showing notes rendering
  at beginning, middle, and end of tracks
- Add persistent tests for note data completeness

## Deliverables
1. Fixed/regenerated note JSON files for all 12 tracks
2. Tests: note data completeness, duration coverage, field validation
3. Playwright visual validation with screenshots
4. Session log with screenshot evidence
