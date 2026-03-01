"""Biology simulation - DNA, RNA, proteins, and epigenetics.

Models:
- DNA strand assembly from nucleotides
- RNA transcription
- Protein translation via codon table
- Epigenetic modifications (methylation, histone acetylation)
- Cell division with mutation
- Natural selection pressure
"""
import math
import random
from dataclasses import dataclass, field
from typing import Optional

from simulator.constants import (
    NUCLEOTIDE_BASES, RNA_BASES, CODON_TABLE, AMINO_ACIDS,
    METHYLATION_PROBABILITY, DEMETHYLATION_PROBABILITY,
    HISTONE_ACETYLATION_PROB, HISTONE_DEACETYLATION_PROB,
    CHROMATIN_REMODEL_ENERGY, UV_MUTATION_RATE,
    COSMIC_RAY_MUTATION_RATE, K_B,
)
from simulator.chemistry import Molecule, ChemicalSystem


@dataclass
class EpigeneticMark:
    """An epigenetic modification at a specific genomic position."""
    position: int
    mark_type: str  # "methylation", "acetylation", "phosphorylation"
    active: bool = True
    generation_added: int = 0

    def to_compact(self) -> str:
        m = self.mark_type[0].upper()
        state = "+" if self.active else "-"
        return f"{m}{self.position}{state}"


@dataclass
class Gene:
    """A gene: a segment of DNA that encodes a protein."""
    name: str
    sequence: list = field(default_factory=list)  # List of bases
    start_pos: int = 0
    end_pos: int = 0
    expression_level: float = 1.0  # 0.0 = silenced, 1.0 = fully active
    epigenetic_marks: list = field(default_factory=list)
    essential: bool = False

    @property
    def length(self) -> int:
        return len(self.sequence)

    @property
    def is_silenced(self) -> bool:
        """Gene is silenced if heavily methylated."""
        methyl_count = sum(
            1 for m in self.epigenetic_marks
            if m.mark_type == "methylation" and m.active
        )
        return methyl_count > self.length * 0.3

    def methylate(self, position: int, generation: int = 0):
        """Add methylation mark."""
        if 0 <= position < self.length:
            self.epigenetic_marks.append(EpigeneticMark(
                position=position,
                mark_type="methylation",
                generation_added=generation,
            ))
            self._update_expression()

    def demethylate(self, position: int):
        """Remove methylation mark."""
        self.epigenetic_marks = [
            m for m in self.epigenetic_marks
            if not (m.position == position and m.mark_type == "methylation")
        ]
        self._update_expression()

    def acetylate(self, position: int, generation: int = 0):
        """Add histone acetylation (increases expression)."""
        self.epigenetic_marks.append(EpigeneticMark(
            position=position,
            mark_type="acetylation",
            generation_added=generation,
        ))
        self._update_expression()

    def _update_expression(self):
        """Update expression level based on epigenetic marks."""
        methyl = sum(
            1 for m in self.epigenetic_marks
            if m.mark_type == "methylation" and m.active
        )
        acetyl = sum(
            1 for m in self.epigenetic_marks
            if m.mark_type == "acetylation" and m.active
        )
        # Methylation suppresses, acetylation activates
        suppression = min(1.0, methyl / max(1, self.length) * 3)
        activation = min(1.0, acetyl / max(1, self.length) * 5)
        self.expression_level = max(0.0, min(1.0,
                                             1.0 - suppression + activation))

    def transcribe(self) -> list:
        """Transcribe DNA to mRNA (T -> U)."""
        if self.is_silenced:
            return []
        rna = []
        for base in self.sequence:
            if base == "T":
                rna.append("U")
            else:
                rna.append(base)
        return rna

    def mutate(self, rate: float = 0.001) -> int:
        """Apply random point mutations. Returns mutation count."""
        mutations = 0
        for i in range(self.length):
            if random.random() < rate:
                old = self.sequence[i]
                choices = [b for b in NUCLEOTIDE_BASES if b != old]
                self.sequence[i] = random.choice(choices)
                mutations += 1
        return mutations

    def to_compact(self) -> str:
        seq = "".join(self.sequence[:20])
        if self.length > 20:
            seq += f"...({self.length})"
        marks = "".join(m.to_compact() for m in self.epigenetic_marks[:5])
        return f"G:{self.name}[{seq}]e={self.expression_level:.2f}{{{marks}}}"


