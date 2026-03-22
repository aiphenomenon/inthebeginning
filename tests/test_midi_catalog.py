"""Tests for the MIDI catalog generator and its output.

Validates that the generated midi_catalog.json is complete, consistent,
and accurately represents the MIDI library on disk.
"""

import json
import os
import unittest

# Paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG_PATH = os.path.join(
    PROJECT_ROOT, "apps", "cosmic-runner-v3", "audio", "midi_catalog.json"
)
MIDI_LIBRARY = os.path.join(
    PROJECT_ROOT, "apps", "audio", "midi_library"
)

VALID_ERAS = {"Renaissance", "Baroque", "Classical", "Romantic", "Late Romantic", "Folk"}


def _load_catalog():
    """Load and return the MIDI catalog JSON."""
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _scan_midi_files():
    """Walk the MIDI library and return a set of relative paths."""
    midi_files = set()
    for dirpath, _dirnames, filenames in os.walk(MIDI_LIBRARY):
        for filename in filenames:
            if filename.lower().endswith((".mid", ".midi")):
                relpath = os.path.relpath(
                    os.path.join(dirpath, filename), MIDI_LIBRARY
                )
                midi_files.add(relpath)
    return midi_files


class TestMidiCatalogExists(unittest.TestCase):
    """Test that the catalog file exists and is valid JSON."""

    def test_catalog_file_exists(self):
        """The catalog JSON file must exist on disk."""
        self.assertTrue(
            os.path.isfile(CATALOG_PATH),
            f"Catalog not found at {CATALOG_PATH}",
        )

    def test_catalog_is_valid_json(self):
        """The catalog must parse as valid JSON without errors."""
        try:
            _load_catalog()
        except json.JSONDecodeError as exc:
            self.fail(f"Catalog is not valid JSON: {exc}")


class TestCatalogStructure(unittest.TestCase):
    """Test that the catalog has the required top-level fields."""

    @classmethod
    def setUpClass(cls):
        cls.catalog = _load_catalog()

    def test_has_version(self):
        """Catalog must have a version field."""
        self.assertIn("version", self.catalog)

    def test_has_total_midis(self):
        """Catalog must have a total_midis count."""
        self.assertIn("total_midis", self.catalog)
        self.assertIsInstance(self.catalog["total_midis"], int)

    def test_has_total_composers(self):
        """Catalog must have a total_composers count."""
        self.assertIn("total_composers", self.catalog)
        self.assertIsInstance(self.catalog["total_composers"], int)

    def test_has_total_size_bytes(self):
        """Catalog must have a total_size_bytes count."""
        self.assertIn("total_size_bytes", self.catalog)
        self.assertIsInstance(self.catalog["total_size_bytes"], int)

    def test_has_license_summary(self):
        """Catalog must have a license_summary string."""
        self.assertIn("license_summary", self.catalog)
        self.assertIsInstance(self.catalog["license_summary"], str)

    def test_has_eras(self):
        """Catalog must have an eras dict."""
        self.assertIn("eras", self.catalog)
        self.assertIsInstance(self.catalog["eras"], dict)

    def test_has_composers(self):
        """Catalog must have a composers list."""
        self.assertIn("composers", self.catalog)
        self.assertIsInstance(self.catalog["composers"], list)

    def test_has_midis(self):
        """Catalog must have a midis list."""
        self.assertIn("midis", self.catalog)
        self.assertIsInstance(self.catalog["midis"], list)


class TestMidiEntries(unittest.TestCase):
    """Test that each MIDI entry has required fields and valid values."""

    @classmethod
    def setUpClass(cls):
        cls.catalog = _load_catalog()

    def test_all_entries_have_required_fields(self):
        """Every MIDI entry must have path, name, composer, era, and size."""
        required_fields = {"path", "name", "composer", "era", "size"}
        for i, entry in enumerate(self.catalog["midis"]):
            for field in required_fields:
                self.assertIn(
                    field,
                    entry,
                    f"Entry {i} ({entry.get('path', 'unknown')}) missing '{field}'",
                )

    def test_era_classifications_are_valid(self):
        """Every MIDI entry must have an era from the valid set."""
        for entry in self.catalog["midis"]:
            self.assertIn(
                entry["era"],
                VALID_ERAS,
                f"Entry {entry['path']} has invalid era '{entry['era']}'",
            )

    def test_sizes_are_non_negative(self):
        """Every MIDI entry must have a non-negative file size."""
        for entry in self.catalog["midis"]:
            self.assertGreaterEqual(
                entry["size"],
                0,
                f"Entry {entry['path']} has negative size {entry['size']}",
            )

    def test_names_are_nonempty(self):
        """Every MIDI entry must have a non-empty piece name."""
        for entry in self.catalog["midis"]:
            self.assertTrue(
                entry["name"].strip(),
                f"Entry {entry['path']} has empty name",
            )

    def test_paths_are_relative(self):
        """MIDI paths must be relative (not absolute)."""
        for entry in self.catalog["midis"]:
            self.assertFalse(
                os.path.isabs(entry["path"]),
                f"Entry path is absolute: {entry['path']}",
            )


