"""Tests for universe simulation orchestrator."""
import os
import sys
import unittest
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulator.universe import Universe, EPOCHS, EpochInfo, SimulationMetrics
from simulator.constants import PRESENT_EPOCH


class TestEpochInfo(unittest.TestCase):
    def test_creation(self):
        epoch = EpochInfo(name="Test", start_tick=100,
                          description="A test epoch")
        self.assertEqual(epoch.name, "Test")
        self.assertEqual(epoch.start_tick, 100)

    def test_epochs_list(self):
        self.assertGreater(len(EPOCHS), 5)
        names = [e.name for e in EPOCHS]
        self.assertIn("Planck", names)
        self.assertIn("Present", names)

    def test_epochs_ordered(self):
        for i in range(len(EPOCHS) - 1):
            self.assertLessEqual(
                EPOCHS[i].start_tick, EPOCHS[i + 1].start_tick
            )


class TestSimulationMetrics(unittest.TestCase):
    def test_defaults(self):
        m = SimulationMetrics()
        self.assertEqual(m.wall_time_s, 0.0)
        self.assertEqual(m.particles_created, 0)

    def test_to_dict(self):
        m = SimulationMetrics(
            wall_time_s=1.5,
            particles_created=100,
        )
        d = m.to_dict()
        self.assertEqual(d["wall_time_s"], 1.5)
        self.assertEqual(d["particles"], 100)


class TestUniverse(unittest.TestCase):
    def test_creation(self):
        u = Universe(seed=42)
        self.assertEqual(u.tick, 0)
        self.assertEqual(u.current_epoch_name, "Void")

    def test_step(self):
        u = Universe(seed=42, step_size=1000)
        u.step()
        self.assertEqual(u.tick, 1000)

    def test_epoch_transition(self):
        u = Universe(seed=42, step_size=1000)
        for _ in range(6):
            u.step()
        self.assertNotEqual(u.current_epoch_name, "Void")
        self.assertGreater(len(u.epoch_transitions), 0)

    def test_callbacks(self):
        ticks_seen = []
        epochs_seen = []

        def on_tick(tick, snap):
            ticks_seen.append(tick)

        def on_epoch(tick, old, new):
            epochs_seen.append(new)

        u = Universe(seed=42, step_size=1000, max_ticks=10000)
        u.set_callbacks(on_tick=on_tick, on_epoch=on_epoch)
        u.run()
        self.assertGreater(len(ticks_seen), 0)
        self.assertGreater(len(epochs_seen), 0)

    def test_full_simulation_small(self):
        u = Universe(seed=42, max_ticks=300000, step_size=5000)
        metrics = u.run()
        self.assertGreater(metrics.wall_time_s, 0)
        self.assertEqual(metrics.ticks_completed, 300000)

    def test_full_simulation_standard(self):
        u = Universe(seed=42, max_ticks=300000, step_size=1000)
        metrics = u.run()
        self.assertGreater(metrics.particles_created, 0)
        self.assertGreater(metrics.atoms_formed, 0)

    def test_state_compact(self):
        u = Universe(seed=42, step_size=1000)
        for _ in range(5):
            u.step()
        compact = u.state_compact()
        self.assertIn("U[", compact)
        self.assertIn("QF[", compact)

    def test_summary(self):
        u = Universe(seed=42, max_ticks=10000, step_size=1000)
        u.run()
        summary = u.summary()
        self.assertIn("metrics", summary)
        self.assertIn("final_state", summary)
        self.assertIn("epoch_transitions", summary)

    def test_snapshot(self):
        u = Universe(seed=42, step_size=1000)
        for _ in range(5):
            u.step()
        snap = u._snapshot()
        self.assertIn("tick", snap)
        self.assertIn("epoch", snap)
        self.assertIn("temperature", snap)
        self.assertIn("particles", snap)

    def test_get_epoch_name(self):
        u = Universe(seed=42)
        u.tick = 0
        self.assertEqual(u._get_epoch_name(), "Void")
        u.tick = 1
        self.assertEqual(u._get_epoch_name(), "Planck")
        u.tick = 300000
        self.assertEqual(u._get_epoch_name(), "Present")

    def test_history_recorded(self):
        u = Universe(seed=42, max_ticks=300000, step_size=1000)
        u.run()
        self.assertGreater(len(u.history), 0)

    def test_run_with_progress(self):
        u = Universe(seed=42, max_ticks=10000, step_size=1000)
        metrics = u.run(progress_interval=5000)
        self.assertGreater(metrics.ticks_completed, 0)

    def test_biosphere_emerges(self):
        u = Universe(seed=42, max_ticks=300000, step_size=1000)
        u.run()
        self.assertIsNotNone(u.biosphere)
        self.assertGreater(len(u.biosphere.cells), 0)

    def test_chemical_system_emerges(self):
        u = Universe(seed=42, max_ticks=300000, step_size=1000)
        u.run()
        self.assertIsNotNone(u.chemical_system)
        self.assertGreater(len(u.chemical_system.molecules), 0)


class TestBigBounce(unittest.TestCase):
    """Tests for the Big Bounce perpetual simulation mode."""

    def test_big_bounce_resets_state(self):
        u = Universe(seed=42, max_ticks=10000, step_size=1000)
        u.run()
        self.assertGreater(u.tick, 0)
        u.big_bounce()
        self.assertEqual(u.tick, 0)
        self.assertEqual(u.current_epoch_name, "Void")
        self.assertEqual(u.cycle, 1)

    def test_big_bounce_derives_seed(self):
        u = Universe(seed=42, max_ticks=10000, step_size=1000)
        u.run()
        u.big_bounce()
        # After bounce, should be able to run again
        u.run()
        self.assertGreater(u.tick, 0)

    def test_big_bounce_explicit_seed(self):
        u = Universe(seed=42, max_ticks=10000, step_size=1000)
        u.run()
        u.big_bounce(new_seed=99)
        self.assertEqual(u.cycle, 1)
        u.run()
        self.assertGreater(u.tick, 0)

    def test_run_perpetual_fixed_cycles(self):
        bounces = []
        u = Universe(seed=42, max_ticks=10000, step_size=1000)
        u.run_perpetual(
            on_bounce=lambda c, t: bounces.append(c),
            max_cycles=3
        )
        self.assertEqual(len(bounces), 3)
        self.assertEqual(u.cycle, 2)  # 2 bounces after 3 runs

    def test_big_bounce_clears_history(self):
        u = Universe(seed=42, max_ticks=10000, step_size=1000)
        u.run()
        self.assertGreater(len(u.history), 0)
        u.big_bounce()
        self.assertEqual(len(u.history), 0)
        self.assertEqual(len(u.epoch_transitions), 0)

    def test_cycle_property_initial(self):
        u = Universe(seed=42)
        self.assertEqual(u.cycle, 0)

    def test_summary_includes_cycle(self):
        u = Universe(seed=42, max_ticks=10000, step_size=1000)
        u.run()
        s = u.summary()
        self.assertIn("cycle", s)
        self.assertEqual(s["cycle"], 0)


if __name__ == "__main__":
    unittest.main()
