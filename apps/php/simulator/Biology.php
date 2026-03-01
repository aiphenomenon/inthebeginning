<?php

declare(strict_types=1);

require_once __DIR__ . '/Constants.php';
require_once __DIR__ . '/Chemistry.php';

/**
 * Biology simulation - DNA, RNA, proteins, and epigenetics.
 *
 * Models:
 * - DNA strand assembly from nucleotides
 * - RNA transcription
 * - Protein translation via codon table
 * - Epigenetic modifications (methylation, histone acetylation)
 * - Cell division with mutation
 * - Natural selection pressure
 */

/**
 * An epigenetic modification on a DNA position.
 *
 * Represents methylation, acetylation, or phosphorylation marks that
 * regulate gene expression without altering the DNA sequence itself.
 */
class EpigeneticMark
{
    /**
     * Create a new epigenetic mark.
     *
     * @param int    $position        Base position in the gene sequence.
     * @param string $markType        Type: 'methylation', 'acetylation', or 'phosphorylation'.
     * @param bool   $active          Whether this mark is currently active.
     * @param int    $generationAdded The generation in which this mark was added.
     */
    public function __construct(
        public readonly int $position,
        public readonly string $markType,  // "methylation", "acetylation", "phosphorylation"
        public bool $active = true,
        public readonly int $generationAdded = 0,
    ) {}

    /**
     * Get a compact string representation of this mark (e.g., 'M3+' for active methylation at position 3).
     *
     * @return string Compact mark descriptor.
     */
    public function toCompact(): string
    {
        $m = strtoupper($this->markType[0]);
        $state = $this->active ? '+' : '-';
        return "{$m}{$this->position}{$state}";
    }
}

/**
 * A gene within a DNA strand.
 *
 * Contains a sequence of nucleotide bases, epigenetic marks, and expression level.
 * Supports transcription to mRNA, mutation, methylation, and acetylation.
 */
class Gene
{
    /** @var float Expression level from 0.0 (silenced) to 1.0 (fully expressed). */
    public float $expressionLevel;

    /** @var EpigeneticMark[] */
    public array $epigeneticMarks;

    /**
     * @param string[] $sequence List of bases (A, T, G, C)
     * @param EpigeneticMark[] $epigeneticMarks
     */
    public function __construct(
        public readonly string $name,
        public array $sequence = [],
        public readonly int $startPos = 0,
        public readonly int $endPos = 0,
        float $expressionLevel = 1.0,
        array $epigeneticMarks = [],
        public readonly bool $essential = false,
    ) {
        $this->expressionLevel = $expressionLevel;
        $this->epigeneticMarks = $epigeneticMarks;
    }

    /**
     * Get the length of this gene's sequence in bases.
     *
     * @return int Number of nucleotide bases.
     */
    public function length(): int
    {
        return count($this->sequence);
    }

    /**
     * Check if this gene is silenced by heavy methylation.
     *
     * A gene is silenced when active methylation marks exceed 30% of its length.
     *
     * @return bool True if the gene is epigenetically silenced.
     */
    public function isSilenced(): bool
    {
        $methylCount = 0;
        foreach ($this->epigeneticMarks as $m) {
            if ($m->markType === 'methylation' && $m->active) {
                $methylCount++;
            }
        }
        return $methylCount > $this->length() * 0.3;
    }

    /** Add methylation mark. */
    public function methylate(int $position, int $generation = 0): void
    {
        if ($position >= 0 && $position < $this->length()) {
            $this->epigeneticMarks[] = new EpigeneticMark(
                position: $position,
                markType: 'methylation',
                generationAdded: $generation,
            );
            $this->updateExpression();
        }
    }

    /** Remove methylation mark. */
    public function demethylate(int $position): void
    {
        $this->epigeneticMarks = array_values(array_filter(
            $this->epigeneticMarks,
            fn(EpigeneticMark $m) => !($m->position === $position && $m->markType === 'methylation'),
        ));
        $this->updateExpression();
    }

    /** Add histone acetylation (increases expression). */
    public function acetylate(int $position, int $generation = 0): void
    {
        $this->epigeneticMarks[] = new EpigeneticMark(
            position: $position,
            markType: 'acetylation',
            generationAdded: $generation,
        );
        $this->updateExpression();
    }

