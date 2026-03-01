"""Physical constants and simulation parameters.

All values are in simulation units (SU) scaled for computational tractability.
Real-world proportions are maintained where possible.
"""
import math

# === Fundamental Constants (simulation-scaled) ===
C = 1.0                    # Speed of light (SU)
HBAR = 0.01               # Reduced Planck constant (SU)
K_B = 0.001               # Boltzmann constant (SU)
G = 1e-6                  # Gravitational constant (SU)
ALPHA = 1.0 / 137.0       # Fine structure constant (dimensionless)
E_CHARGE = 0.1            # Elementary charge (SU)
PI = math.pi

# === Particle masses (SU, proportional to real) ===
M_ELECTRON = 1.0
M_UP_QUARK = 4.4          # ~2.2 MeV / 0.511 MeV
M_DOWN_QUARK = 9.4        # ~4.7 MeV / 0.511 MeV
M_PROTON = 1836.0         # Real ratio to electron
M_NEUTRON = 1839.0
M_PHOTON = 0.0
M_NEUTRINO = 1e-6
M_W_BOSON = 157000.0
M_Z_BOSON = 178000.0
M_HIGGS = 245000.0

# === Force coupling strengths (dimensionless) ===
STRONG_COUPLING = 1.0
EM_COUPLING = ALPHA
WEAK_COUPLING = 1e-6
GRAVITY_COUPLING = 1e-38

# === Nuclear parameters ===
NUCLEAR_RADIUS = 0.01     # SU
BINDING_ENERGY_DEUTERIUM = 2.22   # MeV equivalent
BINDING_ENERGY_HELIUM4 = 28.3
BINDING_ENERGY_CARBON12 = 92.16
BINDING_ENERGY_IRON56 = 492.26

# === Cosmic timeline (simulation ticks) ===
PLANCK_EPOCH = 1
INFLATION_EPOCH = 10
ELECTROWEAK_EPOCH = 100
QUARK_EPOCH = 1000
HADRON_EPOCH = 5000
NUCLEOSYNTHESIS_EPOCH = 10000
RECOMBINATION_EPOCH = 50000
STAR_FORMATION_EPOCH = 100000
SOLAR_SYSTEM_EPOCH = 200000
EARTH_EPOCH = 210000
LIFE_EPOCH = 250000
DNA_EPOCH = 280000
PRESENT_EPOCH = 300000

# === Temperature scale (simulation Kelvin) ===
T_PLANCK = 1e10
T_ELECTROWEAK = 1e8
T_QUARK_HADRON = 1e6
T_NUCLEOSYNTHESIS = 1e4
T_RECOMBINATION = 3000.0
T_CMB = 2.725
T_STELLAR_CORE = 1.5e4
T_EARTH_SURFACE = 288.0

# === Chemistry parameters ===
ELECTRON_SHELLS = [2, 8, 18, 32, 32, 18, 8]  # Max electrons per shell
BOND_ENERGY_COVALENT = 3.5    # eV equivalent
BOND_ENERGY_IONIC = 5.0
BOND_ENERGY_HYDROGEN = 0.2
BOND_ENERGY_VAN_DER_WAALS = 0.01

# === Biology parameters ===
NUCLEOTIDE_BASES = ["A", "T", "G", "C"]
RNA_BASES = ["A", "U", "G", "C"]
AMINO_ACIDS = [
    "Ala", "Arg", "Asn", "Asp", "Cys", "Gln", "Glu", "Gly",
    "His", "Ile", "Leu", "Lys", "Met", "Phe", "Pro", "Ser",
    "Thr", "Trp", "Tyr", "Val",
]
CODON_TABLE = {
    "AUG": "Met",  # Start
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
}

# === Epigenetic parameters ===
METHYLATION_PROBABILITY = 0.03
DEMETHYLATION_PROBABILITY = 0.01
HISTONE_ACETYLATION_PROB = 0.02
HISTONE_DEACETYLATION_PROB = 0.015
CHROMATIN_REMODEL_ENERGY = 1.5

# === Environmental parameters ===
UV_MUTATION_RATE = 1e-4
COSMIC_RAY_MUTATION_RATE = 1e-6
THERMAL_FLUCTUATION = 0.01
RADIATION_DAMAGE_THRESHOLD = 10.0
