"""Quantum and subatomic physics simulation.

Models quantum fields, particles, wave functions, superposition,
entanglement (simplified), and the quark-hadron transition.
Quantum effects influence atomic-level phenomena through
measurement/decoherence events.
"""
import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from simulator.constants import (
    HBAR, C, M_UP_QUARK, M_DOWN_QUARK, M_ELECTRON, M_PROTON,
    M_NEUTRON, M_PHOTON, M_NEUTRINO, STRONG_COUPLING, EM_COUPLING,
    WEAK_COUPLING, ALPHA, E_CHARGE, PI, T_PLANCK, T_ELECTROWEAK,
    T_QUARK_HADRON, NUCLEAR_RADIUS,
)


class ParticleType(Enum):
    # Quarks
    UP = "up"
    DOWN = "down"
    # Leptons
    ELECTRON = "electron"
    POSITRON = "positron"
    NEUTRINO = "neutrino"
    # Gauge bosons
    PHOTON = "photon"
    GLUON = "gluon"
    W_BOSON = "W"
    Z_BOSON = "Z"
    # Composite
    PROTON = "proton"
    NEUTRON = "neutron"


class Spin(Enum):
    UP = +0.5
    DOWN = -0.5


class Color(Enum):
    RED = "r"
    GREEN = "g"
    BLUE = "b"
    ANTI_RED = "ar"
    ANTI_GREEN = "ag"
    ANTI_BLUE = "ab"


PARTICLE_MASSES = {
    ParticleType.UP: M_UP_QUARK,
    ParticleType.DOWN: M_DOWN_QUARK,
    ParticleType.ELECTRON: M_ELECTRON,
    ParticleType.POSITRON: M_ELECTRON,
    ParticleType.NEUTRINO: M_NEUTRINO,
    ParticleType.PHOTON: M_PHOTON,
    ParticleType.GLUON: M_PHOTON,
    ParticleType.PROTON: M_PROTON,
    ParticleType.NEUTRON: M_NEUTRON,
}

PARTICLE_CHARGES = {
    ParticleType.UP: 2.0 / 3.0,
    ParticleType.DOWN: -1.0 / 3.0,
    ParticleType.ELECTRON: -1.0,
    ParticleType.POSITRON: 1.0,
    ParticleType.NEUTRINO: 0.0,
    ParticleType.PHOTON: 0.0,
    ParticleType.GLUON: 0.0,
    ParticleType.PROTON: 1.0,
    ParticleType.NEUTRON: 0.0,
}


@dataclass
class WaveFunction:
    """Simplified quantum wave function with amplitude and phase."""
    amplitude: float = 1.0
    phase: float = 0.0
    coherent: bool = True

    @property
    def probability(self) -> float:
        """Born rule: |psi|^2"""
        return self.amplitude ** 2

    def evolve(self, dt: float, energy: float):
        """Time evolution: phase rotation by E*dt/hbar."""
        if self.coherent:
            self.phase += energy * dt / HBAR
            self.phase %= (2 * PI)

    def collapse(self) -> bool:
        """Measurement: collapse to eigenstate. Returns True if 'detected'."""
        result = random.random() < self.probability
        self.amplitude = 1.0 if result else 0.0
        self.coherent = False
        return result

    def superpose(self, other: "WaveFunction") -> "WaveFunction":
        """Superposition of two states."""
        # Interference depends on phase difference
        phase_diff = self.phase - other.phase
        combined_amp = math.sqrt(
            self.amplitude ** 2 + other.amplitude ** 2
            + 2 * self.amplitude * other.amplitude * math.cos(phase_diff)
        )
        combined_phase = (self.phase + other.phase) / 2
        return WaveFunction(
            amplitude=min(combined_amp, 1.0),
            phase=combined_phase,
            coherent=True,
        )

    def to_compact(self) -> str:
        return f"ψ({self.amplitude:.3f}∠{self.phase:.2f})"