    /**
     * Recalculate expression level based on current epigenetic marks.
     *
     * Methylation suppresses expression; acetylation activates it.
     */
    public function updateExpression(): void
    {
        $methyl = 0;
        $acetyl = 0;
        foreach ($this->epigeneticMarks as $m) {
            if ($m->markType === 'methylation' && $m->active) {
                $methyl++;
            }
            if ($m->markType === 'acetylation' && $m->active) {
                $acetyl++;
            }
        }
        $len = max(1, $this->length());
        $suppression = min(1.0, $methyl / $len * 3);
        $activation = min(1.0, $acetyl / $len * 5);
        $this->expressionLevel = max(0.0, min(1.0, 1.0 - $suppression + $activation));
    }

    /** Transcribe DNA to mRNA (T -> U). */
    public function transcribe(): array
    {
        if ($this->isSilenced()) {
            return [];
        }
        $rna = [];
        foreach ($this->sequence as $base) {
            $rna[] = ($base === 'T') ? 'U' : $base;
        }
        return $rna;
    }

    /** Apply random point mutations. Returns mutation count. */
    public function mutate(float $rate = 0.001): int
    {
        $mutations = 0;
        $len = $this->length();
        for ($i = 0; $i < $len; $i++) {
            if (self::rand() < $rate) {
                $old = $this->sequence[$i];
                $choices = array_values(array_filter(NUCLEOTIDE_BASES, fn($b) => $b !== $old));
                $this->sequence[$i] = $choices[array_rand($choices)];
                $mutations++;
            }
        }
        return $mutations;
    }

    private static function rand(): float
    {
        return mt_rand() / (mt_getrandmax() + 1);
    }
}

/**
 * A double-stranded DNA molecule containing genes.
 *
 * Supports complementary strand generation, GC content analysis,
 * random strand generation, semi-conservative replication with mutations,
 * environmental mutation, and epigenetic modification.
 */
class DNAStrand
{
    /** @var array<string, string> Watson-Crick base pairing rules. */
    private const COMPLEMENT = ['A' => 'T', 'T' => 'A', 'G' => 'C', 'C' => 'G'];

    /** @var string[] */
    public array $sequence;

    /** @var Gene[] */
    public array $genes;

    public int $generation;
    public int $mutationCount;

    /**
     * @param string[] $sequence
     * @param Gene[]   $genes
     */
    public function __construct(
        array $sequence = [],
        array $genes = [],
        int $generation = 0,
        int $mutationCount = 0,
    ) {
        $this->sequence = $sequence;
        $this->genes = $genes;
        $this->generation = $generation;
        $this->mutationCount = $mutationCount;
    }

    public function length(): int
    {
        return count($this->sequence);
    }

    /** @return string[] */
    public function complementaryStrand(): array
    {
        return array_map(
            fn(string $b) => self::COMPLEMENT[$b] ?? 'N',
            $this->sequence,
        );
    }

    public function gcContent(): float
    {
        if (empty($this->sequence)) {
            return 0.0;
        }
        $gc = 0;
        foreach ($this->sequence as $b) {
            if ($b === 'G' || $b === 'C') {
                $gc++;
            }
        }
        return $gc / count($this->sequence);
    }

    /** Generate a random DNA strand with genes. */
    public static function randomStrand(int $length, int $numGenes = 3): self
    {
        $sequence = [];
        for ($i = 0; $i < $length; $i++) {
            $sequence[] = NUCLEOTIDE_BASES[array_rand(NUCLEOTIDE_BASES)];
        }
        $strand = new self(sequence: $sequence);

        // Place genes along the strand
        $geneLen = intdiv($length, $numGenes + 1);
        for ($i = 0; $i < $numGenes; $i++) {
            $start = $i * $geneLen + mt_rand(0, max(0, intdiv($geneLen, 4)));
            $end = $start + intdiv($geneLen, 2);
            if ($end > $length) {
                $end = $length;
            }

            $gene = new Gene(
                name: "gene_{$i}",
                sequence: array_slice($sequence, $start, $end - $start),
                startPos: $start,
                endPos: $end,
                essential: ($i === 0), // First gene is essential
            );
            $strand->genes[] = $gene;
        }

        return $strand;
    }

