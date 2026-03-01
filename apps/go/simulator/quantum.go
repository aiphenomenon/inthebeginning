package simulator

import (
	"math"
	"math/rand"
	"sync/atomic"
)

// ParticleType enumerates all particle types.
type ParticleType int

const (
	ParticleUp ParticleType = iota
	ParticleDown
	ParticleElectron
	ParticlePositron
	ParticleNeutrino
	ParticlePhoton
	ParticleGluon
	ParticleWBoson
	ParticleZBoson
	ParticleProton
	ParticleNeutron
)

// String returns the display name for a particle type.
func (pt ParticleType) String() string {
	switch pt {
	case ParticleUp:
		return "up"
	case ParticleDown:
		return "down"
	case ParticleElectron:
		return "electron"
	case ParticlePositron:
		return "positron"
	case ParticleNeutrino:
		return "neutrino"
	case ParticlePhoton:
		return "photon"
	case ParticleGluon:
		return "gluon"
	case ParticleWBoson:
		return "W"
	case ParticleZBoson:
		return "Z"
	case ParticleProton:
		return "proton"
	case ParticleNeutron:
		return "neutron"
	default:
		return "unknown"
	}
}

// Spin represents quantum spin.
type Spin int

const (
	SpinUp   Spin = iota
	SpinDown
)

// Color represents quark color charge.
type Color int

const (
	ColorRed Color = iota
	ColorGreen
	ColorBlue
	ColorAntiRed
	ColorAntiGreen
	ColorAntiBlue
	ColorNone
)

// particleMasses maps particle type to mass.
var particleMasses = map[ParticleType]float64{
	ParticleUp:       MUpQuark,
	ParticleDown:     MDownQuark,
	ParticleElectron: MElectron,
	ParticlePositron: MElectron,
	ParticleNeutrino: MNeutrino,
	ParticlePhoton:   MPhoton,
	ParticleGluon:    MPhoton,
	ParticleProton:   MProton,
	ParticleNeutron:  MNeutron,
}

// particleCharges maps particle type to charge.
var particleCharges = map[ParticleType]float64{
	ParticleUp:       2.0 / 3.0,
	ParticleDown:     -1.0 / 3.0,
	ParticleElectron: -1.0,
	ParticlePositron: 1.0,
	ParticleNeutrino: 0.0,
	ParticlePhoton:   0.0,
	ParticleGluon:    0.0,
	ParticleProton:   1.0,
	ParticleNeutron:  0.0,
}

// WaveFunction is a simplified quantum wave function with amplitude and phase.
type WaveFunction struct {
	Amplitude float64
	Phase     float64
	Coherent  bool
}

// NewWaveFunction returns a default wave function.
func NewWaveFunction() WaveFunction {
	return WaveFunction{Amplitude: 1.0, Phase: 0.0, Coherent: true}
}

// Probability returns |psi|^2 (Born rule).
func (wf *WaveFunction) Probability() float64 {
	return wf.Amplitude * wf.Amplitude
}

// Evolve performs time evolution: phase rotation by E*dt/hbar.
func (wf *WaveFunction) Evolve(dt, energy float64) {
	if wf.Coherent {
		wf.Phase += energy * dt / HBAR
		wf.Phase = math.Mod(wf.Phase, 2*PI)
	}
}

// Collapse performs measurement, returning true if particle is "detected".
func (wf *WaveFunction) Collapse(rng *rand.Rand) bool {
	result := rng.Float64() < wf.Probability()
	if result {
		wf.Amplitude = 1.0
	} else {
		wf.Amplitude = 0.0
	}
	wf.Coherent = false
	return result
}

// particleIDGen is the global particle ID counter.
var particleIDGen atomic.Int64

// Particle represents a quantum particle with position, momentum, and quantum numbers.
type Particle struct {
	Type          ParticleType
	Position      [3]float64
	Momentum      [3]float64
	SpinState     Spin
	ColorCharge   Color
	WaveFn        WaveFunction
	EntangledWith int64 // ID of entangled partner, 0 if none
	ID            int64
}

