package simulator

import (
	"math"
	"math/rand"
	"sync/atomic"
)

// ElementInfo stores periodic table data for an element.
type ElementInfo struct {
	Symbol            string
	Name              string
	Group             int
	Period            int
	Electronegativity float64
}

// Elements is a partial periodic table.
var Elements = map[int]ElementInfo{
	1:  {"H", "Hydrogen", 1, 1, 2.20},
	2:  {"He", "Helium", 18, 1, 0.0},
	3:  {"Li", "Lithium", 1, 2, 0.98},
	4:  {"Be", "Beryllium", 2, 2, 1.57},
	5:  {"B", "Boron", 13, 2, 2.04},
	6:  {"C", "Carbon", 14, 2, 2.55},
	7:  {"N", "Nitrogen", 15, 2, 3.04},
	8:  {"O", "Oxygen", 16, 2, 3.44},
	9:  {"F", "Fluorine", 17, 2, 3.98},
	10: {"Ne", "Neon", 18, 2, 0.0},
	11: {"Na", "Sodium", 1, 3, 0.93},
	12: {"Mg", "Magnesium", 2, 3, 1.31},
	13: {"Al", "Aluminum", 13, 3, 1.61},
	14: {"Si", "Silicon", 14, 3, 1.90},
	15: {"P", "Phosphorus", 15, 3, 2.19},
	16: {"S", "Sulfur", 16, 3, 2.58},
	17: {"Cl", "Chlorine", 17, 3, 3.16},
	18: {"Ar", "Argon", 18, 3, 0.0},
	19: {"K", "Potassium", 1, 4, 0.82},
	20: {"Ca", "Calcium", 2, 4, 1.00},
	26: {"Fe", "Iron", 8, 4, 1.83},
}

// ElectronShell represents an electron shell with quantum numbers.
type ElectronShell struct {
	N            int // Principal quantum number
	MaxElectrons int
	Electrons    int
}

// Full returns true if the shell is full.
func (s *ElectronShell) Full() bool {
	return s.Electrons >= s.MaxElectrons
}

// atomIDGen is the global atom ID counter.
var atomIDGen atomic.Int64

// Atom represents an atom with protons, neutrons, and electron shells.
type Atom struct {
	AtomicNumber     int
	MassNumber       int
	ElectronCount    int
	Position         [3]float64
	Velocity         [3]float64
	Shells           []ElectronShell
	Bonds            []int64 // IDs of bonded atoms
	ID               int64
	IonizationEnergy float64
}

// NewAtom creates a new atom with the given atomic number and optional mass number.
func NewAtom(atomicNumber, massNumber int) *Atom {
	if massNumber == 0 {
		massNumber = atomicNumber * 2
		if atomicNumber == 1 {
			massNumber = 1
		}
	}
	a := &Atom{
		AtomicNumber:  atomicNumber,
		MassNumber:    massNumber,
		ElectronCount: atomicNumber, // neutral atom
		ID:            atomIDGen.Add(1),
		Bonds:         make([]int64, 0),
	}
	a.buildShells()
	a.computeIonizationEnergy()
	return a
}

func (a *Atom) buildShells() {
	a.Shells = nil
	remaining := a.ElectronCount
	for i, maxE := range ElectronShells {
		if remaining <= 0 {
			break
		}
		e := remaining
		if e > maxE {
			e = maxE
		}
		a.Shells = append(a.Shells, ElectronShell{
			N:            i + 1,
			MaxElectrons: maxE,
			Electrons:    e,
		})
		remaining -= e
	}
}

func (a *Atom) computeIonizationEnergy() {
	if len(a.Shells) == 0 || a.Shells[len(a.Shells)-1].Electrons == 0 {
		a.IonizationEnergy = 0.0
		return
	}
	n := float64(a.Shells[len(a.Shells)-1].N)
	innerE := 0
	for i := 0; i < len(a.Shells)-1; i++ {
		innerE += a.Shells[i].Electrons
	}
	zEff := float64(a.AtomicNumber - innerE)
	a.IonizationEnergy = 13.6 * zEff * zEff / (n * n)
}

// Symbol returns the element symbol.
func (a *Atom) Symbol() string {
	if elem, ok := Elements[a.AtomicNumber]; ok {
		return elem.Symbol
	}
	return "?"
}

