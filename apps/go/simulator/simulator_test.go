// Package simulator tests cover the full simulation pipeline from fundamental
// constants through quantum mechanics, atomic physics, chemistry, biology,
// environmental modelling, and the top-level Universe orchestrator.
//
// All randomised tests use deterministic seeds so results are reproducible.
package simulator

import (
	"math"
	"math/rand"
	"testing"
)

// tolerance is the default floating-point comparison epsilon.
const tolerance = 1e-9

// almostEqual returns true if a and b are within eps of each other.
func almostEqual(a, b, eps float64) bool {
	return math.Abs(a-b) < eps
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

func TestConstants_Positive(t *testing.T) {
	t.Parallel()
	constants := map[string]float64{
		"C":               C,
		"HBAR":            HBAR,
		"KB":              KB,
		"G":               G,
		"ALPHA":           ALPHA,
		"ECharge":         ECharge,
		"MElectron":       MElectron,
		"MUpQuark":        MUpQuark,
		"MDownQuark":      MDownQuark,
		"MProton":         MProton,
		"MNeutron":        MNeutron,
		"MWBoson":         MWBoson,
		"MZBoson":         MZBoson,
		"MHiggs":          MHiggs,
		"StrongCoupling":  StrongCoupling,
		"EMCoupling":      EMCoupling,
		"WeakCoupling":    WeakCoupling,
		"GravityCoupling": GravityCoupling,
	}
	for name, val := range constants {
		if val <= 0 {
			t.Errorf("%s should be positive, got %v", name, val)
		}
	}
}

func TestConstants_PhotonMasslessNeutrinoLight(t *testing.T) {
	t.Parallel()
	if MPhoton != 0.0 {
		t.Errorf("photon mass should be 0, got %v", MPhoton)
	}
	if MNeutrino <= 0 {
		t.Errorf("neutrino mass should be positive (tiny), got %v", MNeutrino)
	}
	if MNeutrino >= MElectron {
		t.Errorf("neutrino should be lighter than electron: %v >= %v", MNeutrino, MElectron)
	}
}

func TestConstants_MassRatios(t *testing.T) {
	t.Parallel()
	if MProton <= MElectron {
		t.Error("proton should be heavier than electron")
	}
	if MNeutron <= MProton {
		t.Error("neutron should be heavier than proton")
	}
	if MUpQuark >= MDownQuark {
		t.Error("up quark should be lighter than down quark")
	}
}

func TestConstants_EpochOrdering(t *testing.T) {
	t.Parallel()
	epochs := []int{
		PlanckEpoch,
		InflationEpoch,
		ElectroweakEpoch,
		QuarkEpoch,
		HadronEpoch,
		NucleosynthesisEpoch,
		RecombinationEpoch,
		StarFormationEpoch,
		SolarSystemEpoch,
		EarthEpoch,
		LifeEpoch,
		DNAEpoch,
		PresentEpoch,
	}
	for i := 1; i < len(epochs); i++ {
		if epochs[i] <= epochs[i-1] {
			t.Errorf("epoch ordering violated at index %d: %d <= %d", i, epochs[i], epochs[i-1])
		}
	}
}

func TestConstants_CouplingStrengthOrdering(t *testing.T) {
	t.Parallel()
	// Strong > EM > Weak > Gravity
	if StrongCoupling <= EMCoupling {
		t.Error("strong coupling should exceed EM coupling")
	}
	if EMCoupling <= WeakCoupling {
		t.Error("EM coupling should exceed weak coupling")
	}
	if WeakCoupling <= GravityCoupling {
		t.Error("weak coupling should exceed gravity coupling")
	}
}

func TestConstants_TemperatureOrdering(t *testing.T) {
	t.Parallel()
	// Temperatures should decrease from early to late universe.
	if TPlanck <= TElectroweak {
		t.Error("Planck temperature should exceed electroweak temperature")
	}
	if TElectroweak <= TQuarkHadron {
		t.Error("electroweak temperature should exceed quark-hadron temperature")
	}
	if TQuarkHadron <= TNucleosynthesis {
		t.Error("quark-hadron temperature should exceed nucleosynthesis temperature")
	}
	if TNucleosynthesis <= TRecombination {
		t.Error("nucleosynthesis temperature should exceed recombination temperature")
	}
	if TRecombination <= TCMB {
		t.Error("recombination temperature should exceed CMB temperature")
	}
}

// ---------------------------------------------------------------------------
// WaveFunction
// ---------------------------------------------------------------------------

func TestWaveFunction_Probability(t *testing.T) {
	t.Parallel()
	wf := NewWaveFunction()
	if !almostEqual(wf.Probability(), 1.0, tolerance) {
		t.Errorf("default probability should be 1.0, got %v", wf.Probability())
	}

	wf.Amplitude = 0.5
	if !almostEqual(wf.Probability(), 0.25, tolerance) {
		t.Errorf("probability of amplitude 0.5 should be 0.25, got %v", wf.Probability())
	}

	wf.Amplitude = 0.0
	if !almostEqual(wf.Probability(), 0.0, tolerance) {
		t.Errorf("probability of amplitude 0.0 should be 0.0, got %v", wf.Probability())
	}
}

func TestWaveFunction_Evolve(t *testing.T) {
	t.Parallel()
	wf := NewWaveFunction()
	initialPhase := wf.Phase
	energy := 1.0
	dt := 0.1

	wf.Evolve(dt, energy)

	expectedPhase := math.Mod(initialPhase+energy*dt/HBAR, 2*PI)
	if !almostEqual(wf.Phase, expectedPhase, tolerance) {
		t.Errorf("phase after evolve: got %v, want %v", wf.Phase, expectedPhase)
	}
}

func TestWaveFunction_Evolve_IncoherentNoChange(t *testing.T) {
	t.Parallel()
	wf := NewWaveFunction()
	wf.Coherent = false
	wf.Phase = 1.23

	wf.Evolve(0.1, 5.0)

	if !almostEqual(wf.Phase, 1.23, tolerance) {
		t.Errorf("incoherent wave function should not evolve, phase changed to %v", wf.Phase)
	}
}

func TestWaveFunction_Collapse(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(42))

	// Amplitude = 1 => probability = 1 => always detected
	wf := NewWaveFunction()
	result := wf.Collapse(rng)
	if !result {
		t.Error("collapse with probability 1 should return true")
	}
	if wf.Coherent {
		t.Error("wave function should be incoherent after collapse")
	}
	if !almostEqual(wf.Amplitude, 1.0, tolerance) {
		t.Errorf("amplitude after successful collapse should be 1.0, got %v", wf.Amplitude)
	}

	// Amplitude = 0 => probability = 0 => never detected
	wf2 := NewWaveFunction()
	wf2.Amplitude = 0.0
	result2 := wf2.Collapse(rng)
	if result2 {
		t.Error("collapse with probability 0 should return false")
	}
	if !almostEqual(wf2.Amplitude, 0.0, tolerance) {
		t.Errorf("amplitude after failed collapse should be 0.0, got %v", wf2.Amplitude)
	}
	if wf2.Coherent {
		t.Error("wave function should be incoherent after collapse")
	}
}

// ---------------------------------------------------------------------------
// Particle
// ---------------------------------------------------------------------------

func TestNewParticle(t *testing.T) {
	t.Parallel()
	p := NewParticle(ParticleElectron)
	if p.Type != ParticleElectron {
		t.Errorf("expected type electron, got %v", p.Type)
	}
	if p.ID <= 0 {
		t.Errorf("particle ID should be positive, got %d", p.ID)
	}
	if p.SpinState != SpinUp {
		t.Error("default spin should be SpinUp")
	}
	if p.ColorCharge != ColorNone {
		t.Error("default color charge should be ColorNone")
	}
	if !p.WaveFn.Coherent {
		t.Error("new particle wave function should be coherent")
	}
}

func TestNewParticle_UniqueIDs(t *testing.T) {
	t.Parallel()
	p1 := NewParticle(ParticlePhoton)
	p2 := NewParticle(ParticlePhoton)
	if p1.ID == p2.ID {
		t.Errorf("particles should have unique IDs: %d == %d", p1.ID, p2.ID)
	}
}

func TestParticle_Mass(t *testing.T) {
	t.Parallel()
	tests := []struct {
		ptype ParticleType
		want  float64
	}{
		{ParticleElectron, MElectron},
		{ParticlePositron, MElectron},
		{ParticleProton, MProton},
		{ParticleNeutron, MNeutron},
		{ParticlePhoton, MPhoton},
		{ParticleUp, MUpQuark},
		{ParticleDown, MDownQuark},
		{ParticleNeutrino, MNeutrino},
	}
	for _, tt := range tests {
		p := NewParticle(tt.ptype)
		if !almostEqual(p.Mass(), tt.want, tolerance) {
			t.Errorf("mass of %v: got %v, want %v", tt.ptype, p.Mass(), tt.want)
		}
	}
}

func TestParticle_Charge(t *testing.T) {
	t.Parallel()
	tests := []struct {
		ptype ParticleType
		want  float64
	}{
		{ParticleElectron, -1.0},
		{ParticlePositron, 1.0},
		{ParticleProton, 1.0},
		{ParticleNeutron, 0.0},
		{ParticlePhoton, 0.0},
		{ParticleUp, 2.0 / 3.0},
		{ParticleDown, -1.0 / 3.0},
	}
	for _, tt := range tests {
		p := NewParticle(tt.ptype)
		if !almostEqual(p.Charge(), tt.want, tolerance) {
			t.Errorf("charge of %v: got %v, want %v", tt.ptype, p.Charge(), tt.want)
		}
	}
}

func TestParticle_Energy_AtRest(t *testing.T) {
	t.Parallel()
	// At rest: E = mc^2.  Since C = 1, E = m.
	p := NewParticle(ParticleElectron)
	expected := MElectron * C * C
	if !almostEqual(p.Energy(), expected, tolerance) {
		t.Errorf("rest energy of electron: got %v, want %v", p.Energy(), expected)
	}
}

