/**
 * Physical constants and simulation parameters.
 *
 * All values are in simulation units (SU) scaled for computational tractability.
 * Real-world proportions are maintained where possible.
 * Faithful port of simulator/constants.py
 */

// === Fundamental Constants (simulation-scaled) ===
export const C = 1.0;                      // Speed of light (SU)
export const HBAR = 0.01;                  // Reduced Planck constant (SU)
export const K_B = 0.001;                  // Boltzmann constant (SU)
export const G = 1e-6;                     // Gravitational constant (SU)
export const ALPHA = 1.0 / 137.0;          // Fine structure constant (dimensionless)
export const E_CHARGE = 0.1;               // Elementary charge (SU)
export const PI = Math.PI;

// === Particle masses (SU, proportional to real) ===
export const M_ELECTRON = 1.0;
export const M_UP_QUARK = 4.4;            // ~2.2 MeV / 0.511 MeV
export const M_DOWN_QUARK = 9.4;           // ~4.7 MeV / 0.511 MeV
export const M_PROTON = 1836.0;            // Real ratio to electron
export const M_NEUTRON = 1839.0;
export const M_PHOTON = 0.0;
export const M_NEUTRINO = 1e-6;
export const M_W_BOSON = 157000.0;
export const M_Z_BOSON = 178000.0;
export const M_HIGGS = 245000.0;

// === Force coupling strengths (dimensionless) ===
export const STRONG_COUPLING = 1.0;
export const EM_COUPLING = ALPHA;
export const WEAK_COUPLING = 1e-6;
export const GRAVITY_COUPLING = 1e-38;

// === Nuclear parameters ===
export const NUCLEAR_RADIUS = 0.01;        // SU
export const BINDING_ENERGY_DEUTERIUM = 2.22;   // MeV equivalent
export const BINDING_ENERGY_HELIUM4 = 28.3;
export const BINDING_ENERGY_CARBON12 = 92.16;
export const BINDING_ENERGY_IRON56 = 492.26;

// === Cosmic timeline (simulation ticks) ===
export const PLANCK_EPOCH = 1;
export const INFLATION_EPOCH = 10;
export const ELECTROWEAK_EPOCH = 100;
export const QUARK_EPOCH = 1000;
export const HADRON_EPOCH = 5000;
export const NUCLEOSYNTHESIS_EPOCH = 10000;
export const RECOMBINATION_EPOCH = 50000;
export const STAR_FORMATION_EPOCH = 100000;
export const SOLAR_SYSTEM_EPOCH = 200000;
export const EARTH_EPOCH = 210000;
export const LIFE_EPOCH = 250000;
export const DNA_EPOCH = 280000;
export const PRESENT_EPOCH = 300000;

// === Temperature scale (simulation Kelvin) ===
export const T_PLANCK = 1e10;
export const T_ELECTROWEAK = 1e8;
export const T_QUARK_HADRON = 1e6;
export const T_NUCLEOSYNTHESIS = 1e4;
export const T_RECOMBINATION = 3000.0;
export const T_CMB = 2.725;
export const T_STELLAR_CORE = 1.5e4;
export const T_EARTH_SURFACE = 288.0;

// === Chemistry parameters ===
export const ELECTRON_SHELLS: number[] = [2, 8, 18, 32, 32, 18, 8]; // Max electrons per shell
export const BOND_ENERGY_COVALENT = 3.5;   // eV equivalent
export const BOND_ENERGY_IONIC = 5.0;
export const BOND_ENERGY_HYDROGEN = 0.2;
export const BOND_ENERGY_VAN_DER_WAALS = 0.01;

// === Biology parameters ===
export const NUCLEOTIDE_BASES: string[] = ["A", "T", "G", "C"];
export const RNA_BASES: string[] = ["A", "U", "G", "C"];
export const AMINO_ACIDS: string[] = [
    "Ala", "Arg", "Asn", "Asp", "Cys", "Gln", "Glu", "Gly",
    "His", "Ile", "Leu", "Lys", "Met", "Phe", "Pro", "Ser",
    "Thr", "Trp", "Tyr", "Val",
];

