"""Atomic physics simulation.

Models atoms with electron shells, ionization, chemical bonding potential,
and the periodic table. Atoms emerge from the quantum/nuclear level
when temperature drops below recombination threshold.
"""
import math
import random
from dataclasses import dataclass, field
from typing import Optional

from simulator.constants import (
    ELECTRON_SHELLS, BOND_ENERGY_COVALENT, BOND_ENERGY_IONIC,
    BOND_ENERGY_HYDROGEN, T_RECOMBINATION, E_CHARGE, HBAR,
    M_ELECTRON, ALPHA, C, K_B,
)
from simulator.quantum import Particle, ParticleType, QuantumField


# Periodic table data: (symbol, name, group, period, electronegativity)
ELEMENTS = {
    1: ("H", "Hydrogen", 1, 1, 2.20),
    2: ("He", "Helium", 18, 1, 0.0),
    3: ("Li", "Lithium", 1, 2, 0.98),
    4: ("Be", "Beryllium", 2, 2, 1.57),
    5: ("B", "Boron", 13, 2, 2.04),
    6: ("C", "Carbon", 14, 2, 2.55),
    7: ("N", "Nitrogen", 15, 2, 3.04),
    8: ("O", "Oxygen", 16, 2, 3.44),
    9: ("F", "Fluorine", 17, 2, 3.98),
    10: ("Ne", "Neon", 18, 2, 0.0),
    11: ("Na", "Sodium", 1, 3, 0.93),
    12: ("Mg", "Magnesium", 2, 3, 1.31),
    13: ("Al", "Aluminum", 13, 3, 1.61),
    14: ("Si", "Silicon", 14, 3, 1.90),
    15: ("P", "Phosphorus", 15, 3, 2.19),
    16: ("S", "Sulfur", 16, 3, 2.58),
    17: ("Cl", "Chlorine", 17, 3, 3.16),
    18: ("Ar", "Argon", 18, 3, 0.0),
    19: ("K", "Potassium", 1, 4, 0.82),
    20: ("Ca", "Calcium", 2, 4, 1.00),
    26: ("Fe", "Iron", 8, 4, 1.83),
}


@dataclass
class ElectronShell:
    """An electron shell with quantum numbers."""
    n: int                    # Principal quantum number
    max_electrons: int        # 2n^2
    electrons: int = 0        # Current electron count

    @property
    def full(self) -> bool:
        return self.electrons >= self.max_electrons

    @property
    def empty(self) -> bool:
        return self.electrons == 0

    def add_electron(self) -> bool:
        """Add an electron if shell not full."""
        if not self.full:
            self.electrons += 1
            return True
        return False

    def remove_electron(self) -> bool:
        """Remove an electron if shell not empty."""
        if not self.empty:
            self.electrons -= 1
            return True
        return False