// NewParticle creates a new particle with a unique ID.
func NewParticle(ptype ParticleType) *Particle {
	return &Particle{
		Type:        ptype,
		SpinState:   SpinUp,
		ColorCharge: ColorNone,
		WaveFn:      NewWaveFunction(),
		ID:          particleIDGen.Add(1),
	}
}

// Mass returns the particle mass.
func (p *Particle) Mass() float64 {
	m, ok := particleMasses[p.Type]
	if !ok {
		return 0.0
	}
	return m
}

// Charge returns the particle charge.
func (p *Particle) Charge() float64 {
	c, ok := particleCharges[p.Type]
	if !ok {
		return 0.0
	}
	return c
}

// Energy returns E = sqrt(p^2*c^2 + m^2*c^4).
func (p *Particle) Energy() float64 {
	p2 := p.Momentum[0]*p.Momentum[0] + p.Momentum[1]*p.Momentum[1] + p.Momentum[2]*p.Momentum[2]
	mc2 := p.Mass() * C * C
	return math.Sqrt(p2*C*C + mc2*mc2)
}

// QuantumField represents a quantum field that can create and annihilate particles.
type QuantumField struct {
	Temperature     float64
	Particles       []*Particle
	VacuumEnergy    float64
	TotalCreated    int
	TotalAnnihilated int
	rng             *rand.Rand
}

// NewQuantumField creates a new quantum field.
func NewQuantumField(temperature float64, rng *rand.Rand) *QuantumField {
	return &QuantumField{
		Temperature: temperature,
		Particles:   make([]*Particle, 0, 128),
		rng:         rng,
	}
}

// PairProduction creates a particle-antiparticle pair from vacuum energy.
// Returns the two particles or nil if energy is insufficient.
func (qf *QuantumField) PairProduction(energy float64) (*Particle, *Particle) {
	if energy < 2*MElectron*C*C {
		return nil, nil
	}

	var pType, apType ParticleType
	if energy >= 2*MProton*C*C && qf.rng.Float64() < 0.1 {
		pType = ParticleUp
		apType = ParticleDown
	} else {
		pType = ParticleElectron
		apType = ParticlePositron
	}

	dir := [3]float64{qf.rng.NormFloat64(), qf.rng.NormFloat64(), qf.rng.NormFloat64()}
	norm := math.Sqrt(dir[0]*dir[0] + dir[1]*dir[1] + dir[2]*dir[2])
	if norm < 1e-20 {
		norm = 1.0
	}
	pMom := energy / (2 * C)

	particle := NewParticle(pType)
	particle.SpinState = SpinUp
	for i := 0; i < 3; i++ {
		particle.Momentum[i] = dir[i] / norm * pMom
	}

	antiparticle := NewParticle(apType)
	antiparticle.SpinState = SpinDown
	for i := 0; i < 3; i++ {
		antiparticle.Momentum[i] = -dir[i] / norm * pMom
	}

	particle.EntangledWith = antiparticle.ID
	antiparticle.EntangledWith = particle.ID

	qf.Particles = append(qf.Particles, particle, antiparticle)
	qf.TotalCreated += 2

	return particle, antiparticle
}

// Annihilate annihilates a particle-antiparticle pair and returns the energy released.
func (qf *QuantumField) Annihilate(p1, p2 *Particle) float64 {
	energy := p1.Energy() + p2.Energy()
	qf.removeParticle(p1)
	qf.removeParticle(p2)
	qf.TotalAnnihilated += 2
	qf.VacuumEnergy += energy * 0.01

	photon1 := NewParticle(ParticlePhoton)
	photon1.Momentum = [3]float64{energy / (2 * C), 0, 0}
	photon2 := NewParticle(ParticlePhoton)
	photon2.Momentum = [3]float64{-energy / (2 * C), 0, 0}
	qf.Particles = append(qf.Particles, photon1, photon2)

	return energy
}

// removeParticle removes a particle from the field.
func (qf *QuantumField) removeParticle(p *Particle) {
	for i, pp := range qf.Particles {
		if pp == p {
			qf.Particles[i] = qf.Particles[len(qf.Particles)-1]
			qf.Particles[len(qf.Particles)-1] = nil
			qf.Particles = qf.Particles[:len(qf.Particles)-1]
			return
		}
	}
}