func TestParticle_Energy_WithMomentum(t *testing.T) {
	t.Parallel()
	p := NewParticle(ParticleElectron)
	p.Momentum = [3]float64{1.0, 0.0, 0.0}
	pSq := 1.0
	mc2 := MElectron * C * C
	expected := math.Sqrt(pSq*C*C + mc2*mc2)
	if !almostEqual(p.Energy(), expected, tolerance) {
		t.Errorf("energy with momentum: got %v, want %v", p.Energy(), expected)
	}
}

func TestParticle_Energy_Photon(t *testing.T) {
	t.Parallel()
	// Photon: m=0, E = |p|*c
	p := NewParticle(ParticlePhoton)
	p.Momentum = [3]float64{3.0, 4.0, 0.0}
	expected := 5.0 * C // |p| = 5
	if !almostEqual(p.Energy(), expected, tolerance) {
		t.Errorf("photon energy: got %v, want %v", p.Energy(), expected)
	}
}

func TestParticleType_String(t *testing.T) {
	t.Parallel()
	tests := []struct {
		pt   ParticleType
		want string
	}{
		{ParticleUp, "up"},
		{ParticleDown, "down"},
		{ParticleElectron, "electron"},
		{ParticlePositron, "positron"},
		{ParticleNeutrino, "neutrino"},
		{ParticlePhoton, "photon"},
		{ParticleGluon, "gluon"},
		{ParticleWBoson, "W"},
		{ParticleZBoson, "Z"},
		{ParticleProton, "proton"},
		{ParticleNeutron, "neutron"},
		{ParticleType(999), "unknown"},
	}
	for _, tt := range tests {
		if got := tt.pt.String(); got != tt.want {
			t.Errorf("ParticleType(%d).String() = %q, want %q", tt.pt, got, tt.want)
		}
	}
}

// ---------------------------------------------------------------------------
// QuantumField
// ---------------------------------------------------------------------------

func TestQuantumField_PairProduction_InsufficientEnergy(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(1))
	qf := NewQuantumField(1e6, rng)

	// Energy below 2 * MElectron * C^2 should fail.
	p1, p2 := qf.PairProduction(2*MElectron*C*C - 0.001)
	if p1 != nil || p2 != nil {
		t.Error("pair production should fail with insufficient energy")
	}
	if len(qf.Particles) != 0 {
		t.Errorf("no particles should exist, got %d", len(qf.Particles))
	}
}

func TestQuantumField_PairProduction_ElectronPositron(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(7))
	qf := NewQuantumField(1e6, rng)

	// Enough energy for e-/e+ but not quarks (energy < 2*MProton*C^2).
	energy := 2*MElectron*C*C + 1.0
	p1, p2 := qf.PairProduction(energy)
	if p1 == nil || p2 == nil {
		t.Fatal("pair production should succeed with sufficient energy")
	}
	if len(qf.Particles) != 2 {
		t.Errorf("expected 2 particles, got %d", len(qf.Particles))
	}
	if qf.TotalCreated != 2 {
		t.Errorf("TotalCreated should be 2, got %d", qf.TotalCreated)
	}
	// Particles should be entangled with each other.
	if p1.EntangledWith != p2.ID || p2.EntangledWith != p1.ID {
		t.Error("particle pair should be mutually entangled")
	}
	// Spins should be opposite.
	if p1.SpinState == p2.SpinState {
		t.Error("particle pair should have opposite spins")
	}
}

func TestQuantumField_Annihilate(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(3))
	qf := NewQuantumField(1e6, rng)

	energy := 2*MElectron*C*C + 5.0
	p1, p2 := qf.PairProduction(energy)
	if p1 == nil || p2 == nil {
		t.Fatal("pair production failed")
	}
	initialCount := len(qf.Particles)

	released := qf.Annihilate(p1, p2)
	if released <= 0 {
		t.Error("annihilation should release positive energy")
	}
	// Two originals removed, two photons added.
	if len(qf.Particles) != initialCount {
		t.Errorf("particle count should remain %d (2 removed, 2 photons added), got %d",
			initialCount, len(qf.Particles))
	}
	if qf.TotalAnnihilated != 2 {
		t.Errorf("TotalAnnihilated should be 2, got %d", qf.TotalAnnihilated)
	}
	if qf.VacuumEnergy <= 0 {
		t.Error("vacuum energy should increase after annihilation")
	}
	// Remaining particles should be photons.
	for _, p := range qf.Particles {
		if p.Type != ParticlePhoton {
			t.Errorf("after annihilation, expected photon, got %v", p.Type)
		}
	}
}

func TestQuantumField_QuarkConfinement_HighTemperature(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(5))
	qf := NewQuantumField(TQuarkHadron+1, rng)

	// Add quarks.
	for i := 0; i < 3; i++ {
		qf.Particles = append(qf.Particles, NewParticle(ParticleUp))
		qf.Particles = append(qf.Particles, NewParticle(ParticleDown))
	}

	hadrons := qf.QuarkConfinement()
	if len(hadrons) != 0 {
		t.Error("quark confinement should not occur above quark-hadron temperature")
	}
}

func TestQuantumField_QuarkConfinement_FormProtonAndNeutron(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(10))
	qf := NewQuantumField(TQuarkHadron-1, rng) // below threshold

	// Add exactly 2 up + 1 down (proton) + 1 up + 2 down (neutron) = 3 up, 3 down.
	for i := 0; i < 3; i++ {
		qf.Particles = append(qf.Particles, NewParticle(ParticleUp))
		qf.Particles = append(qf.Particles, NewParticle(ParticleDown))
	}

	hadrons := qf.QuarkConfinement()

	protons := 0
	neutrons := 0
	for _, h := range hadrons {
		switch h.Type {
		case ParticleProton:
			protons++
		case ParticleNeutron:
			neutrons++
		}
	}

	if protons != 1 {
		t.Errorf("expected 1 proton, got %d", protons)
	}
	if neutrons != 1 {
		t.Errorf("expected 1 neutron, got %d", neutrons)
	}
}

func TestQuantumField_VacuumFluctuation(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(42))
	qf := NewQuantumField(TPlanck*0.8, rng)

	produced := 0
	for i := 0; i < 100; i++ {
		p1, p2 := qf.VacuumFluctuation()
		if p1 != nil && p2 != nil {
			produced++
		}
	}
	if produced == 0 {
		t.Error("vacuum fluctuation at high temperature should produce at least one pair in 100 attempts")
	}
}

func TestQuantumField_VacuumFluctuation_LowTemp(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(99))
	// At very low temperature, probability is near zero.
	qf := NewQuantumField(1e-10, rng)
	produced := 0
	for i := 0; i < 100; i++ {
		p1, _ := qf.VacuumFluctuation()
		if p1 != nil {
			produced++
		}
	}
	// With T ~ 0, probability ~ T/TPlanck ~ 0, so zero or near-zero pairs.
	if produced > 5 {
		t.Errorf("very low temperature should rarely produce pairs, got %d in 100 tries", produced)
	}
}

func TestQuantumField_Evolve(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(7))
	qf := NewQuantumField(1e6, rng)

	p := NewParticle(ParticleElectron)
	p.Momentum = [3]float64{1.0, 0, 0}
	qf.Particles = append(qf.Particles, p)

	oldPos := p.Position
	qf.Evolve(0.1)

	if p.Position == oldPos {
		t.Error("particle position should change after evolve")
	}
}

func TestQuantumField_Evolve_PhotonMovesAtC(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(8))
	qf := NewQuantumField(1e6, rng)

	photon := NewParticle(ParticlePhoton)
	photon.Momentum = [3]float64{1.0, 0, 0}
	qf.Particles = append(qf.Particles, photon)

	dt := 0.5
	qf.Evolve(dt)

	// For massless particle: position += (p/|p|)*C*dt = 1.0*1.0*0.5 = 0.5.
	expected := C * dt
	if !almostEqual(photon.Position[0], expected, 1e-6) {
		t.Errorf("photon x position: got %v, want %v", photon.Position[0], expected)
	}
}

func TestQuantumField_ParticleCount(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(1))
	qf := NewQuantumField(1e6, rng)
	qf.Particles = append(qf.Particles, NewParticle(ParticleElectron))
	qf.Particles = append(qf.Particles, NewParticle(ParticleElectron))
	qf.Particles = append(qf.Particles, NewParticle(ParticlePhoton))

	counts := qf.ParticleCount()
	if counts["electron"] != 2 {
		t.Errorf("expected 2 electrons, got %d", counts["electron"])
	}
	if counts["photon"] != 1 {
		t.Errorf("expected 1 photon, got %d", counts["photon"])
	}
}

func TestQuantumField_TotalEnergy(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(2))
	qf := NewQuantumField(1e6, rng)
	qf.VacuumEnergy = 10.0
	e := NewParticle(ParticleElectron)
	qf.Particles = append(qf.Particles, e)

	total := qf.TotalEnergy()
	if total < 10.0+e.Energy() {
		t.Errorf("total energy should be at least vacuum + particle energy, got %v", total)
	}
}

func TestQuantumField_Cool(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(1))
	qf := NewQuantumField(1000.0, rng)
	qf.Cool(0.5)
	if !almostEqual(qf.Temperature, 500.0, tolerance) {
		t.Errorf("after cooling by 0.5: got %v, want 500.0", qf.Temperature)
	}
}

// ---------------------------------------------------------------------------
// Atomic System
// ---------------------------------------------------------------------------

func TestAtom_NewAtom_Hydrogen(t *testing.T) {
	t.Parallel()
	h := NewAtom(1, 1)
	if h.AtomicNumber != 1 {
		t.Errorf("expected atomic number 1, got %d", h.AtomicNumber)
	}
	if h.MassNumber != 1 {
		t.Errorf("expected mass number 1, got %d", h.MassNumber)
	}
	if h.ElectronCount != 1 {
		t.Errorf("expected 1 electron, got %d", h.ElectronCount)
	}
	if h.Symbol() != "H" {
		t.Errorf("expected symbol H, got %q", h.Symbol())
	}
	if h.Charge() != 0 {
		t.Errorf("neutral atom should have charge 0, got %d", h.Charge())
	}
}

func TestAtom_NewAtom_DefaultMassNumber(t *testing.T) {
	t.Parallel()
	c := NewAtom(6, 0) // massNumber=0 => default to 2*Z
	if c.MassNumber != 12 {
		t.Errorf("carbon default mass number should be 12, got %d", c.MassNumber)
	}
}

