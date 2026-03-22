#!/usr/bin/env python3
"""Generate a JSON catalog of all MIDI files in the midi_library.

Scans the midi_library directory recursively, classifies each MIDI file
by composer, era, and source, and writes a structured JSON catalog to
the cosmic-runner-v3 audio directory.

Usage:
    python tools/generate_midi_catalog.py
"""

import json
import os
import re

# Paths
MIDI_LIBRARY = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "apps", "audio", "midi_library"
)
OUTPUT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "apps", "cosmic-runner-v3", "audio", "midi_catalog.json"
)
ATTRIBUTION_PATH = os.path.join(MIDI_LIBRARY, "ATTRIBUTION.md")

# Era classifications based on composer birth years and musicological convention.
# Format: directory_name -> (era, display_name)
COMPOSER_ERA_MAP = {
    # Renaissance (c.1400-1600)
    "DuFay": ("Renaissance", "DuFay"),
    "Ockeghem": ("Renaissance", "Ockeghem"),
    "Busnoys": ("Renaissance", "Busnoys"),
    "Josquin": ("Renaissance", "Josquin des Prez"),
    "Isaac": ("Renaissance", "Isaac"),
    "Obrecht": ("Renaissance", "Obrecht"),
    "Brumel": ("Renaissance", "Brumel"),
    "Compere": ("Renaissance", "Compere"),
    "Mouton": ("Renaissance", "Mouton"),
    "Tallis": ("Renaissance", "Tallis"),

    # Baroque (1600-1750)
    "Blow": ("Baroque", "Blow"),
    "Lully": ("Baroque", "Lully"),
    "Corelli": ("Baroque", "Corelli"),
    "Pachelbel": ("Baroque", "Pachelbel"),
    "Purcell": ("Baroque", "Purcell"),
    "Albinoni": ("Baroque", "Albinoni"),
    "Couperin": ("Baroque", "Couperin"),
    "Vivaldi": ("Baroque", "Vivaldi"),
    "Rameau": ("Baroque", "Rameau"),
    "Telemann": ("Baroque", "Telemann"),
    "Bach": ("Baroque", "Bach"),
    "Handel": ("Baroque", "Handel"),
    "Scarlatti": ("Baroque", "Scarlatti"),
    "Daquin": ("Baroque", "Daquin"),
    "Krieger": ("Baroque", "Krieger"),
    "Mouret": ("Baroque", "Mouret"),
    "Petzold": ("Baroque", "Petzold"),
    "CPEBach": ("Baroque", "C.P.E. Bach"),
    "JCBach": ("Baroque", "J.C. Bach"),
    "WFBach": ("Baroque", "W.F. Bach"),
    "LeopoldMozart": ("Classical", "Leopold Mozart"),
    "Wagenseil": ("Classical", "Wagenseil"),
    "Caccini": ("Baroque", "Caccini"),

    # Classical (1750-1820)
    "Gluck": ("Classical", "Gluck"),
    "Haydn": ("Classical", "Haydn"),
    "Clementi": ("Classical", "Clementi"),
    "Mozart": ("Classical", "Mozart"),
    "Salieri": ("Classical", "Salieri"),
    "Dussek": ("Classical", "Dussek"),
    "Hummel": ("Classical", "Hummel"),
    "Beethoven": ("Classical", "Beethoven"),
    "Diabelli": ("Classical", "Diabelli"),
    "Kuhlau": ("Classical", "Kuhlau"),
    "Czerny": ("Classical", "Czerny"),
    "Wanhal": ("Classical", "Wanhal"),
    "Ries": ("Classical", "Ries"),

    # Romantic (1820-1900)
    "Schubert": ("Romantic", "Schubert"),
    "Rossini": ("Romantic", "Rossini"),
    "Donizetti": ("Romantic", "Donizetti"),
    "Bellini": ("Romantic", "Bellini"),
    "Mendelssohn": ("Romantic", "Mendelssohn"),
    "Chopin": ("Romantic", "Chopin"),
    "Schumann": ("Romantic", "Schumann"),
    "Liszt": ("Romantic", "Liszt"),
    "Alkan": ("Romantic", "Alkan"),
    "Heller": ("Romantic", "Heller"),
    "Franck": ("Romantic", "Franck"),
    "Lalo": ("Romantic", "Lalo"),
    "Brahms": ("Romantic", "Brahms"),
    "Borodin": ("Romantic", "Borodin"),
    "Saint-Saens": ("Romantic", "Saint-Saens"),
    "Bizet": ("Romantic", "Bizet"),
    "Mussorgsky": ("Romantic", "Mussorgsky"),
    "Tchaikovsky": ("Romantic", "Tchaikovsky"),
    "Ponchielli": ("Romantic", "Ponchielli"),
    "Massenet": ("Romantic", "Massenet"),
    "Faure": ("Romantic", "Faure"),
    "Wagner": ("Romantic", "Wagner"),
    "Verdi": ("Romantic", "Verdi"),
    "Offenbach": ("Romantic", "Offenbach"),
    "Gounod": ("Romantic", "Gounod"),
    "Boccherini": ("Romantic", "Boccherini"),
    "Adam": ("Romantic", "Adam"),
    "Albeniz": ("Romantic", "Albeniz"),
    "Delibes": ("Romantic", "Delibes"),
    "Flotow": ("Romantic", "Flotow"),
    "Giordani": ("Romantic", "Giordani"),
    "Herold": ("Romantic", "Herold"),
    "Mercadante": ("Romantic", "Mercadante"),
    "Minkus": ("Romantic", "Minkus"),
    "Monti": ("Romantic", "Monti"),
    "Paganini": ("Romantic", "Paganini"),
    "Sarasate": ("Romantic", "Sarasate"),
    "Weber": ("Romantic", "Weber"),
    "Reinecke": ("Romantic", "Reinecke"),
    "Scharwenka": ("Romantic", "Scharwenka"),
    "Jadassohn": ("Romantic", "Jadassohn"),
    "Fibich": ("Romantic", "Fibich"),
    "DiCapua": ("Romantic", "Di Capua"),
    "Ivanovici": ("Romantic", "Ivanovici"),
    "Duvernoy": ("Romantic", "Duvernoy"),
    "Maykapar": ("Romantic", "Maykapar"),
    "Paderewski": ("Romantic", "Paderewski"),
    "Pierne": ("Romantic", "Pierne"),
    "Rebikov": ("Romantic", "Rebikov"),
    "Lincke": ("Romantic", "Lincke"),
    "MacDowell": ("Romantic", "MacDowell"),
    "Lamb": ("Romantic", "Lamb"),
    "Bruckner": ("Romantic", "Bruckner"),
    "Dukas": ("Romantic", "Dukas"),
    "Mascagni": ("Romantic", "Mascagni"),
    "Leoncavallo": ("Romantic", "Leoncavallo"),
    "Puccini": ("Romantic", "Puccini"),
    "Clarke": ("Romantic", "Clarke"),

    # Late Romantic / Early Modern (1890-1920)
    "Debussy": ("Late Romantic", "Debussy"),
    "Satie": ("Late Romantic", "Satie"),
    "Glazunov": ("Late Romantic", "Glazunov"),
    "Rachmaninoff": ("Late Romantic", "Rachmaninoff"),
    "Scriabin": ("Late Romantic", "Scriabin"),
    "Ravel": ("Late Romantic", "Ravel"),
    "Holst": ("Late Romantic", "Holst"),
    "Grainger": ("Late Romantic", "Grainger"),
    "RichardStrauss": ("Late Romantic", "Richard Strauss"),
    "Elgar": ("Late Romantic", "Elgar"),
    "Mahler": ("Late Romantic", "Mahler"),
    "Strauss": ("Late Romantic", "Strauss"),
    "Sousa": ("Late Romantic", "Sousa"),
    "Confrey": ("Late Romantic", "Confrey"),
    "Joplin": ("Late Romantic", "Joplin"),

    # Folk
    "TraditionalFolk": ("Folk", "Traditional Folk"),
}

