// QuantumField.swift
// InTheBeginning – macOS Screensaver
//
// Quantum and subatomic physics simulation.
// Models quantum fields, particles, wave functions, superposition,
// entanglement (simplified), and the quark-hadron transition.

import Foundation

// MARK: - Enums

enum ParticleType: String, CaseIterable {
    case up       = "up"
    case down     = "down"
    case electron = "electron"
    case positron = "positron"
    case neutrino = "neutrino"
    case photon   = "photon"
    case gluon    = "gluon"
    case wBoson   = "W"
    case zBoson   = "Z"
    case proton   = "proton"
    case neutron  = "neutron"
}

enum Spin: Double {
    case up   =  0.5
    case down = -0.5
}

enum QuarkColor: String {
    case red       = "r"
    case green     = "g"
    case blue      = "b"
    case antiRed   = "ar"
    case antiGreen = "ag"
    case antiBlue  = "ab"
}

// MARK: - Mass / Charge Tables

func particleMass(_ type: ParticleType) -> Double {
    switch type {
    case .up:       return kMassUpQuark
    case .down:     return kMassDownQuark
    case .electron: return kMassElectron
    case .positron: return kMassElectron
    case .neutrino: return kMassNeutrino
    case .photon:   return kMassPhoton
    case .gluon:    return kMassPhoton
    case .proton:   return kMassProton
    case .neutron:  return kMassNeutron
    case .wBoson:   return kMassWBoson
    case .zBoson:   return kMassZBoson
    }
}

func particleCharge(_ type: ParticleType) -> Double {
    switch type {
    case .up:       return  2.0 / 3.0
    case .down:     return -1.0 / 3.0
    case .electron: return -1.0
    case .positron: return  1.0
    case .neutrino: return  0.0
    case .photon:   return  0.0
    case .gluon:    return  0.0
    case .proton:   return  1.0
    case .neutron:  return  0.0
    case .wBoson:   return  1.0
    case .zBoson:   return  0.0
    }
}

// MARK: - Wave Function

struct WaveFunction {
    var amplitude: Double = 1.0
    var phase: Double     = 0.0
    var coherent: Bool    = true

    var probability: Double { amplitude * amplitude }

    mutating func evolve(dt: Double, energy: Double) {
        guard coherent else { return }
        phase += energy * dt / kHBar
        phase = phase.truncatingRemainder(dividingBy: 2.0 * kPi)
    }

    mutating func collapse() -> Bool {
        let result = Double.random(in: 0..<1) < probability
        amplitude = result ? 1.0 : 0.0
        coherent = false
        return result
    }
}

// MARK: - Particle

private var _particleIDCounter: Int = 0

final class Particle {
    let particleID: Int
    var particleType: ParticleType
    var position: SIMD3<Double>
    var momentum: SIMD3<Double>
    var spin: Spin
    var color: QuarkColor?
    var waveFn: WaveFunction
    var entangledWith: Int?

    var mass: Double   { particleMass(particleType) }
    var charge: Double { particleCharge(particleType) }

    /// Relativistic energy: E = sqrt(p^2 c^2 + m^2 c^4)
    var energy: Double {
        let p2 = simd_length_squared(momentum)
        let m = mass
        return (p2 * kSpeedOfLight * kSpeedOfLight
              + m * m * pow(kSpeedOfLight, 4)).squareRoot()
    }

    init(type: ParticleType,
         position: SIMD3<Double> = .zero,
         momentum: SIMD3<Double> = .zero,
         spin: Spin = .up,
         color: QuarkColor? = nil) {
        _particleIDCounter += 1
        self.particleID = _particleIDCounter
        self.particleType = type
        self.position = position
        self.momentum = momentum
        self.spin = spin
        self.color = color
        self.waveFn = WaveFunction()
        self.entangledWith = nil
    }
}

// MARK: - Entangled Pair

struct EntangledPair {
    let particleA: Particle
    let particleB: Particle
}

// MARK: - Quantum Field

final class QuantumField {
    var temperature: Double
    var particles: [Particle] = []
    var entangledPairs: [EntangledPair] = []
    var vacuumEnergy: Double = 0.0
    var totalCreated: Int = 0
    var totalAnnihilated: Int = 0

    init(temperature: Double = kTempPlanck) {
        self.temperature = temperature
    }

    /// Reset the quantum field to initial conditions for a new cycle.
    func reset(temperature: Double) {
        self.temperature = temperature
        particles.removeAll()
        entangledPairs.removeAll()
        vacuumEnergy = 0.0
        totalCreated = 0
        totalAnnihilated = 0
    }

    // MARK: Pair Production

