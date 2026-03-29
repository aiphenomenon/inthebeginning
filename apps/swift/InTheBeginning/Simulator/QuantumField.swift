// QuantumField.swift
// InTheBeginning
//
// Quantum and subatomic physics simulation.
// Models quantum fields, particles, wave functions, superposition,
// entanglement (simplified), and the quark-hadron transition.

import Foundation
#if canImport(simd)
import simd
#endif

// MARK: - Cross-platform SIMD helpers

private func vectorLength(_ v: SIMD3<Double>) -> Double {
    sqrt(v.x * v.x + v.y * v.y + v.z * v.z)
}

private func vectorLengthSquared(_ v: SIMD3<Double>) -> Double {
    v.x * v.x + v.y * v.y + v.z * v.z
}

// MARK: - Enums

enum ParticleType: String, CaseIterable, Sendable {
    case up = "up"
    case down = "down"
    case electron = "electron"
    case positron = "positron"
    case neutrino = "neutrino"
    case photon = "photon"
    case gluon = "gluon"
    case wBoson = "W"
    case zBoson = "Z"
    case proton = "proton"
    case neutron = "neutron"
}

enum Spin: Double, Sendable {
    case up = 0.5
    case down = -0.5

    static func random() -> Spin {
        Bool.random() ? .up : .down
    }
}

enum QuarkColor: String, CaseIterable, Sendable {
    case red = "r"
    case green = "g"
    case blue = "b"
    case antiRed = "ar"
    case antiGreen = "ag"
    case antiBlue = "ab"
}

// MARK: - Particle Properties Lookup

enum ParticleProperties {
    static func mass(of type: ParticleType) -> Double {
        switch type {
        case .up:       return ParticleMass.upQuark
        case .down:     return ParticleMass.downQuark
        case .electron: return ParticleMass.electron
        case .positron: return ParticleMass.electron
        case .neutrino: return ParticleMass.neutrino
        case .photon:   return ParticleMass.photon
        case .gluon:    return ParticleMass.photon
        case .proton:   return ParticleMass.proton
        case .neutron:  return ParticleMass.neutron
        case .wBoson:   return ParticleMass.wBoson
        case .zBoson:   return ParticleMass.zBoson
        }
    }

    static func charge(of type: ParticleType) -> Double {
        switch type {
        case .up:       return 2.0 / 3.0
        case .down:     return -1.0 / 3.0
        case .electron: return -1.0
        case .positron: return 1.0
        case .neutrino: return 0.0
        case .photon:   return 0.0
        case .gluon:    return 0.0
        case .proton:   return 1.0
        case .neutron:  return 0.0
        case .wBoson:   return 1.0
        case .zBoson:   return 0.0
        }
    }

    /// Color used for rendering this particle type
    static func displayColor(of type: ParticleType) -> SIMD4<Float> {
        switch type {
        case .up:       return SIMD4<Float>(1.0, 0.3, 0.3, 1.0)   // Red
        case .down:     return SIMD4<Float>(0.3, 0.3, 1.0, 1.0)   // Blue
        case .electron: return SIMD4<Float>(0.2, 0.8, 1.0, 1.0)   // Cyan
        case .positron: return SIMD4<Float>(1.0, 0.8, 0.2, 1.0)   // Gold
        case .neutrino: return SIMD4<Float>(0.6, 0.6, 0.6, 0.4)   // Gray (ghostly)
        case .photon:   return SIMD4<Float>(1.0, 1.0, 0.8, 0.9)   // White-yellow
        case .gluon:    return SIMD4<Float>(0.0, 1.0, 0.0, 0.8)   // Green
        case .proton:   return SIMD4<Float>(1.0, 0.4, 0.1, 1.0)   // Orange-red
        case .neutron:  return SIMD4<Float>(0.5, 0.5, 0.7, 1.0)   // Blue-gray
        case .wBoson:   return SIMD4<Float>(0.9, 0.2, 0.9, 0.8)   // Magenta
        case .zBoson:   return SIMD4<Float>(0.7, 0.2, 1.0, 0.8)   // Purple
        }
    }
}

// MARK: - Wave Function