@dataclass
class Atom:
    """An atom with protons, neutrons, and electron shells."""
    atomic_number: int      # Number of protons
    mass_number: int = 0    # Protons + neutrons
    electron_count: int = 0
    position: list = field(default_factory=lambda: [0.0, 0.0, 0.0])
    velocity: list = field(default_factory=lambda: [0.0, 0.0, 0.0])
    shells: list = field(default_factory=list)
    bonds: list = field(default_factory=list)  # IDs of bonded atoms
    atom_id: int = 0
    ionization_energy: float = 0.0

    _id_counter = 0

    def __post_init__(self):
        Atom._id_counter += 1
        self.atom_id = Atom._id_counter

        if self.mass_number == 0:
            self.mass_number = self.atomic_number * 2  # Approximate
            if self.atomic_number == 1:
                self.mass_number = 1

        if self.electron_count == 0:
            self.electron_count = self.atomic_number  # Neutral atom

        if not self.shells:
            self._build_shells()

        self._compute_ionization_energy()

    def _build_shells(self):
        """Fill electron shells according to Aufbau principle."""
        self.shells = []
        remaining = self.electron_count
        for i, max_e in enumerate(ELECTRON_SHELLS):
            if remaining <= 0:
                break
            shell = ElectronShell(
                n=i + 1,
                max_electrons=max_e,
                electrons=min(remaining, max_e),
            )
            self.shells.append(shell)
            remaining -= shell.electrons

    def _compute_ionization_energy(self):
        """Estimate ionization energy from shell structure."""
        if not self.shells or self.shells[-1].empty:
            self.ionization_energy = 0.0
            return
        n = self.shells[-1].n
        z_eff = self.atomic_number - sum(
            s.electrons for s in self.shells[:-1]
        )
        # Hydrogen-like approximation: E = 13.6 * Z_eff^2 / n^2
        self.ionization_energy = 13.6 * z_eff ** 2 / n ** 2

    @property
    def symbol(self) -> str:
        elem = ELEMENTS.get(self.atomic_number)
        return elem[0] if elem else f"E{self.atomic_number}"

    @property
    def name(self) -> str:
        elem = ELEMENTS.get(self.atomic_number)
        return elem[1] if elem else f"Element-{self.atomic_number}"

    @property
    def electronegativity(self) -> float:
        elem = ELEMENTS.get(self.atomic_number)
        return elem[4] if elem else 1.0

    @property
    def charge(self) -> int:
        return self.atomic_number - self.electron_count

    @property
    def valence_electrons(self) -> int:
        if not self.shells:
            return 0
        return self.shells[-1].electrons

    @property
    def needs_electrons(self) -> int:
        """How many electrons needed to fill valence shell."""
        if not self.shells:
            return 0
        shell = self.shells[-1]
        return shell.max_electrons - shell.electrons

    @property
    def is_noble_gas(self) -> bool:
        if not self.shells:
            return False
        return self.shells[-1].full

    @property
    def is_ion(self) -> bool:
        return self.charge != 0

    def ionize(self) -> bool:
        """Remove outermost electron."""
        if self.electron_count > 0:
            self.electron_count -= 1
            self._build_shells()
            self._compute_ionization_energy()
            return True
        return False

    def capture_electron(self) -> bool:
        """Capture a free electron."""
        self.electron_count += 1
        self._build_shells()
        self._compute_ionization_energy()
        return True

    def can_bond_with(self, other: "Atom") -> bool:
        """Check if bonding is possible."""
        if self.is_noble_gas or other.is_noble_gas:
            return False
        if len(self.bonds) >= 4 or len(other.bonds) >= 4:
            return False
        return True

    def bond_type(self, other: "Atom") -> str:
        """Determine bond type based on electronegativity difference."""
        diff = abs(self.electronegativity - other.electronegativity)
        if diff > 1.7:
            return "ionic"
        elif diff > 0.4:
            return "polar_covalent"
        else:
            return "covalent"

    def bond_energy(self, other: "Atom") -> float:
        """Calculate bond energy."""
        btype = self.bond_type(other)
        if btype == "ionic":
            return BOND_ENERGY_IONIC
        elif btype == "polar_covalent":
            return (BOND_ENERGY_COVALENT + BOND_ENERGY_IONIC) / 2
        else:
            return BOND_ENERGY_COVALENT

    def distance_to(self, other: "Atom") -> float:
        """Euclidean distance to another atom."""
        return math.sqrt(sum(
            (a - b) ** 2 for a, b in zip(self.position, other.position)
        ))

    def to_compact(self) -> str:
        charge_str = ""
        if self.charge > 0:
            charge_str = f"+{self.charge}"
        elif self.charge < 0:
            charge_str = str(self.charge)
        shells_str = ".".join(str(s.electrons) for s in self.shells)
        return (f"{self.symbol}{self.mass_number}{charge_str}"
                f"[{shells_str}]b{len(self.bonds)}")


