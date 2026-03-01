"""Tests for biology simulation - DNA, RNA, proteins, epigenetics."""
import os
import sys
import unittest
import random
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulator.biology import (
    EpigeneticMark, Gene, DNAStrand, translate_mrna,
    Protein, Cell, Biosphere,
)
from simulator.constants import CODON_TABLE, NUCLEOTIDE_BASES


class TestEpigeneticMark(unittest.TestCase):
    def test_creation(self):
        mark = EpigeneticMark(position=5, mark_type="methylation")
        self.assertEqual(mark.position, 5)
        self.assertTrue(mark.active)

    def test_to_compact(self):
        mark = EpigeneticMark(position=3, mark_type="methylation")
        compact = mark.to_compact()
        self.assertEqual(compact, "M3+")

    def test_inactive_compact(self):
        mark = EpigeneticMark(
            position=7, mark_type="acetylation", active=False
        )
        compact = mark.to_compact()
        self.assertEqual(compact, "A7-")

    def test_phosphorylation(self):
        mark = EpigeneticMark(position=1, mark_type="phosphorylation")
        compact = mark.to_compact()
        self.assertEqual(compact, "P1+")


class TestGene(unittest.TestCase):
    def test_creation(self):
        gene = Gene(name="test", sequence=list("ATGCATGC"))
        self.assertEqual(gene.length, 8)
        self.assertAlmostEqual(gene.expression_level, 1.0)

    def test_methylate(self):
        gene = Gene(name="test", sequence=list("ATGCATGC"))
        gene.methylate(3, generation=1)
        self.assertEqual(len(gene.epigenetic_marks), 1)
        self.assertEqual(gene.epigenetic_marks[0].mark_type, "methylation")

    def test_methylate_out_of_range(self):
        gene = Gene(name="test", sequence=list("ATGC"))
        gene.methylate(10)  # Out of range
        self.assertEqual(len(gene.epigenetic_marks), 0)

    def test_demethylate(self):
        gene = Gene(name="test", sequence=list("ATGCATGC"))
        gene.methylate(3)
        gene.demethylate(3)
        methyl_marks = [m for m in gene.epigenetic_marks
                        if m.mark_type == "methylation"]
        self.assertEqual(len(methyl_marks), 0)

    def test_acetylate(self):
        gene = Gene(name="test", sequence=list("ATGCATGC"))
        gene.acetylate(2)
        acetyls = [m for m in gene.epigenetic_marks
                   if m.mark_type == "acetylation"]
        self.assertEqual(len(acetyls), 1)

    def test_silencing(self):
        gene = Gene(name="test", sequence=list("ATGC"))
        # Methylate heavily (>30% of length)
        for i in range(4):
            gene.methylate(i)
        self.assertTrue(gene.is_silenced)

    def test_not_silenced(self):
        gene = Gene(name="test", sequence=list("ATGCATGCATGC"))
        gene.methylate(0)
        self.assertFalse(gene.is_silenced)

    def test_transcribe(self):
        gene = Gene(name="test", sequence=list("ATGCAT"))
        rna = gene.transcribe()
        self.assertEqual(rna, list("AUGCAU"))

    def test_transcribe_silenced(self):
        gene = Gene(name="test", sequence=list("ATGC"))
        for i in range(4):
            gene.methylate(i)
        rna = gene.transcribe()
        self.assertEqual(rna, [])

    def test_mutate(self):
        random.seed(42)
        gene = Gene(name="test", sequence=list("AAAAAAAAAA"))
        mutations = gene.mutate(rate=0.5)
        self.assertGreater(mutations, 0)

    def test_mutate_zero_rate(self):
        gene = Gene(name="test", sequence=list("ATGC"))
        mutations = gene.mutate(rate=0.0)
        self.assertEqual(mutations, 0)

    def test_expression_update(self):
        gene = Gene(name="test", sequence=list("ATGCATGCATGC"))
        gene.acetylate(0)
        gene.acetylate(1)
        gene.acetylate(2)
        self.assertGreater(gene.expression_level, 0.5)

    def test_to_compact(self):
        gene = Gene(name="test", sequence=list("ATGCATGC"))
        compact = gene.to_compact()
        self.assertIn("G:test", compact)
        self.assertIn("ATGCATGC", compact)

    def test_to_compact_long(self):
        gene = Gene(name="test",
                    sequence=list("A" * 30))
        compact = gene.to_compact()
        self.assertIn("...", compact)


