#pragma once
/// Physical constants and simulation parameters.
///
/// All values are in simulation units (SU) scaled for computational tractability.
/// Real-world proportions are maintained where possible.

#include <array>
#include <cmath>
#include <string_view>
#include <unordered_map>

namespace sim {

// === Fundamental Constants (simulation-scaled) ===
inline constexpr double C            = 1.0;          // Speed of light (SU)
inline constexpr double HBAR         = 0.01;         // Reduced Planck constant (SU)
inline constexpr double K_B          = 0.001;        // Boltzmann constant (SU)
inline constexpr double G_CONST      = 1e-6;         // Gravitational constant (SU)
inline constexpr double ALPHA        = 1.0 / 137.0;  // Fine structure constant
inline constexpr double E_CHARGE     = 0.1;          // Elementary charge (SU)
inline constexpr double PI           = 3.14159265358979323846;

// === Particle masses (SU, proportional to real) ===
inline constexpr double M_ELECTRON   = 1.0;
inline constexpr double M_UP_QUARK   = 4.4;
inline constexpr double M_DOWN_QUARK = 9.4;
inline constexpr double M_PROTON     = 1836.0;
inline constexpr double M_NEUTRON    = 1839.0;
inline constexpr double M_PHOTON     = 0.0;
inline constexpr double M_NEUTRINO   = 1e-6;
inline constexpr double M_W_BOSON    = 157000.0;
inline constexpr double M_Z_BOSON    = 178000.0;
inline constexpr double M_HIGGS      = 245000.0;

// === Force coupling strengths (dimensionless) ===
inline constexpr double STRONG_COUPLING  = 1.0;
inline constexpr double EM_COUPLING      = ALPHA;
inline constexpr double WEAK_COUPLING    = 1e-6;
inline constexpr double GRAVITY_COUPLING = 1e-38;

// === Nuclear parameters ===
inline constexpr double NUCLEAR_RADIUS           = 0.01;
inline constexpr double BINDING_ENERGY_DEUTERIUM = 2.22;
inline constexpr double BINDING_ENERGY_HELIUM4   = 28.3;
inline constexpr double BINDING_ENERGY_CARBON12  = 92.16;
inline constexpr double BINDING_ENERGY_IRON56    = 492.26;

// === Cosmic timeline (simulation ticks) ===
inline constexpr int PLANCK_EPOCH          = 1;
inline constexpr int INFLATION_EPOCH       = 10;
inline constexpr int ELECTROWEAK_EPOCH     = 100;
inline constexpr int QUARK_EPOCH           = 1000;
inline constexpr int HADRON_EPOCH          = 5000;
inline constexpr int NUCLEOSYNTHESIS_EPOCH = 10000;
inline constexpr int RECOMBINATION_EPOCH   = 50000;
inline constexpr int STAR_FORMATION_EPOCH  = 100000;
inline constexpr int SOLAR_SYSTEM_EPOCH    = 200000;
inline constexpr int EARTH_EPOCH           = 210000;
inline constexpr int LIFE_EPOCH            = 250000;
inline constexpr int DNA_EPOCH             = 280000;
inline constexpr int PRESENT_EPOCH         = 300000;

// === Temperature scale (simulation Kelvin) ===
inline constexpr double T_PLANCK         = 1e10;
inline constexpr double T_ELECTROWEAK    = 1e8;
inline constexpr double T_QUARK_HADRON   = 1e6;
inline constexpr double T_NUCLEOSYNTHESIS= 1e4;
inline constexpr double T_RECOMBINATION  = 3000.0;
inline constexpr double T_CMB            = 2.725;
inline constexpr double T_STELLAR_CORE   = 1.5e4;
inline constexpr double T_EARTH_SURFACE  = 288.0;

// === Chemistry parameters ===
inline constexpr std::array<int, 7> ELECTRON_SHELLS = {2, 8, 18, 32, 32, 18, 8};
inline constexpr double BOND_ENERGY_COVALENT       = 3.5;
inline constexpr double BOND_ENERGY_IONIC           = 5.0;
inline constexpr double BOND_ENERGY_HYDROGEN        = 0.2;
inline constexpr double BOND_ENERGY_VAN_DER_WAALS   = 0.01;

// === Biology parameters ===
inline constexpr std::array<char, 4> NUCLEOTIDE_BASES = {'A', 'T', 'G', 'C'};
inline constexpr std::array<char, 4> RNA_BASES        = {'A', 'U', 'G', 'C'};

inline constexpr std::array<std::string_view, 20> AMINO_ACIDS = {
    "Ala", "Arg", "Asn", "Asp", "Cys", "Gln", "Glu", "Gly",
    "His", "Ile", "Leu", "Lys", "Met", "Phe", "Pro", "Ser",
    "Thr", "Trp", "Tyr", "Val",
};

// === Epigenetic parameters ===
inline constexpr double METHYLATION_PROBABILITY     = 0.03;
inline constexpr double DEMETHYLATION_PROBABILITY   = 0.01;
inline constexpr double HISTONE_ACETYLATION_PROB    = 0.02;
inline constexpr double HISTONE_DEACETYLATION_PROB  = 0.015;
inline constexpr double CHROMATIN_REMODEL_ENERGY    = 1.5;

// === Environmental parameters ===
inline constexpr double UV_MUTATION_RATE            = 1e-4;
inline constexpr double COSMIC_RAY_MUTATION_RATE    = 1e-6;
inline constexpr double THERMAL_FLUCTUATION         = 0.01;
inline constexpr double RADIATION_DAMAGE_THRESHOLD  = 10.0;

// === Particle types ===
enum class ParticleType : int {
    Up = 0,
    Down,
    Electron,
    Positron,
    Neutrino,
    Photon,
    Gluon,
    WBoson,
    ZBoson,
    Proton,
    Neutron,
    Count
};

inline constexpr const char* particleTypeName(ParticleType t) {
    switch (t) {
        case ParticleType::Up:       return "up";
        case ParticleType::Down:     return "down";
        case ParticleType::Electron: return "electron";
        case ParticleType::Positron: return "positron";
        case ParticleType::Neutrino: return "neutrino";
        case ParticleType::Photon:   return "photon";
        case ParticleType::Gluon:    return "gluon";
        case ParticleType::WBoson:   return "W";
        case ParticleType::ZBoson:   return "Z";
        case ParticleType::Proton:   return "proton";
        case ParticleType::Neutron:  return "neutron";
        default:                     return "unknown";
    }
}

inline constexpr double particleMass(ParticleType t) {
    switch (t) {
        case ParticleType::Up:       return M_UP_QUARK;
        case ParticleType::Down:     return M_DOWN_QUARK;
        case ParticleType::Electron: return M_ELECTRON;
        case ParticleType::Positron: return M_ELECTRON;
        case ParticleType::Neutrino: return M_NEUTRINO;
        case ParticleType::Photon:   return M_PHOTON;
        case ParticleType::Gluon:    return M_PHOTON;
        case ParticleType::Proton:   return M_PROTON;
        case ParticleType::Neutron:  return M_NEUTRON;
        default:                     return 0.0;
    }
}

inline constexpr double particleCharge(ParticleType t) {
    switch (t) {
        case ParticleType::Up:       return  2.0 / 3.0;
        case ParticleType::Down:     return -1.0 / 3.0;
        case ParticleType::Electron: return -1.0;
        case ParticleType::Positron: return  1.0;
        case ParticleType::Neutrino: return  0.0;
        case ParticleType::Photon:   return  0.0;
        case ParticleType::Gluon:    return  0.0;
        case ParticleType::Proton:   return  1.0;
        case ParticleType::Neutron:  return  0.0;
        default:                     return  0.0;
    }
}

enum class Spin : int {
    Up   = 0,
    Down = 1
};

inline constexpr double spinValue(Spin s) {
    return s == Spin::Up ? 0.5 : -0.5;
}

enum class Color : int {
    Red = 0,
    Green,
    Blue,
    AntiRed,
    AntiGreen,
    AntiBlue,
    None
};

// === Epoch info ===
struct EpochEntry {
    std::string_view name;
    int              startTick;
    std::string_view description;
};

inline constexpr std::array<EpochEntry, 13> EPOCHS = {{
    {"Planck",          PLANCK_EPOCH,          "All forces unified, T~10^32K"},
    {"Inflation",       INFLATION_EPOCH,       "Exponential expansion, quantum fluctuations seed structure"},
    {"Electroweak",     ELECTROWEAK_EPOCH,     "Electromagnetic and weak forces separate"},
    {"Quark",           QUARK_EPOCH,           "Quark-gluon plasma, free quarks"},
    {"Hadron",          HADRON_EPOCH,          "Quarks confined into protons and neutrons"},
    {"Nucleosynthesis", NUCLEOSYNTHESIS_EPOCH, "Light nuclei form: H, He, Li"},
    {"Recombination",   RECOMBINATION_EPOCH,   "Atoms form, universe becomes transparent"},
    {"Star Formation",  STAR_FORMATION_EPOCH,  "First stars ignite, heavier elements forged"},
    {"Solar System",    SOLAR_SYSTEM_EPOCH,    "Our solar system coalesces from stellar debris"},
    {"Earth",           EARTH_EPOCH,           "Earth forms, oceans appear"},
    {"Life",            LIFE_EPOCH,            "First self-replicating molecules"},
    {"DNA Era",         DNA_EPOCH,             "DNA-based life, epigenetics emerge"},
    {"Present",         PRESENT_EPOCH,         "Complex life, intelligence"},
}};

// === Element data ===
struct ElementInfo {
    const char* symbol;
    const char* name;
    int         group;
    int         period;
    double      electronegativity;
};

inline const std::unordered_map<int, ElementInfo>& elements() {
    static const std::unordered_map<int, ElementInfo> table = {
        { 1, {"H",  "Hydrogen",   1, 1, 2.20}},
        { 2, {"He", "Helium",    18, 1, 0.00}},
        { 3, {"Li", "Lithium",    1, 2, 0.98}},
        { 4, {"Be", "Beryllium",  2, 2, 1.57}},
        { 5, {"B",  "Boron",     13, 2, 2.04}},
        { 6, {"C",  "Carbon",    14, 2, 2.55}},
        { 7, {"N",  "Nitrogen",  15, 2, 3.04}},
        { 8, {"O",  "Oxygen",    16, 2, 3.44}},
        { 9, {"F",  "Fluorine",  17, 2, 3.98}},
        {10, {"Ne", "Neon",      18, 2, 0.00}},
        {11, {"Na", "Sodium",     1, 3, 0.93}},
        {12, {"Mg", "Magnesium",  2, 3, 1.31}},
        {13, {"Al", "Aluminum",  13, 3, 1.61}},
        {14, {"Si", "Silicon",   14, 3, 1.90}},
        {15, {"P",  "Phosphorus",15, 3, 2.19}},
        {16, {"S",  "Sulfur",    16, 3, 2.58}},
        {17, {"Cl", "Chlorine",  17, 3, 3.16}},
        {18, {"Ar", "Argon",     18, 3, 0.00}},
        {19, {"K",  "Potassium",  1, 4, 0.82}},
        {20, {"Ca", "Calcium",    2, 4, 1.00}},
        {26, {"Fe", "Iron",       8, 4, 1.83}},
    };
    return table;
}

// === Codon table ===
inline const std::unordered_map<std::string, std::string>& codonTable() {
    static const std::unordered_map<std::string, std::string> table = {
        {"AUG", "Met"},
        {"UUU", "Phe"}, {"UUC", "Phe"},
        {"UUA", "Leu"}, {"UUG", "Leu"}, {"CUU", "Leu"}, {"CUC", "Leu"},
        {"CUA", "Leu"}, {"CUG", "Leu"},
        {"AUU", "Ile"}, {"AUC", "Ile"}, {"AUA", "Ile"},
        {"GUU", "Val"}, {"GUC", "Val"}, {"GUA", "Val"}, {"GUG", "Val"},
        {"UCU", "Ser"}, {"UCC", "Ser"}, {"UCA", "Ser"}, {"UCG", "Ser"},
        {"CCU", "Pro"}, {"CCC", "Pro"}, {"CCA", "Pro"}, {"CCG", "Pro"},
        {"ACU", "Thr"}, {"ACC", "Thr"}, {"ACA", "Thr"}, {"ACG", "Thr"},
        {"GCU", "Ala"}, {"GCC", "Ala"}, {"GCA", "Ala"}, {"GCG", "Ala"},
        {"UAU", "Tyr"}, {"UAC", "Tyr"},
        {"CAU", "His"}, {"CAC", "His"},
        {"CAA", "Gln"}, {"CAG", "Gln"},
        {"AAU", "Asn"}, {"AAC", "Asn"},
        {"AAA", "Lys"}, {"AAG", "Lys"},
        {"GAU", "Asp"}, {"GAC", "Asp"},
        {"GAA", "Glu"}, {"GAG", "Glu"},
        {"UGU", "Cys"}, {"UGC", "Cys"},
        {"UGG", "Trp"},
        {"CGU", "Arg"}, {"CGC", "Arg"}, {"CGA", "Arg"}, {"CGG", "Arg"},
        {"AGU", "Ser"}, {"AGC", "Ser"},
        {"AGA", "Arg"}, {"AGG", "Arg"},
        {"GGU", "Gly"}, {"GGC", "Gly"}, {"GGA", "Gly"}, {"GGG", "Gly"},
        {"UAA", "STOP"}, {"UAG", "STOP"}, {"UGA", "STOP"},
    };
    return table;
}

} // namespace sim
