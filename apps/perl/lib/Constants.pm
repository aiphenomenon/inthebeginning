package Constants;

# Physical constants and simulation parameters.
# All values are in simulation units (SU) scaled for computational tractability.
# Real-world proportions are maintained where possible.

use strict;
use warnings;
use POSIX qw(M_PI);
use Exporter 'import';

our @EXPORT_OK = qw(
    $C $HBAR $K_B $G $ALPHA $E_CHARGE $PI

    $M_ELECTRON $M_UP_QUARK $M_DOWN_QUARK $M_PROTON $M_NEUTRON
    $M_PHOTON $M_NEUTRINO $M_W_BOSON $M_Z_BOSON $M_HIGGS

    $STRONG_COUPLING $EM_COUPLING $WEAK_COUPLING $GRAVITY_COUPLING

    $NUCLEAR_RADIUS $BINDING_ENERGY_DEUTERIUM $BINDING_ENERGY_HELIUM4
    $BINDING_ENERGY_CARBON12 $BINDING_ENERGY_IRON56

    $PLANCK_EPOCH $INFLATION_EPOCH $ELECTROWEAK_EPOCH $QUARK_EPOCH
    $HADRON_EPOCH $NUCLEOSYNTHESIS_EPOCH $RECOMBINATION_EPOCH
    $STAR_FORMATION_EPOCH $SOLAR_SYSTEM_EPOCH $EARTH_EPOCH
    $LIFE_EPOCH $DNA_EPOCH $PRESENT_EPOCH

    $T_PLANCK $T_ELECTROWEAK $T_QUARK_HADRON $T_NUCLEOSYNTHESIS
    $T_RECOMBINATION $T_CMB $T_STELLAR_CORE $T_EARTH_SURFACE

    @ELECTRON_SHELLS $BOND_ENERGY_COVALENT $BOND_ENERGY_IONIC
    $BOND_ENERGY_HYDROGEN $BOND_ENERGY_VAN_DER_WAALS

    @NUCLEOTIDE_BASES @RNA_BASES @AMINO_ACIDS %CODON_TABLE

    $METHYLATION_PROBABILITY $DEMETHYLATION_PROBABILITY
    $HISTONE_ACETYLATION_PROB $HISTONE_DEACETYLATION_PROB
    $CHROMATIN_REMODEL_ENERGY

    $UV_MUTATION_RATE $COSMIC_RAY_MUTATION_RATE
    $THERMAL_FLUCTUATION $RADIATION_DAMAGE_THRESHOLD
);

our %EXPORT_TAGS = (all => \@EXPORT_OK);

# === Fundamental Constants (simulation-scaled) ===
our $C         = 1.0;                  # Speed of light (SU)
our $HBAR      = 0.01;                 # Reduced Planck constant (SU)
our $K_B       = 0.001;                # Boltzmann constant (SU)
our $G         = 1e-6;                 # Gravitational constant (SU)
our $ALPHA     = 1.0 / 137.0;          # Fine structure constant (dimensionless)
our $E_CHARGE  = 0.1;                  # Elementary charge (SU)
our $PI        = M_PI;

# === Particle masses (SU, proportional to real) ===
our $M_ELECTRON   = 1.0;
our $M_UP_QUARK   = 4.4;              # ~2.2 MeV / 0.511 MeV
our $M_DOWN_QUARK = 9.4;              # ~4.7 MeV / 0.511 MeV
our $M_PROTON     = 1836.0;           # Real ratio to electron
our $M_NEUTRON    = 1839.0;
our $M_PHOTON     = 0.0;
our $M_NEUTRINO   = 1e-6;
our $M_W_BOSON    = 157000.0;
our $M_Z_BOSON    = 178000.0;
our $M_HIGGS      = 245000.0;

# === Force coupling strengths (dimensionless) ===
our $STRONG_COUPLING  = 1.0;
our $EM_COUPLING      = $ALPHA;
our $WEAK_COUPLING    = 1e-6;
our $GRAVITY_COUPLING = 1e-38;

# === Nuclear parameters ===
our $NUCLEAR_RADIUS           = 0.01;     # SU
our $BINDING_ENERGY_DEUTERIUM = 2.22;     # MeV equivalent
our $BINDING_ENERGY_HELIUM4   = 28.3;
our $BINDING_ENERGY_CARBON12  = 92.16;
our $BINDING_ENERGY_IRON56    = 492.26;

# === Cosmic timeline (simulation ticks) ===
our $PLANCK_EPOCH          = 1;
our $INFLATION_EPOCH       = 10;
our $ELECTROWEAK_EPOCH     = 100;
our $QUARK_EPOCH           = 1000;
our $HADRON_EPOCH          = 5000;
our $NUCLEOSYNTHESIS_EPOCH = 10000;
our $RECOMBINATION_EPOCH   = 50000;
our $STAR_FORMATION_EPOCH  = 100000;
our $SOLAR_SYSTEM_EPOCH    = 200000;
our $EARTH_EPOCH           = 210000;
our $LIFE_EPOCH            = 250000;
our $DNA_EPOCH             = 280000;
our $PRESENT_EPOCH         = 300000;

# === Temperature scale (simulation Kelvin) ===
our $T_PLANCK          = 1e10;
our $T_ELECTROWEAK     = 1e8;
our $T_QUARK_HADRON    = 1e6;
our $T_NUCLEOSYNTHESIS = 1e4;
our $T_RECOMBINATION   = 3000.0;
our $T_CMB             = 2.725;
our $T_STELLAR_CORE    = 1.5e4;
our $T_EARTH_SURFACE   = 288.0;

# === Chemistry parameters ===
our @ELECTRON_SHELLS          = (2, 8, 18, 32, 32, 18, 8);  # Max electrons per shell
our $BOND_ENERGY_COVALENT     = 3.5;     # eV equivalent
our $BOND_ENERGY_IONIC        = 5.0;
our $BOND_ENERGY_HYDROGEN     = 0.2;
our $BOND_ENERGY_VAN_DER_WAALS = 0.01;

# === Biology parameters ===
our @NUCLEOTIDE_BASES = qw(A T G C);
our @RNA_BASES        = qw(A U G C);
our @AMINO_ACIDS = qw(
    Ala Arg Asn Asp Cys Gln Glu Gly
    His Ile Leu Lys Met Phe Pro Ser
    Thr Trp Tyr Val
);

our %CODON_TABLE = (
    'AUG' => 'Met',    # Start
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
);

# === Epigenetic parameters ===
our $METHYLATION_PROBABILITY     = 0.03;
our $DEMETHYLATION_PROBABILITY   = 0.01;
our $HISTONE_ACETYLATION_PROB    = 0.02;
our $HISTONE_DEACETYLATION_PROB  = 0.015;
our $CHROMATIN_REMODEL_ENERGY    = 1.5;

# === Environmental parameters ===
our $UV_MUTATION_RATE            = 1e-4;
our $COSMIC_RAY_MUTATION_RATE    = 1e-6;
our $THERMAL_FLUCTUATION         = 0.01;
our $RADIATION_DAMAGE_THRESHOLD  = 10.0;

1;