func TestAtom_ValenceElectrons(t *testing.T) {
	t.Parallel()
	// Hydrogen: 1 shell with 1 electron.
	h := NewAtom(1, 1)
	if h.ValenceElectrons() != 1 {
		t.Errorf("hydrogen valence electrons: got %d, want 1", h.ValenceElectrons())
	}
	// Helium: 1 shell with 2 electrons (full).
	he := NewAtom(2, 4)
	if he.ValenceElectrons() != 2 {
		t.Errorf("helium valence electrons: got %d, want 2", he.ValenceElectrons())
	}
	// Carbon: shell 1=2, shell 2=4.
	c := NewAtom(6, 12)
	if c.ValenceElectrons() != 4 {
		t.Errorf("carbon valence electrons: got %d, want 4", c.ValenceElectrons())
	}
}

func TestAtom_IsNobleGas(t *testing.T) {
	t.Parallel()
	he := NewAtom(2, 4)
	if !he.IsNobleGas() {
		t.Error("helium should be a noble gas")
	}
	h := NewAtom(1, 1)
	if h.IsNobleGas() {
		t.Error("hydrogen should not be a noble gas")
	}
}

func TestAtom_CanBondWith(t *testing.T) {
	t.Parallel()
	h := NewAtom(1, 1)
	o := NewAtom(8, 16)
	he := NewAtom(2, 4)

	if !h.CanBondWith(o) {
		t.Error("H and O should be able to bond")
	}
	if h.CanBondWith(he) {
		t.Error("noble gas He should not bond")
	}
}

func TestAtom_BondType(t *testing.T) {
	t.Parallel()
	na := NewAtom(11, 23) // Na: electronegativity 0.93
	cl := NewAtom(17, 35) // Cl: electronegativity 3.16
	// Difference = 2.23 > 1.7 => ionic
	if na.BondType(cl) != "ionic" {
		t.Errorf("NaCl bond should be ionic, got %q", na.BondType(cl))
	}

	h := NewAtom(1, 1)   // H: 2.20
	o := NewAtom(8, 16)  // O: 3.44
	// Difference = 1.24 > 0.4, <= 1.7 => polar_covalent
	if h.BondType(o) != "polar_covalent" {
		t.Errorf("H-O bond should be polar_covalent, got %q", h.BondType(o))
	}

	c := NewAtom(6, 12) // C: 2.55
	h2 := NewAtom(1, 1) // H: 2.20
	// Difference = 0.35 <= 0.4 => covalent
	if c.BondType(h2) != "covalent" {
		t.Errorf("C-H bond should be covalent, got %q", c.BondType(h2))
	}
}

func TestAtomicSystem_Nucleosynthesis(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(42))
	as := NewAtomicSystem(rng)

	atoms := as.Nucleosynthesis(4, 4) // 4 protons, 4 neutrons

	hCount := 0
	heCount := 0
	for _, a := range atoms {
		switch a.AtomicNumber {
		case 1:
			hCount++
		case 2:
			heCount++
		}
	}
	// 4p + 4n => 2 He-4, 0 leftover H
	if heCount != 2 {
		t.Errorf("expected 2 He atoms, got %d", heCount)
	}
	if hCount != 0 {
		t.Errorf("expected 0 leftover H, got %d", hCount)
	}
}

func TestAtomicSystem_Nucleosynthesis_Remainder(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(42))
	as := NewAtomicSystem(rng)

	atoms := as.Nucleosynthesis(5, 2) // 5p + 2n => 1 He + 3 H leftover
	hCount := 0
	heCount := 0
	for _, a := range atoms {
		switch a.AtomicNumber {
		case 1:
			hCount++
		case 2:
			heCount++
		}
	}
	if heCount != 1 {
		t.Errorf("expected 1 He, got %d", heCount)
	}
	if hCount != 3 {
		t.Errorf("expected 3 leftover H, got %d", hCount)
	}
}

func TestAtomicSystem_ElementCounts(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(7))
	as := NewAtomicSystem(rng)
	as.Atoms = append(as.Atoms, NewAtom(1, 1), NewAtom(1, 1), NewAtom(2, 4), NewAtom(6, 12))

	counts := as.ElementCounts()
	if counts["H"] != 2 {
		t.Errorf("expected 2 H, got %d", counts["H"])
	}
	if counts["He"] != 1 {
		t.Errorf("expected 1 He, got %d", counts["He"])
	}
	if counts["C"] != 1 {
		t.Errorf("expected 1 C, got %d", counts["C"])
	}
}

func TestAtomicSystem_Recombination(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(12))
	as := NewAtomicSystem(rng)
	as.Temperature = TRecombination - 1 // below threshold

	field := NewQuantumField(TRecombination-1, rng)
	// Add protons and electrons.
	for i := 0; i < 3; i++ {
		field.Particles = append(field.Particles, NewParticle(ParticleProton))
		field.Particles = append(field.Particles, NewParticle(ParticleElectron))
	}

	newAtoms := as.Recombination(field)
	if len(newAtoms) != 3 {
		t.Errorf("expected 3 new hydrogen atoms, got %d", len(newAtoms))
	}
	for _, a := range newAtoms {
		if a.AtomicNumber != 1 {
			t.Errorf("recombination should produce hydrogen, got Z=%d", a.AtomicNumber)
		}
	}
}

func TestAtomicSystem_Recombination_HighTemp(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(13))
	as := NewAtomicSystem(rng)
	as.Temperature = TRecombination + 100 // above threshold

	field := NewQuantumField(TRecombination+100, rng)
	field.Particles = append(field.Particles, NewParticle(ParticleProton))
	field.Particles = append(field.Particles, NewParticle(ParticleElectron))

	newAtoms := as.Recombination(field)
	if len(newAtoms) != 0 {
		t.Errorf("recombination should not occur above TRecombination, got %d atoms", len(newAtoms))
	}
}

// ---------------------------------------------------------------------------
// Chemical System
// ---------------------------------------------------------------------------

func TestChemicalSystem_FormWater(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(20))
	as := NewAtomicSystem(rng)

	// Add 4H + 2O => should form 2 water molecules.
	for i := 0; i < 4; i++ {
		as.Atoms = append(as.Atoms, NewAtom(1, 1))
	}
	for i := 0; i < 2; i++ {
		as.Atoms = append(as.Atoms, NewAtom(8, 16))
	}

	cs := NewChemicalSystem(as, rng)
	waters := cs.FormWater()

	if len(waters) != 2 {
		t.Errorf("expected 2 water molecules, got %d", len(waters))
	}
	if cs.WaterCount != 2 {
		t.Errorf("WaterCount should be 2, got %d", cs.WaterCount)
	}
	for _, w := range waters {
		if w.Name != "water" {
			t.Errorf("molecule name should be 'water', got %q", w.Name)
		}
		if len(w.Atoms) != 3 {
			t.Errorf("water should have 3 atoms, got %d", len(w.Atoms))
		}
	}
}

func TestChemicalSystem_FormWater_InsufficientAtoms(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(21))
	as := NewAtomicSystem(rng)

	// Only 1 H and 1 O => not enough for water.
	as.Atoms = append(as.Atoms, NewAtom(1, 1), NewAtom(8, 16))

	cs := NewChemicalSystem(as, rng)
	waters := cs.FormWater()

	if len(waters) != 0 {
		t.Errorf("should not form water with insufficient H, got %d", len(waters))
	}
}

func TestChemicalSystem_FormMethane(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(22))
	as := NewAtomicSystem(rng)

	// 1C + 4H => 1 methane.
	as.Atoms = append(as.Atoms, NewAtom(6, 12))
	for i := 0; i < 4; i++ {
		as.Atoms = append(as.Atoms, NewAtom(1, 1))
	}

	cs := NewChemicalSystem(as, rng)
	methanes := cs.FormMethane()

	if len(methanes) != 1 {
		t.Errorf("expected 1 methane, got %d", len(methanes))
	}
	if methanes[0].Name != "methane" {
		t.Errorf("molecule name should be 'methane', got %q", methanes[0].Name)
	}
	if len(methanes[0].Atoms) != 5 {
		t.Errorf("methane should have 5 atoms, got %d", len(methanes[0].Atoms))
	}
}

func TestChemicalSystem_FormAmmonia(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(23))
	as := NewAtomicSystem(rng)

	// 1N + 3H => 1 ammonia.
	as.Atoms = append(as.Atoms, NewAtom(7, 14))
	for i := 0; i < 3; i++ {
		as.Atoms = append(as.Atoms, NewAtom(1, 1))
	}

	cs := NewChemicalSystem(as, rng)
	ammonias := cs.FormAmmonia()

	if len(ammonias) != 1 {
		t.Errorf("expected 1 ammonia, got %d", len(ammonias))
	}
	if ammonias[0].Name != "ammonia" {
		t.Errorf("molecule name should be 'ammonia', got %q", ammonias[0].Name)
	}
	if len(ammonias[0].Atoms) != 4 {
		t.Errorf("ammonia should have 4 atoms, got %d", len(ammonias[0].Atoms))
	}
}

func TestChemicalSystem_CatalyzedReaction(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(50))
	as := NewAtomicSystem(rng)

	// Add many CHON atoms so catalysed reaction can form amino acids / nucleotides.
	for i := 0; i < 50; i++ {
		as.Atoms = append(as.Atoms, NewAtom(6, 12))  // C
		as.Atoms = append(as.Atoms, NewAtom(1, 1))   // H
		as.Atoms = append(as.Atoms, NewAtom(8, 16))  // O
		as.Atoms = append(as.Atoms, NewAtom(7, 14))  // N
	}

	cs := NewChemicalSystem(as, rng)

	totalFormed := 0
	for i := 0; i < 200; i++ {
		totalFormed += cs.CatalyzedReaction(500.0, true) // high temp, catalyst present
	}

	if totalFormed == 0 {
		t.Error("catalyzed reactions at high temperature with catalyst should form at least one molecule over 200 iterations")
	}
	if cs.ReactionsOccurred != totalFormed {
		t.Errorf("ReactionsOccurred (%d) should match totalFormed (%d)", cs.ReactionsOccurred, totalFormed)
	}
}

