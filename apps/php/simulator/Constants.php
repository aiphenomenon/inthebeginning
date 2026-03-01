<?php

declare(strict_types=1);

/**
 * Physical constants and simulation parameters.
 *
 * All values are in simulation units (SU) scaled for computational tractability.
 * Real-world proportions are maintained where possible.
 */

// === Fundamental Constants (simulation-scaled) ===
const C = 1.0;                     // Speed of light (SU)
const HBAR = 0.01;                 // Reduced Planck constant (SU)
const K_B = 0.001;                 // Boltzmann constant (SU)
const G_CONST = 1e-6;              // Gravitational constant (SU)
const ALPHA = 1.0 / 137.0;         // Fine structure constant (dimensionless)
const E_CHARGE = 0.1;              // Elementary charge (SU)

// === Particle masses (SU, proportional to real) ===
const M_ELECTRON = 1.0;
const M_UP_QUARK = 4.4;            // ~2.2 MeV / 0.511 MeV
const M_DOWN_QUARK = 9.4;          // ~4.7 MeV / 0.511 MeV
const M_PROTON = 1836.0;           // Real ratio to electron
const M_NEUTRON = 1839.0;
const M_PHOTON = 0.0;
const M_NEUTRINO = 1e-6;
const M_W_BOSON = 157000.0;
const M_Z_BOSON = 178000.0;
const M_HIGGS = 245000.0;

// === Force coupling strengths (dimensionless) ===
const STRONG_COUPLING = 1.0;
const EM_COUPLING = ALPHA;
const WEAK_COUPLING = 1e-6;
const GRAVITY_COUPLING = 1e-38;

// === Nuclear parameters ===
const NUCLEAR_RADIUS = 0.01;       // SU
const BINDING_ENERGY_DEUTERIUM = 2.22;   // MeV equivalent
const BINDING_ENERGY_HELIUM4 = 28.3;
const BINDING_ENERGY_CARBON12 = 92.16;
const BINDING_ENERGY_IRON56 = 492.26;

// === Cosmic timeline (simulation ticks) ===
const PLANCK_EPOCH = 1;
const INFLATION_EPOCH = 10;
const ELECTROWEAK_EPOCH = 100;
const QUARK_EPOCH = 1000;
const HADRON_EPOCH = 5000;
const NUCLEOSYNTHESIS_EPOCH = 10000;
const RECOMBINATION_EPOCH = 50000;
const STAR_FORMATION_EPOCH = 100000;
const SOLAR_SYSTEM_EPOCH = 200000;
const EARTH_EPOCH = 210000;
const LIFE_EPOCH = 250000;
const DNA_EPOCH = 280000;
const PRESENT_EPOCH = 300000;

// === Temperature scale (simulation Kelvin) ===
const T_PLANCK = 1e10;
const T_ELECTROWEAK = 1e8;
const T_QUARK_HADRON = 1e6;
const T_NUCLEOSYNTHESIS = 1e4;
const T_RECOMBINATION = 3000.0;
const T_CMB = 2.725;
const T_STELLAR_CORE = 1.5e4;
const T_EARTH_SURFACE = 288.0;

// === Chemistry parameters ===
const ELECTRON_SHELLS = [2, 8, 18, 32, 32, 18, 8]; // Max electrons per shell
const BOND_ENERGY_COVALENT = 3.5;    // eV equivalent
const BOND_ENERGY_IONIC = 5.0;
const BOND_ENERGY_HYDROGEN = 0.2;
const BOND_ENERGY_VAN_DER_WAALS = 0.01;

// === Biology parameters ===
const NUCLEOTIDE_BASES = ['A', 'T', 'G', 'C'];
const RNA_BASES = ['A', 'U', 'G', 'C'];
const AMINO_ACIDS = [
    'Ala', 'Arg', 'Asn', 'Asp', 'Cys', 'Gln', 'Glu', 'Gly',
    'His', 'Ile', 'Leu', 'Lys', 'Met', 'Phe', 'Pro', 'Ser',
    'Thr', 'Trp', 'Tyr', 'Val',
];
const CODON_TABLE = [
    'AUG' => 'Met',  // Start
    'UUU' => 'Phe', 'UUC' => 'Phe',
    'UUA' => 'Leu', 'UUG' => 'Leu', 'CUU' => 'Leu', 'CUC' => 'Leu',
    'CUA' => 'Leu', 'CUG' => 'Leu',
    'AUU' => 'Ile', 'AUC' => 'Ile', 'AUA' => 'Ile',
    'GUU' => 'Val', 'GUC' => 'Val', 'GUA' => 'Val', 'GUG' => 'Val',
    'UCU' => 'Ser', 'UCC' => 'Ser', 'UCA' => 'Ser', 'UCG' => 'Ser',
    'CCU' => 'Pro', 'CCC' => 'Pro', 'CCA' => 'Pro', 'CCG' => 'Pro',
    'ACU' => 'Thr', 'ACC' => 'Thr', 'ACA' => 'Thr', 'ACG' => 'Thr',
    'GCU' => 'Ala', 'GCC' => 'Ala', 'GCA' => 'Ala', 'GCG' => 'Ala',
    'UAU' => 'Tyr', 'UAC' => 'Tyr',
    'CAU' => 'His', 'CAC' => 'His',
    'CAA' => 'Gln', 'CAG' => 'Gln',
    'AAU' => 'Asn', 'AAC' => 'Asn',
    'AAA' => 'Lys', 'AAG' => 'Lys',
    'GAU' => 'Asp', 'GAC' => 'Asp',
    'GAA' => 'Glu', 'GAG' => 'Glu',
    'UGU' => 'Cys', 'UGC' => 'Cys',
    'UGG' => 'Trp',
    'CGU' => 'Arg', 'CGC' => 'Arg', 'CGA' => 'Arg', 'CGG' => 'Arg',
    'AGU' => 'Ser', 'AGC' => 'Ser',
    'AGA' => 'Arg', 'AGG' => 'Arg',
    'GGU' => 'Gly', 'GGC' => 'Gly', 'GGA' => 'Gly', 'GGG' => 'Gly',
    'UAA' => 'STOP', 'UAG' => 'STOP', 'UGA' => 'STOP',
];

