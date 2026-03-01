"""Chemistry simulation - molecular assembly and reactions.

Models formation of molecules from atoms: water, amino acids,
nucleotides, and other biomolecules essential for life.
Chemical reactions are driven by energy, catalysis, and concentration.
"""
import math
import random
from dataclasses import dataclass, field
from typing import Optional

from simulator.constants import (
    K_B, BOND_ENERGY_COVALENT, BOND_ENERGY_HYDROGEN,
    BOND_ENERGY_VAN_DER_WAALS, AMINO_ACIDS,
)
from simulator.atomic import Atom, AtomicSystem


@dataclass
class Molecule:
    """A molecule: a collection of bonded atoms."""
    atoms: list = field(default_factory=list)
    name: str = ""
    formula: str = ""
    molecule_id: int = 0
    energy: float = 0.0
    position: list = field(default_factory=lambda: [0.0, 0.0, 0.0])
    is_organic: bool = False
    functional_groups: list = field(default_factory=list)

    _id_counter = 0

    def __post_init__(self):
        Molecule._id_counter += 1
        self.molecule_id = Molecule._id_counter
        if not self.formula and self.atoms:
            self._compute_formula()

    def _compute_formula(self):
        """Compute chemical formula from constituent atoms."""
        counts = {}
        for atom in self.atoms:
            sym = atom.symbol
            counts[sym] = counts.get(sym, 0) + 1

        # Standard chemistry ordering: C, H, then alphabetical
        parts = []
        for sym in ["C", "H"]:
            if sym in counts:
                n = counts.pop(sym)
                parts.append(f"{sym}{n}" if n > 1 else sym)
        for sym in sorted(counts):
            n = counts[sym]
            parts.append(f"{sym}{n}" if n > 1 else sym)
        self.formula = "".join(parts)

        # Check if organic
        has_c = any(a.atomic_number == 6 for a in self.atoms)
        has_h = any(a.atomic_number == 1 for a in self.atoms)
        self.is_organic = has_c and has_h

    @property
    def molecular_weight(self) -> float:
        return sum(a.mass_number for a in self.atoms)

    @property
    def atom_count(self) -> int:
        return len(self.atoms)

    def to_compact(self) -> str:
        return f"{self.name or self.formula}(mw={self.molecular_weight})"


class ChemicalReaction:
    """A chemical reaction with reactants, products, and energy."""

    def __init__(self, reactants: list, products: list,
                 activation_energy: float = 1.0,
                 delta_h: float = 0.0,
                 name: str = ""):
        self.reactants = reactants
        self.products = products
        self.activation_energy = activation_energy
        self.delta_h = delta_h  # Negative = exothermic
        self.name = name

    def can_proceed(self, temperature: float) -> bool:
        """Check if reaction can proceed at given temperature."""
        thermal_energy = K_B * temperature
        if thermal_energy <= 0:
            return False
        rate = math.exp(-self.activation_energy / thermal_energy)
        return random.random() < rate

    def to_compact(self) -> str:
        r = "+".join(self.reactants)
        p = "+".join(self.products)
        return f"{r}->{p}(Ea={self.activation_energy:.1f},dH={self.delta_h:.1f})"


