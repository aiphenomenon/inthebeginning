// Package simulator implements a physics simulation from the Big Bang through
// the emergence of life, faithfully ported from the Python version.
package simulator

import "math"

// Fundamental Constants (simulation-scaled)
const (
	C       = 1.0            // Speed of light (SU)
	HBAR    = 0.01           // Reduced Planck constant (SU)
	KB      = 0.001          // Boltzmann constant (SU)
	G       = 1e-6           // Gravitational constant (SU)
	ALPHA   = 1.0 / 137.0    // Fine structure constant (dimensionless)
	ECharge = 0.1            // Elementary charge (SU)
	PI      = math.Pi
)

// Particle masses (SU, proportional to real)
const (
	MElectron  = 1.0
	MUpQuark   = 4.4     // ~2.2 MeV / 0.511 MeV
	MDownQuark = 9.4     // ~4.7 MeV / 0.511 MeV
	MProton    = 1836.0  // Real ratio to electron
	MNeutron   = 1839.0
	MPhoton    = 0.0
	MNeutrino  = 1e-6
	MWBoson    = 157000.0
	MZBoson    = 178000.0
	MHiggs     = 245000.0
)

// Force coupling strengths (dimensionless)
const (
	StrongCoupling  = 1.0
	EMCoupling      = ALPHA
	WeakCoupling    = 1e-6
	GravityCoupling = 1e-38
)

// Nuclear parameters
const (
	NuclearRadius          = 0.01  // SU
	BindingEnergyDeuterium = 2.22  // MeV equivalent
	BindingEnergyHelium4   = 28.3
	BindingEnergyCarbon12  = 92.16
	BindingEnergyIron56    = 492.26
)

// Cosmic timeline (simulation ticks)
const (
	PlanckEpoch        = 1
	InflationEpoch     = 10
	ElectroweakEpoch   = 100
	QuarkEpoch         = 1000
	HadronEpoch        = 5000
	NucleosynthesisEpoch = 10000
	RecombinationEpoch = 50000
	StarFormationEpoch = 100000
	SolarSystemEpoch   = 200000
	EarthEpoch         = 210000
	LifeEpoch          = 250000
	DNAEpoch           = 280000
	PresentEpoch       = 300000
)

// Temperature scale (simulation Kelvin)
const (
	TPlanck          = 1e10
	TElectroweak     = 1e8
	TQuarkHadron     = 1e6
	TNucleosynthesis = 1e4
	TRecombination   = 3000.0
	TCMB             = 2.725
	TStellarCore     = 1.5e4
	TEarthSurface    = 288.0
)

// Chemistry parameters
const (
	BondEnergyCovalent     = 3.5  // eV equivalent
	BondEnergyIonic        = 5.0
	BondEnergyHydrogen     = 0.2
	BondEnergyVanDerWaals  = 0.01
)

// ElectronShells defines max electrons per shell.
var ElectronShells = []int{2, 8, 18, 32, 32, 18, 8}

// Biology parameters
var NucleotideBases = []string{"A", "T", "G", "C"}
var RNABases = []string{"A", "U", "G", "C"}

// AminoAcids is the list of standard amino acids.
var AminoAcids = []string{
	"Ala", "Arg", "Asn", "Asp", "Cys", "Gln", "Glu", "Gly",
	"His", "Ile", "Leu", "Lys", "Met", "Phe", "Pro", "Ser",
	"Thr", "Trp", "Tyr", "Val",
}

// CodonTable maps RNA codons to amino acids. "STOP" signals termination.
var CodonTable = map[string]string{
	"AUG": "Met", // Start
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

// Epigenetic parameters
const (
	MethylationProbability      = 0.03
	DemethylationProbability    = 0.01
	HistoneAcetylationProb      = 0.02
	HistoneDeacetylationProb    = 0.015
	ChromatinRemodelEnergy      = 1.5
)

// Environmental parameters
const (
	UVMutationRate            = 1e-4
	CosmicRayMutationRate     = 1e-6
	ThermalFluctuation        = 0.01
	RadiationDamageThreshold  = 10.0
)