class AtomicSystem:
    """Collection of atoms with interactions."""

    def __init__(self, temperature: float = T_RECOMBINATION):
        self.atoms: list[Atom] = []
        self.temperature = temperature
        self.free_electrons: list[Particle] = []
        self.bonds_formed = 0
        self.bonds_broken = 0

    def recombination(self, field: QuantumField) -> list[Atom]:
        """Capture free electrons into ions when T < T_recombination."""
        if self.temperature > T_RECOMBINATION:
            return []

        new_atoms = []
        protons = [p for p in field.particles
                   if p.particle_type == ParticleType.PROTON]
        electrons = [p for p in field.particles
                     if p.particle_type == ParticleType.ELECTRON]

        for proton in protons:
            if not electrons:
                break
            electron = electrons.pop()
            atom = Atom(
                atomic_number=1,
                mass_number=1,
                position=proton.position[:],
                velocity=proton.momentum[:],
            )
            new_atoms.append(atom)
            self.atoms.append(atom)

            if proton in field.particles:
                field.particles.remove(proton)
            if electron in field.particles:
                field.particles.remove(electron)

        return new_atoms

    def nucleosynthesis(self, protons: int = 0, neutrons: int = 0) -> list[Atom]:
        """Form heavier elements through nuclear fusion.

        Simplified: combines protons and neutrons into nuclei.
        """
        new_atoms = []

        # Hydrogen is trivial (1 proton)
        # Helium-4: 2 protons + 2 neutrons
        while protons >= 2 and neutrons >= 2:
            he = Atom(
                atomic_number=2,
                mass_number=4,
                position=[random.gauss(0, 10) for _ in range(3)],
            )
            new_atoms.append(he)
            self.atoms.append(he)
            protons -= 2
            neutrons -= 2

        # Remaining protons become hydrogen
        for _ in range(protons):
            h = Atom(
                atomic_number=1,
                mass_number=1,
                position=[random.gauss(0, 10) for _ in range(3)],
            )
            new_atoms.append(h)
            self.atoms.append(h)

        return new_atoms

    def stellar_nucleosynthesis(self, temperature: float) -> list[Atom]:
        """Form heavier elements in stellar cores.

        Carbon (6), Nitrogen (7), Oxygen (8), and up to Iron (26).
        """
        new_atoms = []

        # Need high temperatures and existing lighter elements
        if temperature < 1e3:
            return new_atoms

        heliums = [a for a in self.atoms if a.atomic_number == 2]

        # Triple-alpha process: 3 He -> C
        while len(heliums) >= 3 and random.random() < 0.01:
            for _ in range(3):
                he = heliums.pop()
                self.atoms.remove(he)

            carbon = Atom(
                atomic_number=6,
                mass_number=12,
                position=[random.gauss(0, 5) for _ in range(3)],
            )
            new_atoms.append(carbon)
            self.atoms.append(carbon)

        # C + He -> O
        carbons = [a for a in self.atoms if a.atomic_number == 6]
        heliums = [a for a in self.atoms if a.atomic_number == 2]
        while carbons and heliums and random.random() < 0.02:
            c = carbons.pop()
            he = heliums.pop()
            self.atoms.remove(c)
            self.atoms.remove(he)

            oxygen = Atom(
                atomic_number=8,
                mass_number=16,
                position=c.position[:],
            )
            new_atoms.append(oxygen)
            self.atoms.append(oxygen)

        # O + He -> Ne -> Mg -> Si -> S -> Ar -> Ca -> ... -> Fe
        # (simplified chain)
        oxygens = [a for a in self.atoms if a.atomic_number == 8]
        heliums = [a for a in self.atoms if a.atomic_number == 2]
        if oxygens and heliums and random.random() < 0.005:
            o = oxygens[0]
            he = heliums[0]
            self.atoms.remove(o)
            self.atoms.remove(he)
            # Jump to nitrogen for variety
            nitrogen = Atom(
                atomic_number=7,
                mass_number=14,
                position=o.position[:],
            )
            new_atoms.append(nitrogen)
            self.atoms.append(nitrogen)

        return new_atoms

    def attempt_bond(self, a1: Atom, a2: Atom) -> bool:
        """Try to form a chemical bond between two atoms."""
        if not a1.can_bond_with(a2):
            return False

        dist = a1.distance_to(a2)
        bond_dist = 2.0  # Typical bond distance in SU

        if dist > bond_dist * 3:
            return False

        # Bond formation probability depends on temperature and distance
        energy_barrier = a1.bond_energy(a2)
        thermal_energy = K_B * self.temperature
        if thermal_energy > 0:
            prob = math.exp(-energy_barrier / thermal_energy)
        else:
            prob = 1.0 if dist < bond_dist else 0.0

        if random.random() < prob:
            a1.bonds.append(a2.atom_id)
            a2.bonds.append(a1.atom_id)
            self.bonds_formed += 1
            return True
        return False

    def break_bond(self, a1: Atom, a2: Atom) -> bool:
        """Break a bond due to thermal energy."""
        if a2.atom_id not in a1.bonds:
            return False

        energy_barrier = a1.bond_energy(a2)
        thermal_energy = K_B * self.temperature

        if thermal_energy > energy_barrier * 0.5:
            prob = math.exp(-energy_barrier / (thermal_energy + 1e-20))
            if random.random() < prob:
                a1.bonds.remove(a2.atom_id)
                a2.bonds.remove(a1.atom_id)
                self.bonds_broken += 1
                return True
        return False

    def cool(self, factor: float = 0.999):
        """Cool the atomic system."""
        self.temperature *= factor

    def element_counts(self) -> dict:
        """Count atoms by element."""
        counts = {}
        for a in self.atoms:
            sym = a.symbol
            counts[sym] = counts.get(sym, 0) + 1
        return counts

    def to_compact(self) -> str:
        counts = self.element_counts()
        count_str = ",".join(f"{k}:{v}" for k, v in sorted(counts.items()))
        return (f"AS[T={self.temperature:.1e} n={len(self.atoms)} "
                f"bonds={self.bonds_formed} {count_str}]")