    /** Semi-conservative replication with possible errors. */
    public function replicate(): self
    {
        $newSequence = $this->sequence;
        $newGenes = [];

        foreach ($this->genes as $gene) {
            $newMarks = [];
            foreach ($gene->epigeneticMarks as $m) {
                // Some marks lost in replication
                if (self::rand() < 0.7) {
                    $newMarks[] = new EpigeneticMark(
                        position: $m->position,
                        markType: $m->markType,
                        active: $m->active && self::rand() < 0.8,
                        generationAdded: $m->generationAdded,
                    );
                }
            }

            $newGene = new Gene(
                name: $gene->name,
                sequence: $gene->sequence, // arrays are copied by value in PHP
                startPos: $gene->startPos,
                endPos: $gene->endPos,
                essential: $gene->essential,
                epigeneticMarks: $newMarks,
            );
            $newGene->updateExpression();
            $newGenes[] = $newGene;
        }

        return new self(
            sequence: $newSequence,
            genes: $newGenes,
            generation: $this->generation + 1,
        );
    }

    /** Apply environmental mutations. */
    public function applyMutations(float $uvIntensity = 0.0, float $cosmicRayFlux = 0.0): int
    {
        $totalMutations = 0;
        $rate = UV_MUTATION_RATE * $uvIntensity + COSMIC_RAY_MUTATION_RATE * $cosmicRayFlux;

        foreach ($this->genes as $gene) {
            $totalMutations += $gene->mutate($rate);
        }

        // Also mutate non-genic regions
        $len = $this->length();
        for ($i = 0; $i < $len; $i++) {
            if (self::rand() < $rate) {
                $old = $this->sequence[$i];
                $choices = array_values(array_filter(NUCLEOTIDE_BASES, fn($b) => $b !== $old));
                $this->sequence[$i] = $choices[array_rand($choices)];
                $totalMutations++;
            }
        }

        $this->mutationCount += $totalMutations;
        return $totalMutations;
    }

    /** Environmental epigenetic modifications. */
    public function applyEpigeneticChanges(float $temperature, int $generation = 0): void
    {
        foreach ($this->genes as $gene) {
            // Methylation
            if (self::rand() < METHYLATION_PROBABILITY) {
                $pos = mt_rand(0, max(0, $gene->length() - 1));
                $gene->methylate($pos, $generation);
            }

            // Demethylation
            if (self::rand() < DEMETHYLATION_PROBABILITY) {
                $methyls = array_filter(
                    $gene->epigeneticMarks,
                    fn(EpigeneticMark $m) => $m->markType === 'methylation',
                );
                if (!empty($methyls)) {
                    $methyls = array_values($methyls);
                    $mark = $methyls[array_rand($methyls)];
                    $gene->demethylate($mark->position);
                }
            }

            // Histone acetylation (temperature-dependent)
            $thermalFactor = min(2.0, $temperature / 300.0);
            if (self::rand() < HISTONE_ACETYLATION_PROB * $thermalFactor) {
                $pos = mt_rand(0, max(0, $gene->length() - 1));
                $gene->acetylate($pos, $generation);
            }

            // Histone deacetylation
            if (self::rand() < HISTONE_DEACETYLATION_PROB) {
                $acetyls = array_filter(
                    $gene->epigeneticMarks,
                    fn(EpigeneticMark $m) => $m->markType === 'acetylation',
                );
                if (!empty($acetyls)) {
                    $acetyls = array_values($acetyls);
                    $mark = $acetyls[array_rand($acetyls)];
                    $mark->active = false;
                    $gene->updateExpression();
                }
            }
        }
    }

    private static function rand(): float
    {
        return mt_rand() / (mt_getrandmax() + 1);
    }
}

/** Translate mRNA to protein (amino acid sequence). */
function translateMRNA(array $mrna): array
{
    $protein = [];
    $i = 0;
    $started = false;

    while ($i + 2 < count($mrna)) {
        $codon = $mrna[$i] . $mrna[$i + 1] . $mrna[$i + 2];
        $aa = CODON_TABLE[$codon] ?? null;

        if ($aa === 'Met' && !$started) {
            $started = true;
            $protein[] = $aa;
        } elseif ($started) {
            if ($aa === 'STOP') {
                break;
            } elseif ($aa !== null) {
                $protein[] = $aa;
            }
        }
        $i += 3;
    }

    return $protein;
}

class Protein
{
    /** @var string[] */
    public array $aminoAcids;

    public string $name;
    public string $function; // "enzyme", "structural", "signaling"
    public bool $folded;
    public bool $active;

    /**
     * @param string[] $aminoAcids
     */
    public function __construct(
        array $aminoAcids = [],
        string $name = '',
        string $function = '',
        bool $folded = false,
        bool $active = true,
    ) {
        $this->aminoAcids = $aminoAcids;
        $this->name = $name;
        $this->function = $function;
        $this->folded = $folded;
        $this->active = $active;
    }

