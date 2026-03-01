<?php

declare(strict_types=1);

require_once __DIR__ . '/Constants.php';
require_once __DIR__ . '/Quantum.php';

/**
 * Atomic physics simulation.
 *
 * Models atoms with electron shells, ionization, chemical bonding potential,
 * and the periodic table. Atoms emerge from the quantum/nuclear level
 * when temperature drops below recombination threshold.
 */

/**
 * An electron shell (energy level) within an atom.
 *
 * Models the capacity and occupancy of a principal quantum shell,
 * supporting addition and removal of electrons.
 */
class ElectronShell
{
    /** @var int Current number of electrons in this shell. */
    public int $electrons;

    /**
     * Create an electron shell.
     *
     * @param int $n            Principal quantum number (1, 2, 3, ...).
     * @param int $maxElectrons Maximum electrons this shell can hold.
     * @param int $electrons    Initial electron count.
     */
    public function __construct(
        public readonly int $n,
        public readonly int $maxElectrons,
        int $electrons = 0,
    ) {
        $this->electrons = $electrons;
    }

    /**
     * Check if this shell is fully occupied.
     *
     * @return bool True if electron count equals or exceeds max capacity.
     */
    public function isFull(): bool
    {
        return $this->electrons >= $this->maxElectrons;
    }

    /**
     * Check if this shell has no electrons.
     *
     * @return bool True if electron count is zero.
     */
    public function isEmpty(): bool
    {
        return $this->electrons === 0;
    }

    /**
     * Add one electron to this shell if not full.
     *
     * @return bool True if the electron was added, false if shell is full.
     */
    public function addElectron(): bool
    {
        if (!$this->isFull()) {
            $this->electrons++;
            return true;
        }
        return false;
    }

    /**
     * Remove one electron from this shell if not empty.
     *
     * @return bool True if an electron was removed, false if shell is empty.
     */
    public function removeElectron(): bool
    {
        if (!$this->isEmpty()) {
            $this->electrons--;
            return true;
        }
        return false;
    }
}

/**
 * An atom with protons, neutrons, and electron shells.
 *
 * Models atomic structure including electron configuration, ionization,
 * electronegativity, chemical bonding potential, and inter-atom distance.
 * Atoms are the building blocks created during recombination and nucleosynthesis.
 */
class Atom
{
    /** @var int Auto-incrementing counter for unique atom IDs. */
    private static int $idCounter = 0;

    /** @var int Unique identifier for this atom instance. */
    public readonly int $atomId;
    public int $massNumber;
    public int $electronCount;

    /** @var float[] */
    public array $position;

    /** @var float[] */
    public array $velocity;

    /** @var ElectronShell[] */
    public array $shells = [];

    /** @var int[] atom IDs of bonded atoms */
    public array $bonds = [];

    public float $ionizationEnergy = 0.0;

    /**
     * Create a new atom.
     *
     * @param int        $atomicNumber Number of protons (determines element).
     * @param int        $massNumber   Protons + neutrons (0 = auto-calculated).
     * @param int        $electronCount Number of electrons (0 = neutral atom).
     * @param float[]|null $position   3D position vector [x, y, z].
     * @param float[]|null $velocity   3D velocity vector [vx, vy, vz].
     */
    public function __construct(
        public readonly int $atomicNumber,
        int $massNumber = 0,
        int $electronCount = 0,
        ?array $position = null,
        ?array $velocity = null,
    ) {
        self::$idCounter++;
        $this->atomId = self::$idCounter;
        $this->position = $position ?? [0.0, 0.0, 0.0];
        $this->velocity = $velocity ?? [0.0, 0.0, 0.0];

        $this->massNumber = $massNumber ?: ($atomicNumber === 1 ? 1 : $atomicNumber * 2);
        $this->electronCount = $electronCount ?: $atomicNumber; // Neutral atom

        $this->buildShells();
        $this->computeIonizationEnergy();
    }

    /**
     * Reset the atom ID counter (useful for testing).
     */
    public static function resetIdCounter(): void
    {
        self::$idCounter = 0;
    }

    /**
     * Build electron shell configuration based on current electron count.
     */
    private function buildShells(): void
    {
        $this->shells = [];
        $remaining = $this->electronCount;
        foreach (ELECTRON_SHELLS as $i => $maxE) {
            if ($remaining <= 0) {
                break;
            }
            $electrons = min($remaining, $maxE);
            $this->shells[] = new ElectronShell(
                n: $i + 1,
                maxElectrons: $maxE,
                electrons: $electrons,
            );
            $remaining -= $electrons;
        }
    }