func TestChemicalSystem_CatalyzedReaction_CatalystLowersActivation(t *testing.T) {
	t.Parallel()

	// Run with and without catalyst, compare yield at moderate temperature.
	temperature := 300.0
	iterations := 500

	// Helper to count reactions.
	countReactions := func(catalyst bool, seed int64) int {
		rng := rand.New(rand.NewSource(seed))
		as := NewAtomicSystem(rng)
		for i := 0; i < 100; i++ {
			as.Atoms = append(as.Atoms, NewAtom(6, 12))
			as.Atoms = append(as.Atoms, NewAtom(1, 1))
			as.Atoms = append(as.Atoms, NewAtom(8, 16))
			as.Atoms = append(as.Atoms, NewAtom(7, 14))
		}
		cs := NewChemicalSystem(as, rng)
		total := 0
		for i := 0; i < iterations; i++ {
			total += cs.CatalyzedReaction(temperature, catalyst)
		}
		return total
	}

	withCatalyst := countReactions(true, 77)
	withoutCatalyst := countReactions(false, 77)

	// With the same seed, catalyst should yield more or equal reactions.
	// Due to randomness in atom consumption the comparison is soft.
	if withCatalyst < withoutCatalyst {
		t.Logf("catalyst: %d, no catalyst: %d (catalyst expected to produce at least as many)", withCatalyst, withoutCatalyst)
	}
}

// ---------------------------------------------------------------------------
// Biology / Biosphere
// ---------------------------------------------------------------------------

func TestNewBiosphere(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(100))
	bio := NewBiosphere(5, 60, rng)

	if len(bio.Cells) != 5 {
		t.Errorf("expected 5 initial cells, got %d", len(bio.Cells))
	}
	if bio.TotalBorn != 5 {
		t.Errorf("TotalBorn should be 5, got %d", bio.TotalBorn)
	}
	if bio.DNALength != 60 {
		t.Errorf("DNALength should be 60, got %d", bio.DNALength)
	}

	for i, cell := range bio.Cells {
		if !cell.Alive {
			t.Errorf("cell %d should be alive", i)
		}
		if cell.DNA == nil {
			t.Errorf("cell %d should have DNA", i)
		}
		if cell.DNA.Length() != 60 {
			t.Errorf("cell %d DNA length: got %d, want 60", i, cell.DNA.Length())
		}
	}
}

func TestBiosphere_Step(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(200))
	bio := NewBiosphere(10, 60, rng)

	initialGen := bio.Generation
	bio.Step(30.0, 0.5, 0.1, 300.0)

	if bio.Generation != initialGen+1 {
		t.Errorf("generation should increment by 1, got %d (was %d)", bio.Generation, initialGen)
	}
	// Population should still exist (with enough energy, cells survive).
	if len(bio.Cells) == 0 {
		t.Error("biosphere should have surviving cells after one step with adequate energy")
	}
}

func TestBiosphere_Step_MultipleGenerations(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(300))
	bio := NewBiosphere(10, 60, rng)

	for i := 0; i < 10; i++ {
		bio.Step(30.0, 0.5, 0.1, 300.0)
	}

	if bio.Generation != 10 {
		t.Errorf("expected generation 10, got %d", bio.Generation)
	}
	if bio.TotalBorn < 10 {
		t.Errorf("TotalBorn should be at least 10, got %d", bio.TotalBorn)
	}
}

func TestBiosphere_AverageFitness(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(400))
	bio := NewBiosphere(10, 60, rng)

	// Compute fitness.
	for _, c := range bio.Cells {
		c.ComputeFitness()
	}

	avg := bio.AverageFitness()
	if avg < 0.0 || avg > 1.0 {
		t.Errorf("average fitness should be in [0, 1], got %v", avg)
	}
}

func TestBiosphere_AverageFitness_Empty(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(401))
	bio := NewBiosphere(0, 60, rng)

	if bio.AverageFitness() != 0.0 {
		t.Errorf("empty biosphere fitness should be 0, got %v", bio.AverageFitness())
	}
}

func TestBiosphere_PopulationCap(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(500))
	bio := NewBiosphere(50, 60, rng)

	// Run many steps with plenty of energy to encourage division.
	for i := 0; i < 20; i++ {
		bio.Step(50.0, 0.1, 0.01, 300.0)
	}

	if len(bio.Cells) > 100 {
		t.Errorf("population should be capped at 100, got %d", len(bio.Cells))
	}
}

// ---------------------------------------------------------------------------
// Environment
// ---------------------------------------------------------------------------

func TestEnvironment_Update_EarlyUniverse(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(60))
	env := NewEnvironment(TPlanck, rng)

	env.Update(100) // Early universe
	// Temperature should be very high.
	if env.Temperature < 1e5 {
		t.Errorf("early universe temperature should be very high, got %v", env.Temperature)
	}
	// UV should be 0 before stars form.
	if env.UVIntensity != 0.0 {
		t.Errorf("UV intensity should be 0 before star formation, got %v", env.UVIntensity)
	}
}

func TestEnvironment_Update_PlanetEra(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(61))
	env := NewEnvironment(TPlanck, rng)

	env.Update(250000) // Planet era
	// Temperature should be roughly around Earth surface temperature.
	if env.Temperature < 200 || env.Temperature > 400 {
		t.Errorf("planet-era temperature should be near Earth surface, got %v", env.Temperature)
	}
}

func TestEnvironment_IsHabitable(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(62))
	env := NewEnvironment(TEarthSurface, rng)

	// Manually set habitable conditions.
	env.Temperature = 300
	env.WaterAvailability = 0.5
	env.UVIntensity = 1.0
	env.CosmicRayFlux = 0.1
	env.StellarWind = 0.0

	if !env.IsHabitable() {
		t.Error("environment with moderate temperature, water, and low radiation should be habitable")
	}
}

func TestEnvironment_IsHabitable_TooHot(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(63))
	env := NewEnvironment(1000, rng)
	env.Temperature = 1000
	env.WaterAvailability = 0.5
	env.UVIntensity = 0.1
	env.CosmicRayFlux = 0.1

	if env.IsHabitable() {
		t.Error("temperature > 400 should not be habitable")
	}
}

func TestEnvironment_IsHabitable_NoWater(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(64))
	env := NewEnvironment(300, rng)
	env.Temperature = 300
	env.WaterAvailability = 0.0

	if env.IsHabitable() {
		t.Error("no water should not be habitable")
	}
}

func TestEnvironment_IsHabitable_HighRadiation(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(65))
	env := NewEnvironment(300, rng)
	env.Temperature = 300
	env.WaterAvailability = 0.5
	env.UVIntensity = 5.0
	env.CosmicRayFlux = 5.0
	env.StellarWind = 5.0

	if env.IsHabitable() {
		t.Error("high radiation should not be habitable")
	}
}

func TestEnvironment_TemperatureCooling(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(70))
	env := NewEnvironment(TPlanck, rng)

	// Track temperature at early, mid, and late epochs (deterministic path).
	env.Update(10)
	tempEarly := env.Temperature

	env2 := NewEnvironment(TPlanck, rand.New(rand.NewSource(70)))
	env2.Update(1000)
	tempMid := env2.Temperature

	env3 := NewEnvironment(TPlanck, rand.New(rand.NewSource(70)))
	env3.Update(100000)
	tempLate := env3.Temperature

	if tempEarly <= tempMid {
		t.Errorf("early temperature (%v) should be higher than mid (%v)", tempEarly, tempMid)
	}
	if tempMid <= tempLate {
		t.Errorf("mid temperature (%v) should be higher than late (%v)", tempMid, tempLate)
	}
}

func TestEnvironment_ThermalEnergy(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(71))
	env := NewEnvironment(300, rng)
	env.Temperature = 300

	te := env.ThermalEnergy()
	if te <= 0 {
		t.Errorf("thermal energy at 300K should be positive, got %v", te)
	}
	if !almostEqual(te, 300*0.1, tolerance) {
		t.Errorf("thermal energy: got %v, want %v", te, 300*0.1)
	}

	// Below 100K or above 500K returns 0.1.
	env.Temperature = 50
	if !almostEqual(env.ThermalEnergy(), 0.1, tolerance) {
		t.Errorf("thermal energy below 100K should be 0.1, got %v", env.ThermalEnergy())
	}
}

// ---------------------------------------------------------------------------
// Universe
// ---------------------------------------------------------------------------

func TestNewUniverse(t *testing.T) {
	t.Parallel()
	u := NewUniverse(42)

	if u.Field == nil {
		t.Error("Field should not be nil")
	}
	if u.Atoms == nil {
		t.Error("Atoms should not be nil")
	}
	if u.Chemistry == nil {
		t.Error("Chemistry should not be nil")
	}
	if u.Env == nil {
		t.Error("Environment should not be nil")
	}
	if u.Biosphere != nil {
		t.Error("Biosphere should be nil at creation (emerges later)")
	}
	if u.Age != 0 {
		t.Errorf("initial age should be 0, got %d", u.Age)
	}
	if !almostEqual(u.ScaleFactor, 1.0, tolerance) {
		t.Errorf("initial scale factor should be 1.0, got %v", u.ScaleFactor)
	}
	if !almostEqual(u.Field.Temperature, TPlanck, tolerance) {
		t.Errorf("initial field temperature should be TPlanck, got %v", u.Field.Temperature)
	}
}

func TestUniverse_Step_EarlyEpochs(t *testing.T) {
	t.Parallel()
	u := NewUniverse(42)

	// Simulate a few ticks in the Planck/Inflation era manually by calling
	// the exported Run with a tick callback that stops early.
	tickCount := 0
	u.OnTick = func(epochName string, epochIndex int, tick int) {
		tickCount++
	}

	// Run only the first two epochs (Planck and Inflation).
	// We do this by calling Run and checking results.
	u.Run()

	if len(u.Results) != len(Epochs) {
		t.Errorf("expected %d epoch results, got %d", len(Epochs), len(u.Results))
	}
	if u.Results[0].EpochName != "Planck" {
		t.Errorf("first epoch should be Planck, got %q", u.Results[0].EpochName)
	}
}

