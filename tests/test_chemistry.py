"""Tests for chemistry simulation."""
import os
import sys
import unittest
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulator.chemistry import Molecule, ChemicalReaction, ChemicalSystem
from simulator.atomic import Atom, AtomicSystem


class TestMolecule(unittest.TestCase):
    def test_creation(self):
        m = Molecule(name="test")
        self.assertEqual(m.name, "test")
        self.assertGreater(m.molecule_id, 0)

    def test_formula_computation(self):
        atoms = [
            Atom(atomic_number=6),  # C
            Atom(atomic_number=1),  # H
            Atom(atomic_number=1),  # H
            Atom(atomic_number=1),  # H
            Atom(atomic_number=1),  # H
        ]
        m = Molecule(atoms=atoms)
        self.assertEqual(m.formula, "CH4")
        self.assertTrue(m.is_organic)

    def test_formula_inorganic(self):
        atoms = [
            Atom(atomic_number=11),  # Na
            Atom(atomic_number=17),  # Cl
        ]
        m = Molecule(atoms=atoms)
        self.assertFalse(m.is_organic)

    def test_molecular_weight(self):
        atoms = [
            Atom(atomic_number=1),  # H
            Atom(atomic_number=1),  # H
            Atom(atomic_number=8),  # O
        ]
        m = Molecule(atoms=atoms)
        self.assertGreater(m.molecular_weight, 0)

    def test_atom_count(self):
        atoms = [Atom(atomic_number=1) for _ in range(3)]
        m = Molecule(atoms=atoms)
        self.assertEqual(m.atom_count, 3)

    def test_to_compact(self):
        m = Molecule(name="water", atoms=[Atom(atomic_number=1)])
        compact = m.to_compact()
        self.assertIn("water", compact)

    def test_formula_water(self):
        atoms = [
            Atom(atomic_number=1),
            Atom(atomic_number=1),
            Atom(atomic_number=8),
        ]
        m = Molecule(atoms=atoms)
        self.assertIn("H", m.formula)
        self.assertIn("O", m.formula)


class TestChemicalReaction(unittest.TestCase):
    def test_creation(self):
        rxn = ChemicalReaction(
            reactants=["H2", "O2"],
            products=["H2O"],
            activation_energy=1.0,
            delta_h=-5.0,
            name="combustion",
        )
        self.assertEqual(rxn.name, "combustion")

    def test_can_proceed_hot(self):
        rxn = ChemicalReaction(
            reactants=["A"], products=["B"],
            activation_energy=0.001,
        )
        self.assertTrue(rxn.can_proceed(temperature=10000))

    def test_can_proceed_cold(self):
        rxn = ChemicalReaction(
            reactants=["A"], products=["B"],
            activation_energy=1000.0,
        )
        # Very high barrier, very cold - shouldn't proceed
        results = [rxn.can_proceed(temperature=0.001) for _ in range(100)]
        self.assertFalse(any(results))

    def test_can_proceed_zero_temp(self):
        rxn = ChemicalReaction(
            reactants=["A"], products=["B"],
            activation_energy=1.0,
        )
        self.assertFalse(rxn.can_proceed(temperature=0.0))

    def test_to_compact(self):
        rxn = ChemicalReaction(
            reactants=["H2", "O2"],
            products=["H2O"],
        )
        compact = rxn.to_compact()
        self.assertIn("H2+O2->H2O", compact)


class TestChemicalSystem(unittest.TestCase):
    def setUp(self):
        self.asys = AtomicSystem(temperature=300)

    def _add_atoms(self, z, count):
        for _ in range(count):
            self.asys.atoms.append(Atom(atomic_number=z))

    def test_form_water(self):
        self._add_atoms(1, 4)  # H
        self._add_atoms(8, 2)  # O
        chem = ChemicalSystem(self.asys)
        waters = chem.form_water()
        self.assertEqual(len(waters), 2)
        self.assertEqual(chem.water_count, 2)

    def test_form_water_insufficient_h(self):
        self._add_atoms(1, 1)
        self._add_atoms(8, 2)
        chem = ChemicalSystem(self.asys)
        waters = chem.form_water()
        self.assertEqual(len(waters), 0)

    def test_form_methane(self):
        self._add_atoms(6, 1)  # C
        self._add_atoms(1, 4)  # H
        chem = ChemicalSystem(self.asys)
        methanes = chem.form_methane()
        self.assertEqual(len(methanes), 1)

    def test_form_methane_insufficient(self):
        self._add_atoms(6, 1)
        self._add_atoms(1, 2)
        chem = ChemicalSystem(self.asys)
        methanes = chem.form_methane()
        self.assertEqual(len(methanes), 0)

    def test_form_ammonia(self):
        self._add_atoms(7, 1)  # N
        self._add_atoms(1, 3)  # H
        chem = ChemicalSystem(self.asys)
        ammonias = chem.form_ammonia()
        self.assertEqual(len(ammonias), 1)

    def test_form_ammonia_insufficient(self):
        self._add_atoms(7, 1)
        self._add_atoms(1, 1)
        chem = ChemicalSystem(self.asys)
        ammonias = chem.form_ammonia()
        self.assertEqual(len(ammonias), 0)

    def test_form_amino_acid(self):
        self._add_atoms(6, 5)   # C
        self._add_atoms(1, 10)  # H
        self._add_atoms(8, 5)   # O
        self._add_atoms(7, 3)   # N
        chem = ChemicalSystem(self.asys)
        aa = chem.form_amino_acid("Gly")
        self.assertIsNotNone(aa)
        self.assertEqual(aa.name, "Gly")
        self.assertEqual(chem.amino_acid_count, 1)

    def test_form_amino_acid_insufficient(self):
        self._add_atoms(6, 1)
        chem = ChemicalSystem(self.asys)
        aa = chem.form_amino_acid()
        self.assertIsNone(aa)

    def test_form_nucleotide(self):
        self._add_atoms(6, 10)
        self._add_atoms(1, 20)
        self._add_atoms(8, 10)
        self._add_atoms(7, 5)
        chem = ChemicalSystem(self.asys)
        nuc = chem.form_nucleotide("A")
        self.assertIsNotNone(nuc)
        self.assertEqual(chem.nucleotide_count, 1)

    def test_form_nucleotide_insufficient(self):
        self._add_atoms(6, 2)
        chem = ChemicalSystem(self.asys)
        nuc = chem.form_nucleotide()
        self.assertIsNone(nuc)

    def test_catalyzed_reaction(self):
        random.seed(42)
        self._add_atoms(6, 20)
        self._add_atoms(1, 40)
        self._add_atoms(8, 20)
        self._add_atoms(7, 10)
        chem = ChemicalSystem(self.asys)
        formed = 0
        for _ in range(100):
            formed += chem.catalyzed_reaction(
                temperature=300, catalyst_present=True
            )
        self.assertGreater(formed, 0)

    def test_molecule_census(self):
        self._add_atoms(1, 4)
        self._add_atoms(8, 2)
        chem = ChemicalSystem(self.asys)
        chem.form_water()
        census = chem.molecule_census()
        self.assertEqual(census.get("water", 0), 2)

    def test_to_compact(self):
        chem = ChemicalSystem(self.asys)
        compact = chem.to_compact()
        self.assertIn("CS[", compact)


if __name__ == "__main__":
    unittest.main()