    public function length(): int
    {
        return count($this->aminoAcids);
    }

    /** Simplified protein folding - probability based on length. */
    public function fold(): bool
    {
        if ($this->length() < 3) {
            $this->folded = false;
            return false;
        }
        $foldProb = min(0.9, 0.5 + 0.1 * log($this->length() + 1));
        $this->folded = (mt_rand() / (mt_getrandmax() + 1)) < $foldProb;
        return $this->folded;
    }
}

class Cell
{
    private static int $idCounter = 0;

    public readonly int $cellId;
    public DNAStrand $dna;

    /** @var Protein[] */
    public array $proteins;

    public float $fitness;
    public bool $alive;
    public int $generation;
    public float $energy;

    public function __construct(
        ?DNAStrand $dna = null,
        array $proteins = [],
        float $fitness = 1.0,
        bool $alive = true,
        int $generation = 0,
        float $energy = 100.0,
    ) {
        self::$idCounter++;
        $this->cellId = self::$idCounter;
        $this->dna = $dna ?? DNAStrand::randomStrand(100);
        $this->proteins = $proteins;
        $this->fitness = $fitness;
        $this->alive = $alive;
        $this->generation = $generation;
        $this->energy = $energy;
    }

    public static function resetIdCounter(): void
    {
        self::$idCounter = 0;
    }

    /** Central dogma: DNA -> mRNA -> Protein. */
    public function transcribeAndTranslate(): array
    {
        $newProteins = [];
        foreach ($this->dna->genes as $gene) {
            if ($gene->expressionLevel < 0.1) {
                continue; // Silenced
            }

            // Transcribe
            $mrna = $gene->transcribe();
            if (empty($mrna)) {
                continue;
            }

            // Translate
            $aaSeq = translateMRNA($mrna);
            if (empty($aaSeq)) {
                continue;
            }

            // Probability of producing protein scales with expression
            if (self::rand() > $gene->expressionLevel) {
                continue;
            }

            $functions = ['enzyme', 'structural', 'signaling'];
            $protein = new Protein(
                aminoAcids: $aaSeq,
                name: "protein_{$gene->name}",
                function: $functions[array_rand($functions)],
            );
            $protein->fold();
            $newProteins[] = $protein;
            $this->proteins[] = $protein;
        }

        return $newProteins;
    }

    /** Basic metabolism: consume energy, produce waste. */
    public function metabolize(float $environmentEnergy = 10.0): void
    {
        $enzymeCount = 0;
        foreach ($this->proteins as $p) {
            if ($p->function === 'enzyme' && $p->folded && $p->active) {
                $enzymeCount++;
            }
        }
        $efficiency = 0.3 + 0.15 * $enzymeCount;
        $this->energy += $environmentEnergy * $efficiency;
        $this->energy -= 3.0; // Basal metabolic cost
        $this->energy = min($this->energy, 200.0); // Energy cap

        if ($this->energy <= 0) {
            $this->alive = false;
        }
    }

    /** Cell division with DNA replication and possible mutation. */
    public function divide(): ?Cell
    {
        if (!$this->alive || $this->energy < 50.0) {
            return null;
        }

        $newDna = $this->dna->replicate();
        $this->energy /= 2; // Split energy

        $daughter = new Cell(
            dna: $newDna,
            generation: $this->generation + 1,
            energy: $this->energy,
        );

        // Daughter transcribes its own proteins
        $daughter->transcribeAndTranslate();

        return $daughter;
    }

    /** Compute cell fitness based on functional proteins and DNA integrity. */
    public function computeFitness(): float
    {
        if (!$this->alive) {
            $this->fitness = 0.0;
            return 0.0;
        }

        // Essential genes must be active
        $essentialActive = true;
        foreach ($this->dna->genes as $g) {
            if ($g->essential && $g->isSilenced()) {
                $essentialActive = false;
                break;
            }
        }
        if (!$essentialActive) {
            $this->fitness = 0.1;
            return 0.1;
        }

        // Fitness from proteins
        $functionalProteins = 0;
        foreach ($this->proteins as $p) {
            if ($p->folded && $p->active) {
                $functionalProteins++;
            }
        }
        $geneCount = max(1, count($this->dna->genes));
        $proteinFitness = min(1.0, $functionalProteins / $geneCount);

        // Fitness from energy
        $energyFitness = min(1.0, $this->energy / 100.0);

        // GC content near 0.5 is optimal
        $gcFitness = 1.0 - abs($this->dna->gcContent() - 0.5) * 2;

        $this->fitness = $proteinFitness * 0.4 + $energyFitness * 0.3 + $gcFitness * 0.3;
        return $this->fitness;
    }