# Source mapping: composer directory -> list of sources
# Derived from ATTRIBUTION.md
COMPOSER_SOURCES = {
    "Bach": ["narcisse-dev", "MusicNet", "MAESTRO", "ADL Piano MIDI"],
    "Beethoven": ["narcisse-dev", "MusicNet", "MAESTRO", "ADL Piano MIDI"],
    "Brahms": ["ASAP", "MusicNet", "MAESTRO", "ADL Piano MIDI"],
    "Brumel": ["narcisse-dev"],
    "Busnoys": ["narcisse-dev"],
    "Chopin": ["narcisse-dev", "ASAP", "ADL Piano MIDI"],
    "Compere": ["narcisse-dev"],
    "Corelli": ["narcisse-dev"],
    "Debussy": ["ASAP", "MAESTRO", "ADL Piano MIDI"],
    "DuFay": ["narcisse-dev"],
    "Handel": ["MAESTRO", "synthetic", "ADL Piano MIDI"],
    "Haydn": ["narcisse-dev", "MAESTRO", "synthetic", "ADL Piano MIDI"],
    "Hummel": ["narcisse-dev"],
    "Isaac": ["narcisse-dev"],
    "Joplin": ["narcisse-dev"],
    "Josquin": ["narcisse-dev"],
    "Mendelssohn": ["MAESTRO", "synthetic", "ADL Piano MIDI"],
    "Mouton": ["narcisse-dev"],
    "Mozart": ["narcisse-dev", "MAESTRO", "ADL Piano MIDI"],
    "Obrecht": ["narcisse-dev"],
    "Ockeghem": ["narcisse-dev"],
    "Scarlatti": ["narcisse-dev", "ADL Piano MIDI"],
    "Schubert": ["ASAP", "MusicNet", "MAESTRO", "ADL Piano MIDI"],
    "Schumann": ["ASAP", "MAESTRO", "ADL Piano MIDI"],
    "Tchaikovsky": ["MAESTRO", "synthetic", "ADL Piano MIDI"],
    "Vivaldi": ["thewildwestmidis"],
    "TraditionalFolk": ["Nottingham Music Database"],
}