    private function computeIonizationEnergy(): void
    {
        if (empty($this->shells) || end($this->shells)->isEmpty()) {
            $this->ionizationEnergy = 0.0;
            return;
        }
        $lastShell = end($this->shells);
        $n = $lastShell->n;
        $innerElectrons = 0;
        foreach ($this->shells as $s) {
            if ($s !== $lastShell) {
                $innerElectrons += $s->electrons;
            }
        }
        $zEff = $this->atomicNumber - $innerElectrons;
        // Hydrogen-like approximation: E = 13.6 * Z_eff^2 / n^2
        $this->ionizationEnergy = 13.6 * $zEff ** 2 / $n ** 2;
    }

    /**
     * Get the chemical symbol for this element (e.g., 'H', 'He', 'C').
     *
     * @return string The element symbol, or 'E{Z}' for unknown elements.
     */
    public function symbol(): string
    {
        $elem = ELEMENTS[$this->atomicNumber] ?? null;
        return $elem ? $elem[0] : "E{$this->atomicNumber}";
    }

    /**
     * Get the full element name (e.g., 'Hydrogen', 'Carbon').
     *
     * @return string The element name, or 'Element-{Z}' for unknown elements.
     */
    public function name(): string
    {
        $elem = ELEMENTS[$this->atomicNumber] ?? null;
        return $elem ? $elem[1] : "Element-{$this->atomicNumber}";
    }

    /**
     * Get the Pauling electronegativity of this element.
     *
     * @return float Electronegativity value (0.0 for noble gases, ~4.0 for fluorine).
     */
    public function electronegativity(): float
    {
        $elem = ELEMENTS[$this->atomicNumber] ?? null;
        return $elem ? $elem[4] : 1.0;
    }

    /**
     * Get the net ionic charge (protons minus electrons).
     *
     * @return int Positive for cations, negative for anions, 0 for neutral.
     */
    public function charge(): int
    {
        return $this->atomicNumber - $this->electronCount;
    }

    /**
     * Get the number of electrons in the outermost shell.
     *
     * @return int Valence electron count.
     */
    public function valenceElectrons(): int
    {
        if (empty($this->shells)) {
            return 0;
        }
        return end($this->shells)->electrons;
    }

    /**
     * Get the number of additional electrons needed to fill the outermost shell.
     *
     * @return int Number of electrons needed (0 if shell is full).
     */
    public function needsElectrons(): int
    {
        if (empty($this->shells)) {
            return 0;
        }
        $shell = end($this->shells);
        return $shell->maxElectrons - $shell->electrons;
    }

    /**
     * Check if this atom has a full outer electron shell (noble gas configuration).
     *
     * @return bool True if the outermost shell is fully occupied.
     */
    public function isNobleGas(): bool
    {
        if (empty($this->shells)) {
            return false;
        }
        return end($this->shells)->isFull();
    }

    /**
     * Check if this atom is an ion (non-zero charge).
     *
     * @return bool True if the atom has gained or lost electrons.
     */
    public function isIon(): bool
    {
        return $this->charge() !== 0;
    }

    /**
     * Remove one electron from the atom (ionization).
     *
     * @return bool True if successful, false if no electrons remain.
     */
    public function ionize(): bool
    {
        if ($this->electronCount > 0) {
            $this->electronCount--;
            $this->buildShells();
            $this->computeIonizationEnergy();
            return true;
        }
        return false;
    }

    /**
     * Add one electron to the atom (electron capture).
     *
     * @return bool Always returns true.
     */
    public function captureElectron(): bool
    {
        $this->electronCount++;
        $this->buildShells();
        $this->computeIonizationEnergy();
        return true;
    }

    /**
     * Check if this atom can form a chemical bond with another atom.
     *
     * Noble gases and atoms with 4 existing bonds cannot form new bonds.
     *
     * @param Atom $other The other atom to potentially bond with.
     * @return bool True if bonding is possible.
     */
    public function canBondWith(Atom $other): bool
    {
        if ($this->isNobleGas() || $other->isNobleGas()) {
            return false;
        }
        if (count($this->bonds) >= 4 || count($other->bonds) >= 4) {
            return false;
        }
        return true;
    }

    /**
     * Determine the bond type based on electronegativity difference.
     *
     * @param Atom $other The other atom in the bond.
     * @return string 'ionic', 'polar_covalent', or 'covalent'.
     */
    public function bondType(Atom $other): string
    {
        $diff = abs($this->electronegativity() - $other->electronegativity());
        if ($diff > 1.7) {
            return 'ionic';
        } elseif ($diff > 0.4) {
            return 'polar_covalent';
        }
        return 'covalent';
    }

