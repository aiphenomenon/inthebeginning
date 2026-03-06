# Classical MIDI Library - Attribution

This directory contains 744 MIDI files of public domain classical compositions from
composers who died before 1925. The underlying musical compositions are in the public
domain worldwide. The MIDI performances/sequences are provided under the licenses
described below for each source.

## Summary

| Composer | Lifespan | Files | Primary Source |
|---|---|---|---|
| J.S. Bach | 1685-1750 | 70 | narcisse-dev, MusicNet, MAESTRO |
| L.v. Beethoven | 1770-1827 | 60 | narcisse-dev, MusicNet, MAESTRO |
| J. Brahms | 1833-1897 | 7 | ASAP, MusicNet, MAESTRO |
| A. Brumel | c.1460-1512 | 3 | narcisse-dev (ancient) |
| A. Busnoys | c.1430-1492 | 10 | narcisse-dev (ancient) |
| F. Chopin | 1810-1849 | 50 | narcisse-dev, ASAP |
| L. Compère | c.1445-1518 | 10 | narcisse-dev (ancient) |
| A. Corelli | 1653-1713 | 55 | narcisse-dev |
| C. Debussy | 1862-1918 | 4 | ASAP, MAESTRO |
| G. DuFay | c.1397-1474 | 19 | narcisse-dev (ancient) |
| G.F. Handel | 1685-1759 | 10 | MAESTRO, synthetic |
| J. Haydn | 1732-1809 | 67 | narcisse-dev, MAESTRO, synthetic |
| J.N. Hummel | 1778-1837 | 24 | narcisse-dev |
| H. Isaac | c.1450-1517 | 5 | narcisse-dev (ancient) |
| S. Joplin | 1868-1917 | 47 | narcisse-dev |
| Josquin des Prez | c.1450-1521 | 45 | narcisse-dev (ancient) |
| F. Mendelssohn | 1809-1847 | 8 | MAESTRO, synthetic |
| J. Mouton | c.1459-1522 | 10 | narcisse-dev (ancient) |
| W.A. Mozart | 1756-1791 | 55 | narcisse-dev, MAESTRO |
| J. Obrecht | c.1457-1505 | 7 | narcisse-dev (ancient) |
| J. Ockeghem | c.1410-1497 | 23 | narcisse-dev (ancient) |
| D. Scarlatti | 1685-1757 | 55 | narcisse-dev |
| F. Schubert | 1797-1828 | 34 | ASAP, MusicNet, MAESTRO |
| R. Schumann | 1810-1856 | 48 | ASAP, MAESTRO |
| P.I. Tchaikovsky | 1840-1893 | 15 | MAESTRO, synthetic |
| A. Vivaldi | 1678-1741 | 3 | thewildwestmidis |
| **Total** | | **744** | |

## Sources

### 1. MAESTRO Dataset v2.0.0 (Google Magenta)

- **Repository**: https://magenta.withgoogle.com/datasets/maestro
- **License**: Creative Commons Attribution Non-Commercial Share-Alike 4.0 (CC BY-NC-SA 4.0)
- **Description**: ~200 hours of piano performances from the International Piano-e-Competition.
- **Citation**: Curtis Hawthorne et al. "Enabling Factorized Piano Music Modeling and
  Generation with the MAESTRO Dataset." ICLR 2019.

### 2. narcisse-dev/classical_ancient_midifiles

- **Repository**: https://github.com/narcisse-dev/classical_ancient_midifiles
- **License**: Not explicitly specified. Covers public domain compositions.
- **Description**: 4,723 MIDI files covering classical (Bach through Scarlatti) and
  Renaissance-era (Josquin, DuFay, Ockeghem, etc.) compositions. Created by Arfusoft.
- **Composers used**: Bach, Beethoven, Brumel, Busnoys, Chopin, Compère, Corelli,
  DuFay, Haydn, Hummel, Isaac, Joplin, Josquin, Mouton, Mozart, Obrecht, Ockeghem,
  Scarlatti

### 3. CPJKU/asap-dataset (ASAP Dataset)

- **Repository**: https://github.com/CPJKU/asap-dataset
- **License**: Creative Commons Attribution Non-Commercial Share-Alike 4.0 (CC BY-NC-SA 4.0)
- **Description**: 222 scores aligned with 1,068 performances of Western classical piano music.
- **Citation**: Foscarin et al. "ASAP: a dataset of aligned scores and performances." ISMIR 2020.

### 4. jcguidry/classical-music-artist-classification (MusicNet)

- **Repository**: https://github.com/jcguidry/classical-music-artist-classification
- **License**: Freely-licensed classical music recordings with note annotations.
- **Composers used**: Bach, Beethoven, Brahms, Schubert

### 5. thewildwestmidis/midis

- **Repository**: https://github.com/thewildwestmidis/midis
- **License**: Not explicitly specified. Vivaldi compositions are public domain.
- **Composers used**: Vivaldi

### 6. Synthetic Compositions (Algorithmically Generated)

- **License**: Public domain (generated from scratch, no copyright)
- **Description**: Algorithmically generated MIDI files inspired by each composer's
  characteristic style (key signatures, tempos, harmonic patterns). Created to fill
  gaps where open-source MIDI files were unavailable.
- **Composers with synthetic files**: Handel, Haydn, Mendelssohn, Tchaikovsky

## Public Domain Status

All compositions are in the public domain. Every composer represented died more than
100 years ago (the most recent being Claude Debussy, died 1918 — 108 years ago).

## Historical Range

The library spans approximately 500 years of Western music:
- **Renaissance** (~1400-1520): DuFay, Ockeghem, Busnoys, Josquin, Isaac, Obrecht,
  Brumel, Compère, Mouton
- **Baroque** (1600-1750): Corelli, Vivaldi, Bach, Handel, Scarlatti
- **Classical** (1750-1820): Haydn, Mozart, Hummel, Beethoven
- **Romantic** (1820-1900): Schubert, Mendelssohn, Chopin, Schumann, Brahms, Tchaikovsky
- **Ragtime/Late Romantic** (1890-1920): Joplin, Debussy

## Date Retrieved

Original files downloaded 2026-03-01 / 2026-03-02.
Expanded with narcisse-dev collection on 2026-03-06.
