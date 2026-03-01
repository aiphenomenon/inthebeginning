<?php

declare(strict_types=1);

require_once __DIR__ . '/Constants.php';

/**
 * Quantum and subatomic physics simulation.
 *
 * Models quantum fields, particles, wave functions, superposition,
 * entanglement (simplified), and the quark-hadron transition.
 */

/**
 * Enumeration of fundamental and composite particle types.
 *
 * Includes quarks (up, down), leptons (electron, positron, neutrino),
 * gauge bosons (photon, gluon, W, Z), and composite hadrons (proton, neutron).
 * Each case provides its mass and electric charge in simulation units.
 */
enum ParticleType: string
{
    // Quarks
    case Up = 'up';
    case Down = 'down';
    // Leptons
    case Electron = 'electron';
    case Positron = 'positron';
    case Neutrino = 'neutrino';
    // Gauge bosons
    case Photon = 'photon';
    case Gluon = 'gluon';
    case WBoson = 'W';
    case ZBoson = 'Z';
    // Composite
    case Proton = 'proton';
    case Neutron = 'neutron';

    /**
     * Get the rest mass of this particle type in simulation units.
     *
     * @return float The particle mass (0.0 for massless particles like photons).
     */
    public function mass(): float
    {
        return match ($this) {
            self::Up       => M_UP_QUARK,
            self::Down     => M_DOWN_QUARK,
            self::Electron => M_ELECTRON,
            self::Positron => M_ELECTRON,
            self::Neutrino => M_NEUTRINO,
            self::Photon   => M_PHOTON,
            self::Gluon    => M_PHOTON,
            self::Proton   => M_PROTON,
            self::Neutron  => M_NEUTRON,
            self::WBoson   => M_W_BOSON,
            self::ZBoson   => M_Z_BOSON,
        };
    }

    /**
     * Get the electric charge of this particle type in units of the elementary charge.
     *
     * @return float The charge (-1.0 for electron, +1.0 for proton, etc.).
     */
    public function charge(): float
    {
        return match ($this) {
            self::Up       => 2.0 / 3.0,
            self::Down     => -1.0 / 3.0,
            self::Electron => -1.0,
            self::Positron => 1.0,
            self::Neutrino => 0.0,
            self::Photon   => 0.0,
            self::Gluon    => 0.0,
            self::Proton   => 1.0,
            self::Neutron  => 0.0,
            self::WBoson   => 1.0,
            self::ZBoson   => 0.0,
        };
    }
}

/**
 * Spin quantum number for fermions.
 *
 * Represents the intrinsic angular momentum projection: +1/2 (Up) or -1/2 (Down).
 */
enum Spin: string
{
    case Up = 'up';
    case Down = 'down';

    /**
     * Get the numerical spin value.
     *
     * @return float +0.5 for Up, -0.5 for Down.
     */
    public function value(): float
    {
        return match ($this) {
            self::Up   => +0.5,
            self::Down => -0.5,
        };
    }
}

/**
 * Color charge for quarks and gluons in the strong interaction.
 *
 * Quarks carry one of three colors (red, green, blue); antiquarks carry anti-colors.
 * Color-neutral (white) combinations form observable hadrons.
 */
enum Color: string
{
    case Red = 'r';
    case Green = 'g';
    case Blue = 'b';
    case AntiRed = 'ar';
    case AntiGreen = 'ag';
    case AntiBlue = 'ab';
}

/**
 * Quantum mechanical wave function representation.
 *
 * Models the probability amplitude, phase, and coherence of a quantum state.
 * Supports time evolution, measurement collapse, and superposition of states.
 */
class WaveFunction
{
    /**
     * Create a new wave function.
     *
     * @param float $amplitude Probability amplitude (0.0 to 1.0).
     * @param float $phase     Phase angle in radians.
     * @param bool  $coherent  Whether the state maintains quantum coherence.
     */
    public function __construct(
        public float $amplitude = 1.0,
        public float $phase = 0.0,
        public bool $coherent = true,
    ) {}