// Electronegativity returns the electronegativity of the atom.
func (a *Atom) Electronegativity() float64 {
	if elem, ok := Elements[a.AtomicNumber]; ok {
		return elem.Electronegativity
	}
	return 1.0
}

// Charge returns the net charge of the atom.
func (a *Atom) Charge() int {
	return a.AtomicNumber - a.ElectronCount
}

// ValenceElectrons returns valence electrons.
func (a *Atom) ValenceElectrons() int {
	if len(a.Shells) == 0 {
		return 0
	}
	return a.Shells[len(a.Shells)-1].Electrons
}

// IsNobleGas returns true if the outermost shell is full.
func (a *Atom) IsNobleGas() bool {
	if len(a.Shells) == 0 {
		return false
	}
	return a.Shells[len(a.Shells)-1].Full()
}

// CanBondWith checks if bonding is possible with another atom.
func (a *Atom) CanBondWith(other *Atom) bool {
	if a.IsNobleGas() || other.IsNobleGas() {
		return false
	}
	if len(a.Bonds) >= 4 || len(other.Bonds) >= 4 {
		return false
	}
	return true
}

// BondType determines bond type based on electronegativity difference.
func (a *Atom) BondType(other *Atom) string {
	diff := math.Abs(a.Electronegativity() - other.Electronegativity())
	if diff > 1.7 {
		return "ionic"
	} else if diff > 0.4 {
		return "polar_covalent"
	}
	return "covalent"
}

// BondEnergy calculates bond energy.
func (a *Atom) BondEnergy(other *Atom) float64 {
	btype := a.BondType(other)
	switch btype {
	case "ionic":
		return BondEnergyIonic
	case "polar_covalent":
		return (BondEnergyCovalent + BondEnergyIonic) / 2
	default:
		return BondEnergyCovalent
	}
}

// DistanceTo returns Euclidean distance to another atom.
func (a *Atom) DistanceTo(other *Atom) float64 {
	dx := a.Position[0] - other.Position[0]
	dy := a.Position[1] - other.Position[1]
	dz := a.Position[2] - other.Position[2]
	return math.Sqrt(dx*dx + dy*dy + dz*dz)
}

// HasBondWith returns true if a bond exists with the given atom ID.
func (a *Atom) HasBondWith(id int64) bool {
	for _, b := range a.Bonds {
		if b == id {
			return true
		}
	}
	return false
}

// RemoveBond removes a bond by atom ID.
func (a *Atom) RemoveBond(id int64) {
	for i, b := range a.Bonds {
		if b == id {
			a.Bonds = append(a.Bonds[:i], a.Bonds[i+1:]...)
			return
		}
	}
}

// AtomicSystem is a collection of atoms with interactions.
type AtomicSystem struct {
	Atoms        []*Atom
	Temperature  float64
	BondsFormed  int
	BondsBroken  int
	rng          *rand.Rand
}

// NewAtomicSystem creates a new atomic system.
func NewAtomicSystem(rng *rand.Rand) *AtomicSystem {
	return &AtomicSystem{
		Atoms:       make([]*Atom, 0, 128),
		Temperature: TRecombination,
		rng:         rng,
	}
}

// Recombination captures free electrons into ions when T < T_recombination.
func (as *AtomicSystem) Recombination(field *QuantumField) []*Atom {
	if as.Temperature > TRecombination {
		return nil
	}

	var newAtoms []*Atom
	var protons []*Particle
	var electrons []*Particle
	for _, p := range field.Particles {
		switch p.Type {
		case ParticleProton:
			protons = append(protons, p)
		case ParticleElectron:
			electrons = append(electrons, p)
		}
	}

	for _, proton := range protons {
		if len(electrons) == 0 {
			break
		}
		electron := electrons[len(electrons)-1]
		electrons = electrons[:len(electrons)-1]

		atom := NewAtom(1, 1)
		atom.Position = proton.Position
		atom.Velocity = proton.Momentum

		newAtoms = append(newAtoms, atom)
		as.Atoms = append(as.Atoms, atom)

		field.removeParticle(proton)
		field.removeParticle(electron)
	}

	return newAtoms
}