@dataclass
class Particle:
    """A quantum particle with position, momentum, and quantum numbers."""
    particle_type: ParticleType
    position: list = field(default_factory=lambda: [0.0, 0.0, 0.0])
    momentum: list = field(default_factory=lambda: [0.0, 0.0, 0.0])
    spin: Spin = Spin.UP
    color: Optional[Color] = None
    wave_fn: WaveFunction = field(default_factory=WaveFunction)
    entangled_with: Optional[int] = None  # ID of entangled partner
    particle_id: int = 0

    _id_counter = 0

    def __post_init__(self):
        Particle._id_counter += 1
        self.particle_id = Particle._id_counter

    @property
    def mass(self) -> float:
        return PARTICLE_MASSES.get(self.particle_type, 0.0)

    @property
    def charge(self) -> float:
        return PARTICLE_CHARGES.get(self.particle_type, 0.0)

    @property
    def energy(self) -> float:
        """E = sqrt(p^2c^2 + m^2c^4)"""
        p2 = sum(p ** 2 for p in self.momentum)
        return math.sqrt(p2 * C ** 2 + (self.mass * C ** 2) ** 2)

    @property
    def wavelength(self) -> float:
        """de Broglie wavelength: lambda = h / p"""
        p = math.sqrt(sum(p ** 2 for p in self.momentum))
        if p < 1e-20:
            return float("inf")
        return 2 * PI * HBAR / p

    def to_compact(self) -> str:
        return (f"{self.particle_type.value}"
                f"[{self.position[0]:.1f},{self.position[1]:.1f},"
                f"{self.position[2]:.1f}]"
                f"s={self.spin.value}")


@dataclass
class EntangledPair:
    """A pair of entangled particles (EPR pair)."""
    particle_a: Particle
    particle_b: Particle
    bell_state: str = "phi+"  # Bell state type

    def measure_a(self) -> Spin:
        """Measure particle A, instantly determining B."""
        if random.random() < 0.5:
            self.particle_a.spin = Spin.UP
            self.particle_b.spin = Spin.DOWN
        else:
            self.particle_a.spin = Spin.DOWN
            self.particle_b.spin = Spin.UP
        self.particle_a.wave_fn.coherent = False
        self.particle_b.wave_fn.coherent = False
        return self.particle_a.spin


