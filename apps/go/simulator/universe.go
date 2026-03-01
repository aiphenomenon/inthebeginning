package simulator

import (
	"fmt"
	"math/rand"
)

// EpochName maps epoch tick thresholds to human-readable names.
type EpochInfo struct {
	Name        string
	StartTick   int
	Description string
	Symbol      string
}

// Epochs defines the 13 cosmic epochs in chronological order.
var Epochs = []EpochInfo{
	{"Planck", PlanckEpoch, "Quantum gravity dominates; spacetime foam", "*"},
	{"Inflation", InflationEpoch, "Exponential expansion of spacetime", "~"},
	{"Electroweak", ElectroweakEpoch, "Electroweak symmetry breaking; W/Z bosons acquire mass", "!"},
	{"QuarkGluon", QuarkEpoch, "Quark-gluon plasma; free quarks and gluons", "#"},
	{"Hadron", HadronEpoch, "Quarks confine into protons and neutrons", "@"},
	{"Nucleosynthesis", NucleosynthesisEpoch, "Light nuclei form: H, He, Li", "%"},
	{"Recombination", RecombinationEpoch, "Electrons captured by nuclei; atoms form", "&"},
	{"StarFormation", StarFormationEpoch, "First stars ignite; heavy element forging", "+"},
	{"SolarSystem", SolarSystemEpoch, "Protoplanetary disk collapses; planets form", "O"},
	{"EarthFormation", EarthEpoch, "Rocky planet cools; oceans condense", "o"},
	{"LifeEmergence", LifeEpoch, "First protocells arise from prebiotic chemistry", "."},
	{"DNAEvolution", DNAEpoch, "DNA replication, mutation, and natural selection", "="},
	{"Present", PresentEpoch, "Complex life; billions of years of evolution", "^"},
}

// EpochResult stores the outcome of simulating one epoch.
type EpochResult struct {
	EpochName    string
	StartTick    int
	EndTick      int
	Temperature  float64
	ParticleCount int
	AtomCount    int
	MoleculeCount int
	CellCount    int
	Events       []string
}

// Universe is the top-level orchestrator that drives the entire simulation
// from the Planck epoch through to the present.
type Universe struct {
	Field     *QuantumField
	Atoms     *AtomicSystem
	Chemistry *ChemicalSystem
	Biosphere *Biosphere
	Env       *Environment

	Age           int // current tick
	ScaleFactor   float64
	Results       []EpochResult
	rng           *rand.Rand

	// Callback invoked after each epoch completes. May be nil.
	OnEpochComplete func(result EpochResult)

	// Callback invoked each simulation tick. May be nil.
	// Receives the current epoch name, epoch index, and tick number.
	OnTick func(epochName string, epochIndex int, tick int)
}

// NewUniverse creates a brand new universe ready for simulation.
func NewUniverse(seed int64) *Universe {
	rng := rand.New(rand.NewSource(seed))
	field := NewQuantumField(TPlanck, rng)
	atoms := NewAtomicSystem(rng)
	chem := NewChemicalSystem(atoms, rng)
	env := NewEnvironment(TPlanck, rng)

	return &Universe{
		Field:       field,
		Atoms:       atoms,
		Chemistry:   chem,
		Env:         env,
		ScaleFactor: 1.0,
		Results:     make([]EpochResult, 0, len(Epochs)),
		rng:         rng,
	}
}

// Run executes the full simulation across all 13 epochs.
func (u *Universe) Run() {
	for i, epoch := range Epochs {
		endTick := PresentEpoch
		if i+1 < len(Epochs) {
			endTick = Epochs[i+1].StartTick
		}
		result := u.simulateEpoch(epoch, endTick, i)
		u.Results = append(u.Results, result)
		if u.OnEpochComplete != nil {
			u.OnEpochComplete(result)
		}
	}
}