// Nucleosynthesis forms heavier elements through nuclear fusion.
func (as *AtomicSystem) Nucleosynthesis(protons, neutrons int) []*Atom {
	var newAtoms []*Atom

	// Helium-4: 2 protons + 2 neutrons
	for protons >= 2 && neutrons >= 2 {
		he := NewAtom(2, 4)
		he.Position = [3]float64{as.rng.NormFloat64() * 10, as.rng.NormFloat64() * 10, as.rng.NormFloat64() * 10}
		newAtoms = append(newAtoms, he)
		as.Atoms = append(as.Atoms, he)
		protons -= 2
		neutrons -= 2
	}

	// Remaining protons become hydrogen
	for i := 0; i < protons; i++ {
		h := NewAtom(1, 1)
		h.Position = [3]float64{as.rng.NormFloat64() * 10, as.rng.NormFloat64() * 10, as.rng.NormFloat64() * 10}
		newAtoms = append(newAtoms, h)
		as.Atoms = append(as.Atoms, h)
	}

	return newAtoms
}

// StellarNucleosynthesis forms heavier elements in stellar cores.
func (as *AtomicSystem) StellarNucleosynthesis(temperature float64) []*Atom {
	var newAtoms []*Atom
	if temperature < 1e3 {
		return newAtoms
	}

	// Collect heliums
	var heliumIdx []int
	for i, a := range as.Atoms {
		if a.AtomicNumber == 2 {
			heliumIdx = append(heliumIdx, i)
		}
	}

	// Triple-alpha process: 3 He -> C
	for len(heliumIdx) >= 3 && as.rng.Float64() < 0.01 {
		// Remove 3 heliums (iterate from end to preserve indices)
		toRemove := heliumIdx[len(heliumIdx)-3:]
		heliumIdx = heliumIdx[:len(heliumIdx)-3]
		// Remove in reverse order to keep indices valid
		for i := len(toRemove) - 1; i >= 0; i-- {
			idx := toRemove[i]
			as.Atoms = append(as.Atoms[:idx], as.Atoms[idx+1:]...)
		}

		carbon := NewAtom(6, 12)
		carbon.Position = [3]float64{as.rng.NormFloat64() * 5, as.rng.NormFloat64() * 5, as.rng.NormFloat64() * 5}
		newAtoms = append(newAtoms, carbon)
		as.Atoms = append(as.Atoms, carbon)
	}

	// C + He -> O
	for as.rng.Float64() < 0.02 {
		ci, hi := -1, -1
		for i, a := range as.Atoms {
			if a.AtomicNumber == 6 && ci == -1 {
				ci = i
			}
			if a.AtomicNumber == 2 && hi == -1 {
				hi = i
			}
		}
		if ci == -1 || hi == -1 {
			break
		}

		pos := as.Atoms[ci].Position
		// Remove in correct order
		if ci > hi {
			as.Atoms = append(as.Atoms[:ci], as.Atoms[ci+1:]...)
			as.Atoms = append(as.Atoms[:hi], as.Atoms[hi+1:]...)
		} else {
			as.Atoms = append(as.Atoms[:hi], as.Atoms[hi+1:]...)
			as.Atoms = append(as.Atoms[:ci], as.Atoms[ci+1:]...)
		}

		oxygen := NewAtom(8, 16)
		oxygen.Position = pos
		newAtoms = append(newAtoms, oxygen)
		as.Atoms = append(as.Atoms, oxygen)
	}

	// O + He -> N (simplified fusion chain)
	if as.rng.Float64() < 0.005 {
		oi, hi := -1, -1
		for i, a := range as.Atoms {
			if a.AtomicNumber == 8 && oi == -1 {
				oi = i
			}
			if a.AtomicNumber == 2 && hi == -1 {
				hi = i
			}
		}
		if oi != -1 && hi != -1 {
			pos := as.Atoms[oi].Position
			if oi > hi {
				as.Atoms = append(as.Atoms[:oi], as.Atoms[oi+1:]...)
				as.Atoms = append(as.Atoms[:hi], as.Atoms[hi+1:]...)
			} else {
				as.Atoms = append(as.Atoms[:hi], as.Atoms[hi+1:]...)
				as.Atoms = append(as.Atoms[:oi], as.Atoms[oi+1:]...)
			}

			nitrogen := NewAtom(7, 14)
			nitrogen.Position = pos
			newAtoms = append(newAtoms, nitrogen)
			as.Atoms = append(as.Atoms, nitrogen)
		}
	}

	return newAtoms
}

// ElementCounts returns atom counts by element symbol.
func (as *AtomicSystem) ElementCounts() map[string]int {
	counts := make(map[string]int)
	for _, a := range as.Atoms {
		counts[a.Symbol()]++
	}
	return counts
}