# Default source for ADL Piano MIDI composers not in the above map
ADL_COMPOSERS = {
    "Adam", "Albeniz", "Albinoni", "Alkan", "Bellini", "Bizet", "Blow",
    "Boccherini", "Borodin", "Bruckner", "CPEBach", "Caccini", "Clarke",
    "Clementi", "Confrey", "Couperin", "Czerny", "Daquin", "Delibes",
    "DiCapua", "Diabelli", "Donizetti", "Dukas", "Dussek", "Duvernoy",
    "Elgar", "Faure", "Fibich", "Flotow", "Franck", "Giordani", "Glazunov",
    "Gluck", "Gounod", "Grainger", "Heller", "Herold", "Holst", "Ivanovici",
    "JCBach", "Jadassohn", "Krieger", "Kuhlau", "Lalo", "Lamb",
    "Leoncavallo", "LeopoldMozart", "Lincke", "Liszt", "Lully", "MacDowell",
    "Mahler", "Mascagni", "Massenet", "Maykapar", "Mercadante", "Minkus",
    "Monti", "Mouret", "Mussorgsky", "Offenbach", "Pachelbel", "Paderewski",
    "Paganini", "Petzold", "Pierne", "Ponchielli", "Puccini", "Purcell",
    "Rachmaninoff", "Rameau", "Ravel", "Rebikov", "Reinecke",
    "RichardStrauss", "Ries", "Rossini", "Saint-Saens", "Salieri",
    "Sarasate", "Satie", "Scharwenka", "Scriabin", "Sousa", "Strauss",
    "Tallis", "Telemann", "Verdi", "WFBach", "Wagenseil", "Wagner",
    "Wanhal", "Weber",
}


def clean_piece_name(filename, composer_dir):
    """Clean up a MIDI filename into a human-readable piece name.

    Removes prefixes (adl_, nottingham_), file extensions, and converts
    underscores/separators into spaces. Handles Unicode escape sequences.

    Args:
        filename: The raw filename (e.g., 'adl_Moonlight_Sonata.mid')
        composer_dir: The composer directory name for context

    Returns:
        A cleaned piece name string (e.g., 'Moonlight Sonata')
    """
    name = filename
    # Remove extension
    name = re.sub(r'\.(mid|midi)$', '', name, flags=re.IGNORECASE)

    # Remove common prefixes
    name = re.sub(r'^adl_', '', name)
    name = re.sub(r'^nottingham_', '', name)

    # Replace Unicode escape sequences like U00fc with actual characters
    def replace_unicode(m):
        try:
            return chr(int(m.group(1), 16))
        except (ValueError, OverflowError):
            return m.group(0)
    name = re.sub(r'U([0-9a-fA-F]{4})', replace_unicode, name)

    # Replace underscores with spaces
    name = name.replace('_', ' ')

    # Clean up multiple spaces
    name = re.sub(r'\s+', ' ', name).strip()

    # Capitalize first letter if it's lowercase
    if name and name[0].islower():
        name = name[0].upper() + name[1:]

    return name