// simulateEpoch runs the simulation from the current age to endTick.
func (u *Universe) simulateEpoch(epoch EpochInfo, endTick int, epochIndex int) EpochResult {
	result := EpochResult{
		EpochName: epoch.Name,
		StartTick: epoch.StartTick,
		EndTick:   endTick,
		Events:    make([]string, 0),
	}

	// Determine step size to keep each epoch tractable.
	totalTicks := endTick - epoch.StartTick
	step := 1
	if totalTicks > 500 {
		step = totalTicks / 200
	}
	if step < 1 {
		step = 1
	}

	for tick := epoch.StartTick; tick < endTick; tick += step {
		u.Age = tick
		u.Env.Update(tick)
		u.Field.Temperature = u.Env.Temperature

		switch {
		// --- Planck & Inflation: vacuum fluctuations produce particles ---
		case tick < ElectroweakEpoch:
			for i := 0; i < 5; i++ {
				u.Field.VacuumFluctuation()
			}
			u.Field.Evolve(0.01)
			u.ScaleFactor *= 1.001

		// --- Electroweak: symmetry breaking, more pair production ---
		case tick < QuarkEpoch:
			for i := 0; i < 3; i++ {
				u.Field.VacuumFluctuation()
			}
			// Extra pair production from thermal energy
			energy := u.Env.Temperature * KB * 10
			u.Field.PairProduction(energy)
			u.Field.Evolve(0.01)
			u.Field.Cool(0.999)

		// --- Quark-Gluon Plasma: quarks and gluons free ---
		case tick < HadronEpoch:
			u.Field.VacuumFluctuation()
			u.Field.Evolve(0.01)
			u.Field.Cool(0.999)

		// --- Hadron Epoch: quark confinement ---
		case tick < NucleosynthesisEpoch:
			u.Field.Cool(0.998)
			hadrons := u.Field.QuarkConfinement()
			if len(hadrons) > 0 {
				result.Events = append(result.Events,
					fmt.Sprintf("Quark confinement: %d hadrons formed", len(hadrons)))
			}
			u.Field.Evolve(0.01)

		// --- Big Bang Nucleosynthesis: light nuclei ---
		case tick < RecombinationEpoch:
			u.Field.Cool(0.9995)
			// Count protons & neutrons for nucleosynthesis
			protons, neutrons := 0, 0
			for _, p := range u.Field.Particles {
				if p.Type == ParticleProton {
					protons++
				}
				if p.Type == ParticleNeutron {
					neutrons++
				}
			}
			if protons > 1 && neutrons > 1 {
				newAtoms := u.Atoms.Nucleosynthesis(protons/4, neutrons/4)
				if len(newAtoms) > 0 {
					result.Events = append(result.Events,
						fmt.Sprintf("Nucleosynthesis: %d nuclei formed", len(newAtoms)))
				}
			}

		// --- Recombination: atoms form ---
		case tick < StarFormationEpoch:
			u.Atoms.Temperature = u.Env.Temperature
			newAtoms := u.Atoms.Recombination(u.Field)
			if len(newAtoms) > 0 {
				result.Events = append(result.Events,
					fmt.Sprintf("Recombination: %d atoms formed", len(newAtoms)))
			}

		// --- Star Formation: heavy elements ---
		case tick < SolarSystemEpoch:
			newElements := u.Atoms.StellarNucleosynthesis(TStellarCore)
			if len(newElements) > 0 {
				result.Events = append(result.Events,
					fmt.Sprintf("Stellar nucleosynthesis: %d heavy elements forged", len(newElements)))
			}

		// --- Solar System Formation ---
		case tick < EarthEpoch:
			// Produce some extra atoms for planet building
			if len(u.Atoms.Atoms) < 80 {
				for _, z := range []int{1, 1, 1, 1, 6, 7, 8, 8, 14, 26} {
					u.Atoms.Atoms = append(u.Atoms.Atoms, NewAtom(z, 0))
				}
				result.Events = append(result.Events, "Accretion disk: elements aggregating")
			}

		// --- Earth Formation: chemistry begins ---
		case tick < LifeEpoch:
			// Ensure we have enough CHON atoms for prebiotic chemistry
			if len(u.Atoms.Atoms) < 120 {
				for _, z := range []int{1, 1, 1, 1, 1, 1, 6, 6, 6, 7, 7, 8, 8, 8} {
					u.Atoms.Atoms = append(u.Atoms.Atoms, NewAtom(z, 0))
				}
			}
			waters := u.Chemistry.FormWater()
			if len(waters) > 0 {
				result.Events = append(result.Events,
					fmt.Sprintf("Oceans forming: %d water molecules", len(waters)))
			}
			u.Chemistry.FormMethane()
			u.Chemistry.FormAmmonia()
			u.Chemistry.CatalyzedReaction(u.Env.Temperature, false)

		// --- Life Emergence: first cells ---
		case tick < DNAEpoch:
			// Keep enriching with atoms for amino acids / nucleotides
			if u.rng.Float64() < 0.3 {
				for _, z := range []int{1, 1, 6, 7, 8} {
					u.Atoms.Atoms = append(u.Atoms.Atoms, NewAtom(z, 0))
				}
			}
			u.Chemistry.CatalyzedReaction(u.Env.Temperature, true)

			// Bootstrap biosphere when enough nucleotides exist
			if u.Biosphere == nil && u.Chemistry.NucleotideCount >= 2 {
				u.Biosphere = NewBiosphere(5, 60, u.rng)
				result.Events = append(result.Events,
					"LIFE EMERGES: first protocells self-assemble!")
			}
			if u.Biosphere != nil {
				u.Biosphere.Step(
					u.Env.ThermalEnergy(),
					u.Env.UVIntensity,
					u.Env.CosmicRayFlux,
					u.Env.Temperature,
				)
			}

		// --- DNA Evolution & Present ---
		default:
			if u.Biosphere == nil {
				u.Biosphere = NewBiosphere(5, 60, u.rng)
				result.Events = append(result.Events,
					"LIFE EMERGES: first protocells self-assemble!")
			}
			u.Biosphere.Step(
				u.Env.ThermalEnergy(),
				u.Env.UVIntensity,
				u.Env.CosmicRayFlux,
				u.Env.Temperature,
			)
		}

		if u.OnTick != nil {
			u.OnTick(epoch.Name, epochIndex, tick)
		}
	}

	// Snapshot state at end of epoch
	result.Temperature = u.Env.Temperature
	result.ParticleCount = len(u.Field.Particles)
	result.AtomCount = len(u.Atoms.Atoms)
	result.MoleculeCount = len(u.Chemistry.Molecules)
	if u.Biosphere != nil {
		result.CellCount = len(u.Biosphere.Cells)
	}

	return result
}

