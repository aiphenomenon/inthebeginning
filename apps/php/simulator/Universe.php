<?php

declare(strict_types=1);

require_once __DIR__ . '/Constants.php';
require_once __DIR__ . '/Quantum.php';
require_once __DIR__ . '/Atomic.php';
require_once __DIR__ . '/Chemistry.php';
require_once __DIR__ . '/Biology.php';
require_once __DIR__ . '/Environment.php';

/**
 * Universe orchestrator - runs the full cosmic simulation through 13 epochs.
 */

/**
 * Universe orchestrator - runs the full cosmic simulation through 13 epochs.
 *
 * Coordinates quantum fields, atomic systems, chemical reactions, biological
 * evolution, and environmental changes from the Planck epoch through the
 * present day. Each epoch applies temperature cooling, spatial expansion,
 * and epoch-specific physics.
 */
class Universe
{
    private const EPOCH_NAMES = [
        'Planck',
        'Inflation',
        'Electroweak',
        'Quark-Gluon Plasma',
        'Hadron',
        'Nucleosynthesis',
        'Recombination',
        'Star Formation',
        'Solar System',
        'Earth Formation',
        'Life Emergence',
        'DNA Evolution',
        'Present Day',
    ];

    private const EPOCH_TEMPS = [
        T_PLANCK, 1e27, T_ELECTROWEAK, T_QUARK_HADRON,
        1e10, T_NUCLEOSYNTHESIS, T_RECOMBINATION,
        1e6, 5778.0, T_EARTH_SURFACE, 300.0, 298.0, 295.0,
    ];

    public int $currentEpoch = 0;
    public int $currentTick = 0;
    public float $temperature;
    public float $scaleFactor = 1e-35;
    public int $populationCount = 0;

    private int $ticksPerEpoch;
    private int $cycle = 0;
    private ?QuantumField $quantumField = null;
    private ?AtomicSystem $atomicSystem = null;
    private ?ChemicalSystem $chemicalSystem = null;
    private ?Biosphere $biosphere = null;
    private ?Environment $environment = null;

    public array $stats = [
        'particles_created' => 0,
        'atoms_formed' => 0,
        'molecules_formed' => 0,
        'lifeforms_created' => 0,
    ];

    /**
     * Create a new Universe simulation.
     *
     * @param int $ticksPerEpoch Number of simulation ticks to execute per epoch.
     */
    public function __construct(int $ticksPerEpoch = 100)
    {
        $this->ticksPerEpoch = $ticksPerEpoch;
        $this->temperature = T_PLANCK;
    }

    /**
     * Get the display name of the current epoch.
     *
     * @return string Epoch name (e.g., 'Planck', 'Inflation', 'Present Day').
     */
    public function epochName(): string
    {
        return self::EPOCH_NAMES[$this->currentEpoch] ?? 'Unknown';
    }

    private function coolTemperature(): void
    {
        $target = self::EPOCH_TEMPS[$this->currentEpoch] ?? 295.0;
        $rate = 0.05 + 0.02 * $this->currentEpoch;
        $this->temperature += ($target - $this->temperature) * $rate;
    }

    private function expandSpace(): void
    {
        if ($this->currentEpoch === 1) {
            $this->scaleFactor *= 1e3;
        } elseif ($this->currentEpoch < 7) {
            $this->scaleFactor *= 1.5;
        } else {
            $this->scaleFactor *= 1.01;
        }
    }

    private function stepQuantum(): void
    {
        if ($this->quantumField === null) return;

        // Pair production in early universe
        $energy = $this->temperature * K_B;
        $result = $this->quantumField->pairProduction($energy);
        if ($result !== null) {
            $this->stats['particles_created'] = count($this->quantumField->particles);
        }

        // Quark confinement during hadron epoch
        if ($this->currentEpoch >= 4) {
            $this->quantumField->quarkConfinement();
        }
    }

    private function stepAtomic(): void
    {
        if ($this->atomicSystem === null) return;
        // Atoms form during recombination
        $this->stats['atoms_formed'] = count($this->atomicSystem->atoms);
    }

