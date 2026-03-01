package simulator

import (
	"math"
	"math/rand"
	"sync/atomic"
)

// moleculeIDGen is the global molecule ID counter.
var moleculeIDGen atomic.Int64

// Molecule represents a collection of bonded atoms.
type Molecule struct {
	Atoms            []*Atom
	Name             string
	Formula          string
	ID               int64
	Energy           float64
	Position         [3]float64
	IsOrganic        bool
	FunctionalGroups []string
}

// NewMolecule creates a new molecule.
func NewMolecule(atoms []*Atom, name string) *Molecule {
	m := &Molecule{
		Atoms:            atoms,
		Name:             name,
		ID:               moleculeIDGen.Add(1),
		FunctionalGroups: make([]string, 0),
	}
	if len(atoms) > 0 {
		m.Position = atoms[0].Position
	}
	m.computeFormula()
	return m
}

func (m *Molecule) computeFormula() {
	counts := make(map[string]int)
	for _, a := range m.Atoms {
		counts[a.Symbol()]++
	}

	hasC := false
	hasH := false
	for _, a := range m.Atoms {
		if a.AtomicNumber == 6 {
			hasC = true
		}
		if a.AtomicNumber == 1 {
			hasH = true
		}
	}
	m.IsOrganic = hasC && hasH

	if m.Formula != "" {
		return
	}

	formula := ""
	// Standard chemistry ordering: C, H, then alphabetical
	for _, sym := range []string{"C", "H"} {
		if n, ok := counts[sym]; ok {
			if n > 1 {
				formula += sym + string(rune('0'+n)) // simplified for small counts
			} else {
				formula += sym
			}
			delete(counts, sym)
		}
	}
	// Remaining alphabetical
	for sym, n := range counts {
		if n > 1 {
			formula += sym + string(rune('0'+n))
		} else {
			formula += sym
		}
	}
	m.Formula = formula
}

// MolecularWeight returns the sum of atom mass numbers.
func (m *Molecule) MolecularWeight() int {
	w := 0
	for _, a := range m.Atoms {
		w += a.MassNumber
	}
	return w
}

// ChemicalSystem manages molecular assembly and chemical reactions.
type ChemicalSystem struct {
	Atomic           *AtomicSystem
	Molecules        []*Molecule
	ReactionsOccurred int
	WaterCount       int
	AminoAcidCount   int
	NucleotideCount  int
	rng              *rand.Rand
}

// NewChemicalSystem creates a new chemical system.
func NewChemicalSystem(atomicSystem *AtomicSystem, rng *rand.Rand) *ChemicalSystem {
	return &ChemicalSystem{
		Atomic:    atomicSystem,
		Molecules: make([]*Molecule, 0, 64),
		rng:       rng,
	}
}

// unbondedAtoms returns atoms of a given atomic number that have no bonds (or fewer than maxBonds).
func (cs *ChemicalSystem) unbondedAtoms(atomicNumber int, maxBonds int) []*Atom {
	var result []*Atom
	for _, a := range cs.Atomic.Atoms {
		if a.AtomicNumber == atomicNumber && len(a.Bonds) < maxBonds {
			result = append(result, a)
		}
	}
	return result
}

// FormWater forms water molecules: 2H + O -> H2O.
func (cs *ChemicalSystem) FormWater() []*Molecule {
	var waters []*Molecule
	hydrogens := cs.unbondedAtoms(1, 1)  // H with 0 bonds
	oxygens := cs.unbondedAtoms(8, 2)     // O with < 2 bonds

	for len(hydrogens) >= 2 && len(oxygens) > 0 {
		h1 := hydrogens[len(hydrogens)-1]
		hydrogens = hydrogens[:len(hydrogens)-1]
		h2 := hydrogens[len(hydrogens)-1]
		hydrogens = hydrogens[:len(hydrogens)-1]
		o := oxygens[len(oxygens)-1]
		oxygens = oxygens[:len(oxygens)-1]

		water := NewMolecule([]*Atom{h1, h2, o}, "water")
		water.Position = o.Position
		waters = append(waters, water)
		cs.Molecules = append(cs.Molecules, water)
		cs.WaterCount++

		h1.Bonds = append(h1.Bonds, o.ID)
		h2.Bonds = append(h2.Bonds, o.ID)
		o.Bonds = append(o.Bonds, h1.ID, h2.ID)
	}

	return waters
}