    /** Born rule: |psi|^2 */
    public function probability(): float
    {
        return $this->amplitude ** 2;
    }

    /** Time evolution: phase rotation by E*dt/hbar. */
    public function evolve(float $dt, float $energy): void
    {
        if ($this->coherent) {
            $this->phase += $energy * $dt / HBAR;
            $this->phase = fmod($this->phase, 2 * M_PI);
        }
    }

    /** Measurement: collapse to eigenstate. Returns true if 'detected'. */
    public function collapse(): bool
    {
        $result = (mt_rand() / mt_getrandmax()) < $this->probability();
        $this->amplitude = $result ? 1.0 : 0.0;
        $this->coherent = false;
        return $result;
    }

    /** Superposition of two states. */
    public function superpose(WaveFunction $other): WaveFunction
    {
        $phaseDiff = $this->phase - $other->phase;
        $combinedAmp = sqrt(
            $this->amplitude ** 2 + $other->amplitude ** 2
            + 2 * $this->amplitude * $other->amplitude * cos($phaseDiff)
        );
        $combinedPhase = ($this->phase + $other->phase) / 2;
        return new WaveFunction(
            amplitude: min($combinedAmp, 1.0),
            phase: $combinedPhase,
            coherent: true,
        );
    }

    /**
     * Serialize the wave function to an associative array.
     *
     * @return array{amplitude: float, phase: float, coherent: bool}
     */
    public function toArray(): array
    {
        return [
            'amplitude' => round($this->amplitude, 3),
            'phase'     => round($this->phase, 2),
            'coherent'  => $this->coherent,
        ];
    }
}

/**
 * A quantum particle with position, momentum, spin, color charge, and wave function.
 *
 * Represents fundamental particles (quarks, leptons, bosons) and composite hadrons.
 * Each particle has a unique ID, relativistic energy, and de Broglie wavelength.
 */
class Particle
{
    /** @var int Auto-incrementing counter for unique particle IDs. */
    private static int $idCounter = 0;

    /** @var int Unique identifier for this particle instance. */
    public readonly int $particleId;

    /** @var float[] */
    public array $position;

    /** @var float[] */
    public array $momentum;

    public Spin $spin;
    public ?Color $color;
    public WaveFunction $waveFn;
    public ?int $entangledWith;

    /**
     * Create a new particle.
     *
     * @param ParticleType      $particleType  The type of particle (electron, proton, etc.).
     * @param float[]|null      $position      3D position vector [x, y, z] in simulation units.
     * @param float[]|null      $momentum      3D momentum vector [px, py, pz].
     * @param Spin|null         $spin          Spin state (Up or Down); defaults to Up.
     * @param Color|null        $color         Color charge for quarks; null for non-colored particles.
     * @param WaveFunction|null $waveFn        Wave function; defaults to unit amplitude coherent state.
     * @param int|null          $entangledWith Particle ID of the entangled partner, or null.
     */
    public function __construct(
        public readonly ParticleType $particleType,
        ?array $position = null,
        ?array $momentum = null,
        ?Spin $spin = null,
        ?Color $color = null,
        ?WaveFunction $waveFn = null,
        ?int $entangledWith = null,
    ) {
        self::$idCounter++;
        $this->particleId = self::$idCounter;
        $this->position = $position ?? [0.0, 0.0, 0.0];
        $this->momentum = $momentum ?? [0.0, 0.0, 0.0];
        $this->spin = $spin ?? Spin::Up;
        $this->color = $color;
        $this->waveFn = $waveFn ?? new WaveFunction();
        $this->entangledWith = $entangledWith;
    }

    /**
     * Reset the particle ID counter (useful for testing).
     */
    public static function resetIdCounter(): void
    {
        self::$idCounter = 0;
    }

    /**
     * Get the rest mass of this particle.
     *
     * @return float The mass in simulation units.
     */
    public function mass(): float
    {
        return $this->particleType->mass();
    }

