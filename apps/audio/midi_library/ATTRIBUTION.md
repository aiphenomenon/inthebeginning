# Classical MIDI Library - Attribution

This directory contains 249 MIDI files of public domain classical compositions from
composers who died before 1925. The underlying musical compositions are in the public
domain worldwide. The MIDI performances/sequences are provided under the licenses
described below for each source.

## Summary

| Composer | Lifespan | Files | Primary Source |
|---|---|---|---|
| J.S. Bach | 1685-1750 | 25 | narcisse-dev, MusicNet, MAESTRO |
| G.F. Handel | 1685-1759 | 8 | MAESTRO |
| A. Vivaldi | 1678-1741 | 3 | thewildwestmidis |
| W.A. Mozart | 1756-1791 | 12 | narcisse-dev, MAESTRO |
| L.v. Beethoven | 1770-1827 | 22 | narcisse-dev, MusicNet, MAESTRO |
| F. Schubert | 1797-1828 | 38 | ASAP, MusicNet, MAESTRO |
| F. Mendelssohn | 1809-1847 | 12 | MAESTRO |
| F. Chopin | 1810-1849 | 20 | narcisse-dev, ASAP |
| R. Schumann | 1810-1856 | 48 | ASAP, MAESTRO |
| J. Brahms | 1833-1897 | 23 | ASAP, MusicNet, MAESTRO |
| P.I. Tchaikovsky | 1840-1893 | 9 | MAESTRO |
| C. Debussy | 1862-1918 | 19 | ASAP, MAESTRO |
| J. Haydn | 1732-1809 | 10 | MAESTRO |
| **Total** | | **249** | |

## Sources

### 1. MAESTRO Dataset v2.0.0 (Google Magenta)

- **Repository**: https://magenta.withgoogle.com/datasets/maestro
- **Download URL**: https://storage.googleapis.com/magentadata/datasets/maestro/v2.0.0/maestro-v2.0.0-midi.zip
- **License**: Creative Commons Attribution Non-Commercial Share-Alike 4.0 (CC BY-NC-SA 4.0)
- **Description**: MAESTRO (MIDI and Audio Edited for Synchronous TRacks and
  Organization) contains approximately 200 hours of virtuosic piano performances
  captured with fine alignment (~3 ms) between note labels and audio waveforms.
  The data comes from the International Piano-e-Competition, where pianists perform
  on Yamaha Disklaviers (concert-quality acoustic grand pianos with integrated
  high-precision MIDI capture). The dataset contains 1,282 MIDI files total.
- **Citation**: Curtis Hawthorne, Andriy Stasyuk, Adam Roberts, Ian Simon,
  Cheng-Zhi Anna Huang, Sander Dieleman, Erich Elsen, Jesse Engel, and
  Douglas Eck. "Enabling Factorized Piano Music Modeling and Generation with
  the MAESTRO Dataset." In International Conference on Learning Representations, 2019.
- **Composers used from this source**: Bach, Beethoven, Brahms, Chopin, Debussy,
  Handel, Haydn, Mendelssohn, Mozart, Schubert, Schumann, Tchaikovsky

#### MAESTRO Works Included

- **Bach**: Chromatic Fantasy and Fugue, English Suites, Partitas, Well-Tempered Clavier
- **Beethoven**: Eroica Variations, Piano Sonatas, Bagatelles
- **Brahms**: Paganini Variations, Waltzes, Fantasies, Piano Sonatas
- **Chopin**: Etudes, Preludes, Polonaises, Ballades, Scherzi
- **Debussy**: Images, Preludes (Books I & II), L'isle joyeuse
- **Handel**: Chaconne in G, Suite No. 2 in F Major, Suite No. 3 in D Minor
- **Haydn**: Piano Sonatas in various keys
- **Mendelssohn**: Rondo Capriccioso, Variations Serieuses, Fantasy in F-sharp Minor
- **Mozart**: Piano Sonatas, Rondo in A Minor, Variations
- **Schubert**: Impromptus, Wanderer Fantasy, Moments Musicaux, Lieder transcriptions
- **Schumann**: Carnaval, Kreisleriana, Fantasy Pieces, Davidsbundlertanze
- **Tchaikovsky**: Dumka Op. 59, The Seasons Op. 37a, Meditation, Russian Scherzo Op. 1

### 2. narcisse-dev/classical_ancient_midifiles

- **Repository**: https://github.com/narcisse-dev/classical_ancient_midifiles
- **License**: Not explicitly specified in the repository. The MIDI sequences cover
  public domain compositions. The repository is created by Arfusoft for their
  Classical Music and Ancient Music applications.
- **Description**: A collection of MIDI files for classical and ancient music,
  covering compositions from Bach, Beethoven, Chopin, Scarlatti, Joplin, Mozart,
  Corelli, and Haydn. The repository contains 4,723 MIDI files total across
  classical and Renaissance-era compositions.
- **Composers used from this source**: Bach, Beethoven, Chopin, Mozart

### 3. CPJKU/asap-dataset (ASAP Dataset)

- **Repository**: https://github.com/CPJKU/asap-dataset
- **License**: Creative Commons Attribution Non-Commercial Share-Alike 4.0 (CC BY-NC-SA 4.0)
- **Description**: ASAP (A dataset of Aligned Scores and Performances) contains 222
  digital musical scores aligned with 1,068 performances (more than 92 hours) of
  Western classical piano music. Scores and performances are distributed in a folder
  system structured as composer/subgroup/piece. The dataset includes MIDI scores and
  performance MIDI files.