// FormMethane forms methane: C + 4H -> CH4.
func (cs *ChemicalSystem) FormMethane() []*Molecule {
	var methanes []*Molecule
	carbons := cs.unbondedAtoms(6, 1)
	hydrogens := cs.unbondedAtoms(1, 1)

	for len(carbons) > 0 && len(hydrogens) >= 4 {
		c := carbons[len(carbons)-1]
		carbons = carbons[:len(carbons)-1]

		hs := make([]*Atom, 4)
		for i := 0; i < 4; i++ {
			hs[i] = hydrogens[len(hydrogens)-1]
			hydrogens = hydrogens[:len(hydrogens)-1]
		}

		atoms := append([]*Atom{c}, hs...)
		methane := NewMolecule(atoms, "methane")
		methane.Position = c.Position
		methanes = append(methanes, methane)
		cs.Molecules = append(cs.Molecules, methane)

		for _, h := range hs {
			c.Bonds = append(c.Bonds, h.ID)
			h.Bonds = append(h.Bonds, c.ID)
		}
	}

	return methanes
}

// FormAmmonia forms ammonia: N + 3H -> NH3.
func (cs *ChemicalSystem) FormAmmonia() []*Molecule {
	var ammonias []*Molecule
	nitrogens := cs.unbondedAtoms(7, 1)
	hydrogens := cs.unbondedAtoms(1, 1)

	for len(nitrogens) > 0 && len(hydrogens) >= 3 {
		n := nitrogens[len(nitrogens)-1]
		nitrogens = nitrogens[:len(nitrogens)-1]

		hs := make([]*Atom, 3)
		for i := 0; i < 3; i++ {
			hs[i] = hydrogens[len(hydrogens)-1]
			hydrogens = hydrogens[:len(hydrogens)-1]
		}

		atoms := append([]*Atom{n}, hs...)
		ammonia := NewMolecule(atoms, "ammonia")
		ammonia.Position = n.Position
		ammonias = append(ammonias, ammonia)
		cs.Molecules = append(cs.Molecules, ammonia)

		for _, h := range hs {
			n.Bonds = append(n.Bonds, h.ID)
			h.Bonds = append(h.Bonds, n.ID)
		}
	}

	return ammonias
}

// FormAminoAcid forms an amino acid from available atoms (simplified).
// Requires 2C + 5H + 2O + 1N minimum (glycine).
func (cs *ChemicalSystem) FormAminoAcid(aaType string) *Molecule {
	carbons := cs.unbondedAtoms(6, 1)
	hydrogens := cs.unbondedAtoms(1, 1)
	oxygens := cs.unbondedAtoms(8, 2)
	nitrogens := cs.unbondedAtoms(7, 1)

	if len(carbons) < 2 || len(hydrogens) < 5 || len(oxygens) < 2 || len(nitrogens) < 1 {
		return nil
	}

	atoms := make([]*Atom, 0, 10)
	for i := 0; i < 2; i++ {
		atoms = append(atoms, carbons[len(carbons)-1])
		carbons = carbons[:len(carbons)-1]
	}
	for i := 0; i < 5; i++ {
		atoms = append(atoms, hydrogens[len(hydrogens)-1])
		hydrogens = hydrogens[:len(hydrogens)-1]
	}
	for i := 0; i < 2; i++ {
		atoms = append(atoms, oxygens[len(oxygens)-1])
		oxygens = oxygens[:len(oxygens)-1]
	}
	atoms = append(atoms, nitrogens[len(nitrogens)-1])

	aa := NewMolecule(atoms, aaType)
	aa.Position = atoms[0].Position
	aa.IsOrganic = true
	aa.FunctionalGroups = []string{"amino", "carboxyl"}
	cs.Molecules = append(cs.Molecules, aa)
	cs.AminoAcidCount++

	// Form internal bonds
	for i := 1; i < len(atoms); i++ {
		atoms[0].Bonds = append(atoms[0].Bonds, atoms[i].ID)
		atoms[i].Bonds = append(atoms[i].Bonds, atoms[0].ID)
	}

	return aa
}