// Snapshot captures the current state of the universe for external consumers.
type Snapshot struct {
	Epoch         string       `json:"epoch"`
	EpochIndex    int          `json:"epoch_index"`
	Tick          int          `json:"tick"`
	Temperature   float64      `json:"temperature"`
	Particles     int          `json:"particles"`
	Atoms         int          `json:"atoms"`
	Molecules     int          `json:"molecules"`
	Cells         int          `json:"cells"`
	TotalEpochs   int          `json:"total_epochs"`
	ParticlePos   [][3]float64 `json:"particle_pos,omitempty"`
	ParticleTypes []string     `json:"particle_types,omitempty"`
}

// TakeSnapshot returns a Snapshot of the current universe state.
// If includePositions is true, particle positions and types are included.
func (u *Universe) TakeSnapshot(epochName string, epochIndex int, includePositions bool) Snapshot {
	s := Snapshot{
		Epoch:       epochName,
		EpochIndex:  epochIndex,
		Tick:        u.Age,
		Temperature: u.Env.Temperature,
		Particles:   len(u.Field.Particles),
		Atoms:       len(u.Atoms.Atoms),
		Molecules:   len(u.Chemistry.Molecules),
		TotalEpochs: len(Epochs),
	}
	if u.Biosphere != nil {
		s.Cells = len(u.Biosphere.Cells)
	}
	if includePositions {
		maxParticles := 200
		count := len(u.Field.Particles)
		if count > maxParticles {
			count = maxParticles
		}
		s.ParticlePos = make([][3]float64, count)
		s.ParticleTypes = make([]string, count)
		for i := 0; i < count; i++ {
			s.ParticlePos[i] = u.Field.Particles[i].Position
			s.ParticleTypes[i] = u.Field.Particles[i].Type.String()
		}
	}
	return s
}

// Summary returns a human-readable summary of the simulation.
func (u *Universe) Summary() string {
	s := ""
	s += fmt.Sprintf("Universe age: %d ticks\n", u.Age)
	s += fmt.Sprintf("Particles: %d (created: %d, annihilated: %d)\n",
		len(u.Field.Particles), u.Field.TotalCreated, u.Field.TotalAnnihilated)
	s += fmt.Sprintf("Total field energy: %.2f\n", u.Field.TotalEnergy())
	s += fmt.Sprintf("Atoms: %d\n", len(u.Atoms.Atoms))
	s += fmt.Sprintf("Element census: %v\n", u.Atoms.ElementCounts())
	s += fmt.Sprintf("Molecules: %d (water: %d, amino acids: %d, nucleotides: %d)\n",
		len(u.Chemistry.Molecules), u.Chemistry.WaterCount, u.Chemistry.AminoAcidCount, u.Chemistry.NucleotideCount)
	s += fmt.Sprintf("Chemical reactions: %d\n", u.Chemistry.ReactionsOccurred)
	if u.Biosphere != nil {
		s += fmt.Sprintf("Living cells: %d (born: %d, died: %d)\n",
			len(u.Biosphere.Cells), u.Biosphere.TotalBorn, u.Biosphere.TotalDied)
		s += fmt.Sprintf("Generations: %d\n", u.Biosphere.Generation)
		s += fmt.Sprintf("Average fitness: %.4f\n", u.Biosphere.AverageFitness())
		s += fmt.Sprintf("Average GC content: %.4f\n", u.Biosphere.AverageGCContent())
		s += fmt.Sprintf("Total mutations: %d\n", u.Biosphere.TotalMutations())
	}
	s += fmt.Sprintf("Environment: T=%.2f K, habitable=%v\n", u.Env.Temperature, u.Env.IsHabitable())
	s += fmt.Sprintf("Environmental events witnessed: %d\n", len(u.Env.EventHistory))
	return s
}
