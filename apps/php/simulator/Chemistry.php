<?php

declare(strict_types=1);

require_once __DIR__ . '/Constants.php';
require_once __DIR__ . '/Atomic.php';

/**
 * Chemistry simulation - molecular assembly and reactions.
 *
 * Models formation of molecules from atoms: water, amino acids,
 * nucleotides, and other biomolecules essential for life.
 * Chemical reactions are driven by energy, catalysis, and concentration.
 */

class Molecule
{
    private static int $idCounter = 0;

    public readonly int $moleculeId;
    public string $formula;
    public bool $isOrganic;

    /**
     * @param Atom[]   $atoms
     * @param string   $name
     * @param float[]  $position
     * @param float    $energy
     * @param string[] $functionalGroups
     */
    public function __construct(
        public array $atoms = [],
        public string $name = '',
        ?string $formula = null,
        ?array $position = null,
        public float $energy = 0.0,
        bool $isOrganic = false,
        public array $functionalGroups = [],
    ) {
        self::$idCounter++;
        $this->moleculeId = self::$idCounter;
        $this->isOrganic = $isOrganic;

        if ($formula !== null) {
            $this->formula = $formula;
        } elseif (!empty($this->atoms)) {
            $this->computeFormula();
        } else {
            $this->formula = '';
        }
    }

    public static function resetIdCounter(): void
    {
        self::$idCounter = 0;
    }

    private function computeFormula(): void
    {
        $counts = [];
        foreach ($this->atoms as $atom) {
            $sym = $atom->symbol();
            $counts[$sym] = ($counts[$sym] ?? 0) + 1;
        }

        // Standard chemistry ordering: C, H, then alphabetical
        $parts = [];
        foreach (['C', 'H'] as $sym) {
            if (isset($counts[$sym])) {
                $n = $counts[$sym];
                $parts[] = $n > 1 ? "{$sym}{$n}" : $sym;
                unset($counts[$sym]);
            }
        }
        ksort($counts);
        foreach ($counts as $sym => $n) {
            $parts[] = $n > 1 ? "{$sym}{$n}" : $sym;
        }
        $this->formula = implode('', $parts);

        // Check if organic
        $hasC = false;
        $hasH = false;
        foreach ($this->atoms as $a) {
            if ($a->atomicNumber === 6) $hasC = true;
            if ($a->atomicNumber === 1) $hasH = true;
        }
        $this->isOrganic = $hasC && $hasH;
    }

    public function molecularWeight(): float
    {
        $total = 0.0;
        foreach ($this->atoms as $a) {
            $total += $a->massNumber;
        }
        return $total;
    }

    public function atomCount(): int
    {
        return count($this->atoms);
    }
}

class ChemicalReaction
{
    /**
     * @param string[] $reactants
     * @param string[] $products
     */
    public function __construct(
        public readonly array $reactants,
        public readonly array $products,
        public readonly float $activationEnergy = 1.0,
        public readonly float $deltaH = 0.0,
        public readonly string $name = '',
    ) {}

    /** Check if reaction can proceed at given temperature. */
    public function canProceed(float $temperature): bool
    {
        $thermalEnergy = K_B * $temperature;
        if ($thermalEnergy <= 0) {
            return false;
        }
        $rate = exp(-$this->activationEnergy / $thermalEnergy);
        return self::rand() < $rate;
    }

    private static function rand(): float
    {
        return mt_rand() / (mt_getrandmax() + 1);
    }
}

class ChemicalSystem
{
    /** @var Molecule[] */
    public array $molecules = [];

    public int $reactionsOccurred = 0;
    public int $waterCount = 0;
    public int $aminoAcidCount = 0;
    public int $nucleotideCount = 0;

    public function __construct(
        public readonly AtomicSystem $atomic,
    ) {}