    /**
     * Calculate the bond energy for a bond with another atom.
     *
     * @param Atom $other The other atom in the bond.
     * @return float Bond energy in eV equivalent.
     */
    public function bondEnergy(Atom $other): float
    {
        return match ($this->bondType($other)) {
            'ionic'          => BOND_ENERGY_IONIC,
            'polar_covalent' => (BOND_ENERGY_COVALENT + BOND_ENERGY_IONIC) / 2,
            default          => BOND_ENERGY_COVALENT,
        };
    }

    /**
     * Calculate the Euclidean distance to another atom.
     *
     * @param Atom $other The other atom.
     * @return float Distance in simulation units.
     */
    public function distanceTo(Atom $other): float
    {
        $sum = 0.0;
        for ($i = 0; $i < 3; $i++) {
            $sum += ($this->position[$i] - $other->position[$i]) ** 2;
        }
        return sqrt($sum);
    }
}

class AtomicSystem
{
    /** @var Atom[] */
    public array $atoms = [];

    public float $temperature;

    /** @var Particle[] */
    public array $freeElectrons = [];

    public int $bondsFormed = 0;
    public int $bondsBroken = 0;

    public function __construct(float $temperature = T_RECOMBINATION)
    {
        $this->temperature = $temperature;
    }

    /** Capture free electrons into ions when T < T_recombination. */
    public function recombination(QuantumField $field): array
    {
        if ($this->temperature > T_RECOMBINATION) {
            return [];
        }

        $newAtoms = [];
        $protons = [];
        $electrons = [];

        foreach ($field->particles as $p) {
            if ($p->particleType === ParticleType::Proton) {
                $protons[] = $p;
            } elseif ($p->particleType === ParticleType::Electron) {
                $electrons[] = $p;
            }
        }

        foreach ($protons as $proton) {
            if (empty($electrons)) {
                break;
            }
            $electron = array_pop($electrons);
            $atom = new Atom(
                atomicNumber: 1,
                massNumber: 1,
                position: $proton->position,
                velocity: $proton->momentum,
            );
            $newAtoms[] = $atom;
            $this->atoms[] = $atom;

            // Remove from quantum field
            $idx = array_search($proton, $field->particles, true);
            if ($idx !== false) {
                array_splice($field->particles, $idx, 1);
            }
            $idx = array_search($electron, $field->particles, true);
            if ($idx !== false) {
                array_splice($field->particles, $idx, 1);
            }
        }

        return $newAtoms;
    }

    /** Form heavier elements through nuclear fusion. */
    public function nucleosynthesis(int $protons = 0, int $neutrons = 0): array
    {
        $newAtoms = [];

        // Helium-4: 2 protons + 2 neutrons
        while ($protons >= 2 && $neutrons >= 2) {
            $he = new Atom(
                atomicNumber: 2,
                massNumber: 4,
                position: [self::gauss(0, 10), self::gauss(0, 10), self::gauss(0, 10)],
            );
            $newAtoms[] = $he;
            $this->atoms[] = $he;
            $protons -= 2;
            $neutrons -= 2;
        }

        // Remaining protons become hydrogen
        for ($i = 0; $i < $protons; $i++) {
            $h = new Atom(
                atomicNumber: 1,
                massNumber: 1,
                position: [self::gauss(0, 10), self::gauss(0, 10), self::gauss(0, 10)],
            );
            $newAtoms[] = $h;
            $this->atoms[] = $h;
        }

        return $newAtoms;
    }