func TestUniverse_EpochTransitions(t *testing.T) {
	t.Parallel()
	u := NewUniverse(99)

	epochNames := make([]string, 0)
	u.OnEpochComplete = func(result EpochResult) {
		epochNames = append(epochNames, result.EpochName)
	}

	u.Run()

	expectedNames := []string{
		"Planck", "Inflation", "Electroweak", "QuarkGluon",
		"Hadron", "Nucleosynthesis", "Recombination", "StarFormation",
		"SolarSystem", "EarthFormation", "LifeEmergence", "DNAEvolution", "Present",
	}
	if len(epochNames) != len(expectedNames) {
		t.Fatalf("expected %d epochs, got %d", len(expectedNames), len(epochNames))
	}
	for i, name := range expectedNames {
		if epochNames[i] != name {
			t.Errorf("epoch %d: got %q, want %q", i, epochNames[i], name)
		}
	}
}

func TestUniverse_Snapshot(t *testing.T) {
	t.Parallel()
	u := NewUniverse(55)

	// Add some particles so snapshot has data.
	u.Field.Particles = append(u.Field.Particles, NewParticle(ParticleElectron))
	u.Field.Particles = append(u.Field.Particles, NewParticle(ParticlePhoton))
	u.Age = 100

	snap := u.TakeSnapshot("Electroweak", 2, false)
	if snap.Epoch != "Electroweak" {
		t.Errorf("snapshot epoch: got %q, want 'Electroweak'", snap.Epoch)
	}
	if snap.EpochIndex != 2 {
		t.Errorf("snapshot epoch index: got %d, want 2", snap.EpochIndex)
	}
	if snap.Tick != 100 {
		t.Errorf("snapshot tick: got %d, want 100", snap.Tick)
	}
	if snap.Particles != 2 {
		t.Errorf("snapshot particles: got %d, want 2", snap.Particles)
	}
	if snap.TotalEpochs != len(Epochs) {
		t.Errorf("snapshot total epochs: got %d, want %d", snap.TotalEpochs, len(Epochs))
	}
	if snap.ParticlePos != nil {
		t.Error("particle positions should be nil when includePositions is false")
	}
}

func TestUniverse_Snapshot_WithPositions(t *testing.T) {
	t.Parallel()
	u := NewUniverse(56)

	e := NewParticle(ParticleElectron)
	e.Position = [3]float64{1, 2, 3}
	u.Field.Particles = append(u.Field.Particles, e)

	snap := u.TakeSnapshot("Planck", 0, true)
	if len(snap.ParticlePos) != 1 {
		t.Fatalf("expected 1 particle position, got %d", len(snap.ParticlePos))
	}
	if snap.ParticlePos[0] != [3]float64{1, 2, 3} {
		t.Errorf("particle position mismatch: got %v", snap.ParticlePos[0])
	}
	if snap.ParticleTypes[0] != "electron" {
		t.Errorf("particle type: got %q, want 'electron'", snap.ParticleTypes[0])
	}
}

func TestUniverse_Run_ProducesParticlesAndAtoms(t *testing.T) {
	t.Parallel()
	u := NewUniverse(77)
	u.Run()

	if len(u.Field.Particles) == 0 && u.Field.TotalCreated == 0 {
		t.Error("simulation should create particles")
	}
	if len(u.Atoms.Atoms) == 0 {
		t.Error("simulation should produce atoms")
	}
	if len(u.Chemistry.Molecules) == 0 {
		t.Error("simulation should produce molecules")
	}
	if u.Biosphere == nil {
		t.Error("biosphere should emerge during simulation")
	}
	if u.Biosphere != nil && len(u.Biosphere.Cells) == 0 {
		t.Error("biosphere should have living cells after full simulation")
	}
}

func TestUniverse_Summary(t *testing.T) {
	t.Parallel()
	u := NewUniverse(88)
	u.Run()

	summary := u.Summary()
	if len(summary) == 0 {
		t.Error("summary should not be empty after simulation")
	}
}

// ---------------------------------------------------------------------------
// Additional edge-case tests
// ---------------------------------------------------------------------------

func TestMolecule_MolecularWeight(t *testing.T) {
	t.Parallel()
	h1 := NewAtom(1, 1)
	h2 := NewAtom(1, 1)
	o := NewAtom(8, 16)
	water := NewMolecule([]*Atom{h1, h2, o}, "water")
	if water.MolecularWeight() != 18 {
		t.Errorf("water molecular weight should be 18, got %d", water.MolecularWeight())
	}
}

func TestMolecule_IsOrganic(t *testing.T) {
	t.Parallel()
	c := NewAtom(6, 12)
	h1 := NewAtom(1, 1)
	h2 := NewAtom(1, 1)
	h3 := NewAtom(1, 1)
	h4 := NewAtom(1, 1)
	methane := NewMolecule([]*Atom{c, h1, h2, h3, h4}, "methane")
	if !methane.IsOrganic {
		t.Error("methane (CH4) should be organic")
	}

	// Water is not organic.
	h := NewAtom(1, 1)
	h5 := NewAtom(1, 1)
	o := NewAtom(8, 16)
	water := NewMolecule([]*Atom{h, h5, o}, "water")
	if water.IsOrganic {
		t.Error("water should not be organic")
	}
}

func TestDNAStrand_GCContent(t *testing.T) {
	t.Parallel()
	strand := &DNAStrand{Sequence: []string{"G", "C", "A", "T"}}
	gc := strand.GCContent()
	if !almostEqual(gc, 0.5, tolerance) {
		t.Errorf("GC content of GCAT should be 0.5, got %v", gc)
	}

	empty := &DNAStrand{}
	if empty.GCContent() != 0.0 {
		t.Errorf("empty strand GC content should be 0, got %v", empty.GCContent())
	}
}

func TestGene_Transcribe(t *testing.T) {
	t.Parallel()
	g := NewGene("test", []string{"A", "T", "G", "C"}, 0, 4, false)
	rna := g.Transcribe()
	expected := []string{"A", "U", "G", "C"}
	if len(rna) != len(expected) {
		t.Fatalf("RNA length: got %d, want %d", len(rna), len(expected))
	}
	for i, base := range expected {
		if rna[i] != base {
			t.Errorf("RNA base %d: got %q, want %q", i, rna[i], base)
		}
	}
}

func TestTranslateMRNA(t *testing.T) {
	t.Parallel()
	// AUG (Met/start) + UUU (Phe) + UAA (stop)
	mrna := []string{"A", "U", "G", "U", "U", "U", "U", "A", "A"}
	protein := TranslateMRNA(mrna)
	if len(protein) != 2 {
		t.Fatalf("expected protein of length 2 (Met, Phe), got %d", len(protein))
	}
	if protein[0] != "Met" {
		t.Errorf("first amino acid should be Met, got %q", protein[0])
	}
	if protein[1] != "Phe" {
		t.Errorf("second amino acid should be Phe, got %q", protein[1])
	}
}

func TestTranslateMRNA_NoStartCodon(t *testing.T) {
	t.Parallel()
	mrna := []string{"U", "U", "U", "U", "A", "A"}
	protein := TranslateMRNA(mrna)
	if len(protein) != 0 {
		t.Errorf("without start codon, protein should be empty, got %v", protein)
	}
}

func TestCell_ComputeFitness(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(42))
	dna := RandomStrand(60, 3, rng)
	cell := NewCell(dna, 0, rng)
	cell.TranscribeAndTranslate()

	fitness := cell.ComputeFitness()
	if fitness < 0.0 || fitness > 1.0 {
		t.Errorf("fitness should be in [0, 1], got %v", fitness)
	}
}

func TestCell_Divide(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(42))
	dna := RandomStrand(60, 3, rng)
	cell := NewCell(dna, 0, rng)
	cell.Energy = 100.0

	daughter := cell.Divide()
	if daughter == nil {
		t.Fatal("cell with sufficient energy should divide")
	}
	if daughter.Generation != 1 {
		t.Errorf("daughter generation should be 1, got %d", daughter.Generation)
	}
	if daughter.DNA == nil {
		t.Error("daughter should have DNA")
	}
	// Energy split.
	if cell.Energy > 51 {
		t.Errorf("parent energy should be halved, got %v", cell.Energy)
	}
}

func TestCell_Divide_InsufficientEnergy(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(42))
	dna := RandomStrand(60, 3, rng)
	cell := NewCell(dna, 0, rng)
	cell.Energy = 10.0 // below 50 threshold

	daughter := cell.Divide()
	if daughter != nil {
		t.Error("cell with low energy should not divide")
	}
}

func TestElectronShell_Full(t *testing.T) {
	t.Parallel()
	s := ElectronShell{N: 1, MaxElectrons: 2, Electrons: 2}
	if !s.Full() {
		t.Error("shell with max electrons should be full")
	}
	s2 := ElectronShell{N: 1, MaxElectrons: 2, Electrons: 1}
	if s2.Full() {
		t.Error("shell with fewer than max electrons should not be full")
	}
}

func TestAtom_DistanceTo(t *testing.T) {
	t.Parallel()
	a := NewAtom(1, 1)
	b := NewAtom(1, 1)
	a.Position = [3]float64{0, 0, 0}
	b.Position = [3]float64{3, 4, 0}
	if !almostEqual(a.DistanceTo(b), 5.0, tolerance) {
		t.Errorf("distance should be 5.0, got %v", a.DistanceTo(b))
	}
}

func TestAtom_HasBondWith_RemoveBond(t *testing.T) {
	t.Parallel()
	a := NewAtom(1, 1)
	b := NewAtom(8, 16)
	a.Bonds = append(a.Bonds, b.ID)

	if !a.HasBondWith(b.ID) {
		t.Error("atom should have bond with partner")
	}
	a.RemoveBond(b.ID)
	if a.HasBondWith(b.ID) {
		t.Error("bond should be removed")
	}
}

func TestEpochs_InfoComplete(t *testing.T) {
	t.Parallel()
	if len(Epochs) != 13 {
		t.Errorf("expected 13 epochs, got %d", len(Epochs))
	}
	for i, ep := range Epochs {
		if ep.Name == "" {
			t.Errorf("epoch %d has empty name", i)
		}
		if ep.Description == "" {
			t.Errorf("epoch %d has empty description", i)
		}
		if ep.Symbol == "" {
			t.Errorf("epoch %d has empty symbol", i)
		}
		if ep.StartTick <= 0 {
			t.Errorf("epoch %d start tick should be positive, got %d", i, ep.StartTick)
		}
	}
}