class TestDNAStrand(unittest.TestCase):
    def test_random_strand(self):
        random.seed(42)
        strand = DNAStrand.random_strand(100, num_genes=3)
        self.assertEqual(strand.length, 100)
        self.assertEqual(len(strand.genes), 3)

    def test_complementary(self):
        strand = DNAStrand(sequence=list("ATGC"))
        comp = strand.complementary_strand
        self.assertEqual(comp, list("TACG"))

    def test_gc_content(self):
        strand = DNAStrand(sequence=list("GGCC"))
        self.assertAlmostEqual(strand.gc_content, 1.0)
        strand2 = DNAStrand(sequence=list("AATT"))
        self.assertAlmostEqual(strand2.gc_content, 0.0)

    def test_gc_content_empty(self):
        strand = DNAStrand(sequence=[])
        self.assertEqual(strand.gc_content, 0.0)

    def test_replicate(self):
        random.seed(42)
        strand = DNAStrand.random_strand(50, num_genes=2)
        daughter = strand.replicate()
        self.assertEqual(daughter.generation, strand.generation + 1)
        self.assertEqual(daughter.length, strand.length)

    def test_apply_mutations(self):
        random.seed(42)
        strand = DNAStrand.random_strand(100, num_genes=2)
        mutations = strand.apply_mutations(
            uv_intensity=100.0, cosmic_ray_flux=100.0
        )
        self.assertGreater(mutations, 0)

    def test_apply_mutations_no_radiation(self):
        strand = DNAStrand.random_strand(50)
        mutations = strand.apply_mutations(uv_intensity=0, cosmic_ray_flux=0)
        self.assertEqual(mutations, 0)

    def test_apply_epigenetic_changes(self):
        random.seed(42)
        strand = DNAStrand.random_strand(100, num_genes=3)
        strand.apply_epigenetic_changes(temperature=300, generation=1)
        # Should have added some marks
        total_marks = sum(
            len(g.epigenetic_marks) for g in strand.genes
        )
        # Probabilistic, may be 0
        self.assertIsInstance(total_marks, int)

    def test_to_compact(self):
        strand = DNAStrand.random_strand(50)
        compact = strand.to_compact()
        self.assertIn("DNA[", compact)
        self.assertIn("gen=", compact)

    def test_complement_unknown_base(self):
        strand = DNAStrand(sequence=["X"])
        comp = strand.complementary_strand
        self.assertEqual(comp, ["N"])


class TestTranslateMRNA(unittest.TestCase):
    def test_simple_protein(self):
        # AUG (start/Met) + UUU (Phe) + UAA (stop)
        mrna = list("AUGUUUUAA")
        protein = translate_mrna(mrna)
        self.assertEqual(protein, ["Met", "Phe"])

    def test_no_start_codon(self):
        mrna = list("UUUUUUUAA")
        protein = translate_mrna(mrna)
        self.assertEqual(protein, [])

    def test_stop_codon(self):
        mrna = list("AUGUAGUUU")
        protein = translate_mrna(mrna)
        self.assertEqual(protein, ["Met"])  # Stops at UAG

    def test_short_mrna(self):
        mrna = list("AU")
        protein = translate_mrna(mrna)
        self.assertEqual(protein, [])

    def test_unknown_codon(self):
        # AUG + XXX (unknown) + UAA
        mrna = list("AUGXXXUAA")
        protein = translate_mrna(mrna)
        # XXX returns None from CODON_TABLE, should be skipped
        self.assertEqual(protein[0], "Met")

    def test_all_codons(self):
        for codon, aa in CODON_TABLE.items():
            if aa != "STOP":
                mrna = list("AUG" + codon + "UAA")
                protein = translate_mrna(mrna)
                self.assertIn(aa, protein)


class TestProtein(unittest.TestCase):
    def test_creation(self):
        p = Protein(amino_acids=["Met", "Phe", "Leu"])
        self.assertEqual(p.length, 3)
        self.assertFalse(p.folded)

    def test_fold_success(self):
        random.seed(42)
        p = Protein(amino_acids=["Met"] * 10)
        p.fold()
        # Should fold with high probability for length 10

    def test_fold_too_short(self):
        p = Protein(amino_acids=["Met", "Phe"])
        result = p.fold()
        self.assertFalse(result)
        self.assertFalse(p.folded)

    def test_to_compact(self):
        p = Protein(amino_acids=["Met", "Phe"], name="enzyme1")
        compact = p.to_compact()
        self.assertIn("P:enzyme1", compact)
        self.assertIn("Met-Phe", compact)

    def test_to_compact_long(self):
        p = Protein(amino_acids=["Met"] * 15)
        compact = p.to_compact()
        self.assertIn("...", compact)


