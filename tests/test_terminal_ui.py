"""Tests for terminal UI rendering."""
import os
import sys
import unittest
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulator.terminal_ui import (
    box, progress_bar, sparkline, render_epoch_timeline,
    render_particle_counts, render_element_counts,
    render_biosphere, render_environment, render_full_state,
    render_final_report, _strip_ansi, _get_current_epoch,
)
from simulator.universe import Universe, EPOCHS


class TestStripAnsi(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(_strip_ansi("hello"), "hello")

    def test_colored(self):
        self.assertEqual(_strip_ansi("\033[31mred\033[0m"), "red")

    def test_bold(self):
        self.assertEqual(_strip_ansi("\033[1mbold\033[0m"), "bold")


class TestBox(unittest.TestCase):
    def test_basic(self):
        result = box("Title", ["line 1", "line 2"], width=40)
        self.assertIn("Title", result)
        self.assertIn("line 1", result)

    def test_empty_title(self):
        result = box("", ["content"], width=30)
        self.assertIn("content", result)

    def test_long_content(self):
        result = box("T", ["x" * 100], width=20)
        self.assertIn("x", result)


class TestProgressBar(unittest.TestCase):
    def test_full(self):
        result = progress_bar(100, 100, width=20)
        self.assertIn("100.0%", result)

    def test_empty(self):
        result = progress_bar(0, 100, width=20)
        self.assertIn("0.0%", result)

    def test_zero_max(self):
        result = progress_bar(50, 0, width=20)
        self.assertIn("0.0%", result)

    def test_half(self):
        result = progress_bar(50, 100, width=20)
        self.assertIn("50.0%", result)


class TestSparkline(unittest.TestCase):
    def test_basic(self):
        values = [0, 1, 2, 3, 4, 5]
        result = sparkline(values, width=6)
        self.assertEqual(len(result), 6)

    def test_empty(self):
        result = sparkline([], width=10)
        self.assertEqual(result, "")

    def test_constant(self):
        values = [5, 5, 5, 5]
        result = sparkline(values, width=4)
        self.assertEqual(len(result), 4)

    def test_downsampling(self):
        values = list(range(100))
        result = sparkline(values, width=10)
        self.assertEqual(len(result), 10)


class TestRenderFunctions(unittest.TestCase):
    def test_epoch_timeline(self):
        lines = render_epoch_timeline(50000, 300000, EPOCHS, width=50)
        self.assertGreater(len(lines), 0)
        text = "\n".join(lines)
        self.assertIn("Timeline", text)

    def test_get_current_epoch(self):
        name = _get_current_epoch(0, EPOCHS)
        self.assertEqual(name, "Void")
        name = _get_current_epoch(300000, EPOCHS)
        self.assertEqual(name, "Present")

    def test_particle_counts(self):
        counts = {"electron": 10, "proton": 5}
        lines = render_particle_counts(counts)
        self.assertGreater(len(lines), 0)

    def test_particle_counts_empty(self):
        lines = render_particle_counts({})
        self.assertGreater(len(lines), 0)  # Shows "(no particles)"

    def test_element_counts(self):
        counts = {"H": 100, "He": 50, "C": 10}
        lines = render_element_counts(counts)
        self.assertGreater(len(lines), 0)

    def test_element_counts_empty(self):
        lines = render_element_counts({})
        self.assertGreater(len(lines), 0)

    def test_render_biosphere_none(self):
        lines = render_biosphere(None)
        self.assertGreater(len(lines), 0)

    def test_render_biosphere_with_data(self):
        random.seed(42)
        from simulator.biology import Biosphere
        bio = Biosphere(initial_cells=5)
        lines = render_biosphere(bio)
        self.assertGreater(len(lines), 0)

    def test_render_environment(self):
        from simulator.environment import Environment
        env = Environment()
        env.temperature = 300
        env.water_availability = 0.5
        lines = render_environment(env)
        self.assertGreater(len(lines), 0)

    def test_render_environment_with_events(self):
        from simulator.environment import Environment, EnvironmentalEvent
        env = Environment()
        env.temperature = 300
        env.events.append(EnvironmentalEvent(
            event_type="volcanic", intensity=2.0, duration=10
        ))
        lines = render_environment(env)
        text = "\n".join(lines)
        self.assertIn("volcanic", text)


class TestFullRender(unittest.TestCase):
    def test_render_full_state(self):
        random.seed(42)
        u = Universe(seed=42, max_ticks=300000, step_size=10000)
        u.run()
        result = render_full_state(u)
        self.assertIn("IN THE BEGINNING", result)
        self.assertIn("Timeline", result)
        self.assertIn("Quantum Field", result)
        self.assertIn("Atoms", result)

    def test_render_final_report(self):
        random.seed(42)
        u = Universe(seed=42, max_ticks=300000, step_size=1000)
        u.run()
        result = render_final_report(u)
        self.assertIn("SIMULATION COMPLETE", result)
        self.assertIn("Performance", result)
        self.assertIn("Epoch Transitions", result)

    def test_render_final_report_no_biosphere(self):
        u = Universe(seed=42, max_ticks=10000, step_size=1000)
        u.run()
        result = render_final_report(u)
        self.assertIn("SIMULATION COMPLETE", result)


if __name__ == "__main__":
    unittest.main()
