"""Universe simulation orchestrator.

Coordinates all simulation layers from the Big Bang through
emergence of life. Manages the cosmic timeline and transitions
between physical regimes.
"""
import time
import resource
import tracemalloc
from dataclasses import dataclass, field

from simulator.constants import (
    PLANCK_EPOCH, INFLATION_EPOCH, ELECTROWEAK_EPOCH,
    QUARK_EPOCH, HADRON_EPOCH, NUCLEOSYNTHESIS_EPOCH,
    RECOMBINATION_EPOCH, STAR_FORMATION_EPOCH,
    SOLAR_SYSTEM_EPOCH, EARTH_EPOCH, LIFE_EPOCH,
    DNA_EPOCH, PRESENT_EPOCH, T_PLANCK,
)
from simulator.quantum import QuantumField, ParticleType
from simulator.atomic import AtomicSystem, Atom
from simulator.chemistry import ChemicalSystem
from simulator.biology import Biosphere, DNAStrand
from simulator.environment import Environment


@dataclass
class EpochInfo:
    """Information about a cosmic epoch."""
    name: str
    start_tick: int
    description: str
    key_events: list = field(default_factory=list)


EPOCHS = [
    EpochInfo("Planck", PLANCK_EPOCH,
              "All forces unified, T~10^32K"),
    EpochInfo("Inflation", INFLATION_EPOCH,
              "Exponential expansion, quantum fluctuations seed structure"),
    EpochInfo("Electroweak", ELECTROWEAK_EPOCH,
              "Electromagnetic and weak forces separate"),
    EpochInfo("Quark", QUARK_EPOCH,
              "Quark-gluon plasma, free quarks"),
    EpochInfo("Hadron", HADRON_EPOCH,
              "Quarks confined into protons and neutrons"),
    EpochInfo("Nucleosynthesis", NUCLEOSYNTHESIS_EPOCH,
              "Light nuclei form: H, He, Li"),
    EpochInfo("Recombination", RECOMBINATION_EPOCH,
              "Atoms form, universe becomes transparent"),
    EpochInfo("Star Formation", STAR_FORMATION_EPOCH,
              "First stars ignite, heavier elements forged"),
    EpochInfo("Solar System", SOLAR_SYSTEM_EPOCH,
              "Our solar system coalesces from stellar debris"),
    EpochInfo("Earth", EARTH_EPOCH,
              "Earth forms, oceans appear"),
    EpochInfo("Life", LIFE_EPOCH,
              "First self-replicating molecules"),
    EpochInfo("DNA Era", DNA_EPOCH,
              "DNA-based life, epigenetics emerge"),
    EpochInfo("Present", PRESENT_EPOCH,
              "Complex life, intelligence"),
]


@dataclass
class SimulationMetrics:
    """Performance metrics for the simulation."""
    wall_time_s: float = 0.0
    cpu_user_s: float = 0.0
    cpu_system_s: float = 0.0
    peak_memory_kb: int = 0
    ticks_completed: int = 0
    particles_created: int = 0
    atoms_formed: int = 0
    molecules_formed: int = 0
    cells_born: int = 0
    mutations: int = 0

    def to_dict(self) -> dict:
        return {
            "wall_time_s": round(self.wall_time_s, 3),
            "cpu_user_s": round(self.cpu_user_s, 3),
            "cpu_system_s": round(self.cpu_system_s, 3),
            "peak_memory_kb": self.peak_memory_kb,
            "ticks": self.ticks_completed,
            "particles": self.particles_created,
            "atoms": self.atoms_formed,
            "molecules": self.molecules_formed,
            "cells": self.cells_born,
            "mutations": self.mutations,
        }