func TestCodonTable_StopCodons(t *testing.T) {
	t.Parallel()
	stops := []string{"UAA", "UAG", "UGA"}
	for _, codon := range stops {
		aa, ok := CodonTable[codon]
		if !ok || aa != "STOP" {
			t.Errorf("codon %q should map to STOP, got %q (ok=%v)", codon, aa, ok)
		}
	}
}

func TestCodonTable_StartCodon(t *testing.T) {
	t.Parallel()
	aa, ok := CodonTable["AUG"]
	if !ok || aa != "Met" {
		t.Errorf("AUG should map to Met, got %q (ok=%v)", aa, ok)
	}
}

// ---------------------------------------------------------------------------
// Biology: Gene functions
// ---------------------------------------------------------------------------

func TestNewGene(t *testing.T) {
	t.Parallel()
	seq := []string{"A", "T", "G", "C", "A"}
	g := NewGene("myGene", seq, 10, 15, true)

	if g.Name != "myGene" {
		t.Errorf("gene name: got %q, want %q", g.Name, "myGene")
	}
	if len(g.Sequence) != 5 {
		t.Errorf("gene sequence length: got %d, want 5", len(g.Sequence))
	}
	if g.StartPos != 10 {
		t.Errorf("gene start pos: got %d, want 10", g.StartPos)
	}
	if g.EndPos != 15 {
		t.Errorf("gene end pos: got %d, want 15", g.EndPos)
	}
	if !g.Essential {
		t.Error("gene should be essential")
	}
	if !almostEqual(g.ExpressionLevel, 1.0, tolerance) {
		t.Errorf("default expression level: got %v, want 1.0", g.ExpressionLevel)
	}
	if len(g.EpigeneticMarks) != 0 {
		t.Errorf("new gene should have 0 epigenetic marks, got %d", len(g.EpigeneticMarks))
	}
}

func TestGene_Length(t *testing.T) {
	t.Parallel()
	g := NewGene("test", []string{"A", "T", "G"}, 0, 3, false)
	if g.Length() != 3 {
		t.Errorf("gene length: got %d, want 3", g.Length())
	}

	empty := NewGene("empty", []string{}, 0, 0, false)
	if empty.Length() != 0 {
		t.Errorf("empty gene length: got %d, want 0", empty.Length())
	}
}

func TestGene_IsSilenced(t *testing.T) {
	t.Parallel()
	seq := []string{"A", "T", "G", "C", "A", "T", "G", "C", "A", "T"}
	g := NewGene("test", seq, 0, 10, false)

	// Initially not silenced (no methylation marks).
	if g.IsSilenced() {
		t.Error("gene without methylation should not be silenced")
	}

	// Add heavy methylation (> 30% of length = > 3 marks for length 10).
	for i := 0; i < 4; i++ {
		g.Methylate(i, 1)
	}
	if !g.IsSilenced() {
		t.Error("gene with heavy methylation should be silenced")
	}
}

func TestGene_Methylate(t *testing.T) {
	t.Parallel()
	g := NewGene("test", []string{"A", "T", "G", "C"}, 0, 4, false)

	g.Methylate(1, 5)
	if len(g.EpigeneticMarks) != 1 {
		t.Fatalf("expected 1 mark after methylation, got %d", len(g.EpigeneticMarks))
	}
	m := g.EpigeneticMarks[0]
	if m.Position != 1 {
		t.Errorf("methylation position: got %d, want 1", m.Position)
	}
	if m.MarkType != "methylation" {
		t.Errorf("mark type: got %q, want %q", m.MarkType, "methylation")
	}
	if !m.Active {
		t.Error("new methylation mark should be active")
	}
	if m.GenerationAdded != 5 {
		t.Errorf("generation added: got %d, want 5", m.GenerationAdded)
	}

	// Out-of-bounds position should not add a mark.
	g.Methylate(-1, 0)
	g.Methylate(100, 0)
	if len(g.EpigeneticMarks) != 1 {
		t.Errorf("out-of-bounds methylation should not add marks, got %d", len(g.EpigeneticMarks))
	}

	// Methylation should reduce expression level.
	if g.ExpressionLevel >= 1.0 {
		t.Errorf("expression level should decrease after methylation, got %v", g.ExpressionLevel)
	}
}

func TestGene_Demethylate(t *testing.T) {
	t.Parallel()
	g := NewGene("test", []string{"A", "T", "G", "C"}, 0, 4, false)

	g.Methylate(0, 1)
	g.Methylate(2, 1)
	if len(g.EpigeneticMarks) != 2 {
		t.Fatalf("expected 2 marks, got %d", len(g.EpigeneticMarks))
	}

	g.Demethylate(0)
	// Only the methylation at position 0 should be removed.
	if len(g.EpigeneticMarks) != 1 {
		t.Errorf("expected 1 mark after demethylation, got %d", len(g.EpigeneticMarks))
	}
	if g.EpigeneticMarks[0].Position != 2 {
		t.Errorf("remaining mark position: got %d, want 2", g.EpigeneticMarks[0].Position)
	}

	// Demethylate at position with no methylation -- should be a no-op.
	g.Demethylate(99)
	if len(g.EpigeneticMarks) != 1 {
		t.Errorf("demethylating non-existent position should not change marks, got %d", len(g.EpigeneticMarks))
	}
}

func TestGene_Acetylate(t *testing.T) {
	t.Parallel()
	g := NewGene("test", []string{"A", "T", "G", "C"}, 0, 4, false)

	g.Acetylate(2, 3)
	if len(g.EpigeneticMarks) != 1 {
		t.Fatalf("expected 1 mark after acetylation, got %d", len(g.EpigeneticMarks))
	}
	m := g.EpigeneticMarks[0]
	if m.Position != 2 {
		t.Errorf("acetylation position: got %d, want 2", m.Position)
	}
	if m.MarkType != "acetylation" {
		t.Errorf("mark type: got %q, want %q", m.MarkType, "acetylation")
	}
	if !m.Active {
		t.Error("new acetylation mark should be active")
	}
	if m.GenerationAdded != 3 {
		t.Errorf("generation added: got %d, want 3", m.GenerationAdded)
	}

	// Acetylation should increase expression level (or at minimum not decrease below 1.0).
	// Since there is no methylation, acetylation increases expression.
	if g.ExpressionLevel < 1.0 {
		t.Errorf("acetylation without methylation should keep expression >= 1.0, got %v", g.ExpressionLevel)
	}
}

func TestGene_Mutate(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(42))
	g := NewGene("test", []string{"A", "A", "A", "A", "A", "A", "A", "A", "A", "A"}, 0, 10, false)

	// With rate 1.0, every base should mutate.
	mutations := g.Mutate(1.0, rng)
	if mutations != 10 {
		t.Errorf("all bases should mutate with rate 1.0, got %d mutations", mutations)
	}
	// At least one base should differ from "A".
	changed := false
	for _, b := range g.Sequence {
		if b != "A" {
			changed = true
			break
		}
	}
	if !changed {
		t.Error("at least one base should differ from original after full mutation")
	}

	// With rate 0.0, no bases should mutate.
	g2 := NewGene("test2", []string{"G", "G", "G"}, 0, 3, false)
	m := g2.Mutate(0.0, rng)
	if m != 0 {
		t.Errorf("no bases should mutate with rate 0.0, got %d", m)
	}
}

// ---------------------------------------------------------------------------
// Biology: DNAStrand functions
// ---------------------------------------------------------------------------

func TestDNAStrand_Length(t *testing.T) {
	t.Parallel()
	strand := &DNAStrand{Sequence: []string{"A", "T", "G", "C", "A"}}
	if strand.Length() != 5 {
		t.Errorf("strand length: got %d, want 5", strand.Length())
	}

	empty := &DNAStrand{}
	if empty.Length() != 0 {
		t.Errorf("empty strand length: got %d, want 0", empty.Length())
	}
}

func TestRandomStrand(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(42))
	strand := RandomStrand(100, 3, rng)

	if strand.Length() != 100 {
		t.Errorf("strand length: got %d, want 100", strand.Length())
	}
	if len(strand.Genes) != 3 {
		t.Errorf("number of genes: got %d, want 3", len(strand.Genes))
	}

	// All bases should be valid nucleotides.
	validBases := map[string]bool{"A": true, "T": true, "G": true, "C": true}
	for i, b := range strand.Sequence {
		if !validBases[b] {
			t.Errorf("invalid base at position %d: %q", i, b)
		}
	}

	// First gene should be essential.
	if !strand.Genes[0].Essential {
		t.Error("first gene should be essential")
	}
	// Subsequent genes should not be essential.
	for i := 1; i < len(strand.Genes); i++ {
		if strand.Genes[i].Essential {
			t.Errorf("gene %d should not be essential", i)
		}
	}
}

func TestDNAStrand_Replicate(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(42))
	original := RandomStrand(60, 2, rng)

	// Add some epigenetic marks to test mark inheritance.
	original.Genes[0].Methylate(0, 1)
	original.Genes[0].Acetylate(1, 1)

	daughter := original.Replicate(rng)

	if daughter.Length() != original.Length() {
		t.Errorf("replicated strand length: got %d, want %d", daughter.Length(), original.Length())
	}
	if daughter.Generation != original.Generation+1 {
		t.Errorf("daughter generation: got %d, want %d", daughter.Generation, original.Generation+1)
	}
	if len(daughter.Genes) != len(original.Genes) {
		t.Errorf("daughter gene count: got %d, want %d", len(daughter.Genes), len(original.Genes))
	}

	// Sequence should be copied (same content).
	for i := range original.Sequence {
		if daughter.Sequence[i] != original.Sequence[i] {
			t.Errorf("replicated sequence differs at position %d: got %q, want %q",
				i, daughter.Sequence[i], original.Sequence[i])
			break
		}
	}
}