export const CODON_TABLE: Record<string, string> = {
    "AUG": "Met",  // Start
    "UUU": "Phe", "UUC": "Phe",
    "UUA": "Leu", "UUG": "Leu", "CUU": "Leu", "CUC": "Leu",
    "CUA": "Leu", "CUG": "Leu",
    "AUU": "Ile", "AUC": "Ile", "AUA": "Ile",
    "GUU": "Val", "GUC": "Val", "GUA": "Val", "GUG": "Val",
    "UCU": "Ser", "UCC": "Ser", "UCA": "Ser", "UCG": "Ser",
    "CCU": "Pro", "CCC": "Pro", "CCA": "Pro", "CCG": "Pro",
    "ACU": "Thr", "ACC": "Thr", "ACA": "Thr", "ACG": "Thr",
    "GCU": "Ala", "GCC": "Ala", "GCA": "Ala", "GCG": "Ala",
    "UAU": "Tyr", "UAC": "Tyr",
    "CAU": "His", "CAC": "His",
    "CAA": "Gln", "CAG": "Gln",
    "AAU": "Asn", "AAC": "Asn",
    "AAA": "Lys", "AAG": "Lys",
    "GAU": "Asp", "GAC": "Asp",
    "GAA": "Glu", "GAG": "Glu",
    "UGU": "Cys", "UGC": "Cys",
    "UGG": "Trp",
    "CGU": "Arg", "CGC": "Arg", "CGA": "Arg", "CGG": "Arg",
    "AGU": "Ser", "AGC": "Ser",
    "AGA": "Arg", "AGG": "Arg",
    "GGU": "Gly", "GGC": "Gly", "GGA": "Gly", "GGG": "Gly",
    "UAA": "STOP", "UAG": "STOP", "UGA": "STOP",
};

// === Epigenetic parameters ===
export const METHYLATION_PROBABILITY = 0.03;
export const DEMETHYLATION_PROBABILITY = 0.01;
export const HISTONE_ACETYLATION_PROB = 0.02;
export const HISTONE_DEACETYLATION_PROB = 0.015;
export const CHROMATIN_REMODEL_ENERGY = 1.5;

// === Environmental parameters ===
export const UV_MUTATION_RATE = 1e-4;
export const COSMIC_RAY_MUTATION_RATE = 1e-6;
export const THERMAL_FLUCTUATION = 0.01;
export const RADIATION_DAMAGE_THRESHOLD = 10.0;

// === Epoch timeline as ordered list for lookups ===
export interface EpochInfo {
    name: string;
    startTick: number;
    description: string;
}

export const EPOCHS: EpochInfo[] = [
    { name: "Planck", startTick: PLANCK_EPOCH, description: "All forces unified, T~10^32K" },
    { name: "Inflation", startTick: INFLATION_EPOCH, description: "Exponential expansion, quantum fluctuations seed structure" },
    { name: "Electroweak", startTick: ELECTROWEAK_EPOCH, description: "Electromagnetic and weak forces separate" },
    { name: "Quark", startTick: QUARK_EPOCH, description: "Quark-gluon plasma, free quarks" },
    { name: "Hadron", startTick: HADRON_EPOCH, description: "Quarks confined into protons and neutrons" },
    { name: "Nucleosynthesis", startTick: NUCLEOSYNTHESIS_EPOCH, description: "Light nuclei form: H, He, Li" },
    { name: "Recombination", startTick: RECOMBINATION_EPOCH, description: "Atoms form, universe becomes transparent" },
    { name: "Star Formation", startTick: STAR_FORMATION_EPOCH, description: "First stars ignite, heavier elements forged" },
    { name: "Solar System", startTick: SOLAR_SYSTEM_EPOCH, description: "Our solar system coalesces from stellar debris" },
    { name: "Earth", startTick: EARTH_EPOCH, description: "Earth forms, oceans appear" },
    { name: "Life", startTick: LIFE_EPOCH, description: "First self-replicating molecules" },
    { name: "DNA Era", startTick: DNA_EPOCH, description: "DNA-based life, epigenetics emerge" },
    { name: "Present", startTick: PRESENT_EPOCH, description: "Complex life, intelligence" },
];

// === Elements data: [symbol, name, group, period, electronegativity] ===
export const ELEMENTS: Record<number, [string, string, number, number, number]> = {
    1:  ["H",  "Hydrogen",   1,  1, 2.20],
    2:  ["He", "Helium",     18, 1, 0.0],
    3:  ["Li", "Lithium",    1,  2, 0.98],
    4:  ["Be", "Beryllium",  2,  2, 1.57],
    5:  ["B",  "Boron",      13, 2, 2.04],
    6:  ["C",  "Carbon",     14, 2, 2.55],
    7:  ["N",  "Nitrogen",   15, 2, 3.04],
    8:  ["O",  "Oxygen",     16, 2, 3.44],
    9:  ["F",  "Fluorine",   17, 2, 3.98],
    10: ["Ne", "Neon",       18, 2, 0.0],
    11: ["Na", "Sodium",     1,  3, 0.93],
    12: ["Mg", "Magnesium",  2,  3, 1.31],
    13: ["Al", "Aluminum",   13, 3, 1.61],
    14: ["Si", "Silicon",    14, 3, 1.90],
    15: ["P",  "Phosphorus", 15, 3, 2.19],
    16: ["S",  "Sulfur",     16, 3, 2.58],
    17: ["Cl", "Chlorine",   17, 3, 3.16],
    18: ["Ar", "Argon",      18, 3, 0.0],
    19: ["K",  "Potassium",  1,  4, 0.82],
    20: ["Ca", "Calcium",    2,  4, 1.00],
    26: ["Fe", "Iron",       8,  4, 1.83],
};
