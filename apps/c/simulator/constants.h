/*
 * constants.h - Physical constants and simulation parameters.
 *
 * All values are in simulation units (SU) scaled for computational tractability.
 * Real-world proportions are maintained where possible.
 */
#ifndef SIM_CONSTANTS_H
#define SIM_CONSTANTS_H

#include <math.h>

/* === Fundamental Constants (simulation-scaled) === */
#define SIM_C              1.0          /* Speed of light (SU)             */
#define SIM_HBAR           0.01         /* Reduced Planck constant (SU)    */
#define SIM_K_B            0.001        /* Boltzmann constant (SU)         */
#define SIM_G              1e-6         /* Gravitational constant (SU)     */
#define SIM_ALPHA          (1.0/137.0)  /* Fine structure constant         */
#define SIM_E_CHARGE       0.1          /* Elementary charge (SU)          */
#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif
#define SIM_PI             M_PI

/* === Particle masses (SU, proportional to real) === */
#define M_ELECTRON         1.0
#define M_UP_QUARK         4.4
#define M_DOWN_QUARK       9.4
#define M_PROTON           1836.0
#define M_NEUTRON          1839.0
#define M_PHOTON           0.0
#define M_NEUTRINO         1e-6
#define M_W_BOSON          157000.0
#define M_Z_BOSON          178000.0
#define M_HIGGS            245000.0

/* === Force coupling strengths (dimensionless) === */
#define STRONG_COUPLING    1.0
#define EM_COUPLING        SIM_ALPHA
#define WEAK_COUPLING      1e-6
#define GRAVITY_COUPLING   1e-38

/* === Nuclear parameters === */
#define NUCLEAR_RADIUS             0.01
#define BINDING_ENERGY_DEUTERIUM   2.22
#define BINDING_ENERGY_HELIUM4     28.3
#define BINDING_ENERGY_CARBON12    92.16
#define BINDING_ENERGY_IRON56      492.26

/* === Cosmic timeline (simulation ticks) === */
#define PLANCK_EPOCH           1
#define INFLATION_EPOCH        10
#define ELECTROWEAK_EPOCH      100
#define QUARK_EPOCH            1000
#define HADRON_EPOCH           5000
#define NUCLEOSYNTHESIS_EPOCH  10000
#define RECOMBINATION_EPOCH    50000
#define STAR_FORMATION_EPOCH   100000
#define SOLAR_SYSTEM_EPOCH     200000
#define EARTH_EPOCH            210000
#define LIFE_EPOCH             250000
#define DNA_EPOCH              280000
#define PRESENT_EPOCH          300000

/* === Temperature scale (simulation Kelvin) === */
#define T_PLANCK           1e10
#define T_ELECTROWEAK      1e8
#define T_QUARK_HADRON     1e6
#define T_NUCLEOSYNTHESIS  1e4
#define T_RECOMBINATION    3000.0
#define T_CMB              2.725
#define T_STELLAR_CORE     1.5e4
#define T_EARTH_SURFACE    288.0

/* === Chemistry parameters === */
#define ELECTRON_SHELL_COUNT    7
static const int ELECTRON_SHELLS[ELECTRON_SHELL_COUNT] = {2, 8, 18, 32, 32, 18, 8};

#define BOND_ENERGY_COVALENT        3.5
#define BOND_ENERGY_IONIC           5.0
#define BOND_ENERGY_HYDROGEN        0.2
#define BOND_ENERGY_VAN_DER_WAALS   0.01

/* === Biology parameters === */
#define NUCLEOTIDE_BASE_COUNT  4
static const char NUCLEOTIDE_BASES[NUCLEOTIDE_BASE_COUNT] = {'A', 'T', 'G', 'C'};
static const char RNA_BASES[NUCLEOTIDE_BASE_COUNT]        = {'A', 'U', 'G', 'C'};

#define AMINO_ACID_COUNT  20
static const char *AMINO_ACIDS[AMINO_ACID_COUNT] = {
    "Ala", "Arg", "Asn", "Asp", "Cys", "Gln", "Glu", "Gly",
    "His", "Ile", "Leu", "Lys", "Met", "Phe", "Pro", "Ser",
    "Thr", "Trp", "Tyr", "Val",
};

/* === Epigenetic parameters === */
#define METHYLATION_PROBABILITY       0.03
#define DEMETHYLATION_PROBABILITY     0.01
#define HISTONE_ACETYLATION_PROB      0.02
#define HISTONE_DEACETYLATION_PROB    0.015
#define CHROMATIN_REMODEL_ENERGY      1.5

/* === Environmental parameters === */
#define UV_MUTATION_RATE              1e-4
#define COSMIC_RAY_MUTATION_RATE      1e-6
#define THERMAL_FLUCTUATION           0.01
#define RADIATION_DAMAGE_THRESHOLD    10.0

/* === Simulation caps === */
#define MAX_PARTICLES    4096
#define MAX_ATOMS        2048
#define MAX_MOLECULES    1024
#define MAX_CELLS        128
#define MAX_DNA_LENGTH   256
#define MAX_GENES        8
#define MAX_PROTEINS     32
#define MAX_BONDS        8
#define MAX_EVENTS       64

#endif /* SIM_CONSTANTS_H */
