"""Environmental effects simulation.

Models random environmental perturbations that affect the evolution
of the universe from quantum to biological scales:
- Temperature gradients and thermal fluctuations
- Radiation (UV, cosmic rays, stellar winds)
- Geological events (volcanic, tectonic)
- Atmospheric composition changes
- Day/night cycles and seasonal variations
"""
import math
import random
from dataclasses import dataclass, field
from typing import Optional

from simulator.constants import (
    T_PLANCK, T_CMB, T_EARTH_SURFACE, T_STELLAR_CORE,
    UV_MUTATION_RATE, COSMIC_RAY_MUTATION_RATE,
    RADIATION_DAMAGE_THRESHOLD, THERMAL_FLUCTUATION, K_B,
)


@dataclass
class EnvironmentalEvent:
    """A discrete environmental event."""
    event_type: str
    intensity: float
    duration: int  # ticks
    position: list = field(default_factory=lambda: [0.0, 0.0, 0.0])
    tick_occurred: int = 0

    def to_compact(self) -> str:
        return f"Ev:{self.event_type}(i={self.intensity:.2f},d={self.duration})"


class Environment:
    """The physical environment that affects all simulation levels."""

    def __init__(self, initial_temperature: float = T_PLANCK):
        self.temperature = initial_temperature
        self.uv_intensity = 0.0
        self.cosmic_ray_flux = 0.0
        self.stellar_wind = 0.0
        self.atmospheric_density = 0.0
        self.water_availability = 0.0
        self.day_night_cycle = 0.0  # 0-1, 0=midnight, 0.5=noon
        self.season = 0.0  # 0-1, 0=winter, 0.5=summer
        self.events: list[EnvironmentalEvent] = []
        self.event_history: list[EnvironmentalEvent] = []
        self.tick = 0

    def update(self, epoch: int):
        """Update environment based on cosmic epoch."""
        self.tick += 1

        # Temperature evolution (logarithmic cooling)
        if epoch < 1000:
            # Early universe: rapid cooling
            self.temperature = T_PLANCK * math.exp(-epoch / 200)
        elif epoch < 50000:
            # Pre-recombination
            self.temperature = max(
                T_CMB, T_PLANCK * math.exp(-epoch / 200)
            )
        elif epoch < 200000:
            # Post-recombination to star formation
            self.temperature = T_CMB + random.gauss(0, 0.5)
        else:
            # Planet era
            self.temperature = T_EARTH_SURFACE + random.gauss(0, 5)
            # Day/night
            self.day_night_cycle = (self.tick % 100) / 100.0
            temp_mod = 10 * math.sin(self.day_night_cycle * 2 * math.pi)
            self.temperature += temp_mod
            # Seasons
            self.season = (self.tick % 1000) / 1000.0
            season_mod = 15 * math.sin(self.season * 2 * math.pi)
            self.temperature += season_mod

        # UV intensity (appears with stars)
        if epoch > 100000:
            base_uv = 1.0
            # Day/night modulation
            if self.day_night_cycle > 0.25 and self.day_night_cycle < 0.75:
                self.uv_intensity = base_uv * math.sin(
                    (self.day_night_cycle - 0.25) * 2 * math.pi
                )
            else:
                self.uv_intensity = 0.0
        else:
            self.uv_intensity = 0.0

        # Cosmic ray flux
        if epoch > 10000:
            self.cosmic_ray_flux = 0.1 + random.expovariate(10.0)
        else:
            self.cosmic_ray_flux = 1.0  # High in early universe

        # Atmospheric density (grows with planet formation)
        if epoch > 210000:
            self.atmospheric_density = min(1.0, (epoch - 210000) / 50000)
            # Atmosphere shields from UV
            self.uv_intensity *= (1 - self.atmospheric_density * 0.7)
            self.cosmic_ray_flux *= (1 - self.atmospheric_density * 0.5)

        # Water availability
        if epoch > 220000:
            self.water_availability = min(
                1.0, (epoch - 220000) / 30000
            )

        # Random events
        self._generate_events(epoch)

        # Process active events
        self._process_events()

    def _generate_events(self, epoch: int):
        """Generate random environmental events."""
        # Volcanic activity
        if epoch > 210000 and random.random() < 0.005:
            self.events.append(EnvironmentalEvent(
                event_type="volcanic",
                intensity=random.uniform(0.5, 3.0),
                duration=random.randint(10, 100),
                tick_occurred=self.tick,
            ))

        # Asteroid impact
        if random.random() < 0.0001:
            self.events.append(EnvironmentalEvent(
                event_type="asteroid",
                intensity=random.uniform(1.0, 10.0),
                duration=random.randint(50, 500),
                tick_occurred=self.tick,
            ))

        # Solar flare
        if epoch > 100000 and random.random() < 0.01:
            self.events.append(EnvironmentalEvent(
                event_type="solar_flare",
                intensity=random.uniform(0.1, 2.0),
                duration=random.randint(5, 20),
                tick_occurred=self.tick,
            ))

        # Ice age
        if epoch > 250000 and random.random() < 0.001:
            self.events.append(EnvironmentalEvent(
                event_type="ice_age",
                intensity=random.uniform(0.5, 1.5),
                duration=random.randint(500, 2000),
                tick_occurred=self.tick,
            ))

    def _process_events(self):
        """Process active environmental events."""
        active = []
        for event in self.events:
            elapsed = self.tick - event.tick_occurred
            if elapsed < event.duration:
                active.append(event)
                self._apply_event(event)
            else:
                self.event_history.append(event)

        self.events = active

    def _apply_event(self, event: EnvironmentalEvent):
        """Apply an environmental event's effects."""
        if event.event_type == "volcanic":
            self.temperature += event.intensity * 2
            self.atmospheric_density = min(
                1.0, self.atmospheric_density + 0.01
            )
            self.uv_intensity *= 0.9  # Ash blocks UV

        elif event.event_type == "asteroid":
            self.temperature -= event.intensity * 5  # Nuclear winter
            self.cosmic_ray_flux += event.intensity
            self.uv_intensity *= 0.5

        elif event.event_type == "solar_flare":
            self.uv_intensity += event.intensity
            self.cosmic_ray_flux += event.intensity * 0.5

        elif event.event_type == "ice_age":
            self.temperature -= event.intensity * 20
            self.water_availability *= 0.8

    def get_radiation_dose(self) -> float:
        """Total radiation dose from all sources."""
        return self.uv_intensity + self.cosmic_ray_flux + self.stellar_wind

    def is_habitable(self) -> bool:
        """Check if conditions support life."""
        return (
            200 < self.temperature < 400
            and self.water_availability > 0.1
            and self.get_radiation_dose() < RADIATION_DAMAGE_THRESHOLD
        )

    def thermal_energy(self) -> float:
        """Available thermal energy for biological processes.

        Scaled to provide meaningful energy in habitable range.
        At ~300K, returns ~30 units (enough to sustain cell metabolism).
        """
        if self.temperature < 100 or self.temperature > 500:
            return 0.1
        return max(0.1, self.temperature * 0.1)

    def to_compact(self) -> str:
        return (f"Env[T={self.temperature:.1f} "
                f"UV={self.uv_intensity:.3f} "
                f"CR={self.cosmic_ray_flux:.3f} "
                f"atm={self.atmospheric_density:.2f} "
                f"H2O={self.water_availability:.2f} "
                f"hab={'Y' if self.is_habitable() else 'N'} "
                f"ev={len(self.events)}]")