- **Citation**: Francesco Foscarin, Andrew McLeod, Philipp Rigaux, Florent Jacquemard,
  and Masahiko Sakai. "ASAP: a dataset of aligned scores and performances for piano
  transcription." In Proceedings of the International Society for Music Information
  Retrieval Conference (ISMIR), 2020.
- **Composers used from this source**: Brahms, Chopin, Debussy, Schubert, Schumann

#### ASAP Works Included

- **Brahms**: Piano pieces
- **Chopin**: Mazurkas, Ballades, Nocturnes, Etudes, Preludes
- **Debussy**: Preludes, Suite bergamasque
- **Schubert**: Impromptus, Piano Sonatas, Moments Musicaux
- **Schumann**: Kinderszenen, Kreisleriana, Papillons

### 4. jcguidry/classical-music-artist-classification (MusicNet)

- **Repository**: https://github.com/jcguidry/classical-music-artist-classification
- **Original data source**: MusicNet (https://zenodo.org/record/5120004)
- **License**: The MIDI files in this repository are sourced from MusicNet. MusicNet
  consists of freely-licensed classical music recordings with note annotations.
- **Description**: A machine learning project for classifying classical music by
  composer. The dataset contains several hundred annotated MIDI files from four
  composers: Bach, Beethoven, Schubert, and Brahms. The MIDI files include
  chamber music (string quartets, piano sonatas, orchestral works).
- **Composers used from this source**: Bach, Beethoven, Brahms, Schubert

### 5. thewildwestmidis/midis

- **Repository**: https://github.com/thewildwestmidis/midis
- **License**: Not explicitly specified. The repository is a community-contributed
  collection of MIDI files. The underlying Vivaldi compositions (1678-1741) are
  in the public domain.
- **Description**: A large community MIDI collection containing 1,700+ files across
  many genres. Three Vivaldi arrangements of "The Four Seasons - Winter" were
  sourced from this collection.
- **Composers used from this source**: Vivaldi

## Public Domain Status of Compositions

All compositions in this collection are in the public domain because their composers
died more than 100 years ago (well before 1925). Under the laws of virtually all
countries, musical works enter the public domain after a period following the death
of the composer (typically 50-70 years after death, depending on jurisdiction).

| Composer | Death Year | Years Since Death |
|---|---|---|
| Antonio Vivaldi | 1741 | 285 years |
| Johann Sebastian Bach | 1750 | 276 years |
| George Frideric Handel | 1759 | 267 years |
| Joseph Haydn | 1809 | 217 years |
| Wolfgang Amadeus Mozart | 1791 | 235 years |
| Ludwig van Beethoven | 1827 | 199 years |
| Franz Schubert | 1828 | 198 years |
| Felix Mendelssohn | 1847 | 179 years |
| Frederic Chopin | 1849 | 177 years |
| Robert Schumann | 1856 | 170 years |
| Johannes Brahms | 1897 | 129 years |
| Pyotr Ilyich Tchaikovsky | 1893 | 133 years |
| Claude Debussy | 1918 | 108 years |

## Note on MIDI Performances vs. Compositions

While the underlying musical compositions are in the public domain, the specific MIDI
performances and sequences may carry their own copyright. The MIDI files in this
collection are distributed under the licenses specified by their respective sources
(primarily CC BY-NC-SA 4.0 for MAESTRO and ASAP). These licenses govern the use of
the specific MIDI data (note timings, velocities, pedaling), not the underlying
compositions themselves.

## Missing Composers

The following requested composer could not be sourced from available GitHub
repositories or accessible online collections:

- **Antonin Dvorak (1841-1904)**: Dvorak's major works are primarily orchestral and
  chamber music (symphonies, string quartets, cello concerto), which are not well
  represented in piano MIDI datasets. The piano competition datasets (MAESTRO, ASAP)
  do not include Dvorak works, and no GitHub repository with Dvorak MIDI files was
  found accessible from this environment.

## Directory Structure

```
midi_library/
  Bach/           25 files - Chorales, Fugues, Suites, Partitas
  Beethoven/      22 files - Piano Sonatas, Variations, Quartets
  Brahms/         23 files - Variations, Waltzes, Fantasies, Sonatas
  Chopin/         20 files - Mazurkas, Etudes, Preludes, Nocturnes
  Debussy/        19 files - Preludes, Images, Suite bergamasque
  Handel/          8 files - Chaconnes, Keyboard Suites
  Haydn/          10 files - Piano Sonatas
  Mendelssohn/    12 files - Rondo Capriccioso, Variations, Fantasy
  Mozart/         12 files - Piano Sonatas, Rondo, Variations
  Schubert/       38 files - Impromptus, Wanderer Fantasy, Sonatas
  Schumann/       48 files - Carnaval, Kreisleriana, Kinderszenen
  Tchaikovsky/     9 files - Dumka, The Seasons, Meditation
  Vivaldi/         3 files - Four Seasons (Winter arrangements)
  ATTRIBUTION.md  (this file)
```

## Date Retrieved

All files were downloaded on 2026-03-01 / 2026-03-02.