class TestCatalogCompleteness(unittest.TestCase):
    """Test that the catalog contains all MIDI files from the library."""

    @classmethod
    def setUpClass(cls):
        cls.catalog = _load_catalog()
        cls.disk_files = _scan_midi_files()
        cls.catalog_paths = {entry["path"] for entry in cls.catalog["midis"]}

    def test_all_disk_files_in_catalog(self):
        """Every MIDI file on disk must appear in the catalog."""
        missing = self.disk_files - self.catalog_paths
        self.assertEqual(
            missing,
            set(),
            f"{len(missing)} MIDI files on disk not in catalog: {sorted(missing)[:10]}",
        )

    def test_all_catalog_files_on_disk(self):
        """Every catalog entry must correspond to a real file on disk."""
        for entry in self.catalog["midis"]:
            full_path = os.path.join(MIDI_LIBRARY, entry["path"])
            self.assertTrue(
                os.path.isfile(full_path),
                f"Catalog entry does not exist on disk: {entry['path']}",
            )

    def test_total_midis_matches_entries(self):
        """The total_midis field must match the actual number of entries."""
        self.assertEqual(
            self.catalog["total_midis"],
            len(self.catalog["midis"]),
        )

    def test_total_midis_at_least_1854(self):
        """The library must have at least 1854 MIDI files."""
        self.assertGreaterEqual(self.catalog["total_midis"], 1854)

    def test_total_composers_matches(self):
        """The total_composers field must match the composers list length."""
        self.assertEqual(
            self.catalog["total_composers"],
            len(self.catalog["composers"]),
        )


class TestComposerCounts(unittest.TestCase):
    """Test that composer counts match directory contents."""

    @classmethod
    def setUpClass(cls):
        cls.catalog = _load_catalog()

    def test_composer_counts_match_directories(self):
        """Each composer's count must match the number of MIDI files in their directory."""
        # Build a map from display name -> count from catalog entries
        catalog_counts = {}
        for entry in self.catalog["midis"]:
            composer = entry["composer"]
            catalog_counts[composer] = catalog_counts.get(composer, 0) + 1

        # Check against the composers list
        for composer_info in self.catalog["composers"]:
            name = composer_info["name"]
            declared_count = composer_info["count"]
            actual_count = catalog_counts.get(name, 0)
            self.assertEqual(
                declared_count,
                actual_count,
                f"Composer '{name}' declares {declared_count} files "
                f"but catalog has {actual_count} entries",
            )


class TestEraClassifications(unittest.TestCase):
    """Test that era classifications are valid and consistent."""

    @classmethod
    def setUpClass(cls):
        cls.catalog = _load_catalog()

    def test_all_eras_have_required_fields(self):
        """Each era must have years, composers, and count fields."""
        for era_name, era_data in self.catalog["eras"].items():
            self.assertIn("years", era_data, f"Era '{era_name}' missing 'years'")
            self.assertIn("composers", era_data, f"Era '{era_name}' missing 'composers'")
            self.assertIn("count", era_data, f"Era '{era_name}' missing 'count'")

    def test_era_counts_match_midis(self):
        """Era counts must match the number of MIDI entries in that era."""
        era_counts = {}
        for entry in self.catalog["midis"]:
            era = entry["era"]
            era_counts[era] = era_counts.get(era, 0) + 1

        for era_name, era_data in self.catalog["eras"].items():
            self.assertEqual(
                era_data["count"],
                era_counts.get(era_name, 0),
                f"Era '{era_name}' declares count {era_data['count']} "
                f"but catalog has {era_counts.get(era_name, 0)} entries",
            )

    def test_all_six_eras_present(self):
        """All six eras must be represented in the catalog."""
        for era in VALID_ERAS:
            self.assertIn(
                era,
                self.catalog["eras"],
                f"Era '{era}' not found in catalog",
            )


if __name__ == "__main__":
    unittest.main()