    /**
     * Get the electric charge of this particle.
     *
     * @return float The charge in units of the elementary charge.
     */
    public function charge(): float
    {
        return $this->particleType->charge();
    }

    /** E = sqrt(p^2*c^2 + m^2*c^4) */
    public function energy(): float
    {
        $p2 = 0.0;
        foreach ($this->momentum as $p) {
            $p2 += $p ** 2;
        }
        return sqrt($p2 * C ** 2 + ($this->mass() * C ** 2) ** 2);
    }

    /** de Broglie wavelength: lambda = h / p */
    public function wavelength(): float
    {
        $p2 = 0.0;
        foreach ($this->momentum as $p) {
            $p2 += $p ** 2;
        }
        $p = sqrt($p2);
        if ($p < 1e-20) {
            return INF;
        }
        return 2 * M_PI * HBAR / $p;
    }
}

/**
 * An entangled pair of particles sharing a Bell state.
 *
 * Measuring one particle's spin instantly determines the other's spin,
 * modeling the EPR correlation in a simplified form.
 */
class EntangledPair
{
    /**
     * Create an entangled pair.
     *
     * @param Particle $particleA First particle in the pair.
     * @param Particle $particleB Second particle in the pair.
     * @param string   $bellState The Bell state label (e.g., 'phi+').
     */
    public function __construct(
        public readonly Particle $particleA,
        public readonly Particle $particleB,
        public readonly string $bellState = 'phi+',
    ) {}

    /** Measure particle A, instantly determining B. */
    public function measureA(): Spin
    {
        if (mt_rand(0, 1) === 0) {
            $this->particleA->spin = Spin::Up;
            $this->particleB->spin = Spin::Down;
        } else {
            $this->particleA->spin = Spin::Down;
            $this->particleB->spin = Spin::Up;
        }
        $this->particleA->waveFn->coherent = false;
        $this->particleB->waveFn->coherent = false;
        return $this->particleA->spin;
    }
}

/**
 * The quantum field: a thermal bath of particles and vacuum energy.
 *
 * Manages particle creation (pair production), annihilation, quark confinement
 * into hadrons, vacuum fluctuations, decoherence, cooling, and time evolution.
 */
class QuantumField
{
    /** @var float Current temperature of the field in simulation Kelvin. */
    public float $temperature;

    /** @var Particle[] */
    public array $particles = [];

    /** @var EntangledPair[] */
    public array $entangledPairs = [];

    public float $vacuumEnergy = 0.0;
    public int $totalCreated = 0;
    public int $totalAnnihilated = 0;

    /**
     * Create a new quantum field at the given temperature.
     *
     * @param float $temperature Initial field temperature (defaults to Planck temperature).
     */
    public function __construct(float $temperature = T_PLANCK)
    {
        $this->temperature = $temperature;
    }

    /**
     * Create particle-antiparticle pair from vacuum energy.
     * Requires E >= 2mc^2 for the lightest possible pair.
     *
     * @return Particle[]|null
     */
    public function pairProduction(float $energy): ?array
    {
        if ($energy < 2 * M_ELECTRON * C ** 2) {
            return null;
        }

        // Determine what we can produce
        if ($energy >= 2 * M_PROTON * C ** 2 && $this->rand() < 0.1) {
            $pType = ParticleType::Up;
            $apType = ParticleType::Down;
        } else {
            $pType = ParticleType::Electron;
            $apType = ParticleType::Positron;
        }

        $direction = [$this->gauss(0, 1), $this->gauss(0, 1), $this->gauss(0, 1)];
        $norm = sqrt($direction[0] ** 2 + $direction[1] ** 2 + $direction[2] ** 2);
        if ($norm < 1e-20) {
            $norm = 1.0;
        }
        $pMomentum = $energy / (2 * C);

        $particle = new Particle(
            particleType: $pType,
            momentum: [
                $direction[0] / $norm * $pMomentum,
                $direction[1] / $norm * $pMomentum,
                $direction[2] / $norm * $pMomentum,
            ],
            spin: Spin::Up,
        );
        $antiparticle = new Particle(
            particleType: $apType,
            momentum: [
                -$direction[0] / $norm * $pMomentum,
                -$direction[1] / $norm * $pMomentum,
                -$direction[2] / $norm * $pMomentum,
            ],
            spin: Spin::Down,
        );

        // They're entangled
        $particle->entangledWith = $antiparticle->particleId;
        $antiparticle->entangledWith = $particle->particleId;

        $this->particles[] = $particle;
        $this->particles[] = $antiparticle;
        $this->entangledPairs[] = new EntangledPair($particle, $antiparticle);
        $this->totalCreated += 2;

        return [$particle, $antiparticle];
    }