def get_sources(composer_dir):
    """Get the list of sources for a composer.

    Args:
        composer_dir: The composer directory name

    Returns:
        List of source strings
    """
    if composer_dir in COMPOSER_SOURCES:
        return COMPOSER_SOURCES[composer_dir]
    if composer_dir in ADL_COMPOSERS:
        return ["ADL Piano MIDI"]
    return ["unknown"]


def scan_midi_library():
    """Scan the MIDI library and build the catalog data structures.

    Returns:
        Tuple of (midis_list, composer_stats_dict)
    """
    midis = []
    composer_stats = {}  # dir_name -> {count, era, display_name, sources}

    for dirpath, dirnames, filenames in os.walk(MIDI_LIBRARY):
        dirnames.sort()
        for filename in sorted(filenames):
            if not filename.lower().endswith(('.mid', '.midi')):
                continue

            filepath = os.path.join(dirpath, filename)
            relpath = os.path.relpath(filepath, MIDI_LIBRARY)
            size = os.path.getsize(filepath)

            # Extract composer directory (first path component)
            composer_dir = relpath.split(os.sep)[0]

            # Look up era and display name
            era_info = COMPOSER_ERA_MAP.get(composer_dir)
            if era_info is None:
                era = "Unknown"
                display_name = composer_dir
            else:
                era, display_name = era_info

            piece_name = clean_piece_name(filename, composer_dir)

            midis.append({
                "path": relpath,
                "name": piece_name,
                "composer": display_name,
                "era": era,
                "size": size,
            })

            # Track composer stats
            if composer_dir not in composer_stats:
                composer_stats[composer_dir] = {
                    "name": display_name,
                    "era": era,
                    "count": 0,
                    "sources": get_sources(composer_dir),
                }
            composer_stats[composer_dir]["count"] += 1

    return midis, composer_stats


def build_era_summary(composer_stats):
    """Build the era summary section of the catalog.

    Args:
        composer_stats: Dict of composer directory name -> stats

    Returns:
        Dict of era name -> {years, composers, count}
    """
    era_definitions = {
        "Renaissance": "1400-1600",
        "Baroque": "1600-1750",
        "Classical": "1750-1820",
        "Romantic": "1820-1900",
        "Late Romantic": "1890-1920",
        "Folk": "pre-1900",
    }

    eras = {}
    for era_name, years in era_definitions.items():
        composers_in_era = []
        total_count = 0
        for _dir_name, stats in sorted(composer_stats.items()):
            if stats["era"] == era_name:
                composers_in_era.append(stats["name"])
                total_count += stats["count"]
        if composers_in_era:
            eras[era_name] = {
                "years": years,
                "composers": sorted(composers_in_era),
                "count": total_count,
            }

    return eras


def generate_catalog():
    """Generate the full MIDI catalog and write it to disk.

    Returns:
        The catalog dict
    """
    midis, composer_stats = scan_midi_library()
    eras = build_era_summary(composer_stats)

    total_size = sum(m["size"] for m in midis)

    composers_list = []
    for _dir_name, stats in sorted(composer_stats.items(), key=lambda x: x[1]["name"]):
        composers_list.append({
            "name": stats["name"],
            "era": stats["era"],
            "count": stats["count"],
            "sources": stats["sources"],
        })

    catalog = {
        "version": "1.0",
        "total_midis": len(midis),
        "total_composers": len(composer_stats),
        "total_size_bytes": total_size,
        "license_summary": (
            "All compositions public domain (composers died before 1925). "
            "MIDI sequences from MAESTRO (CC BY-NC-SA 4.0), ADL Piano MIDI "
            "(CC-BY 4.0), narcisse-dev, Nottingham Music Database (public domain)."
        ),
        "eras": eras,
        "composers": composers_list,
        "midis": midis,
    }

    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

    return catalog


def main():
    """Entry point: generate the catalog and print summary stats."""
    catalog = generate_catalog()
    print(f"MIDI Catalog generated: {OUTPUT_PATH}")
    print(f"  Total MIDI files: {catalog['total_midis']}")
    print(f"  Total composers:  {catalog['total_composers']}")
    print(f"  Total size:       {catalog['total_size_bytes']:,} bytes")
    print(f"  Eras:")
    for era_name, era_data in catalog["eras"].items():
        print(f"    {era_name} ({era_data['years']}): "
              f"{era_data['count']} files, "
              f"{len(era_data['composers'])} composers")


if __name__ == "__main__":
    main()