    /** Form heavier elements in stellar cores. */
    public function stellarNucleosynthesis(float $temperature): array
    {
        $newAtoms = [];

        if ($temperature < 1e3) {
            return $newAtoms;
        }

        $heliums = [];
        foreach ($this->atoms as $a) {
            if ($a->atomicNumber === 2) {
                $heliums[] = $a;
            }
        }

        // Triple-alpha process: 3 He -> C
        while (count($heliums) >= 3 && self::rand() < 0.01) {
            for ($i = 0; $i < 3; $i++) {
                $he = array_pop($heliums);
                $idx = array_search($he, $this->atoms, true);
                if ($idx !== false) {
                    array_splice($this->atoms, $idx, 1);
                }
            }

            $carbon = new Atom(
                atomicNumber: 6,
                massNumber: 12,
                position: [self::gauss(0, 5), self::gauss(0, 5), self::gauss(0, 5)],
            );
            $newAtoms[] = $carbon;
            $this->atoms[] = $carbon;
        }

        // C + He -> O
        $carbons = [];
        $heliums = [];
        foreach ($this->atoms as $a) {
            if ($a->atomicNumber === 6) {
                $carbons[] = $a;
            } elseif ($a->atomicNumber === 2) {
                $heliums[] = $a;
            }
        }
        while (!empty($carbons) && !empty($heliums) && self::rand() < 0.02) {
            $c = array_pop($carbons);
            $he = array_pop($heliums);

            $idx = array_search($c, $this->atoms, true);
            if ($idx !== false) {
                array_splice($this->atoms, $idx, 1);
            }
            $idx = array_search($he, $this->atoms, true);
            if ($idx !== false) {
                array_splice($this->atoms, $idx, 1);
            }

            $oxygen = new Atom(
                atomicNumber: 8,
                massNumber: 16,
                position: $c->position,
            );
            $newAtoms[] = $oxygen;
            $this->atoms[] = $oxygen;
        }

        // O + He -> N (simplified chain)
        $oxygens = [];
        $heliums = [];
        foreach ($this->atoms as $a) {
            if ($a->atomicNumber === 8) {
                $oxygens[] = $a;
            } elseif ($a->atomicNumber === 2) {
                $heliums[] = $a;
            }
        }
        if (!empty($oxygens) && !empty($heliums) && self::rand() < 0.005) {
            $o = $oxygens[0];
            $he = $heliums[0];

            $idx = array_search($o, $this->atoms, true);
            if ($idx !== false) {
                array_splice($this->atoms, $idx, 1);
            }
            $idx = array_search($he, $this->atoms, true);
            if ($idx !== false) {
                array_splice($this->atoms, $idx, 1);
            }

            $nitrogen = new Atom(
                atomicNumber: 7,
                massNumber: 14,
                position: $o->position,
            );
            $newAtoms[] = $nitrogen;
            $this->atoms[] = $nitrogen;
        }

        return $newAtoms;
    }

    /** Try to form a chemical bond between two atoms. */
    public function attemptBond(Atom $a1, Atom $a2): bool
    {
        if (!$a1->canBondWith($a2)) {
            return false;
        }

        $dist = $a1->distanceTo($a2);
        $bondDist = 2.0;

        if ($dist > $bondDist * 3) {
            return false;
        }

        $energyBarrier = $a1->bondEnergy($a2);
        $thermalEnergy = K_B * $this->temperature;
        if ($thermalEnergy > 0) {
            $prob = exp(-$energyBarrier / $thermalEnergy);
        } else {
            $prob = $dist < $bondDist ? 1.0 : 0.0;
        }

        if (self::rand() < $prob) {
            $a1->bonds[] = $a2->atomId;
            $a2->bonds[] = $a1->atomId;
            $this->bondsFormed++;
            return true;
        }
        return false;
    }

    /** Break a bond due to thermal energy. */
    public function breakBond(Atom $a1, Atom $a2): bool
    {
        if (!in_array($a2->atomId, $a1->bonds)) {
            return false;
        }

        $energyBarrier = $a1->bondEnergy($a2);
        $thermalEnergy = K_B * $this->temperature;

        if ($thermalEnergy > $energyBarrier * 0.5) {
            $prob = exp(-$energyBarrier / ($thermalEnergy + 1e-20));
            if (self::rand() < $prob) {
                $a1->bonds = array_values(array_diff($a1->bonds, [$a2->atomId]));
                $a2->bonds = array_values(array_diff($a2->bonds, [$a1->atomId]));
                $this->bondsBroken++;
                return true;
            }
        }
        return false;
    }

    /** Cool the atomic system. */
    public function cool(float $factor = 0.999): void
    {
        $this->temperature *= $factor;
    }

    /** Count atoms by element. */
    public function elementCounts(): array
    {
        $counts = [];
        foreach ($this->atoms as $a) {
            $sym = $a->symbol();
            $counts[$sym] = ($counts[$sym] ?? 0) + 1;
        }
        return $counts;
    }

    public function toSnapshot(): array
    {
        return [
            'temperature'   => $this->temperature,
            'atom_count'    => count($this->atoms),
            'elements'      => $this->elementCounts(),
            'bonds_formed'  => $this->bondsFormed,
            'bonds_broken'  => $this->bondsBroken,
        ];
    }

    private static function rand(): float
    {
        return mt_rand() / (mt_getrandmax() + 1);
    }

    private static function gauss(float $mean, float $stddev): float
    {
        $u1 = max(1e-10, mt_rand() / (mt_getrandmax() + 1));
        $u2 = mt_rand() / (mt_getrandmax() + 1);
        return $mean + $stddev * sqrt(-2 * log($u1)) * cos(2 * M_PI * $u2);
    }
}