    /** Annihilate particle-antiparticle pair, returning energy. */
    public function annihilate(Particle $p1, Particle $p2): float
    {
        $energy = $p1->energy() + $p2->energy();
        $this->removeParticle($p1);
        $this->removeParticle($p2);
        $this->totalAnnihilated += 2;
        $this->vacuumEnergy += $energy * 0.01;

        // Create photons from annihilation
        $photon1 = new Particle(
            particleType: ParticleType::Photon,
            momentum: [$energy / (2 * C), 0, 0],
        );
        $photon2 = new Particle(
            particleType: ParticleType::Photon,
            momentum: [-$energy / (2 * C), 0, 0],
        );
        $this->particles[] = $photon1;
        $this->particles[] = $photon2;
        return $energy;
    }

    /** Combine quarks into hadrons when temperature drops enough. */
    public function quarkConfinement(): array
    {
        if ($this->temperature > T_QUARK_HADRON) {
            return [];
        }

        $hadrons = [];
        $ups = [];
        $downs = [];

        foreach ($this->particles as $p) {
            if ($p->particleType === ParticleType::Up) {
                $ups[] = $p;
            } elseif ($p->particleType === ParticleType::Down) {
                $downs[] = $p;
            }
        }

        // Form protons (uud)
        while (count($ups) >= 2 && count($downs) >= 1) {
            $u1 = array_pop($ups);
            $u2 = array_pop($ups);
            $d1 = array_pop($downs);

            $u1->color = Color::Red;
            $u2->color = Color::Green;
            $d1->color = Color::Blue;

            $proton = new Particle(
                particleType: ParticleType::Proton,
                position: $u1->position,
                momentum: [
                    $u1->momentum[0] + $u2->momentum[0] + $d1->momentum[0],
                    $u1->momentum[1] + $u2->momentum[1] + $d1->momentum[1],
                    $u1->momentum[2] + $u2->momentum[2] + $d1->momentum[2],
                ],
            );

            $this->removeParticle($u1);
            $this->removeParticle($u2);
            $this->removeParticle($d1);
            $this->particles[] = $proton;
            $hadrons[] = $proton;
        }

        // Form neutrons (udd)
        while (count($ups) >= 1 && count($downs) >= 2) {
            $u1 = array_pop($ups);
            $d1 = array_pop($downs);
            $d2 = array_pop($downs);

            $u1->color = Color::Red;
            $d1->color = Color::Green;
            $d2->color = Color::Blue;

            $neutron = new Particle(
                particleType: ParticleType::Neutron,
                position: $u1->position,
                momentum: [
                    $u1->momentum[0] + $d1->momentum[0] + $d2->momentum[0],
                    $u1->momentum[1] + $d1->momentum[1] + $d2->momentum[1],
                    $u1->momentum[2] + $d1->momentum[2] + $d2->momentum[2],
                ],
            );

            $this->removeParticle($u1);
            $this->removeParticle($d1);
            $this->removeParticle($d2);
            $this->particles[] = $neutron;
            $hadrons[] = $neutron;
        }

        return $hadrons;
    }