    /** Form water molecules: 2H + O -> H2O */
    public function formWater(): array
    {
        $waters = [];
        $hydrogens = [];
        $oxygens = [];

        foreach ($this->atomic->atoms as $a) {
            if ($a->atomicNumber === 1 && empty($a->bonds)) {
                $hydrogens[] = $a;
            } elseif ($a->atomicNumber === 8 && count($a->bonds) < 2) {
                $oxygens[] = $a;
            }
        }

        while (count($hydrogens) >= 2 && !empty($oxygens)) {
            $h1 = array_pop($hydrogens);
            $h2 = array_pop($hydrogens);
            $o = array_pop($oxygens);

            $water = new Molecule(
                atoms: [$h1, $h2, $o],
                name: 'water',
            );
            $waters[] = $water;
            $this->molecules[] = $water;
            $this->waterCount++;

            // Form bonds
            $h1->bonds[] = $o->atomId;
            $h2->bonds[] = $o->atomId;
            $o->bonds[] = $h1->atomId;
            $o->bonds[] = $h2->atomId;
        }

        return $waters;
    }

    /** Form methane: C + 4H -> CH4 */
    public function formMethane(): array
    {
        $methanes = [];
        $carbons = [];
        $hydrogens = [];

        foreach ($this->atomic->atoms as $a) {
            if ($a->atomicNumber === 6 && empty($a->bonds)) {
                $carbons[] = $a;
            } elseif ($a->atomicNumber === 1 && empty($a->bonds)) {
                $hydrogens[] = $a;
            }
        }

        while (!empty($carbons) && count($hydrogens) >= 4) {
            $c = array_pop($carbons);
            $hs = [];
            for ($i = 0; $i < 4; $i++) {
                $hs[] = array_pop($hydrogens);
            }

            $methane = new Molecule(
                atoms: array_merge([$c], $hs),
                name: 'methane',
            );
            $methanes[] = $methane;
            $this->molecules[] = $methane;

            foreach ($hs as $h) {
                $c->bonds[] = $h->atomId;
                $h->bonds[] = $c->atomId;
            }
        }

        return $methanes;
    }

    /** Form ammonia: N + 3H -> NH3 */
    public function formAmmonia(): array
    {
        $ammonias = [];
        $nitrogens = [];
        $hydrogens = [];

        foreach ($this->atomic->atoms as $a) {
            if ($a->atomicNumber === 7 && empty($a->bonds)) {
                $nitrogens[] = $a;
            } elseif ($a->atomicNumber === 1 && empty($a->bonds)) {
                $hydrogens[] = $a;
            }
        }

        while (!empty($nitrogens) && count($hydrogens) >= 3) {
            $n = array_pop($nitrogens);
            $hs = [];
            for ($i = 0; $i < 3; $i++) {
                $hs[] = array_pop($hydrogens);
            }

            $ammonia = new Molecule(
                atoms: array_merge([$n], $hs),
                name: 'ammonia',
            );
            $ammonias[] = $ammonia;
            $this->molecules[] = $ammonia;

            foreach ($hs as $h) {
                $n->bonds[] = $h->atomId;
                $h->bonds[] = $n->atomId;
            }
        }

        return $ammonias;
    }

    /** Form an amino acid from available atoms. */
    public function formAminoAcid(string $aaType = 'Gly'): ?Molecule
    {
        $carbons = [];
        $hydrogens = [];
        $oxygens = [];
        $nitrogens = [];

        foreach ($this->atomic->atoms as $a) {
            if ($a->atomicNumber === 6 && empty($a->bonds)) {
                $carbons[] = $a;
            } elseif ($a->atomicNumber === 1 && empty($a->bonds)) {
                $hydrogens[] = $a;
            } elseif ($a->atomicNumber === 8 && count($a->bonds) < 2) {
                $oxygens[] = $a;
            } elseif ($a->atomicNumber === 7 && empty($a->bonds)) {
                $nitrogens[] = $a;
            }
        }

        if (count($carbons) < 2 || count($hydrogens) < 5
            || count($oxygens) < 2 || count($nitrogens) < 1) {
            return null;
        }

        $atoms = [];
        for ($i = 0; $i < 2; $i++) $atoms[] = array_pop($carbons);
        for ($i = 0; $i < 5; $i++) $atoms[] = array_pop($hydrogens);
        for ($i = 0; $i < 2; $i++) $atoms[] = array_pop($oxygens);
        $atoms[] = array_pop($nitrogens);

        $aa = new Molecule(
            atoms: $atoms,
            name: $aaType,
            isOrganic: true,
            functionalGroups: ['amino', 'carboxyl'],
        );
        $this->molecules[] = $aa;
        $this->aminoAcidCount++;

        // Form internal bonds
        $first = $atoms[0];
        for ($i = 1; $i < count($atoms); $i++) {
            $first->bonds[] = $atoms[$i]->atomId;
            $atoms[$i]->bonds[] = $first->atomId;
        }

        return $aa;
    }

