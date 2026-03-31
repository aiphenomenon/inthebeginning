# V36 Plan — Game V11 Bug Fixes

## Date: 2026-03-31

## Bugs to Fix (24 items)

### Audio/Playback
1. +/- buttons speed gameplay only, NOT music
2. Stop music on refresh/restart (again — may have regressed)
3. WASM playback broken in Firefox+Chrome stable Ubuntu 24.04
4. Synth mutation cacophony — additive noise buildup
5. Sound Mutation unpredictable — examine and fix
6. Sound Mutation button only shows for MIDI/Synth/WASM

### Gameplay/Scoring
7. Grid mode: no final score when non-infinite ends
8. 3D objects too fast on mobile, slightly too fast on desktop
9. 3D emoji pile up at bottom — should fade away
10. 3D jump-over scoring: ±1 player width margin
11. Emoji should not cross lanes (stay in their lane)
12. 2D/3D buttons don't change gameplay visualization
13. Key 3 (grid mode switch) doesn't work in gameplay

### UI/Mobile
14. MIDI track listing: show next/prev 12 tracks
15. Mobile: no next/prev track buttons visible
16. Mobile: multiple taps spawns track listing unexpectedly
17. Mobile 2-player: flick-to-jump gesture
18. Double pause button icon (screenshot provided)

### Data/Content
19. MP3 Album JSON note data incomplete (cuts off ~8s)
20. Instrument Soundbank not honored in Synth mode
21. Instrument Soundbank modal text should mention Synth/WASM not just MIDI

### Visual
22. Theme colors/star shapes more pronounced + "Default" option
23. Controls Guide keyboard mappings don't work in Music mode
24. 2P instructions on main menu incorrect

## Approach
- Create deploy/v11 from v10
- Fix each bug with Playwright verification
- Screenshot before/after for session log
- Commit in batches of 3-5 fixes