struct WaveFunction: Sendable {
    var amplitude: Double = 1.0
    var phase: Double = 0.0
    var coherent: Bool = true

    var probability: Double { amplitude * amplitude }

    mutating func evolve(dt: Double, energy: Double) {
        guard coherent else { return }
        phase += energy * dt / PhysicsConstants.hbar
        phase = phase.truncatingRemainder(dividingBy: 2.0 * .pi)
    }

    mutating func collapse() -> Bool {
        let result = Double.random(in: 0...1) < probability
        amplitude = result ? 1.0 : 0.0
        coherent = false
        return result
    }

    func superposed(with other: WaveFunction) -> WaveFunction {
        let phaseDiff = phase - other.phase
        let combinedAmp = sqrt(
            amplitude * amplitude + other.amplitude * other.amplitude
            + 2.0 * amplitude * other.amplitude * cos(phaseDiff)
        )
        return WaveFunction(
            amplitude: min(combinedAmp, 1.0),
            phase: (phase + other.phase) / 2.0,
            coherent: true
        )
    }
}

// MARK: - Particle

final class Particle: Identifiable, Sendable {
    static let idGenerator = IDGenerator()

    let id: Int
    let particleType: ParticleType
    var position: SIMD3<Double>
    var momentum: SIMD3<Double>
    var spin: Spin
    var color: QuarkColor?
    var waveFn: WaveFunction
    var entangledWithID: Int?

    var mass: Double { ParticleProperties.mass(of: particleType) }
    var charge: Double { ParticleProperties.charge(of: particleType) }

    var energy: Double {
        let p2 = vectorLengthSquared(momentum)
        let mc2 = mass * PhysicsConstants.c * PhysicsConstants.c
        return sqrt(p2 * PhysicsConstants.c * PhysicsConstants.c + mc2 * mc2)
    }

    var wavelength: Double {
        let p = vectorLength(momentum)
        guard p > 1e-20 else { return .infinity }
        return 2.0 * .pi * PhysicsConstants.hbar / p
    }

    init(
        particleType: ParticleType,
        position: SIMD3<Double> = .zero,
        momentum: SIMD3<Double> = .zero,
        spin: Spin = .up,
        color: QuarkColor? = nil,
        waveFn: WaveFunction = WaveFunction(),
        entangledWithID: Int? = nil
    ) {
        self.id = Particle.idGenerator.next()
        self.particleType = particleType
        self.position = position
        self.momentum = momentum
        self.spin = spin
        self.color = color
        self.waveFn = waveFn
        self.entangledWithID = entangledWithID
    }
}

// MARK: - Thread-safe ID Generator

final class IDGenerator: Sendable {
    private let lock = NSLock()
    private var _value: Int = 0

    func next() -> Int {
        lock.lock()
        defer { lock.unlock() }
        _value += 1
        return _value
    }
}

// MARK: - Entangled Pair

struct EntangledPair {
    let particleA: Particle
    let particleB: Particle
    let bellState: String

    init(a: Particle, b: Particle, bellState: String = "phi+") {
        self.particleA = a
        self.particleB = b
        self.bellState = bellState
    }

    func measureA() -> Spin {
        if Bool.random() {
            particleA.spin = .up
            particleB.spin = .down
        } else {
            particleA.spin = .down
            particleB.spin = .up
        }
        particleA.waveFn.coherent = false
        particleB.waveFn.coherent = false
        return particleA.spin
    }
}

// MARK: - Quantum Field

final class QuantumField {
    var temperature: Double
    var particles: [Particle] = []
    var entangledPairs: [EntangledPair] = []
    var vacuumEnergy: Double = 0.0
    var totalCreated: Int = 0
    var totalAnnihilated: Int = 0

    init(temperature: Double = TemperatureScale.planck) {
        self.temperature = temperature
    }

    // MARK: - Pair Production