class QuantumField:
    """Represents a quantum field that can create and annihilate particles."""

    def __init__(self, temperature: float = T_PLANCK):
        self.temperature = temperature
        self.particles: list[Particle] = []
        self.entangled_pairs: list[EntangledPair] = []
        self.vacuum_energy = 0.0
        self.total_created = 0
        self.total_annihilated = 0

    def pair_production(self, energy: float) -> Optional[tuple]:
        """Create particle-antiparticle pair from vacuum energy.

        Requires E >= 2mc^2 for the lightest possible pair.
        """
        if energy < 2 * M_ELECTRON * C ** 2:
            return None

        # Determine what we can produce
        if energy >= 2 * M_PROTON * C ** 2 and random.random() < 0.1:
            # Quark-antiquark pair (simplified as proton-like)
            p_type = ParticleType.UP
            ap_type = ParticleType.DOWN
        else:
            p_type = ParticleType.ELECTRON
            ap_type = ParticleType.POSITRON

        direction = [random.gauss(0, 1) for _ in range(3)]
        norm = math.sqrt(sum(d ** 2 for d in direction)) or 1.0
        p_momentum = energy / (2 * C)

        particle = Particle(
            particle_type=p_type,
            momentum=[d / norm * p_momentum for d in direction],
            spin=Spin.UP,
        )
        antiparticle = Particle(
            particle_type=ap_type,
            momentum=[-d / norm * p_momentum for d in direction],
            spin=Spin.DOWN,
        )

        # They're entangled
        particle.entangled_with = antiparticle.particle_id
        antiparticle.entangled_with = particle.particle_id

        self.particles.extend([particle, antiparticle])
        self.entangled_pairs.append(
            EntangledPair(particle, antiparticle)
        )
        self.total_created += 2

        return (particle, antiparticle)

    def annihilate(self, p1: Particle, p2: Particle) -> float:
        """Annihilate particle-antiparticle pair, returning energy."""
        energy = p1.energy + p2.energy
        if p1 in self.particles:
            self.particles.remove(p1)
        if p2 in self.particles:
            self.particles.remove(p2)
        self.total_annihilated += 2
        self.vacuum_energy += energy * 0.01  # Small fraction to vacuum

        # Create photons from annihilation
        photon1 = Particle(
            particle_type=ParticleType.PHOTON,
            momentum=[energy / (2 * C), 0, 0],
        )
        photon2 = Particle(
            particle_type=ParticleType.PHOTON,
            momentum=[-energy / (2 * C), 0, 0],
        )
        self.particles.extend([photon1, photon2])
        return energy

    def quark_confinement(self) -> list:
        """Combine quarks into hadrons when temperature drops enough."""
        if self.temperature > T_QUARK_HADRON:
            return []

        hadrons = []
        ups = [p for p in self.particles if p.particle_type == ParticleType.UP]
        downs = [p for p in self.particles
                 if p.particle_type == ParticleType.DOWN]

        while len(ups) >= 2 and len(downs) >= 1:
            # Form proton (uud)
            u1, u2 = ups.pop(), ups.pop()
            d1 = downs.pop()

            # Assign colors for color neutrality
            u1.color = Color.RED
            u2.color = Color.GREEN
            d1.color = Color.BLUE

            proton = Particle(
                particle_type=ParticleType.PROTON,
                position=u1.position[:],
                momentum=[
                    u1.momentum[i] + u2.momentum[i] + d1.momentum[i]
                    for i in range(3)
                ],
            )

            for q in (u1, u2, d1):
                if q in self.particles:
                    self.particles.remove(q)
            self.particles.append(proton)
            hadrons.append(proton)

        while len(ups) >= 1 and len(downs) >= 2:
            # Form neutron (udd)
            u1 = ups.pop()
            d1, d2 = downs.pop(), downs.pop()

            u1.color = Color.RED
            d1.color = Color.GREEN
            d2.color = Color.BLUE

            neutron = Particle(
                particle_type=ParticleType.NEUTRON,
                position=u1.position[:],
                momentum=[
                    u1.momentum[i] + d1.momentum[i] + d2.momentum[i]
                    for i in range(3)
                ],
            )

            for q in (u1, d1, d2):
                if q in self.particles:
                    self.particles.remove(q)
            self.particles.append(neutron)
            hadrons.append(neutron)

        return hadrons

    def vacuum_fluctuation(self) -> Optional[tuple]:
        """Spontaneous virtual particle pair from vacuum energy."""
        # Probability scales with temperature
        prob = min(0.5, self.temperature / T_PLANCK)
        if random.random() < prob:
            energy = random.expovariate(1.0 / (self.temperature * 0.001))
            return self.pair_production(energy)
        return None

    def decohere(self, particle: Particle, environment_coupling: float = 0.1):
        """Environmental decoherence of a particle's wave function."""
        if particle.wave_fn.coherent:
            decoherence_rate = environment_coupling * self.temperature
            if random.random() < decoherence_rate:
                particle.wave_fn.collapse()

    def cool(self, factor: float = 0.999):
        """Cool the field (universe expansion)."""
        self.temperature *= factor

    def evolve(self, dt: float = 1.0):
        """Evolve all particles by one time step."""
        for p in self.particles:
            # Update position from momentum
            if p.mass > 0:
                for i in range(3):
                    p.position[i] += p.momentum[i] / p.mass * dt
            else:
                # Massless particles move at c
                p_mag = math.sqrt(sum(x ** 2 for x in p.momentum)) or 1.0
                for i in range(3):
                    p.position[i] += p.momentum[i] / p_mag * C * dt

            # Evolve wave function
            p.wave_fn.evolve(dt, p.energy)

    def particle_count(self) -> dict:
        """Count particles by type."""
        counts = {}
        for p in self.particles:
            key = p.particle_type.value
            counts[key] = counts.get(key, 0) + 1
        return counts

    def total_energy(self) -> float:
        """Total energy in the field."""
        return sum(p.energy for p in self.particles) + self.vacuum_energy

    def to_compact(self) -> str:
        """Compact state representation."""
        counts = self.particle_count()
        count_str = ",".join(f"{k}:{v}" for k, v in sorted(counts.items()))
        return (f"QF[T={self.temperature:.1e} E={self.total_energy():.1e} "
                f"n={len(self.particles)} {count_str}]")