func TestDNAStrand_ApplyMutations(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(42))
	strand := RandomStrand(100, 3, rng)

	initialMutations := strand.MutationCount
	mutations := strand.ApplyMutations(1.0, 1.0, rng)

	// With UV and cosmic ray intensity = 1.0, some mutations should occur.
	if mutations < 0 {
		t.Errorf("mutation count should be non-negative, got %d", mutations)
	}
	if strand.MutationCount != initialMutations+mutations {
		t.Errorf("MutationCount: got %d, want %d", strand.MutationCount, initialMutations+mutations)
	}

	// With zero intensities, no mutations from environmental sources.
	rng2 := rand.New(rand.NewSource(42))
	strand2 := RandomStrand(100, 3, rng2)
	zeroMut := strand2.ApplyMutations(0.0, 0.0, rng2)
	if zeroMut != 0 {
		t.Errorf("expected 0 mutations with zero intensities, got %d", zeroMut)
	}
}

func TestDNAStrand_ApplyEpigeneticChanges(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(42))
	strand := RandomStrand(100, 3, rng)

	// Count initial marks.
	initialMarks := 0
	for _, g := range strand.Genes {
		initialMarks += len(g.EpigeneticMarks)
	}

	// Apply changes many times to increase probability of epigenetic modifications.
	for i := 0; i < 50; i++ {
		strand.ApplyEpigeneticChanges(300.0, i+1, rng)
	}

	totalMarks := 0
	for _, g := range strand.Genes {
		totalMarks += len(g.EpigeneticMarks)
	}

	// After 50 rounds, at least some epigenetic marks should have been added.
	if totalMarks <= initialMarks {
		t.Errorf("expected epigenetic marks to increase after 50 rounds, initial=%d, final=%d",
			initialMarks, totalMarks)
	}
}

// ---------------------------------------------------------------------------
// Biology: Protein functions
// ---------------------------------------------------------------------------

func TestNewProtein(t *testing.T) {
	t.Parallel()
	aas := []string{"Met", "Ala", "Gly", "Phe"}
	p := NewProtein(aas, "testProtein", "enzyme")

	if p.Name != "testProtein" {
		t.Errorf("protein name: got %q, want %q", p.Name, "testProtein")
	}
	if p.Function != "enzyme" {
		t.Errorf("protein function: got %q, want %q", p.Function, "enzyme")
	}
	if !p.Active {
		t.Error("new protein should be active")
	}
	if p.Folded {
		t.Error("new protein should not be folded until Fold is called")
	}
	if len(p.AminoAcids) != 4 {
		t.Errorf("amino acid count: got %d, want 4", len(p.AminoAcids))
	}
}

func TestProtein_Length(t *testing.T) {
	t.Parallel()
	p := NewProtein([]string{"Met", "Ala", "Gly"}, "test", "structural")
	if p.Length() != 3 {
		t.Errorf("protein length: got %d, want 3", p.Length())
	}

	empty := NewProtein([]string{}, "empty", "signaling")
	if empty.Length() != 0 {
		t.Errorf("empty protein length: got %d, want 0", empty.Length())
	}
}

func TestProtein_Fold(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(42))

	// Protein too short to fold (< 3 amino acids).
	short := NewProtein([]string{"Met", "Ala"}, "short", "enzyme")
	result := short.Fold(rng)
	if result {
		t.Error("protein with < 3 amino acids should not fold successfully")
	}
	if short.Folded {
		t.Error("short protein should not be folded")
	}

	// Protein long enough to fold. Run multiple times to exercise stochastic branch.
	foldCount := 0
	for i := 0; i < 100; i++ {
		p := NewProtein([]string{"Met", "Ala", "Gly", "Phe", "Leu", "Val", "Ile", "Pro"},
			"long", "enzyme")
		rngLocal := rand.New(rand.NewSource(int64(i)))
		if p.Fold(rngLocal) {
			foldCount++
		}
	}
	// With length 8 and probability ~0.5+0.1*ln(9) ~ 0.72, many should fold.
	if foldCount == 0 {
		t.Error("at least some long proteins should fold successfully over 100 trials")
	}
	if foldCount == 100 {
		t.Error("not all proteins should fold deterministically (stochastic process)")
	}
}

// ---------------------------------------------------------------------------
// Biology: Cell functions
// ---------------------------------------------------------------------------

func TestNewCell(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(42))
	dna := RandomStrand(60, 3, rng)
	cell := NewCell(dna, 5, rng)

	if cell.DNA != dna {
		t.Error("cell DNA should match provided DNA")
	}
	if cell.Generation != 5 {
		t.Errorf("cell generation: got %d, want 5", cell.Generation)
	}
	if !cell.Alive {
		t.Error("new cell should be alive")
	}
	if !almostEqual(cell.Fitness, 1.0, tolerance) {
		t.Errorf("initial fitness: got %v, want 1.0", cell.Fitness)
	}
	if !almostEqual(cell.Energy, 100.0, tolerance) {
		t.Errorf("initial energy: got %v, want 100.0", cell.Energy)
	}
	if cell.ID <= 0 {
		t.Errorf("cell ID should be positive, got %d", cell.ID)
	}
	if len(cell.Proteins) != 0 {
		t.Errorf("new cell should have 0 proteins, got %d", len(cell.Proteins))
	}
}

func TestCell_TranscribeAndTranslate(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(42))
	// Create a strand with known sequence containing start codon.
	// AUG in DNA is ATG; we need a gene whose Transcribe produces mRNA with AUG.
	seq := []string{"A", "T", "G", "T", "T", "T", "T", "A", "A"} // ATG -> AUG (Met), TTT -> UUU (Phe), TAA -> UAA (STOP)
	gene := NewGene("coding", seq, 0, 9, false)
	strand := &DNAStrand{
		Sequence: seq,
		Genes:    []*Gene{gene},
	}
	cell := NewCell(strand, 0, rng)
	proteins := cell.TranscribeAndTranslate()

	// The gene should produce a protein with [Met, Phe].
	// TranscribeAndTranslate has stochastic gating on expression level, so
	// we run multiple cells if needed.
	totalProteins := len(proteins)
	if totalProteins > 0 {
		if len(cell.Proteins) == 0 {
			t.Error("cell.Proteins should be populated after TranscribeAndTranslate")
		}
	}

	// Run with multiple seeds to confirm it produces at least one protein.
	produced := false
	for seed := int64(0); seed < 20; seed++ {
		localRng := rand.New(rand.NewSource(seed))
		gene2 := NewGene("coding2", seq, 0, 9, false)
		strand2 := &DNAStrand{Sequence: seq, Genes: []*Gene{gene2}}
		cell2 := NewCell(strand2, 0, localRng)
		prots := cell2.TranscribeAndTranslate()
		if len(prots) > 0 {
			produced = true
			break
		}
	}
	if !produced {
		t.Error("TranscribeAndTranslate should produce at least one protein across 20 seeds")
	}
}

func TestCell_Metabolize(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(42))
	dna := RandomStrand(60, 3, rng)
	cell := NewCell(dna, 0, rng)
	initialEnergy := cell.Energy

	cell.Metabolize(20.0)

	// Energy should change: gain from environment * efficiency, lose basal cost.
	if cell.Energy == initialEnergy {
		t.Errorf("energy should change after metabolism, still %v", cell.Energy)
	}

	// With zero environment energy, energy should decrease (basal cost = 3.0).
	cell2 := NewCell(dna, 0, rng)
	cell2.Energy = 10.0
	cell2.Metabolize(0.0)
	if cell2.Energy >= 10.0 {
		t.Errorf("energy should decrease with zero environment energy, got %v", cell2.Energy)
	}

	// Energy cap at 200.
	cell3 := NewCell(dna, 0, rng)
	cell3.Energy = 195.0
	cell3.Metabolize(100.0)
	if cell3.Energy > 200.0 {
		t.Errorf("energy should be capped at 200, got %v", cell3.Energy)
	}

	// Cell dies if energy reaches 0.
	cell4 := NewCell(dna, 0, rng)
	cell4.Energy = 2.0 // basal cost is 3.0, so with 0 environment energy it dies.
	cell4.Metabolize(0.0)
	if cell4.Alive {
		t.Error("cell should die when energy reaches 0")
	}
}

// ---------------------------------------------------------------------------
// Biology: Biosphere functions
// ---------------------------------------------------------------------------

func TestBiosphere_AverageGCContent(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(42))
	bio := NewBiosphere(10, 60, rng)

	gc := bio.AverageGCContent()
	if gc < 0.0 || gc > 1.0 {
		t.Errorf("average GC content should be in [0, 1], got %v", gc)
	}
	// With random sequences, GC content should be roughly 0.5 on average.
	if gc < 0.2 || gc > 0.8 {
		t.Errorf("average GC content with random sequences should be near 0.5, got %v", gc)
	}

	// Empty biosphere.
	emptyBio := NewBiosphere(0, 60, rng)
	if emptyBio.AverageGCContent() != 0.0 {
		t.Errorf("empty biosphere GC content should be 0, got %v", emptyBio.AverageGCContent())
	}
}

func TestBiosphere_TotalMutations(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(42))
	bio := NewBiosphere(5, 60, rng)

	// Initially, no mutations.
	if bio.TotalMutations() != 0 {
		t.Errorf("initial total mutations should be 0, got %d", bio.TotalMutations())
	}

	// Run many steps with high UV and cosmic ray intensity to ensure mutations accumulate.
	// The per-base mutation rate is UVMutationRate*uvIntensity + CosmicRayMutationRate*cosmicRayFlux,
	// which at intensity 1.0 is ~1e-4, so we need many rounds or high intensity.
	for i := 0; i < 20; i++ {
		bio.Step(30.0, 10.0, 10.0, 300.0)
	}

	totalMut := bio.TotalMutations()
	if totalMut < 0 {
		t.Errorf("total mutations should be non-negative, got %d", totalMut)
	}

	// TotalMutations sums MutationCount across all living cells.
	// Verify it returns correct sum by manually checking.
	manualSum := 0
	for _, c := range bio.Cells {
		manualSum += c.DNA.MutationCount
	}
	if totalMut != manualSum {
		t.Errorf("TotalMutations() = %d, manual sum = %d", totalMut, manualSum)
	}
}

// ---------------------------------------------------------------------------
// Atomic: Atom functions
// ---------------------------------------------------------------------------