    /// Create a particle-antiparticle pair from vacuum energy.
    /// Requires E >= 2mc^2 for the lightest possible pair.
    func pairProduction(energy: Double) -> (Particle, Particle)? {
        let minEnergy = 2.0 * ParticleMass.electron * PhysicsConstants.c * PhysicsConstants.c
        guard energy >= minEnergy else { return nil }

        let pType: ParticleType
        let apType: ParticleType

        let protonThreshold = 2.0 * ParticleMass.proton * PhysicsConstants.c * PhysicsConstants.c
        if energy >= protonThreshold && Double.random(in: 0...1) < 0.1 {
            pType = .up
            apType = .down
        } else {
            pType = .electron
            apType = .positron
        }

        let direction = SIMD3<Double>(
            Double.random(in: -1...1),
            Double.random(in: -1...1),
            Double.random(in: -1...1)
        )
        let norm = max(vectorLength(direction), 1e-10)
        let pMomentum = energy / (2.0 * PhysicsConstants.c)
        let dir = direction / norm

        let particle = Particle(
            particleType: pType,
            momentum: dir * pMomentum,
            spin: .up
        )
        let antiparticle = Particle(
            particleType: apType,
            momentum: -dir * pMomentum,
            spin: .down
        )

        particle.entangledWithID = antiparticle.id
        antiparticle.entangledWithID = particle.id

        particles.append(particle)
        particles.append(antiparticle)
        entangledPairs.append(EntangledPair(a: particle, b: antiparticle))
        totalCreated += 2

        return (particle, antiparticle)
    }

    // MARK: - Annihilation

    func annihilate(_ p1: Particle, _ p2: Particle) -> Double {
        let energy = p1.energy + p2.energy
        particles.removeAll { $0.id == p1.id || $0.id == p2.id }
        totalAnnihilated += 2
        vacuumEnergy += energy * 0.01

        let photon1 = Particle(
            particleType: .photon,
            momentum: SIMD3<Double>(energy / (2.0 * PhysicsConstants.c), 0, 0)
        )
        let photon2 = Particle(
            particleType: .photon,
            momentum: SIMD3<Double>(-energy / (2.0 * PhysicsConstants.c), 0, 0)
        )
        particles.append(photon1)
        particles.append(photon2)
        return energy
    }

    // MARK: - Quark Confinement

    /// Combine quarks into hadrons when temperature drops enough.
    func quarkConfinement() -> [Particle] {
        guard temperature <= TemperatureScale.quarkHadron else { return [] }

        var hadrons: [Particle] = []
        var ups = particles.filter { $0.particleType == .up }
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
                particleType: .proton,
                position: u1.position,
                momentum: u1.momentum + u2.momentum + d1.momentum
            )

            particles.removeAll { $0.id == u1.id || $0.id == u2.id || $0.id == d1.id }
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
                particleType: .neutron,
                position: u1.position,
                momentum: u1.momentum + d1.momentum + d2.momentum
            )

            particles.removeAll { $0.id == u1.id || $0.id == d1.id || $0.id == d2.id }
            particles.append(neutron)
            hadrons.append(neutron)
        }

        return hadrons
    }

    // MARK: - Vacuum Fluctuation

    /// Spontaneous virtual particle pair from vacuum energy.
    func vacuumFluctuation() -> (Particle, Particle)? {
        let prob = min(0.5, temperature / TemperatureScale.planck)
        guard Double.random(in: 0...1) < prob else { return nil }
        let lambda = 1.0 / (temperature * 0.001)
        let energy = -log(Double.random(in: 0..<1)) * (1.0 / lambda)
        return pairProduction(energy: energy)
    }

    // MARK: - Decoherence

    func decohere(_ particle: Particle, environmentCoupling: Double = 0.1) {
        guard particle.waveFn.coherent else { return }
        let decoherenceRate = environmentCoupling * temperature
        if Double.random(in: 0...1) < decoherenceRate {
            _ = particle.waveFn.collapse()
        }
    }

    // MARK: - Cool

    func cool(factor: Double = 0.999) {
        temperature *= factor
    }

    // MARK: - Evolve

    /// Evolve all particles by one time step.
    func evolve(dt: Double = 1.0) {
        for p in particles {
            if p.mass > 0 {
                p.position += (p.momentum / p.mass) * dt
            } else {
                let pMag = max(vectorLength(p.momentum), 1e-10)
                p.position += (p.momentum / pMag) * PhysicsConstants.c * dt
            }
            p.waveFn.evolve(dt: dt, energy: p.energy)
        }
    }

    // MARK: - Statistics

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