@dataclass
class DNAStrand:
    """A double-stranded DNA molecule."""
    sequence: list = field(default_factory=list)  # Template strand
    genes: list = field(default_factory=list)
    generation: int = 0
    mutation_count: int = 0

    COMPLEMENT = {"A": "T", "T": "A", "G": "C", "C": "G"}

    @property
    def length(self) -> int:
        return len(self.sequence)

    @property
    def complementary_strand(self) -> list:
        return [self.COMPLEMENT.get(b, "N") for b in self.sequence]

    @property
    def gc_content(self) -> float:
        if not self.sequence:
            return 0.0
        gc = sum(1 for b in self.sequence if b in ("G", "C"))
        return gc / len(self.sequence)

    @classmethod
    def random_strand(cls, length: int, num_genes: int = 3) -> "DNAStrand":
        """Generate a random DNA strand with genes."""
        sequence = [random.choice(NUCLEOTIDE_BASES) for _ in range(length)]
        strand = cls(sequence=sequence)

        # Place genes along the strand
        gene_len = length // (num_genes + 1)
        for i in range(num_genes):
            start = i * gene_len + random.randint(0, gene_len // 4)
            end = start + gene_len // 2
            if end > length:
                end = length

            gene = Gene(
                name=f"gene_{i}",
                sequence=sequence[start:end],
                start_pos=start,
                end_pos=end,
                essential=(i == 0),  # First gene is essential
            )
            strand.genes.append(gene)

        return strand

    def replicate(self) -> "DNAStrand":
        """Semi-conservative replication with possible errors."""
        new_sequence = self.sequence[:]
        new_genes = []

        for gene in self.genes:
            new_gene = Gene(
                name=gene.name,
                sequence=gene.sequence[:],
                start_pos=gene.start_pos,
                end_pos=gene.end_pos,
                essential=gene.essential,
                # Epigenetic marks can be partially inherited
                epigenetic_marks=[
                    EpigeneticMark(
                        position=m.position,
                        mark_type=m.mark_type,
                        active=m.active and random.random() < 0.8,
                        generation_added=m.generation_added,
                    )
                    for m in gene.epigenetic_marks
                    if random.random() < 0.7  # Some marks lost in replication
                ],
            )
            new_gene._update_expression()
            new_genes.append(new_gene)

        return DNAStrand(
            sequence=new_sequence,
            genes=new_genes,
            generation=self.generation + 1,
        )

    def apply_mutations(self, uv_intensity: float = 0.0,
                        cosmic_ray_flux: float = 0.0) -> int:
        """Apply environmental mutations."""
        total_mutations = 0
        rate = (UV_MUTATION_RATE * uv_intensity
                + COSMIC_RAY_MUTATION_RATE * cosmic_ray_flux)

        for gene in self.genes:
            m = gene.mutate(rate)
            total_mutations += m

        # Also mutate non-genic regions
        for i in range(self.length):
            if random.random() < rate:
                old = self.sequence[i]
                choices = [b for b in NUCLEOTIDE_BASES if b != old]
                self.sequence[i] = random.choice(choices)
                total_mutations += 1

        self.mutation_count += total_mutations
        return total_mutations

    def apply_epigenetic_changes(self, temperature: float,
                                 generation: int = 0):
        """Environmental epigenetic modifications."""
        for gene in self.genes:
            # Methylation
            if random.random() < METHYLATION_PROBABILITY:
                pos = random.randint(0, max(0, gene.length - 1))
                gene.methylate(pos, generation)

            # Demethylation
            if random.random() < DEMETHYLATION_PROBABILITY:
                if gene.epigenetic_marks:
                    methyls = [
                        m for m in gene.epigenetic_marks
                        if m.mark_type == "methylation"
                    ]
                    if methyls:
                        mark = random.choice(methyls)
                        gene.demethylate(mark.position)

            # Histone acetylation (temperature-dependent)
            thermal_factor = min(2.0, temperature / 300.0)
            if random.random() < HISTONE_ACETYLATION_PROB * thermal_factor:
                pos = random.randint(0, max(0, gene.length - 1))
                gene.acetylate(pos, generation)

            # Histone deacetylation
            if random.random() < HISTONE_DEACETYLATION_PROB:
                acetyls = [
                    m for m in gene.epigenetic_marks
                    if m.mark_type == "acetylation"
                ]
                if acetyls:
                    mark = random.choice(acetyls)
                    mark.active = False
                    gene._update_expression()

    def to_compact(self) -> str:
        seq = "".join(self.sequence[:30])
        if self.length > 30:
            seq += f"...({self.length})"
        genes = "|".join(g.to_compact() for g in self.genes[:5])
        return (f"DNA[gen={self.generation} mut={self.mutation_count} "
                f"gc={self.gc_content:.2f} {seq}]{{{genes}}}")


def translate_mrna(mrna: list) -> list:
    """Translate mRNA to protein (amino acid sequence)."""
    protein = []
    i = 0
    started = False

    while i + 2 < len(mrna):
        codon = mrna[i] + mrna[i + 1] + mrna[i + 2]
        aa = CODON_TABLE.get(codon)

        if aa == "Met" and not started:
            started = True
            protein.append(aa)
        elif started:
            if aa == "STOP":
                break
            elif aa:
                protein.append(aa)
        i += 3

    return protein


@dataclass
class Protein:
    """A protein: a chain of amino acids."""
    amino_acids: list = field(default_factory=list)
    name: str = ""
    function: str = ""  # "enzyme", "structural", "signaling"
    folded: bool = False
    active: bool = True

    @property
    def length(self) -> int:
        return len(self.amino_acids)

    def fold(self) -> bool:
        """Simplified protein folding - probability based on length."""
        if self.length < 3:
            self.folded = False
            return False
        fold_prob = min(0.9, 0.5 + 0.1 * math.log(self.length + 1))
        self.folded = random.random() < fold_prob
        return self.folded

    def to_compact(self) -> str:
        seq = "-".join(self.amino_acids[:10])
        if self.length > 10:
            seq += f"...({self.length})"
        return f"P:{self.name}[{seq}]f={'Y' if self.folded else 'N'}"


@dataclass
class Cell:
    """A cell with DNA, RNA, and proteins."""
    dna: DNAStrand = field(default_factory=lambda: DNAStrand.random_strand(100))
    proteins: list = field(default_factory=list)
    fitness: float = 1.0
    alive: bool = True
    generation: int = 0
    energy: float = 100.0
    cell_id: int = 0

    _id_counter = 0

    def __post_init__(self):
        Cell._id_counter += 1
        self.cell_id = Cell._id_counter

    def transcribe_and_translate(self) -> list[Protein]:
        """Central dogma: DNA -> mRNA -> Protein."""
        new_proteins = []
        for gene in self.dna.genes:
            if gene.expression_level < 0.1:
                continue  # Silenced

            # Transcribe
            mrna = gene.transcribe()
            if not mrna:
                continue

            # Translate
            aa_seq = translate_mrna(mrna)
            if not aa_seq:
                continue

            # Probability of producing protein scales with expression
            if random.random() > gene.expression_level:
                continue

            protein = Protein(
                amino_acids=aa_seq,
                name=f"protein_{gene.name}",
                function=random.choice(["enzyme", "structural", "signaling"]),
            )
            protein.fold()
            new_proteins.append(protein)
            self.proteins.append(protein)

        return new_proteins

    def metabolize(self, environment_energy: float = 10.0):
        """Basic metabolism: consume energy, produce waste."""
        # Enzymes help extract energy
        enzyme_count = sum(
            1 for p in self.proteins
            if p.function == "enzyme" and p.folded and p.active
        )
        efficiency = 0.3 + 0.15 * enzyme_count
        self.energy += environment_energy * efficiency
        self.energy -= 3.0  # Basal metabolic cost
        self.energy = min(self.energy, 200.0)  # Energy cap

        if self.energy <= 0:
            self.alive = False

    def divide(self) -> Optional["Cell"]:
        """Cell division with DNA replication and possible mutation."""
        if not self.alive or self.energy < 50.0:
            return None

        new_dna = self.dna.replicate()
        self.energy /= 2  # Split energy

        daughter = Cell(
            dna=new_dna,
            generation=self.generation + 1,
            energy=self.energy,
        )

        # Daughter transcribes its own proteins
        daughter.transcribe_and_translate()

        return daughter

    def compute_fitness(self) -> float:
        """Compute cell fitness based on functional proteins and DNA integrity."""
        if not self.alive:
            self.fitness = 0.0
            return 0.0

        # Essential genes must be active
        essential_active = all(
            not g.is_silenced for g in self.dna.genes if g.essential
        )
        if not essential_active:
            self.fitness = 0.1
            return 0.1

        # Fitness from proteins
        functional_proteins = sum(
            1 for p in self.proteins if p.folded and p.active
        )
        protein_fitness = min(1.0, functional_proteins / max(1, len(self.dna.genes)))

        # Fitness from energy
        energy_fitness = min(1.0, self.energy / 100.0)

        # GC content near 0.5 is optimal
        gc_fitness = 1.0 - abs(self.dna.gc_content - 0.5) * 2

        self.fitness = (protein_fitness * 0.4 + energy_fitness * 0.3
                        + gc_fitness * 0.3)
        return self.fitness

    def to_compact(self) -> str:
        return (f"Cell#{self.cell_id}[gen={self.generation} "
                f"fit={self.fitness:.2f} E={self.energy:.0f} "
                f"prot={len(self.proteins)} "
                f"{'alive' if self.alive else 'dead'}]")


class Biosphere:
    """Collection of cells with population dynamics."""

    def __init__(self, initial_cells: int = 5, dna_length: int = 90):
        self.cells: list[Cell] = []
        self.generation = 0
        self.total_born = 0
        self.total_died = 0
        self.dna_length = dna_length

        for _ in range(initial_cells):
            cell = Cell(
                dna=DNAStrand.random_strand(dna_length, num_genes=3),
            )
            cell.transcribe_and_translate()
            self.cells.append(cell)
            self.total_born += 1

    def step(self, environment_energy: float = 10.0,
             uv_intensity: float = 0.0,
             cosmic_ray_flux: float = 0.0,
             temperature: float = 300.0):
        """One generation step."""
        self.generation += 1

        # Metabolize
        for cell in self.cells:
            cell.metabolize(environment_energy)

        # Apply mutations
        for cell in self.cells:
            if cell.alive:
                cell.dna.apply_mutations(uv_intensity, cosmic_ray_flux)
                cell.dna.apply_epigenetic_changes(temperature, self.generation)

        # Transcribe/translate (clear old proteins to prevent unbounded growth)
        for cell in self.cells:
            if cell.alive:
                cell.proteins.clear()
                cell.transcribe_and_translate()

        # Compute fitness
        for cell in self.cells:
            cell.compute_fitness()

        # Selection and reproduction
        alive_cells = [c for c in self.cells if c.alive]
        if alive_cells:
            # Top 50% reproduce
            alive_cells.sort(key=lambda c: c.fitness, reverse=True)
            cutoff = max(1, len(alive_cells) // 2)
            new_cells = []
            for cell in alive_cells[:cutoff]:
                daughter = cell.divide()
                if daughter:
                    new_cells.append(daughter)
                    self.total_born += 1

            self.cells.extend(new_cells)

        # Remove dead cells (keep some history)
        dead = [c for c in self.cells if not c.alive]
        self.total_died += len(dead)
        self.cells = [c for c in self.cells if c.alive]

        # Population cap
        if len(self.cells) > 100:
            self.cells.sort(key=lambda c: c.fitness, reverse=True)
            overflow = self.cells[100:]
            self.total_died += len(overflow)
            self.cells = self.cells[:100]

    def average_fitness(self) -> float:
        if not self.cells:
            return 0.0
        return sum(c.fitness for c in self.cells) / len(self.cells)

    def average_gc_content(self) -> float:
        if not self.cells:
            return 0.0
        return sum(c.dna.gc_content for c in self.cells) / len(self.cells)

    def total_mutations(self) -> int:
        return sum(c.dna.mutation_count for c in self.cells)

    def to_compact(self) -> str:
        return (f"Bio[gen={self.generation} pop={len(self.cells)} "
                f"fit={self.average_fitness():.3f} "
                f"gc={self.average_gc_content():.2f} "
                f"born={self.total_born} died={self.total_died} "
                f"mut={self.total_mutations()}]")