    /** Form a nucleotide (sugar + phosphate + base). */
    public function formNucleotide(string $base = 'A'): ?Molecule
    {
        $carbons = [];
        $hydrogens = [];
        $oxygens = [];
        $nitrogens = [];

        foreach ($this->atomic->atoms as $a) {
            if ($a->atomicNumber === 6 && empty($a->bonds)) {
                $carbons[] = $a;
            } elseif ($a->atomicNumber === 1 && empty($a->bonds)) {
                $hydrogens[] = $a;
            } elseif ($a->atomicNumber === 8 && count($a->bonds) < 2) {
                $oxygens[] = $a;
            } elseif ($a->atomicNumber === 7 && empty($a->bonds)) {
                $nitrogens[] = $a;
            }
        }

        // Simplified requirements
        if (count($carbons) < 5 || count($hydrogens) < 8
            || count($oxygens) < 4 || count($nitrogens) < 2) {
            return null;
        }

        $atoms = [];
        for ($i = 0; $i < 5; $i++) $atoms[] = array_pop($carbons);
        for ($i = 0; $i < 8; $i++) $atoms[] = array_pop($hydrogens);
        for ($i = 0; $i < 4; $i++) $atoms[] = array_pop($oxygens);
        for ($i = 0; $i < 2; $i++) $atoms[] = array_pop($nitrogens);

        $nuc = new Molecule(
            atoms: $atoms,
            name: "nucleotide-{$base}",
            isOrganic: true,
            functionalGroups: ['sugar', 'phosphate', 'base'],
        );
        $this->molecules[] = $nuc;
        $this->nucleotideCount++;

        $first = $atoms[0];
        for ($i = 1; $i < count($atoms); $i++) {
            $first->bonds[] = $atoms[$i]->atomId;
            $atoms[$i]->bonds[] = $first->atomId;
        }

        return $nuc;
    }

    /** Run catalyzed reactions to form complex molecules. */
    public function catalyzedReaction(float $temperature, bool $catalystPresent = false): int
    {
        $formed = 0;
        $eaFactor = $catalystPresent ? 0.3 : 1.0;
        $thermal = K_B * $temperature;

        // Try to form amino acids
        if ($thermal > 0 && count($this->atomic->atoms) > 10) {
            $aaProb = exp(-5.0 * $eaFactor / ($thermal + 1e-20));
            if (self::rand() < $aaProb) {
                $aaType = AMINO_ACIDS[array_rand(AMINO_ACIDS)];
                if ($this->formAminoAcid($aaType) !== null) {
                    $formed++;
                    $this->reactionsOccurred++;
                }
            }
        }

        // Try to form nucleotides
        if ($thermal > 0 && count($this->atomic->atoms) > 19) {
            $nucProb = exp(-8.0 * $eaFactor / ($thermal + 1e-20));
            if (self::rand() < $nucProb) {
                $bases = ['A', 'T', 'G', 'C'];
                $base = $bases[array_rand($bases)];
                if ($this->formNucleotide($base) !== null) {
                    $formed++;
                    $this->reactionsOccurred++;
                }
            }
        }

        return $formed;
    }

    /** Count molecules by type. */
    public function moleculeCensus(): array
    {
        $counts = [];
        foreach ($this->molecules as $m) {
            $key = $m->name ?: $m->formula;
            $counts[$key] = ($counts[$key] ?? 0) + 1;
        }
        return $counts;
    }

    public function toSnapshot(): array
    {
        return [
            'molecule_count'     => count($this->molecules),
            'molecules_by_type'  => $this->moleculeCensus(),
            'water_count'        => $this->waterCount,
            'amino_acid_count'   => $this->aminoAcidCount,
            'nucleotide_count'   => $this->nucleotideCount,
            'reactions_occurred' => $this->reactionsOccurred,
        ];
    }

    private static function rand(): float
    {
        return mt_rand() / (mt_getrandmax() + 1);
    }
}