// FormNucleotide forms a nucleotide (sugar + phosphate + base).
// Simplified: requires C5 + H8 + O4 + N2 minimum.
func (cs *ChemicalSystem) FormNucleotide(base string) *Molecule {
	carbons := cs.unbondedAtoms(6, 1)
	hydrogens := cs.unbondedAtoms(1, 1)
	oxygens := cs.unbondedAtoms(8, 2)
	nitrogens := cs.unbondedAtoms(7, 1)

	if len(carbons) < 5 || len(hydrogens) < 8 || len(oxygens) < 4 || len(nitrogens) < 2 {
		return nil
	}

	atoms := make([]*Atom, 0, 19)
	for i := 0; i < 5; i++ {
		atoms = append(atoms, carbons[len(carbons)-1])
		carbons = carbons[:len(carbons)-1]
	}
	for i := 0; i < 8; i++ {
		atoms = append(atoms, hydrogens[len(hydrogens)-1])
		hydrogens = hydrogens[:len(hydrogens)-1]
	}
	for i := 0; i < 4; i++ {
		atoms = append(atoms, oxygens[len(oxygens)-1])
		oxygens = oxygens[:len(oxygens)-1]
	}
	for i := 0; i < 2; i++ {
		atoms = append(atoms, nitrogens[len(nitrogens)-1])
		nitrogens = nitrogens[:len(nitrogens)-1]
	}

	nuc := NewMolecule(atoms, "nucleotide-"+base)
	nuc.Position = atoms[0].Position
	nuc.IsOrganic = true
	nuc.FunctionalGroups = []string{"sugar", "phosphate", "base"}
	cs.Molecules = append(cs.Molecules, nuc)
	cs.NucleotideCount++

	for i := 1; i < len(atoms); i++ {
		atoms[0].Bonds = append(atoms[0].Bonds, atoms[i].ID)
		atoms[i].Bonds = append(atoms[i].Bonds, atoms[0].ID)
	}

	return nuc
}

// CatalyzedReaction runs catalyzed reactions to form complex molecules.
func (cs *ChemicalSystem) CatalyzedReaction(temperature float64, catalystPresent bool) int {
	formed := 0
	eaFactor := 1.0
	if catalystPresent {
		eaFactor = 0.3
	}

	thermal := KB * temperature

	// Try to form amino acids
	if thermal > 0 && len(cs.Atomic.Atoms) > 10 {
		aaProb := math.Exp(-5.0 * eaFactor / (thermal + 1e-20))
		if cs.rng.Float64() < aaProb {
			aaType := AminoAcids[cs.rng.Intn(len(AminoAcids))]
			if cs.FormAminoAcid(aaType) != nil {
				formed++
				cs.ReactionsOccurred++
			}
		}
	}

	// Try to form nucleotides
	if thermal > 0 && len(cs.Atomic.Atoms) > 19 {
		nucProb := math.Exp(-8.0 * eaFactor / (thermal + 1e-20))
		if cs.rng.Float64() < nucProb {
			bases := []string{"A", "T", "G", "C"}
			base := bases[cs.rng.Intn(len(bases))]
			if cs.FormNucleotide(base) != nil {
				formed++
				cs.ReactionsOccurred++
			}
		}
	}

	return formed
}

// MoleculeCensus returns molecule counts by type name.
func (cs *ChemicalSystem) MoleculeCensus() map[string]int {
	counts := make(map[string]int)
	for _, m := range cs.Molecules {
		key := m.Name
		if key == "" {
			key = m.Formula
		}
		counts[key]++
	}
	return counts
}