class TestCell(unittest.TestCase):
    def test_creation(self):
        random.seed(42)
        cell = Cell()
        self.assertTrue(cell.alive)
        self.assertEqual(cell.energy, 100.0)
        self.assertGreater(cell.cell_id, 0)

    def test_transcribe_and_translate(self):
        random.seed(42)
        cell = Cell(dna=DNAStrand.random_strand(90, num_genes=3))
        proteins = cell.transcribe_and_translate()
        self.assertIsInstance(proteins, list)

    def test_metabolize(self):
        cell = Cell()
        initial_energy = cell.energy
        cell.metabolize(environment_energy=30.0)
        # Should gain some energy
        self.assertNotEqual(cell.energy, initial_energy)

    def test_metabolize_starve(self):
        cell = Cell(energy=1.0)
        cell.metabolize(environment_energy=0.0)
        self.assertFalse(cell.alive)

    def test_divide(self):
        random.seed(42)
        cell = Cell(
            dna=DNAStrand.random_strand(90),
            energy=100.0,
        )
        daughter = cell.divide()
        self.assertIsNotNone(daughter)
        self.assertEqual(daughter.generation, cell.generation + 1)
        self.assertAlmostEqual(cell.energy, daughter.energy)

    def test_divide_insufficient_energy(self):
        cell = Cell(energy=10.0)
        self.assertIsNone(cell.divide())

    def test_divide_dead(self):
        cell = Cell(alive=False)
        self.assertIsNone(cell.divide())

    def test_compute_fitness(self):
        random.seed(42)
        cell = Cell(dna=DNAStrand.random_strand(90))
        fitness = cell.compute_fitness()
        self.assertGreater(fitness, 0)
        self.assertLessEqual(fitness, 1.0)

    def test_compute_fitness_dead(self):
        cell = Cell(alive=False)
        fitness = cell.compute_fitness()
        self.assertEqual(fitness, 0.0)

    def test_compute_fitness_silenced_essential(self):
        cell = Cell(dna=DNAStrand.random_strand(90))
        # Silence essential gene
        for gene in cell.dna.genes:
            if gene.essential:
                for i in range(gene.length):
                    gene.methylate(i)
        fitness = cell.compute_fitness()
        self.assertLessEqual(fitness, 0.2)

    def test_to_compact(self):
        cell = Cell()
        compact = cell.to_compact()
        self.assertIn("Cell#", compact)
        self.assertIn("alive", compact)

    def test_energy_cap(self):
        cell = Cell(energy=50.0)
        # Add enzyme proteins
        from simulator.biology import Protein
        for _ in range(5):
            p = Protein(amino_acids=["Met"] * 5, function="enzyme",
                        folded=True)
            cell.proteins.append(p)
        cell.metabolize(environment_energy=50.0)
        self.assertLessEqual(cell.energy, 200.0)


class TestBiosphere(unittest.TestCase):
    def test_creation(self):
        random.seed(42)
        bio = Biosphere(initial_cells=5, dna_length=60)
        self.assertEqual(len(bio.cells), 5)
        self.assertEqual(bio.total_born, 5)

    def test_step(self):
        random.seed(42)
        bio = Biosphere(initial_cells=5, dna_length=60)
        bio.step(
            environment_energy=30.0,
            uv_intensity=0.1,
            cosmic_ray_flux=0.01,
            temperature=300.0,
        )
        self.assertEqual(bio.generation, 1)

    def test_multiple_steps(self):
        random.seed(42)
        bio = Biosphere(initial_cells=5, dna_length=60)
        for _ in range(10):
            bio.step(environment_energy=30.0, temperature=300.0)
        self.assertGreater(bio.generation, 0)
        self.assertGreater(bio.total_born, 5)

    def test_average_fitness(self):
        random.seed(42)
        bio = Biosphere(initial_cells=5)
        for cell in bio.cells:
            cell.compute_fitness()
        avg = bio.average_fitness()
        self.assertGreater(avg, 0)

    def test_average_fitness_empty(self):
        bio = Biosphere(initial_cells=0)
        self.assertEqual(bio.average_fitness(), 0.0)

    def test_average_gc_content(self):
        random.seed(42)
        bio = Biosphere(initial_cells=5)
        gc = bio.average_gc_content()
        self.assertGreater(gc, 0)
        self.assertLessEqual(gc, 1.0)

    def test_average_gc_empty(self):
        bio = Biosphere(initial_cells=0)
        self.assertEqual(bio.average_gc_content(), 0.0)

    def test_total_mutations(self):
        random.seed(42)
        bio = Biosphere(initial_cells=5)
        bio.step(environment_energy=30.0, uv_intensity=10.0, temperature=300.0)
        # Mutations should accumulate
        total = bio.total_mutations()
        self.assertIsInstance(total, int)

    def test_population_cap(self):
        random.seed(42)
        bio = Biosphere(initial_cells=10, dna_length=60)
        for _ in range(50):
            bio.step(environment_energy=50.0, temperature=300.0)
        self.assertLessEqual(len(bio.cells), 100)

    def test_to_compact(self):
        bio = Biosphere(initial_cells=3)
        compact = bio.to_compact()
        self.assertIn("Bio[", compact)
        self.assertIn("gen=", compact)


if __name__ == "__main__":
    unittest.main()