class ChemicalSystem:
    """Manages molecular assembly and chemical reactions."""

    def __init__(self, atomic_system: AtomicSystem):
        self.atomic = atomic_system
        self.molecules: list[Molecule] = []
        self.reactions_occurred = 0
        self.water_count = 0
        self.amino_acid_count = 0
        self.nucleotide_count = 0

    def form_water(self) -> list[Molecule]:
        """Form water molecules: 2H + O -> H2O"""
        waters = []
        hydrogens = [a for a in self.atomic.atoms
                     if a.atomic_number == 1 and not a.bonds]
        oxygens = [a for a in self.atomic.atoms
                   if a.atomic_number == 8 and len(a.bonds) < 2]

        while len(hydrogens) >= 2 and oxygens:
            h1 = hydrogens.pop()
            h2 = hydrogens.pop()
            o = oxygens.pop()

            water = Molecule(
                atoms=[h1, h2, o],
                name="water",
                position=o.position[:],
            )
            waters.append(water)
            self.molecules.append(water)
            self.water_count += 1

            # Form bonds
            h1.bonds.append(o.atom_id)
            h2.bonds.append(o.atom_id)
            o.bonds.extend([h1.atom_id, h2.atom_id])

        return waters

    def form_methane(self) -> list[Molecule]:
        """Form methane: C + 4H -> CH4"""
        methanes = []
        carbons = [a for a in self.atomic.atoms
                   if a.atomic_number == 6 and not a.bonds]
        hydrogens = [a for a in self.atomic.atoms
                     if a.atomic_number == 1 and not a.bonds]

        while carbons and len(hydrogens) >= 4:
            c = carbons.pop()
            hs = [hydrogens.pop() for _ in range(4)]

            methane = Molecule(
                atoms=[c] + hs,
                name="methane",
                position=c.position[:],
            )
            methanes.append(methane)
            self.molecules.append(methane)

            for h in hs:
                c.bonds.append(h.atom_id)
                h.bonds.append(c.atom_id)

        return methanes

    def form_ammonia(self) -> list[Molecule]:
        """Form ammonia: N + 3H -> NH3"""
        ammonias = []
        nitrogens = [a for a in self.atomic.atoms
                     if a.atomic_number == 7 and not a.bonds]
        hydrogens = [a for a in self.atomic.atoms
                     if a.atomic_number == 1 and not a.bonds]

        while nitrogens and len(hydrogens) >= 3:
            n = nitrogens.pop()
            hs = [hydrogens.pop() for _ in range(3)]

            ammonia = Molecule(
                atoms=[n] + hs,
                name="ammonia",
                position=n.position[:],
            )
            ammonias.append(ammonia)
            self.molecules.append(ammonia)

            for h in hs:
                n.bonds.append(h.atom_id)
                h.bonds.append(n.atom_id)

        return ammonias

    def form_amino_acid(self, aa_type: str = "Gly") -> Optional[Molecule]:
        """Form an amino acid from available atoms.

        Amino acids need: C, H, O, N (and sometimes S).
        Simplified: requires 2C + 5H + 2O + 1N minimum (glycine).
        """
        carbons = [a for a in self.atomic.atoms
                   if a.atomic_number == 6 and not a.bonds]
        hydrogens = [a for a in self.atomic.atoms
                     if a.atomic_number == 1 and not a.bonds]
        oxygens = [a for a in self.atomic.atoms
                   if a.atomic_number == 8 and len(a.bonds) < 2]
        nitrogens = [a for a in self.atomic.atoms
                     if a.atomic_number == 7 and not a.bonds]

        if len(carbons) < 2 or len(hydrogens) < 5:
            return None
        if len(oxygens) < 2 or len(nitrogens) < 1:
            return None

        atoms = (
            [carbons.pop() for _ in range(2)]
            + [hydrogens.pop() for _ in range(5)]
            + [oxygens.pop() for _ in range(2)]
            + [nitrogens.pop()]
        )

        aa = Molecule(
            atoms=atoms,
            name=aa_type,
            position=atoms[0].position[:],
            is_organic=True,
            functional_groups=["amino", "carboxyl"],
        )
        self.molecules.append(aa)
        self.amino_acid_count += 1

        # Form internal bonds
        for i, atom in enumerate(atoms[1:], 1):
            atoms[0].bonds.append(atom.atom_id)
            atom.bonds.append(atoms[0].atom_id)

        return aa

    def form_nucleotide(self, base: str = "A") -> Optional[Molecule]:
        """Form a nucleotide (sugar + phosphate + base).

        Simplified: requires C5 + H10 + O7 + N2 + P minimum.
        We use available atoms to approximate.
        """
        carbons = [a for a in self.atomic.atoms
                   if a.atomic_number == 6 and not a.bonds]
        hydrogens = [a for a in self.atomic.atoms
                     if a.atomic_number == 1 and not a.bonds]
        oxygens = [a for a in self.atomic.atoms
                   if a.atomic_number == 8 and len(a.bonds) < 2]
        nitrogens = [a for a in self.atomic.atoms
                     if a.atomic_number == 7 and not a.bonds]

        # Simplified requirements
        if len(carbons) < 5 or len(hydrogens) < 8:
            return None
        if len(oxygens) < 4 or len(nitrogens) < 2:
            return None

        atoms = (
            [carbons.pop() for _ in range(5)]
            + [hydrogens.pop() for _ in range(8)]
            + [oxygens.pop() for _ in range(4)]
            + [nitrogens.pop() for _ in range(2)]
        )

        nuc = Molecule(
            atoms=atoms,
            name=f"nucleotide-{base}",
            position=atoms[0].position[:],
            is_organic=True,
            functional_groups=["sugar", "phosphate", "base"],
        )
        self.molecules.append(nuc)
        self.nucleotide_count += 1

        for i, atom in enumerate(atoms[1:], 1):
            atoms[0].bonds.append(atom.atom_id)
            atom.bonds.append(atoms[0].atom_id)

        return nuc

    def catalyzed_reaction(self, temperature: float,
                           catalyst_present: bool = False) -> int:
        """Run catalyzed reactions to form complex molecules."""
        formed = 0
        # Activation energy is lower with catalyst
        ea_factor = 0.3 if catalyst_present else 1.0

        thermal = K_B * temperature

        # Try to form amino acids
        if thermal > 0 and len(self.atomic.atoms) > 10:
            aa_prob = math.exp(-5.0 * ea_factor / (thermal + 1e-20))
            if random.random() < aa_prob:
                aa_type = random.choice(AMINO_ACIDS)
                if self.form_amino_acid(aa_type):
                    formed += 1
                    self.reactions_occurred += 1

        # Try to form nucleotides
        if thermal > 0 and len(self.atomic.atoms) > 19:
            nuc_prob = math.exp(-8.0 * ea_factor / (thermal + 1e-20))
            if random.random() < nuc_prob:
                base = random.choice(["A", "T", "G", "C"])
                if self.form_nucleotide(base):
                    formed += 1
                    self.reactions_occurred += 1

        return formed

    def molecule_census(self) -> dict:
        """Count molecules by type."""
        counts = {}
        for m in self.molecules:
            key = m.name or m.formula
            counts[key] = counts.get(key, 0) + 1
        return counts

    def to_compact(self) -> str:
        counts = self.molecule_census()
        count_str = ",".join(f"{k}:{v}" for k, v in sorted(counts.items()))
        return (f"CS[mol={len(self.molecules)} "
                f"H2O={self.water_count} "
                f"aa={self.amino_acid_count} "
                f"nuc={self.nucleotide_count} "
                f"rxn={self.reactions_occurred} {count_str}]")