    private function stepChemistry(): void
    {
        if ($this->chemicalSystem === null) return;
        $this->chemicalSystem->formWater();
        $this->stats['molecules_formed'] = count($this->chemicalSystem->molecules);
    }

    private function stepBiology(): void
    {
        if ($this->biosphere === null) return;
        $this->biosphere->step(
            temperature: $this->temperature,
        );
        $this->populationCount = count($this->biosphere->cells);
        $this->stats['lifeforms_created'] = $this->populationCount;
    }

    /**
     * Run a single epoch of the simulation.
     *
     * Executes ticksPerEpoch ticks, applying temperature cooling, spatial expansion,
     * and the appropriate physics subsystems for this epoch index.
     *
     * @param int $epochIdx The epoch index (0-12).
     * @return array{epoch: string, temperature: float, scale: float, stats: array} Epoch result data.
     */
    public function runEpoch(int $epochIdx): array
    {
        $this->currentEpoch = $epochIdx;

        for ($tick = 1; $tick <= $this->ticksPerEpoch; $tick++) {
            $this->currentTick = $tick;
            $this->coolTemperature();
            $this->expandSpace();

            if ($epochIdx <= 4) {
                $this->stepQuantum();
            }
            if ($epochIdx >= 5 && $epochIdx <= 8) {
                $this->stepAtomic();
            }
            if ($epochIdx >= 8 && $epochIdx <= 11) {
                $this->stepChemistry();
            }
            if ($epochIdx >= 10) {
                $this->stepBiology();
            }
            if ($this->environment !== null) {
                $this->environment->step($this->temperature);
            }
        }

        return [
            'epoch' => $this->epochName(),
            'temperature' => $this->temperature,
            'scale' => $this->scaleFactor,
            'stats' => $this->stats,
        ];
    }

    /**
     * Run the full 13-epoch cosmic simulation from Planck to Present.
     *
     * Initializes all subsystems (quantum field, atomic system, chemical system,
     * biosphere, environment) and runs each epoch in sequence.
     *
     * @param callable|null $onEpochComplete Optional callback invoked after each epoch: fn(int $idx, array $result).
     * @return array<array> Array of 13 epoch result arrays.
     */
    public function run(?callable $onEpochComplete = null): array
    {
        $this->quantumField = new QuantumField();
        $this->atomicSystem = new AtomicSystem();
        $this->chemicalSystem = new ChemicalSystem($this->atomicSystem);
        $this->biosphere = new Biosphere();
        $this->environment = new Environment();

        $results = [];
        for ($epoch = 0; $epoch < 13; $epoch++) {
            $result = $this->runEpoch($epoch);
            $results[] = $result;
            if ($onEpochComplete !== null) {
                $onEpochComplete($epoch, $result);
            }
        }

        return $results;
    }

    /**
     * Reset the universe for a new cycle (Big Bounce).
     *
     * Resets all simulation state -- tick, epoch, temperature, scale factor,
     * population, stats, and subsystems -- back to initial conditions and
     * increments the cycle counter. This allows the simulation to be re-run
     * without constructing a new Universe instance and without memory leaks
     * from accumulated subsystem objects.
     */
    public function bigBounce(): void
    {
        $this->cycle++;
        $this->currentTick = 0;
        $this->currentEpoch = 0;
        $this->temperature = T_PLANCK;
        $this->scaleFactor = 1e-35;
        $this->populationCount = 0;

        // Release subsystem references to free memory
        $this->quantumField = null;
        $this->atomicSystem = null;
        $this->chemicalSystem = null;
        $this->biosphere = null;
        $this->environment = null;

        $this->stats = [
            'particles_created' => 0,
            'atoms_formed' => 0,
            'molecules_formed' => 0,
            'lifeforms_created' => 0,
        ];
    }

    /**
     * Get the current cycle number.
     *
     * The cycle starts at 0 for the first run. Each call to bigBounce()
     * increments the cycle counter by one.
     *
     * @return int Current cycle number (0 = first run).
     */
    public function getCycle(): int
    {
        return $this->cycle;
    }
}
