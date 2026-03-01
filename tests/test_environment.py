"""Tests for environment simulation."""
import os
import sys
import unittest
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulator.environment import Environment, EnvironmentalEvent
from simulator.constants import (
    T_PLANCK, T_CMB, T_EARTH_SURFACE, RADIATION_DAMAGE_THRESHOLD,
)


class TestEnvironmentalEvent(unittest.TestCase):
    def test_creation(self):
        event = EnvironmentalEvent(
            event_type="volcanic",
            intensity=2.0,
            duration=50,
            tick_occurred=100,
        )
        self.assertEqual(event.event_type, "volcanic")
        self.assertEqual(event.intensity, 2.0)

    def test_to_compact(self):
        event = EnvironmentalEvent(
            event_type="asteroid",
            intensity=5.0,
            duration=100,
        )
        compact = event.to_compact()
        self.assertIn("asteroid", compact)
        self.assertIn("5.00", compact)


class TestEnvironment(unittest.TestCase):
    def test_creation(self):
        env = Environment()
        self.assertEqual(env.temperature, T_PLANCK)
        self.assertEqual(env.tick, 0)

    def test_update_early_universe(self):
        env = Environment()
        env.update(epoch=100)
        self.assertLess(env.temperature, T_PLANCK)
        self.assertGreater(env.temperature, 0)

    def test_update_pre_recombination(self):
        env = Environment()
        env.update(epoch=20000)
        self.assertGreaterEqual(env.temperature, T_CMB)

    def test_update_post_recombination(self):
        env = Environment()
        env.update(epoch=60000)

    def test_update_planet_era(self):
        random.seed(42)
        env = Environment()
        env.update(epoch=250000)
        # Temperature should be near Earth surface
        self.assertGreater(env.temperature, 100)
        self.assertLess(env.temperature, 500)

    def test_uv_intensity_before_stars(self):
        env = Environment()
        env.update(epoch=50000)
        self.assertEqual(env.uv_intensity, 0.0)

    def test_uv_intensity_with_stars(self):
        env = Environment()
        # Simulate many ticks to get day/night
        for _ in range(200):
            env.update(epoch=200000)
        # UV should be positive at some point

    def test_cosmic_ray_flux(self):
        env = Environment()
        env.update(epoch=50000)
        self.assertGreater(env.cosmic_ray_flux, 0)

    def test_atmospheric_density(self):
        env = Environment()
        env.update(epoch=250000)
        self.assertGreater(env.atmospheric_density, 0)

    def test_water_availability(self):
        env = Environment()
        env.update(epoch=250000)
        self.assertGreater(env.water_availability, 0)

    def test_is_habitable(self):
        env = Environment()
        env.temperature = 300
        env.water_availability = 0.5
        env.uv_intensity = 0.1
        env.cosmic_ray_flux = 0.1
        self.assertTrue(env.is_habitable())

    def test_not_habitable_too_hot(self):
        env = Environment()
        env.temperature = 1000
        env.water_availability = 0.5
        self.assertFalse(env.is_habitable())

    def test_not_habitable_no_water(self):
        env = Environment()
        env.temperature = 300
        env.water_availability = 0.0
        self.assertFalse(env.is_habitable())

    def test_not_habitable_radiation(self):
        env = Environment()
        env.temperature = 300
        env.water_availability = 0.5
        env.uv_intensity = RADIATION_DAMAGE_THRESHOLD
        self.assertFalse(env.is_habitable())

    def test_thermal_energy(self):
        env = Environment()
        env.temperature = 300
        energy = env.thermal_energy()
        self.assertGreater(energy, 0)
        self.assertAlmostEqual(energy, 30.0)

    def test_thermal_energy_extreme_cold(self):
        env = Environment()
        env.temperature = 50
        energy = env.thermal_energy()
        self.assertAlmostEqual(energy, 0.1)

    def test_thermal_energy_extreme_hot(self):
        env = Environment()
        env.temperature = 1000
        energy = env.thermal_energy()
        self.assertAlmostEqual(energy, 0.1)

    def test_radiation_dose(self):
        env = Environment()
        env.uv_intensity = 1.0
        env.cosmic_ray_flux = 0.5
        env.stellar_wind = 0.2
        self.assertAlmostEqual(env.get_radiation_dose(), 1.7)

    def test_volcanic_event(self):
        env = Environment()
        env.temperature = 300
        event = EnvironmentalEvent(
            event_type="volcanic", intensity=2.0,
            duration=10, tick_occurred=0,
        )
        env.events.append(event)
        env._process_events()
        self.assertGreater(env.temperature, 300)

    def test_asteroid_event(self):
        env = Environment()
        env.temperature = 300
        event = EnvironmentalEvent(
            event_type="asteroid", intensity=5.0,
            duration=10, tick_occurred=0,
        )
        env.events.append(event)
        env._process_events()
        self.assertLess(env.temperature, 300)

    def test_solar_flare_event(self):
        env = Environment()
        env.uv_intensity = 0.5
        event = EnvironmentalEvent(
            event_type="solar_flare", intensity=1.0,
            duration=10, tick_occurred=0,
        )
        env.events.append(event)
        env._process_events()
        self.assertGreater(env.uv_intensity, 0.5)

    def test_ice_age_event(self):
        env = Environment()
        env.temperature = 300
        env.water_availability = 1.0
        event = EnvironmentalEvent(
            event_type="ice_age", intensity=1.0,
            duration=10, tick_occurred=0,
        )
        env.events.append(event)
        env._process_events()
        self.assertLess(env.temperature, 300)
        self.assertLess(env.water_availability, 1.0)

    def test_event_expiration(self):
        env = Environment()
        env.tick = 100
        event = EnvironmentalEvent(
            event_type="volcanic", intensity=1.0,
            duration=10, tick_occurred=50,
        )
        env.events.append(event)
        env._process_events()
        self.assertEqual(len(env.events), 0)
        self.assertEqual(len(env.event_history), 1)

    def test_generate_events(self):
        random.seed(42)
        env = Environment()
        for _ in range(1000):
            env._generate_events(epoch=250000)
        # Should have generated some events
        self.assertGreater(len(env.events), 0)

    def test_to_compact(self):
        env = Environment()
        env.temperature = 300
        compact = env.to_compact()
        self.assertIn("Env[", compact)
        self.assertIn("T=", compact)
        self.assertIn("hab=", compact)

    def test_day_night_cycle(self):
        env = Environment()
        env.update(epoch=250000)
        self.assertGreaterEqual(env.day_night_cycle, 0)
        self.assertLessEqual(env.day_night_cycle, 1)

    def test_season_cycle(self):
        env = Environment()
        env.update(epoch=250000)
        self.assertGreaterEqual(env.season, 0)
        self.assertLessEqual(env.season, 1)


if __name__ == "__main__":
    unittest.main()
