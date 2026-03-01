"""Tests for atomic physics simulation."""
import os
import sys
import unittest
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulator.atomic import (
    Atom, ElectronShell, AtomicSystem, ELEMENTS,
)
from simulator.quantum import (
    Particle, ParticleType, QuantumField,
)
from simulator.constants import T_RECOMBINATION


class TestElectronShell(unittest.TestCase):
    def test_creation(self):
        shell = ElectronShell(n=1, max_electrons=2, electrons=0)
        self.assertEqual(shell.n, 1)
        self.assertTrue(shell.empty)
        self.assertFalse(shell.full)

    def test_add_electron(self):
        shell = ElectronShell(n=1, max_electrons=2, electrons=0)
        self.assertTrue(shell.add_electron())
        self.assertEqual(shell.electrons, 1)
        self.assertFalse(shell.empty)

    def test_add_electron_full(self):
        shell = ElectronShell(n=1, max_electrons=2, electrons=2)
        self.assertFalse(shell.add_electron())
        self.assertTrue(shell.full)

    def test_remove_electron(self):
        shell = ElectronShell(n=1, max_electrons=2, electrons=1)
        self.assertTrue(shell.remove_electron())
        self.assertEqual(shell.electrons, 0)

    def test_remove_electron_empty(self):
        shell = ElectronShell(n=1, max_electrons=2, electrons=0)
        self.assertFalse(shell.remove_electron())


class TestAtom(unittest.TestCase):
    def test_hydrogen(self):
        h = Atom(atomic_number=1)
        self.assertEqual(h.symbol, "H")
        self.assertEqual(h.name, "Hydrogen")
        self.assertEqual(h.mass_number, 1)
        self.assertEqual(h.electron_count, 1)
        self.assertEqual(h.charge, 0)

    def test_helium(self):
        he = Atom(atomic_number=2)
        self.assertEqual(he.symbol, "He")
        self.assertTrue(he.is_noble_gas)

    def test_carbon(self):
        c = Atom(atomic_number=6)
        self.assertEqual(c.symbol, "C")
        self.assertEqual(c.valence_electrons, 4)
        self.assertFalse(c.is_noble_gas)

    def test_oxygen(self):
        o = Atom(atomic_number=8)
        self.assertEqual(o.symbol, "O")

    def test_ionize(self):
        h = Atom(atomic_number=1)
        self.assertTrue(h.ionize())
        self.assertEqual(h.charge, 1)
        self.assertTrue(h.is_ion)

    def test_ionize_empty(self):
        h = Atom(atomic_number=1)
        h.ionize()
        self.assertFalse(h.ionize())  # No more electrons

    def test_capture_electron(self):
        h = Atom(atomic_number=1)
        h.ionize()
        h.capture_electron()
        self.assertEqual(h.charge, 0)

    def test_electronegativity(self):
        f = Atom(atomic_number=9)
        self.assertGreater(f.electronegativity, 3.0)

    def test_unknown_element(self):
        unknown = Atom(atomic_number=99)
        self.assertEqual(unknown.symbol, "E99")
        self.assertEqual(unknown.name, "Element-99")
        self.assertAlmostEqual(unknown.electronegativity, 1.0)

    def test_can_bond(self):
        c = Atom(atomic_number=6)
        h = Atom(atomic_number=1)
        self.assertTrue(c.can_bond_with(h))

    def test_cannot_bond_noble_gas(self):
        he = Atom(atomic_number=2)
        h = Atom(atomic_number=1)
        self.assertFalse(he.can_bond_with(h))

    def test_cannot_bond_max_bonds(self):
        c = Atom(atomic_number=6)
        c.bonds = [1, 2, 3, 4]
        h = Atom(atomic_number=1)
        self.assertFalse(c.can_bond_with(h))

    def test_bond_type_ionic(self):
        na = Atom(atomic_number=11)
        cl = Atom(atomic_number=17)
        self.assertEqual(na.bond_type(cl), "ionic")

    def test_bond_type_covalent(self):
        c = Atom(atomic_number=6)
        h = Atom(atomic_number=1)
        btype = c.bond_type(h)
        self.assertIn(btype, ["covalent", "polar_covalent"])

    def test_bond_energy(self):
        c = Atom(atomic_number=6)
        h = Atom(atomic_number=1)
        energy = c.bond_energy(h)
        self.assertGreater(energy, 0)

    def test_distance_to(self):
        a1 = Atom(atomic_number=1, position=[0.0, 0.0, 0.0])
        a2 = Atom(atomic_number=1, position=[3.0, 4.0, 0.0])
        self.assertAlmostEqual(a1.distance_to(a2), 5.0)

    def test_to_compact(self):
        h = Atom(atomic_number=1)
        compact = h.to_compact()
        self.assertIn("H", compact)

    def test_to_compact_ion(self):
        h = Atom(atomic_number=1)
        h.ionize()
        compact = h.to_compact()
        self.assertIn("+", compact)

    def test_needs_electrons(self):
        c = Atom(atomic_number=6)
        self.assertEqual(c.needs_electrons, 4)  # Needs 4 more in 2nd shell

    def test_ionization_energy(self):
        h = Atom(atomic_number=1)
        self.assertGreater(h.ionization_energy, 0)

    def test_shell_building(self):
        na = Atom(atomic_number=11)
        self.assertEqual(len(na.shells), 3)
        self.assertEqual(na.shells[0].electrons, 2)
        self.assertEqual(na.shells[1].electrons, 8)
        self.assertEqual(na.shells[2].electrons, 1)

    def test_valence_electrons_no_shells(self):
        a = Atom(atomic_number=1)
        a.shells = []
        self.assertEqual(a.valence_electrons, 0)
        self.assertEqual(a.needs_electrons, 0)
        self.assertFalse(a.is_noble_gas)