    /** Spontaneous virtual particle pair from vacuum energy. */
    public function vacuumFluctuation(): ?array
    {
        $prob = min(0.5, $this->temperature / T_PLANCK);
        if ($this->rand() < $prob) {
            $lambda = 1.0 / ($this->temperature * 0.001);
            $energy = $this->exponential($lambda);
            return $this->pairProduction($energy);
        }
        return null;
    }

    /** Environmental decoherence of a particle's wave function. */
    public function decohere(Particle $particle, float $environmentCoupling = 0.1): void
    {
        if ($particle->waveFn->coherent) {
            $decoherenceRate = $environmentCoupling * $this->temperature;
            if ($this->rand() < $decoherenceRate) {
                $particle->waveFn->collapse();
            }
        }
    }

    /** Cool the field (universe expansion). */
    public function cool(float $factor = 0.999): void
    {
        $this->temperature *= $factor;
    }

    /** Evolve all particles by one time step. */
    public function evolveStep(float $dt = 1.0): void
    {
        foreach ($this->particles as $p) {
            $mass = $p->mass();
            if ($mass > 0) {
                for ($i = 0; $i < 3; $i++) {
                    $p->position[$i] += $p->momentum[$i] / $mass * $dt;
                }
            } else {
                // Massless particles move at c
                $pMag = sqrt(
                    $p->momentum[0] ** 2 +
                    $p->momentum[1] ** 2 +
                    $p->momentum[2] ** 2
                );
                if ($pMag < 1e-20) {
                    $pMag = 1.0;
                }
                for ($i = 0; $i < 3; $i++) {
                    $p->position[$i] += $p->momentum[$i] / $pMag * C * $dt;
                }
            }

            // Evolve wave function
            $p->waveFn->evolve($dt, $p->energy());
        }
    }

    /** Count particles by type. */
    public function particleCount(): array
    {
        $counts = [];
        foreach ($this->particles as $p) {
            $key = $p->particleType->value;
            $counts[$key] = ($counts[$key] ?? 0) + 1;
        }
        return $counts;
    }

    /** Total energy in the field. */
    public function totalEnergy(): float
    {
        $total = $this->vacuumEnergy;
        foreach ($this->particles as $p) {
            $total += $p->energy();
        }
        return $total;
    }

    /** Remove a particle from the particles array. */
    private function removeParticle(Particle $target): void
    {
        $idx = array_search($target, $this->particles, true);
        if ($idx !== false) {
            array_splice($this->particles, $idx, 1);
        }
    }

    /** Generate a random float [0, 1). */
    private function rand(): float
    {
        return mt_rand() / (mt_getrandmax() + 1);
    }

    /** Generate a Gaussian random number. */
    private function gauss(float $mean, float $stddev): float
    {
        // Box-Muller transform
        $u1 = max(1e-10, $this->rand());
        $u2 = $this->rand();
        return $mean + $stddev * sqrt(-2 * log($u1)) * cos(2 * M_PI * $u2);
    }

    /** Generate an exponential random variate with given rate parameter. */
    private function exponential(float $lambda): float
    {
        if ($lambda <= 0) {
            $lambda = 1.0;
        }
        return -log(max(1e-10, $this->rand())) / $lambda;
    }

    /**
     * Create a snapshot of the current field state for reporting.
     *
     * @return array{temperature: float, particle_count: int, particles_by_type: array, total_energy: float, vacuum_energy: float, total_created: int, total_annihilated: int}
     */
    public function toSnapshot(): array
    {
        return [
            'temperature'     => $this->temperature,
            'particle_count'  => count($this->particles),
            'particles_by_type' => $this->particleCount(),
            'total_energy'    => round($this->totalEnergy(), 2),
            'vacuum_energy'   => round($this->vacuumEnergy, 4),
            'total_created'   => $this->totalCreated,
            'total_annihilated' => $this->totalAnnihilated,
        ];
    }
}