// === Epigenetic parameters ===
const METHYLATION_PROBABILITY = 0.03;
const DEMETHYLATION_PROBABILITY = 0.01;
const HISTONE_ACETYLATION_PROB = 0.02;
const HISTONE_DEACETYLATION_PROB = 0.015;
const CHROMATIN_REMODEL_ENERGY = 1.5;

// === Environmental parameters ===
const UV_MUTATION_RATE = 1e-4;
const COSMIC_RAY_MUTATION_RATE = 1e-6;
const THERMAL_FLUCTUATION = 0.01;
const RADIATION_DAMAGE_THRESHOLD = 10.0;

/**
 * Periodic table data: atomic_number => [symbol, name, group, period, electronegativity]
 */
const ELEMENTS = [
    1  => ['H',  'Hydrogen',   1,  1, 2.20],
    2  => ['He', 'Helium',     18, 1, 0.0],
    3  => ['Li', 'Lithium',    1,  2, 0.98],
    4  => ['Be', 'Beryllium',  2,  2, 1.57],
    5  => ['B',  'Boron',      13, 2, 2.04],
    6  => ['C',  'Carbon',     14, 2, 2.55],
    7  => ['N',  'Nitrogen',   15, 2, 3.04],
    8  => ['O',  'Oxygen',     16, 2, 3.44],
    9  => ['F',  'Fluorine',   17, 2, 3.98],
    10 => ['Ne', 'Neon',       18, 2, 0.0],
    11 => ['Na', 'Sodium',     1,  3, 0.93],
    12 => ['Mg', 'Magnesium',  2,  3, 1.31],
    13 => ['Al', 'Aluminum',   13, 3, 1.61],
    14 => ['Si', 'Silicon',    14, 3, 1.90],
    15 => ['P',  'Phosphorus', 15, 3, 2.19],
    16 => ['S',  'Sulfur',     16, 3, 2.58],
    17 => ['Cl', 'Chlorine',   17, 3, 3.16],
    18 => ['Ar', 'Argon',      18, 3, 0.0],
    19 => ['K',  'Potassium',  1,  4, 0.82],
    20 => ['Ca', 'Calcium',    2,  4, 1.00],
    26 => ['Fe', 'Iron',       8,  4, 1.83],
];

/**
 * Epoch information for timeline display.
 */
enum Epoch: int
{
    case Planck = PLANCK_EPOCH;
    case Inflation = INFLATION_EPOCH;
    case Electroweak = ELECTROWEAK_EPOCH;
    case Quark = QUARK_EPOCH;
    case Hadron = HADRON_EPOCH;
    case Nucleosynthesis = NUCLEOSYNTHESIS_EPOCH;
    case Recombination = RECOMBINATION_EPOCH;
    case StarFormation = STAR_FORMATION_EPOCH;
    case SolarSystem = SOLAR_SYSTEM_EPOCH;
    case Earth = EARTH_EPOCH;
    case Life = LIFE_EPOCH;
    case DNAEra = DNA_EPOCH;
    case Present = PRESENT_EPOCH;

    public function label(): string
    {
        return match ($this) {
            self::Planck         => 'Planck',
            self::Inflation      => 'Inflation',
            self::Electroweak    => 'Electroweak',
            self::Quark          => 'Quark',
            self::Hadron         => 'Hadron',
            self::Nucleosynthesis => 'Nucleosynthesis',
            self::Recombination  => 'Recombination',
            self::StarFormation  => 'Star Formation',
            self::SolarSystem    => 'Solar System',
            self::Earth          => 'Earth',
            self::Life           => 'Life',
            self::DNAEra         => 'DNA Era',
            self::Present        => 'Present',
        };
    }

    public function description(): string
    {
        return match ($this) {
            self::Planck         => 'All forces unified, T~10^32K',
            self::Inflation      => 'Exponential expansion, quantum fluctuations seed structure',
            self::Electroweak    => 'Electromagnetic and weak forces separate',
            self::Quark          => 'Quark-gluon plasma, free quarks',
            self::Hadron         => 'Quarks confined into protons and neutrons',
            self::Nucleosynthesis => 'Light nuclei form: H, He, Li',
            self::Recombination  => 'Atoms form, universe becomes transparent',
            self::StarFormation  => 'First stars ignite, heavier elements forged',
            self::SolarSystem    => 'Our solar system coalesces from stellar debris',
            self::Earth          => 'Earth forms, oceans appear',
            self::Life           => 'First self-replicating molecules',
            self::DNAEra         => 'DNA-based life, epigenetics emerge',
            self::Present        => 'Complex life, intelligence',
        };
    }
}

/**
 * Get all epochs in order for timeline display.
 *
 * @return list<array{name: string, tick: int, description: string}>
 */
function getEpochTimeline(): array
{
    $timeline = [];
    foreach (Epoch::cases() as $epoch) {
        $timeline[] = [
            'name'        => $epoch->label(),
            'tick'        => $epoch->value,
            'description' => $epoch->description(),
        ];
    }
    return $timeline;
}