    private static function rand(): float
    {
        return mt_rand() / (mt_getrandmax() + 1);
    }
}

class Biosphere
{
    /** @var Cell[] */
    public array $cells = [];

    public int $generation = 0;
    public int $totalBorn = 0;
    public int $totalDied = 0;
    public int $dnaLength;

    public function __construct(int $initialCells = 5, int $dnaLength = 90)
    {
        $this->dnaLength = $dnaLength;

        for ($i = 0; $i < $initialCells; $i++) {
            $cell = new Cell(
                dna: DNAStrand::randomStrand($dnaLength, numGenes: 3),
            );
            $cell->transcribeAndTranslate();
            $this->cells[] = $cell;
            $this->totalBorn++;
        }
    }

    /** One generation step. */
    public function step(
        float $environmentEnergy = 10.0,
        float $uvIntensity = 0.0,
        float $cosmicRayFlux = 0.0,
        float $temperature = 300.0,
    ): void {
        $this->generation++;

        // Metabolize
        foreach ($this->cells as $cell) {
            $cell->metabolize($environmentEnergy);
        }

        // Apply mutations
        foreach ($this->cells as $cell) {
            if ($cell->alive) {
                $cell->dna->applyMutations($uvIntensity, $cosmicRayFlux);
                $cell->dna->applyEpigeneticChanges($temperature, $this->generation);
            }
        }

        // Transcribe/translate
        foreach ($this->cells as $cell) {
            if ($cell->alive) {
                $cell->transcribeAndTranslate();
            }
        }

        // Compute fitness
        foreach ($this->cells as $cell) {
            $cell->computeFitness();
        }

        // Selection and reproduction
        $aliveCells = array_filter($this->cells, fn(Cell $c) => $c->alive);
        $aliveCells = array_values($aliveCells);

        if (!empty($aliveCells)) {
            // Sort by fitness descending
            usort($aliveCells, fn(Cell $a, Cell $b) => $b->fitness <=> $a->fitness);
            $cutoff = max(1, intdiv(count($aliveCells), 2));
            $newCells = [];

            for ($i = 0; $i < $cutoff; $i++) {
                $daughter = $aliveCells[$i]->divide();
                if ($daughter !== null) {
                    $newCells[] = $daughter;
                    $this->totalBorn++;
                }
            }

            $this->cells = array_merge($this->cells, $newCells);
        }

        // Remove dead cells
        $deadCount = 0;
        foreach ($this->cells as $c) {
            if (!$c->alive) {
                $deadCount++;
            }
        }
        $this->totalDied += $deadCount;
        $this->cells = array_values(array_filter($this->cells, fn(Cell $c) => $c->alive));

        // Population cap
        if (count($this->cells) > 100) {
            usort($this->cells, fn(Cell $a, Cell $b) => $b->fitness <=> $a->fitness);
            $overflow = array_slice($this->cells, 100);
            $this->totalDied += count($overflow);
            $this->cells = array_slice($this->cells, 0, 100);
        }
    }

    public function averageFitness(): float
    {
        if (empty($this->cells)) {
            return 0.0;
        }
        $sum = 0.0;
        foreach ($this->cells as $c) {
            $sum += $c->fitness;
        }
        return $sum / count($this->cells);
    }

    public function averageGcContent(): float
    {
        if (empty($this->cells)) {
            return 0.0;
        }
        $sum = 0.0;
        foreach ($this->cells as $c) {
            $sum += $c->dna->gcContent();
        }
        return $sum / count($this->cells);
    }

    public function totalMutations(): int
    {
        $total = 0;
        foreach ($this->cells as $c) {
            $total += $c->dna->mutationCount;
        }
        return $total;
    }

    public function toSnapshot(): array
    {
        return [
            'generation'      => $this->generation,
            'population'      => count($this->cells),
            'average_fitness'  => round($this->averageFitness(), 3),
            'average_gc'       => round($this->averageGcContent(), 2),
            'total_born'       => $this->totalBorn,
            'total_died'       => $this->totalDied,
            'total_mutations'  => $this->totalMutations(),
        ];
    }
}