    /// Create particle-antiparticle pair from vacuum energy.
    /// Requires E >= 2 m_e c^2 for the lightest pair.
    @discardableResult
    func pairProduction(energy: Double) -> (Particle, Particle)? {
        let threshold = 2.0 * kMassElectron * kSpeedOfLight * kSpeedOfLight
        guard energy >= threshold else { return nil }

        let pType: ParticleType
        let apType: ParticleType

        let protonThreshold = 2.0 * kMassProton * kSpeedOfLight * kSpeedOfLight
        if energy >= protonThreshold && Double.random(in: 0..<1) < 0.1 {
            pType  = .up
            apType = .down
        } else {
            pType  = .electron
            apType = .positron
        }

        let dir = SIMD3<Double>(
            Double.random(in: -1...1),
            Double.random(in: -1...1),
            Double.random(in: -1...1)
        )
        let norm = max(simd_length(dir), 1e-20)
        let pMom = energy / (2.0 * kSpeedOfLight)
        let direction = dir / norm

        let particle = Particle(
            type: pType,
            momentum: direction * pMom,
            spin: .up
        )
        let antiparticle = Particle(
            type: apType,
            momentum: -direction * pMom,
            spin: .down
        )
        particle.entangledWith = antiparticle.particleID
        antiparticle.entangledWith = particle.particleID

        particles.append(particle)
        particles.append(antiparticle)
        entangledPairs.append(EntangledPair(particleA: particle, particleB: antiparticle))
        totalCreated += 2
        return (particle, antiparticle)
    }

    // MARK: Annihilation

    @discardableResult
    func annihilate(_ p1: Particle, _ p2: Particle) -> Double {
        let e = p1.energy + p2.energy
        particles.removeAll { $0 === p1 || $0 === p2 }
        totalAnnihilated += 2
        vacuumEnergy += e * 0.01

        let photon1 = Particle(type: .photon, momentum: SIMD3(e / (2.0 * kSpeedOfLight), 0, 0))
        let photon2 = Particle(type: .photon, momentum: SIMD3(-e / (2.0 * kSpeedOfLight), 0, 0))
        particles.append(photon1)
        particles.append(photon2)
        return e
    }

    // MARK: Quark Confinement

    /// Combine quarks into hadrons when temperature drops below quark-hadron transition.
    func quarkConfinement() -> [Particle] {
        guard temperature <= kTempQuarkHadron else { return [] }

        var hadrons: [Particle] = []
        var ups   = particles.filter { $0.particleType == .up }
        var downs = particles.filter { $0.particleType == .down }

        // Form protons (uud)
        while ups.count >= 2 && downs.count >= 1 {
            let u1 = ups.removeLast()
            let u2 = ups.removeLast()
            let d1 = downs.removeLast()

            u1.color = .red
            u2.color = .green
            d1.color = .blue

            let proton = Particle(
                type: .proton,
                position: u1.position,
                momentum: u1.momentum + u2.momentum + d1.momentum
            )
            particles.removeAll { $0 === u1 || $0 === u2 || $0 === d1 }
            particles.append(proton)
            hadrons.append(proton)
        }

        // Form neutrons (udd)
        while ups.count >= 1 && downs.count >= 2 {
            let u1 = ups.removeLast()
            let d1 = downs.removeLast()
            let d2 = downs.removeLast()

            u1.color = .red
            d1.color = .green
            d2.color = .blue

            let neutron = Particle(
                type: .neutron,
                position: u1.position,
                momentum: u1.momentum + d1.momentum + d2.momentum
            )
            particles.removeAll { $0 === u1 || $0 === d1 || $0 === d2 }
            particles.append(neutron)
            hadrons.append(neutron)
        }

        return hadrons
    }

    // MARK: Vacuum Fluctuation

    /// Spontaneous virtual particle pair from vacuum energy.
    @discardableResult
    func vacuumFluctuation() -> (Particle, Particle)? {
        let prob = min(0.5, temperature / kTempPlanck)
        guard Double.random(in: 0..<1) < prob else { return nil }
        let lambda = 1.0 / (temperature * 0.001)
        let energy = -lambda * log(Double.random(in: 0..<1))  // Exponential variate
        return pairProduction(energy: energy)
    }

    // MARK: Evolution

    /// Evolve all particles by one time step.
    func evolve(dt: Double = 1.0) {
        for p in particles {
            if p.mass > 0 {
                p.position += p.momentum / p.mass * dt
            } else {
                let pMag = max(simd_length(p.momentum), 1e-20)
                p.position += (p.momentum / pMag) * kSpeedOfLight * dt
            }
            p.waveFn.evolve(dt: dt, energy: p.energy)
        }
    }

    // MARK: Counting

    func particleCount() -> [ParticleType: Int] {
        var counts: [ParticleType: Int] = [:]
        for p in particles {
            counts[p.particleType, default: 0] += 1
        }
        return counts
    }

    func totalEnergy() -> Double {
        particles.reduce(0.0) { $0 + $1.energy } + vacuumEnergy
    }
}