class Universe:
    """The universe simulator - orchestrates all physical layers."""

    def __init__(self, seed: int = 42, max_ticks: int = PRESENT_EPOCH,
                 step_size: int = 1):
        import random as _random
        _random.seed(seed)

        self.tick = 0
        self.max_ticks = max_ticks
        self.step_size = step_size
        self.current_epoch_name = "Void"

        # Physical layers
        self.quantum_field = QuantumField(temperature=T_PLANCK)
        self.atomic_system = AtomicSystem()
        self.chemical_system = None  # Initialized when atoms exist
        self.biosphere = None  # Initialized when conditions allow

        # Environment
        self.environment = Environment(initial_temperature=T_PLANCK)

        # State tracking
        self.metrics = SimulationMetrics()
        self.history: list[dict] = []
        self.epoch_transitions: list[tuple] = []

        # Callbacks for UI
        self._on_tick = None
        self._on_epoch = None

    def set_callbacks(self, on_tick=None, on_epoch=None):
        """Set callback functions for UI updates."""
        self._on_tick = on_tick
        self._on_epoch = on_epoch

    def _get_epoch_name(self) -> str:
        """Determine current epoch based on tick."""
        name = "Void"
        for epoch in EPOCHS:
            if self.tick >= epoch.start_tick:
                name = epoch.name
        return name

    def _transition_epoch(self, new_epoch: str):
        """Handle epoch transition logic."""
        old_epoch = self.current_epoch_name
        self.current_epoch_name = new_epoch
        self.epoch_transitions.append((self.tick, old_epoch, new_epoch))

        if self._on_epoch:
            self._on_epoch(self.tick, old_epoch, new_epoch)

    def _seed_early_universe(self):
        """Seed the early universe with quarks and leptons."""
        from simulator.quantum import Particle, ParticleType, Spin, Color
        import random

        # Create initial quark population (u, u, d -> proton; u, d, d -> neutron)
        # Baryon asymmetry: slightly more matter than antimatter
        for _ in range(30):
            self.quantum_field.particles.append(Particle(
                particle_type=ParticleType.UP,
                position=[random.gauss(0, 1) for _ in range(3)],
                momentum=[random.gauss(0, 5) for _ in range(3)],
                spin=random.choice([Spin.UP, Spin.DOWN]),
                color=random.choice([Color.RED, Color.GREEN, Color.BLUE]),
            ))
        for _ in range(20):
            self.quantum_field.particles.append(Particle(
                particle_type=ParticleType.DOWN,
                position=[random.gauss(0, 1) for _ in range(3)],
                momentum=[random.gauss(0, 5) for _ in range(3)],
                spin=random.choice([Spin.UP, Spin.DOWN]),
                color=random.choice([Color.RED, Color.GREEN, Color.BLUE]),
            ))
        for _ in range(40):
            self.quantum_field.particles.append(Particle(
                particle_type=ParticleType.ELECTRON,
                position=[random.gauss(0, 2) for _ in range(3)],
                momentum=[random.gauss(0, 3) for _ in range(3)],
            ))
        for _ in range(5):
            self.quantum_field.particles.append(Particle(
                particle_type=ParticleType.PHOTON,
                momentum=[random.gauss(0, 10) for _ in range(3)],
            ))
        self.metrics.particles_created += len(self.quantum_field.particles)

    def step(self):
        """Advance simulation by one tick."""
        self.tick += self.step_size

        # Check epoch transition
        new_epoch = self._get_epoch_name()
        if new_epoch != self.current_epoch_name:
            self._transition_epoch(new_epoch)

        # Update environment
        self.environment.update(self.tick)

        # === Quantum level ===
        if self.tick <= HADRON_EPOCH:
            self.quantum_field.temperature = self.environment.temperature

            # Seed on first quantum tick
            if (not self.quantum_field.particles
                    and self.environment.temperature > 100):
                self._seed_early_universe()

            # Pair production in hot early universe
            if self.environment.temperature > 100:
                n_attempts = min(5, max(1, int(
                    self.environment.temperature / 1000
                )))
                for _ in range(n_attempts):
                    result = self.quantum_field.vacuum_fluctuation()
                    if result:
                        self.metrics.particles_created += 2

            self.quantum_field.evolve(self.step_size)

        # === Hadron formation ===
        if (HADRON_EPOCH - self.step_size < self.tick <= HADRON_EPOCH
                + self.step_size):
            self.quantum_field.temperature = self.environment.temperature
            hadrons = self.quantum_field.quark_confinement()
            if hadrons:
                self.metrics.particles_created += len(hadrons)

        # === Nucleosynthesis ===
        if NUCLEOSYNTHESIS_EPOCH <= self.tick < RECOMBINATION_EPOCH:
            protons = sum(
                1 for p in self.quantum_field.particles
                if p.particle_type == ParticleType.PROTON
            )
            neutrons = sum(
                1 for p in self.quantum_field.particles
                if p.particle_type == ParticleType.NEUTRON
            )
            if protons > 0 or neutrons > 0:
                new_atoms = self.atomic_system.nucleosynthesis(
                    protons, neutrons
                )
                # Remove used particles from quantum field
                to_remove = []
                for p in self.quantum_field.particles:
                    if p.particle_type in (ParticleType.PROTON,
                                           ParticleType.NEUTRON):
                        to_remove.append(p)
                for p in to_remove:
                    self.quantum_field.particles.remove(p)
                self.metrics.atoms_formed += len(new_atoms)

        # === Recombination ===
        if (RECOMBINATION_EPOCH - self.step_size < self.tick
                <= RECOMBINATION_EPOCH + self.step_size):
            self.atomic_system.temperature = self.environment.temperature
            new_atoms = self.atomic_system.recombination(self.quantum_field)
            self.metrics.atoms_formed += len(new_atoms)

        # === Star formation and stellar nucleosynthesis ===
        if STAR_FORMATION_EPOCH <= self.tick < SOLAR_SYSTEM_EPOCH:
            self.atomic_system.temperature = self.environment.temperature
            new_heavy = self.atomic_system.stellar_nucleosynthesis(
                self.environment.temperature * 100  # Stellar core temp
            )
            self.metrics.atoms_formed += len(new_heavy)

        # === Chemistry ===
        if self.tick >= EARTH_EPOCH:
            if self.chemical_system is None:
                self.chemical_system = ChemicalSystem(self.atomic_system)

            # Seed supernova remnants with essential elements for chemistry
            if (EARTH_EPOCH - self.step_size < self.tick
                    <= EARTH_EPOCH + self.step_size):
                import random
                elements_to_seed = [
                    (1, 40), (2, 10), (6, 15), (7, 10), (8, 15),
                    (15, 3),  # Phosphorus for nucleotides
                ]
                for z, count in elements_to_seed:
                    for _ in range(count):
                        from simulator.atomic import Atom
                        a = Atom(
                            atomic_number=z,
                            position=[random.gauss(0, 5) for _ in range(3)],
                        )
                        self.atomic_system.atoms.append(a)
                        self.metrics.atoms_formed += 1

            # Form basic molecules at Earth epoch
            if (EARTH_EPOCH - self.step_size < self.tick
                    <= EARTH_EPOCH + self.step_size):
                waters = self.chemical_system.form_water()
                methanes = self.chemical_system.form_methane()
                ammonias = self.chemical_system.form_ammonia()
                self.metrics.molecules_formed += (
                    len(waters) + len(methanes) + len(ammonias)
                )

            # Catalyzed reactions for complex molecules
            if self.tick > EARTH_EPOCH:
                formed = self.chemical_system.catalyzed_reaction(
                    self.environment.temperature,
                    catalyst_present=(self.tick > LIFE_EPOCH),
                )
                self.metrics.molecules_formed += formed

        # === Biology ===
        if self.tick >= LIFE_EPOCH and self.environment.is_habitable():
            if self.biosphere is None:
                self.biosphere = Biosphere(initial_cells=3, dna_length=90)
                self.metrics.cells_born += 3

            self.biosphere.step(
                environment_energy=self.environment.thermal_energy(),
                uv_intensity=self.environment.uv_intensity,
                cosmic_ray_flux=self.environment.cosmic_ray_flux,
                temperature=self.environment.temperature,
            )

            self.metrics.cells_born = self.biosphere.total_born
            self.metrics.mutations = self.biosphere.total_mutations()

        # Record state snapshot periodically
        if self.tick % max(1, self.max_ticks // 100) == 0:
            self.history.append(self._snapshot())

        if self._on_tick:
            self._on_tick(self.tick, self._snapshot())

    def _snapshot(self) -> dict:
        """Capture current state snapshot."""
        snap = {
            "tick": self.tick,
            "epoch": self.current_epoch_name,
            "temperature": self.environment.temperature,
            "particles": len(self.quantum_field.particles),
            "atoms": len(self.atomic_system.atoms),
        }

        if self.chemical_system:
            snap["molecules"] = len(self.chemical_system.molecules)

        if self.biosphere:
            snap["cells"] = len(self.biosphere.cells)
            snap["fitness"] = round(self.biosphere.average_fitness(), 3)
            snap["mutations"] = self.biosphere.total_mutations()
            snap["generation"] = self.biosphere.generation

        snap["environment"] = self.environment.to_compact()
        return snap

    def run(self, progress_interval: int = 0) -> SimulationMetrics:
        """Run the full simulation with performance tracking."""
        tracemalloc.start()
        t0 = time.monotonic()
        r0 = resource.getrusage(resource.RUSAGE_SELF)

        while self.tick < self.max_ticks:
            self.step()
            self.metrics.ticks_completed = self.tick

            if progress_interval and self.tick % progress_interval == 0:
                pct = self.tick / self.max_ticks * 100
                print(f"  [{pct:5.1f}%] tick={self.tick} "
                      f"epoch={self.current_epoch_name}")

        r1 = resource.getrusage(resource.RUSAGE_SELF)
        t1 = time.monotonic()
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        self.metrics.wall_time_s = t1 - t0
        self.metrics.cpu_user_s = r1.ru_utime - r0.ru_utime
        self.metrics.cpu_system_s = r1.ru_stime - r0.ru_stime
        self.metrics.peak_memory_kb = peak // 1024

        return self.metrics

    def state_compact(self) -> str:
        """Full compact state."""
        parts = [
            f"U[t={self.tick}/{self.max_ticks} e={self.current_epoch_name}]",
            self.quantum_field.to_compact(),
            self.atomic_system.to_compact(),
        ]
        if self.chemical_system:
            parts.append(self.chemical_system.to_compact())
        if self.biosphere:
            parts.append(self.biosphere.to_compact())
        parts.append(self.environment.to_compact())
        return " | ".join(parts)

    def big_bounce(self, new_seed: int = None):
        """Reset the universe for a new cycle (Big Bounce cosmology).

        Preserves the cycle count and derives a new seed from the current
        state if none is provided. Resets all physical layers to initial
        conditions while keeping metrics cumulative.

        This enables perpetual simulation without memory leaks — all
        lists and accumulators are reset to bounded initial state.
        """
        import random as _random
        import hashlib

        # Derive new seed from current state if not provided
        if new_seed is None:
            state_hash = hashlib.sha256(
                f"{self.tick}:{self.current_epoch_name}:{self.metrics.ticks_completed}".encode()
            ).hexdigest()[:8]
            new_seed = int(state_hash, 16)

        _random.seed(new_seed)

        # Increment cycle counter
        self._cycle = getattr(self, '_cycle', 0) + 1

        # Reset tick to 0 but keep max_ticks
        self.tick = 0
        self.current_epoch_name = "Void"

        # Reset physical layers (fresh allocations, old ones get GC'd)
        self.quantum_field = QuantumField(temperature=T_PLANCK)
        self.atomic_system = AtomicSystem()
        self.chemical_system = None
        self.biosphere = None
        self.environment = Environment(initial_temperature=T_PLANCK)

        # Reset history to prevent memory growth
        self.history.clear()
        self.epoch_transitions.clear()

    def run_perpetual(self, on_bounce=None, max_cycles: int = 0,
                      progress_interval: int = 0):
        """Run the simulation in perpetual Big Bounce mode.

        After each cycle completes (reaching Present epoch), the universe
        resets with a derived seed and starts a new cycle. This runs
        indefinitely unless max_cycles is set.

        Args:
            on_bounce: Callback(cycle_number, seed) called at each bounce.
            max_cycles: Stop after N cycles (0 = infinite).
            progress_interval: Print progress every N ticks (0 = silent).

        Returns:
            SimulationMetrics for the final cycle.
        """
        cycle = 0
        while max_cycles == 0 or cycle < max_cycles:
            # Run one full simulation cycle
            self.run(progress_interval=progress_interval)
            cycle += 1

            if on_bounce:
                on_bounce(cycle, self.tick)

            if max_cycles > 0 and cycle >= max_cycles:
                break

            # Big Bounce — reset for next cycle
            self.big_bounce()

        return self.metrics

    @property
    def cycle(self) -> int:
        """Current Big Bounce cycle number (0 = first run)."""
        return getattr(self, '_cycle', 0)

    def summary(self) -> dict:
        """Full simulation summary."""
        return {
            "metrics": self.metrics.to_dict(),
            "final_state": self._snapshot(),
            "epoch_transitions": [
                {"tick": t, "from": f, "to": to}
                for t, f, to in self.epoch_transitions
            ],
            "history_snapshots": len(self.history),
            "cycle": self.cycle,
        }