// QuarkConfinement combines quarks into hadrons when temperature drops enough.
func (qf *QuantumField) QuarkConfinement() []*Particle {
	if qf.Temperature > TQuarkHadron {
		return nil
	}

	var hadrons []*Particle

	var ups, downs []*Particle
	for _, p := range qf.Particles {
		switch p.Type {
		case ParticleUp:
			ups = append(ups, p)
		case ParticleDown:
			downs = append(downs, p)
		}
	}

	// Form protons (uud)
	for len(ups) >= 2 && len(downs) >= 1 {
		u1 := ups[len(ups)-1]
		ups = ups[:len(ups)-1]
		u2 := ups[len(ups)-1]
		ups = ups[:len(ups)-1]
		d1 := downs[len(downs)-1]
		downs = downs[:len(downs)-1]

		u1.ColorCharge = ColorRed
		u2.ColorCharge = ColorGreen
		d1.ColorCharge = ColorBlue

		proton := NewParticle(ParticleProton)
		proton.Position = u1.Position
		for i := 0; i < 3; i++ {
			proton.Momentum[i] = u1.Momentum[i] + u2.Momentum[i] + d1.Momentum[i]
		}

		qf.removeParticle(u1)
		qf.removeParticle(u2)
		qf.removeParticle(d1)
		qf.Particles = append(qf.Particles, proton)
		hadrons = append(hadrons, proton)
	}

	// Form neutrons (udd)
	for len(ups) >= 1 && len(downs) >= 2 {
		u1 := ups[len(ups)-1]
		ups = ups[:len(ups)-1]
		d1 := downs[len(downs)-1]
		downs = downs[:len(downs)-1]
		d2 := downs[len(downs)-1]
		downs = downs[:len(downs)-1]

		u1.ColorCharge = ColorRed
		d1.ColorCharge = ColorGreen
		d2.ColorCharge = ColorBlue

		neutron := NewParticle(ParticleNeutron)
		neutron.Position = u1.Position
		for i := 0; i < 3; i++ {
			neutron.Momentum[i] = u1.Momentum[i] + d1.Momentum[i] + d2.Momentum[i]
		}

		qf.removeParticle(u1)
		qf.removeParticle(d1)
		qf.removeParticle(d2)
		qf.Particles = append(qf.Particles, neutron)
		hadrons = append(hadrons, neutron)
	}

	return hadrons
}

// VacuumFluctuation produces a spontaneous virtual particle pair from vacuum energy.
func (qf *QuantumField) VacuumFluctuation() (*Particle, *Particle) {
	prob := math.Min(0.5, qf.Temperature/TPlanck)
	if qf.rng.Float64() < prob {
		lambda := 1.0 / (qf.Temperature * 0.001)
		if lambda <= 0 {
			return nil, nil
		}
		energy := qf.rng.ExpFloat64() / lambda
		return qf.PairProduction(energy)
	}
	return nil, nil
}

// Cool cools the field (universe expansion).
func (qf *QuantumField) Cool(factor float64) {
	qf.Temperature *= factor
}

// Evolve evolves all particles by one time step.
func (qf *QuantumField) Evolve(dt float64) {
	for _, p := range qf.Particles {
		mass := p.Mass()
		if mass > 0 {
			for i := 0; i < 3; i++ {
				p.Position[i] += p.Momentum[i] / mass * dt
			}
		} else {
			pMag := math.Sqrt(p.Momentum[0]*p.Momentum[0] + p.Momentum[1]*p.Momentum[1] + p.Momentum[2]*p.Momentum[2])
			if pMag < 1e-20 {
				pMag = 1.0
			}
			for i := 0; i < 3; i++ {
				p.Position[i] += p.Momentum[i] / pMag * C * dt
			}
		}
		p.WaveFn.Evolve(dt, p.Energy())
	}
}

// ParticleCount returns counts of particles by type name.
func (qf *QuantumField) ParticleCount() map[string]int {
	counts := make(map[string]int)
	for _, p := range qf.Particles {
		counts[p.Type.String()]++
	}
	return counts
}

// TotalEnergy returns the total energy in the field.
func (qf *QuantumField) TotalEnergy() float64 {
	total := qf.VacuumEnergy
	for _, p := range qf.Particles {
		total += p.Energy()
	}
	return total
}