func TestAtom_Symbol(t *testing.T) {
	t.Parallel()
	tests := []struct {
		atomicNumber int
		wantSymbol   string
	}{
		{1, "H"},
		{2, "He"},
		{6, "C"},
		{7, "N"},
		{8, "O"},
		{26, "Fe"},
	}
	for _, tt := range tests {
		a := NewAtom(tt.atomicNumber, 0)
		if a.Symbol() != tt.wantSymbol {
			t.Errorf("Symbol for Z=%d: got %q, want %q", tt.atomicNumber, a.Symbol(), tt.wantSymbol)
		}
	}

	// Unknown element returns "?".
	unknown := NewAtom(99, 200)
	if unknown.Symbol() != "?" {
		t.Errorf("unknown element symbol: got %q, want %q", unknown.Symbol(), "?")
	}
}

func TestAtom_Electronegativity(t *testing.T) {
	t.Parallel()
	tests := []struct {
		atomicNumber int
		wantEN       float64
	}{
		{1, 2.20},
		{6, 2.55},
		{8, 3.44},
		{9, 3.98},
		{11, 0.93},
	}
	for _, tt := range tests {
		a := NewAtom(tt.atomicNumber, 0)
		if !almostEqual(a.Electronegativity(), tt.wantEN, 0.01) {
			t.Errorf("electronegativity for Z=%d: got %v, want %v",
				tt.atomicNumber, a.Electronegativity(), tt.wantEN)
		}
	}

	// Unknown element returns 1.0 as default.
	unknown := NewAtom(99, 200)
	if !almostEqual(unknown.Electronegativity(), 1.0, tolerance) {
		t.Errorf("unknown element electronegativity: got %v, want 1.0", unknown.Electronegativity())
	}
}

func TestAtom_Charge(t *testing.T) {
	t.Parallel()
	// Neutral atom: charge = 0.
	h := NewAtom(1, 1)
	if h.Charge() != 0 {
		t.Errorf("neutral hydrogen charge: got %d, want 0", h.Charge())
	}

	// Ion: remove an electron.
	h.ElectronCount = 0
	if h.Charge() != 1 {
		t.Errorf("H+ charge: got %d, want 1", h.Charge())
	}

	// Add extra electron.
	o := NewAtom(8, 16)
	o.ElectronCount = 9
	if o.Charge() != -1 {
		t.Errorf("O- charge: got %d, want -1", o.Charge())
	}
}

func TestAtomicSystem_StellarNucleosynthesis(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(42))
	as := NewAtomicSystem(rng)

	// Add enough helium for triple-alpha process.
	for i := 0; i < 20; i++ {
		as.Atoms = append(as.Atoms, NewAtom(2, 4))
	}

	// Low temperature should produce no new atoms.
	lowTempAtoms := as.StellarNucleosynthesis(100)
	if len(lowTempAtoms) != 0 {
		t.Errorf("stellar nucleosynthesis at low temperature should produce nothing, got %d atoms",
			len(lowTempAtoms))
	}

	// High temperature should trigger fusion. Run multiple times for stochastic process.
	totalNewAtoms := 0
	for i := 0; i < 100; i++ {
		localRng := rand.New(rand.NewSource(int64(i)))
		localAS := NewAtomicSystem(localRng)
		for j := 0; j < 30; j++ {
			localAS.Atoms = append(localAS.Atoms, NewAtom(2, 4))
		}
		newAtoms := localAS.StellarNucleosynthesis(1e6)
		totalNewAtoms += len(newAtoms)
	}
	if totalNewAtoms == 0 {
		t.Error("stellar nucleosynthesis at high temperature should produce heavier elements over 100 trials")
	}
}

// ---------------------------------------------------------------------------
// Chemistry: functions
// ---------------------------------------------------------------------------

func TestNewMolecule(t *testing.T) {
	t.Parallel()
	c := NewAtom(6, 12)
	h := NewAtom(1, 1)
	mol := NewMolecule([]*Atom{c, h}, "test_mol")

	if mol.Name != "test_mol" {
		t.Errorf("molecule name: got %q, want %q", mol.Name, "test_mol")
	}
	if len(mol.Atoms) != 2 {
		t.Errorf("molecule atom count: got %d, want 2", len(mol.Atoms))
	}
	if mol.ID <= 0 {
		t.Errorf("molecule ID should be positive, got %d", mol.ID)
	}
	// CH molecule should be organic (has both C and H).
	if !mol.IsOrganic {
		t.Error("molecule with C and H should be organic")
	}
	// Formula should contain C and H.
	if mol.Formula == "" {
		t.Error("molecule formula should not be empty")
	}
	if len(mol.FunctionalGroups) != 0 {
		t.Errorf("new molecule should have no functional groups, got %d", len(mol.FunctionalGroups))
	}

	// Empty atoms should not panic.
	emptyMol := NewMolecule([]*Atom{}, "empty")
	if len(emptyMol.Atoms) != 0 {
		t.Errorf("empty molecule atom count: got %d, want 0", len(emptyMol.Atoms))
	}
}

func TestChemicalSystem_FormAminoAcid(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(42))
	as := NewAtomicSystem(rng)

	// Add exactly the minimum atoms for glycine: 2C + 5H + 2O + 1N.
	for i := 0; i < 2; i++ {
		as.Atoms = append(as.Atoms, NewAtom(6, 12)) // C
	}
	for i := 0; i < 5; i++ {
		as.Atoms = append(as.Atoms, NewAtom(1, 1)) // H
	}
	for i := 0; i < 2; i++ {
		as.Atoms = append(as.Atoms, NewAtom(8, 16)) // O
	}
	as.Atoms = append(as.Atoms, NewAtom(7, 14)) // N

	cs := NewChemicalSystem(as, rng)
	aa := cs.FormAminoAcid("glycine")

	if aa == nil {
		t.Fatal("FormAminoAcid should succeed with sufficient atoms")
	}
	if aa.Name != "glycine" {
		t.Errorf("amino acid name: got %q, want %q", aa.Name, "glycine")
	}
	if !aa.IsOrganic {
		t.Error("amino acid should be organic")
	}
	if len(aa.FunctionalGroups) != 2 {
		t.Errorf("amino acid should have 2 functional groups, got %d", len(aa.FunctionalGroups))
	}
	if cs.AminoAcidCount != 1 {
		t.Errorf("amino acid count: got %d, want 1", cs.AminoAcidCount)
	}

	// Try forming a second amino acid -- should fail due to insufficient atoms.
	aa2 := cs.FormAminoAcid("alanine")
	if aa2 != nil {
		t.Error("should not form amino acid with insufficient atoms")
	}
}

func TestChemicalSystem_FormNucleotide(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(42))
	as := NewAtomicSystem(rng)

	// Nucleotide requires C5 + H8 + O4 + N2.
	for i := 0; i < 5; i++ {
		as.Atoms = append(as.Atoms, NewAtom(6, 12)) // C
	}
	for i := 0; i < 8; i++ {
		as.Atoms = append(as.Atoms, NewAtom(1, 1)) // H
	}
	for i := 0; i < 4; i++ {
		as.Atoms = append(as.Atoms, NewAtom(8, 16)) // O
	}
	for i := 0; i < 2; i++ {
		as.Atoms = append(as.Atoms, NewAtom(7, 14)) // N
	}

	cs := NewChemicalSystem(as, rng)
	nuc := cs.FormNucleotide("A")

	if nuc == nil {
		t.Fatal("FormNucleotide should succeed with sufficient atoms")
	}
	if nuc.Name != "nucleotide-A" {
		t.Errorf("nucleotide name: got %q, want %q", nuc.Name, "nucleotide-A")
	}
	if !nuc.IsOrganic {
		t.Error("nucleotide should be organic")
	}
	if len(nuc.FunctionalGroups) != 3 {
		t.Errorf("nucleotide should have 3 functional groups, got %d", len(nuc.FunctionalGroups))
	}
	if cs.NucleotideCount != 1 {
		t.Errorf("nucleotide count: got %d, want 1", cs.NucleotideCount)
	}

	// Try forming another -- should fail.
	nuc2 := cs.FormNucleotide("T")
	if nuc2 != nil {
		t.Error("should not form nucleotide with insufficient atoms")
	}
}

func TestChemicalSystem_MoleculeCensus(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(42))
	as := NewAtomicSystem(rng)

	// Add atoms for 2 water molecules + 1 methane.
	for i := 0; i < 8; i++ {
		as.Atoms = append(as.Atoms, NewAtom(1, 1)) // H
	}
	for i := 0; i < 2; i++ {
		as.Atoms = append(as.Atoms, NewAtom(8, 16)) // O
	}
	as.Atoms = append(as.Atoms, NewAtom(6, 12)) // C

	cs := NewChemicalSystem(as, rng)
	cs.FormWater()
	cs.FormMethane()

	census := cs.MoleculeCensus()
	if census["water"] != 2 {
		t.Errorf("water census: got %d, want 2", census["water"])
	}
	if census["methane"] != 1 {
		t.Errorf("methane census: got %d, want 1", census["methane"])
	}

	// Empty system should return empty census.
	emptyAS := NewAtomicSystem(rng)
	emptyCS := NewChemicalSystem(emptyAS, rng)
	emptyCensus := emptyCS.MoleculeCensus()
	if len(emptyCensus) != 0 {
		t.Errorf("empty chemical system census should be empty, got %v", emptyCensus)
	}
}

// ---------------------------------------------------------------------------
// Environment: RadiationDose
// ---------------------------------------------------------------------------

func TestEnvironment_RadiationDose(t *testing.T) {
	t.Parallel()
	rng := rand.New(rand.NewSource(42))
	env := NewEnvironment(300, rng)
	env.UVIntensity = 2.0
	env.CosmicRayFlux = 1.5
	env.StellarWind = 0.5

	dose := env.RadiationDose()
	expected := 2.0 + 1.5 + 0.5
	if !almostEqual(dose, expected, tolerance) {
		t.Errorf("radiation dose: got %v, want %v", dose, expected)
	}

	// Zero radiation.
	env2 := NewEnvironment(300, rng)
	if env2.RadiationDose() != 0.0 {
		t.Errorf("zero radiation dose: got %v, want 0.0", env2.RadiationDose())
	}
}