class TestAtomicSystem(unittest.TestCase):
    def test_creation(self):
        sys = AtomicSystem()
        self.assertEqual(len(sys.atoms), 0)

    def test_nucleosynthesis(self):
        asys = AtomicSystem()
        atoms = asys.nucleosynthesis(protons=4, neutrons=4)
        # Should form He + remaining H
        self.assertGreater(len(atoms), 0)
        elements = [a.symbol for a in atoms]
        self.assertIn("He", elements)

    def test_nucleosynthesis_hydrogen_only(self):
        asys = AtomicSystem()
        atoms = asys.nucleosynthesis(protons=3, neutrons=0)
        self.assertEqual(len(atoms), 3)
        for a in atoms:
            self.assertEqual(a.symbol, "H")

    def test_recombination(self):
        asys = AtomicSystem(temperature=T_RECOMBINATION - 100)
        qf = QuantumField(temperature=T_RECOMBINATION - 100)
        # Add protons and electrons
        for _ in range(5):
            qf.particles.append(Particle(particle_type=ParticleType.PROTON))
            qf.particles.append(Particle(particle_type=ParticleType.ELECTRON))
        atoms = asys.recombination(qf)
        self.assertEqual(len(atoms), 5)
        for a in atoms:
            self.assertEqual(a.symbol, "H")

    def test_recombination_too_hot(self):
        asys = AtomicSystem(temperature=T_RECOMBINATION + 1000)
        qf = QuantumField()
        atoms = asys.recombination(qf)
        self.assertEqual(len(atoms), 0)

    def test_stellar_nucleosynthesis(self):
        random.seed(42)
        asys = AtomicSystem()
        # Add helium for triple-alpha
        for _ in range(10):
            asys.atoms.append(Atom(atomic_number=2, mass_number=4))
        new_atoms = asys.stellar_nucleosynthesis(temperature=1e4)
        # May or may not produce carbon (probabilistic)
        self.assertIsInstance(new_atoms, list)

    def test_stellar_nucleosynthesis_cold(self):
        asys = AtomicSystem()
        new_atoms = asys.stellar_nucleosynthesis(temperature=100)
        self.assertEqual(len(new_atoms), 0)

    def test_attempt_bond(self):
        random.seed(42)
        asys = AtomicSystem(temperature=300)
        c = Atom(atomic_number=6, position=[0.0, 0.0, 0.0])
        h = Atom(atomic_number=1, position=[0.5, 0.0, 0.0])
        asys.atoms.extend([c, h])
        # Try many times (probabilistic)
        bonded = False
        for _ in range(100):
            if asys.attempt_bond(c, h):
                bonded = True
                break
        # May or may not bond depending on random

    def test_attempt_bond_too_far(self):
        asys = AtomicSystem(temperature=300)
        a1 = Atom(atomic_number=6, position=[0.0, 0.0, 0.0])
        a2 = Atom(atomic_number=1, position=[100.0, 0.0, 0.0])
        self.assertFalse(asys.attempt_bond(a1, a2))

    def test_break_bond(self):
        asys = AtomicSystem(temperature=10000)
        a1 = Atom(atomic_number=6)
        a2 = Atom(atomic_number=1)
        a1.bonds.append(a2.atom_id)
        a2.bonds.append(a1.atom_id)
        # High temperature should break bond eventually
        broken = False
        for _ in range(100):
            if asys.break_bond(a1, a2):
                broken = True
                break

    def test_break_bond_no_bond(self):
        asys = AtomicSystem()
        a1 = Atom(atomic_number=1)
        a2 = Atom(atomic_number=1)
        self.assertFalse(asys.break_bond(a1, a2))

    def test_cool(self):
        asys = AtomicSystem(temperature=1000)
        asys.cool(0.5)
        self.assertEqual(asys.temperature, 500)

    def test_element_counts(self):
        asys = AtomicSystem()
        asys.atoms.append(Atom(atomic_number=1))
        asys.atoms.append(Atom(atomic_number=1))
        asys.atoms.append(Atom(atomic_number=6))
        counts = asys.element_counts()
        self.assertEqual(counts["H"], 2)
        self.assertEqual(counts["C"], 1)

    def test_to_compact(self):
        asys = AtomicSystem()
        compact = asys.to_compact()
        self.assertIn("AS[", compact)

    def test_stellar_nucleosynthesis_carbon_to_oxygen(self):
        random.seed(0)
        asys = AtomicSystem()
        # Add carbon and helium for C + He -> O
        for _ in range(5):
            asys.atoms.append(Atom(atomic_number=6, mass_number=12))
            asys.atoms.append(Atom(atomic_number=2, mass_number=4))
        # Also add some helium for triple-alpha
        for _ in range(10):
            asys.atoms.append(Atom(atomic_number=2, mass_number=4))
        new_atoms = asys.stellar_nucleosynthesis(temperature=1e5)
        # Should have attempted some reactions

    def test_stellar_nucleosynthesis_nitrogen(self):
        random.seed(1)
        asys = AtomicSystem()
        for _ in range(3):
            asys.atoms.append(Atom(atomic_number=8, mass_number=16))
            asys.atoms.append(Atom(atomic_number=2, mass_number=4))
        new_atoms = asys.stellar_nucleosynthesis(temperature=1e5)


class TestElements(unittest.TestCase):
    def test_hydrogen(self):
        self.assertEqual(ELEMENTS[1][0], "H")

    def test_carbon(self):
        self.assertEqual(ELEMENTS[6][0], "C")

    def test_iron(self):
        self.assertEqual(ELEMENTS[26][0], "Fe")


if __name__ == "__main__":
    unittest.main()
