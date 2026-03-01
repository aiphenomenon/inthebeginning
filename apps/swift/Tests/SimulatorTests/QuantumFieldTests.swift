// QuantumFieldTests.swift
// Tests for QuantumField.swift

import XCTest
@testable import InTheBeginningSimulator

final class QuantumFieldTests: XCTestCase {

    // MARK: - ParticleType

    func testParticleTypeAllCases() {
        XCTAssertEqual(ParticleType.allCases.count, 11)
    }

    func testParticleTypeRawValues() {
        XCTAssertEqual(ParticleType.up.rawValue, "up")
        XCTAssertEqual(ParticleType.proton.rawValue, "proton")
        XCTAssertEqual(ParticleType.photon.rawValue, "photon")
    }

    // MARK: - Spin

    func testSpinValues() {
        XCTAssertEqual(Spin.up.rawValue, 0.5)
        XCTAssertEqual(Spin.down.rawValue, -0.5)
    }

    func testSpinRandom() {
        var gotUp = false
        var gotDown = false
        for _ in 0..<100 {
            let s = Spin.random()
            if s == .up { gotUp = true }
            if s == .down { gotDown = true }
        }
        XCTAssertTrue(gotUp, "Expected to get spin up in 100 trials")
        XCTAssertTrue(gotDown, "Expected to get spin down in 100 trials")
    }

    // MARK: - QuarkColor

    func testQuarkColorAllCases() {
        XCTAssertEqual(QuarkColor.allCases.count, 6)
    }

    // MARK: - ParticleProperties

    func testMassLookup() {
        XCTAssertEqual(ParticleProperties.mass(of: .electron), ParticleMass.electron)
        XCTAssertEqual(ParticleProperties.mass(of: .proton), ParticleMass.proton)
        XCTAssertEqual(ParticleProperties.mass(of: .photon), ParticleMass.photon)
    }

    func testChargeLookup() {
        XCTAssertEqual(ParticleProperties.charge(of: .electron), -1.0)
        XCTAssertEqual(ParticleProperties.charge(of: .positron), 1.0)
        XCTAssertEqual(ParticleProperties.charge(of: .proton), 1.0)
        XCTAssertEqual(ParticleProperties.charge(of: .neutron), 0.0)
        XCTAssertEqual(ParticleProperties.charge(of: .photon), 0.0)
    }

    func testQuarkCharges() {
        XCTAssertEqual(ParticleProperties.charge(of: .up), 2.0 / 3.0, accuracy: 1e-10)
        XCTAssertEqual(ParticleProperties.charge(of: .down), -1.0 / 3.0, accuracy: 1e-10)
    }

    // MARK: - WaveFunction

    func testWaveFunctionDefaults() {
        let wf = WaveFunction()
        XCTAssertEqual(wf.amplitude, 1.0)
        XCTAssertEqual(wf.phase, 0.0)
        XCTAssertTrue(wf.coherent)
    }

    func testWaveFunctionProbability() {
        let wf = WaveFunction(amplitude: 0.5, phase: 0.0)
        XCTAssertEqual(wf.probability, 0.25, accuracy: 1e-10)
    }

    func testWaveFunctionProbabilityFullAmplitude() {
        let wf = WaveFunction()
        XCTAssertEqual(wf.probability, 1.0)
    }

    func testWaveFunctionEvolve() {
        var wf = WaveFunction()
        wf.evolve(dt: 1.0, energy: 1.0)
        XCTAssertNotEqual(wf.phase, 0.0)
        XCTAssertTrue(wf.coherent)
    }

    func testWaveFunctionEvolveIncoherent() {
        var wf = WaveFunction()
        wf.coherent = false
        let phaseBefore = wf.phase
        wf.evolve(dt: 1.0, energy: 1.0)
        XCTAssertEqual(wf.phase, phaseBefore)
    }

    func testWaveFunctionCollapse() {
        var wf = WaveFunction()
        let _ = wf.collapse()
        XCTAssertFalse(wf.coherent)
        XCTAssertTrue(wf.amplitude == 0.0 || wf.amplitude == 1.0)
    }

    func testWaveFunctionSuperposition() {
        let wf1 = WaveFunction(amplitude: 0.7, phase: 0.0)
        let wf2 = WaveFunction(amplitude: 0.7, phase: 0.0)
        let superposed = wf1.superposed(with: wf2)
        XCTAssertTrue(superposed.coherent)
        XCTAssertGreaterThan(superposed.amplitude, 0.0)
        XCTAssertLessThanOrEqual(superposed.amplitude, 1.0)
    }

    func testSuperpositionConstructiveInterference() {
        let wf1 = WaveFunction(amplitude: 0.5, phase: 0.0)
        let wf2 = WaveFunction(amplitude: 0.5, phase: 0.0)
        let result = wf1.superposed(with: wf2)
        // Same phase => constructive interference => higher amplitude
        XCTAssertGreaterThan(result.amplitude, 0.5)
    }

    // MARK: - Particle

    func testParticleCreation() {
        let p = Particle(particleType: .electron)
        XCTAssertEqual(p.particleType, .electron)
        XCTAssertEqual(p.position, .zero)
        XCTAssertEqual(p.momentum, .zero)
        XCTAssertEqual(p.spin, .up)
        XCTAssertNil(p.color)
        XCTAssertNil(p.entangledWithID)
    }

    func testParticleUniqueIDs() {
        let p1 = Particle(particleType: .electron)
        let p2 = Particle(particleType: .electron)
        XCTAssertNotEqual(p1.id, p2.id)
    }

    func testParticleMass() {
        let electron = Particle(particleType: .electron)
        XCTAssertEqual(electron.mass, ParticleMass.electron)

        let proton = Particle(particleType: .proton)
        XCTAssertEqual(proton.mass, ParticleMass.proton)
    }

    func testParticleCharge() {
        let electron = Particle(particleType: .electron)
        XCTAssertEqual(electron.charge, -1.0)

        let proton = Particle(particleType: .proton)
        XCTAssertEqual(proton.charge, 1.0)
    }

    func testParticleEnergy() {
        let p = Particle(particleType: .electron, momentum: SIMD3<Double>(1.0, 0.0, 0.0))
        XCTAssertGreaterThan(p.energy, 0.0)
    }

    func testPhotonEnergyFromMomentum() {
        let photon = Particle(particleType: .photon, momentum: SIMD3<Double>(1.0, 0.0, 0.0))
        XCTAssertGreaterThan(photon.energy, 0.0)
    }

    func testParticleWavelength() {
        let p = Particle(particleType: .electron, momentum: SIMD3<Double>(1.0, 0.0, 0.0))
        XCTAssertTrue(p.wavelength.isFinite)
        XCTAssertGreaterThan(p.wavelength, 0.0)
    }

    func testParticleZeroMomentumWavelength() {
        let p = Particle(particleType: .electron)
        XCTAssertTrue(p.wavelength.isInfinite)
    }

    func testParticleWithPosition() {
        let pos = SIMD3<Double>(1.0, 2.0, 3.0)
        let p = Particle(particleType: .proton, position: pos)
        XCTAssertEqual(p.position, pos)
    }

    func testParticleWithColor() {
        let p = Particle(particleType: .up, color: .red)
        XCTAssertEqual(p.color, .red)
    }

    // MARK: - IDGenerator

    func testIDGeneratorMonotonic() {
        let gen = IDGenerator()
        let id1 = gen.next()
        let id2 = gen.next()
        let id3 = gen.next()
        XCTAssertLessThan(id1, id2)
        XCTAssertLessThan(id2, id3)
    }

    // MARK: - EntangledPair

    func testEntangledPairCreation() {
        let a = Particle(particleType: .electron)
        let b = Particle(particleType: .positron)
        let pair = EntangledPair(a: a, b: b)
        XCTAssertEqual(pair.bellState, "phi+")
        XCTAssertEqual(pair.particleA.id, a.id)
        XCTAssertEqual(pair.particleB.id, b.id)
    }

    func testEntangledPairMeasurement() {
        let a = Particle(particleType: .electron, spin: .up)
        let b = Particle(particleType: .positron, spin: .up)
        let pair = EntangledPair(a: a, b: b)
        let spinA = pair.measureA()
        // Measurement collapses wave functions
        XCTAssertFalse(a.waveFn.coherent)
        XCTAssertFalse(b.waveFn.coherent)
        // Spins should be anti-correlated
        if spinA == .up {
            XCTAssertEqual(b.spin, .down)
        } else {
            XCTAssertEqual(b.spin, .up)
        }
    }

    // MARK: - QuantumField

    func testQuantumFieldInit() {
        let field = QuantumField()
        XCTAssertEqual(field.temperature, TemperatureScale.planck)
        XCTAssertTrue(field.particles.isEmpty)
        XCTAssertEqual(field.vacuumEnergy, 0.0)
        XCTAssertEqual(field.totalCreated, 0)
        XCTAssertEqual(field.totalAnnihilated, 0)
    }

    func testQuantumFieldCustomTemperature() {
        let field = QuantumField(temperature: 1000.0)
        XCTAssertEqual(field.temperature, 1000.0)
    }

    func testPairProduction() {
        let field = QuantumField()
        let minEnergy = 2.0 * ParticleMass.electron * PhysicsConstants.c * PhysicsConstants.c
        let result = field.pairProduction(energy: minEnergy * 2.0)
        XCTAssertNotNil(result)
        XCTAssertEqual(field.particles.count, 2)
        XCTAssertEqual(field.totalCreated, 2)
    }

    func testPairProductionInsufficientEnergy() {
        let field = QuantumField()
        let result = field.pairProduction(energy: 0.001)
        XCTAssertNil(result)
        XCTAssertTrue(field.particles.isEmpty)
    }

    func testPairProductionEntanglement() {
        let field = QuantumField()
        let energy = 2.0 * ParticleMass.electron * PhysicsConstants.c * PhysicsConstants.c * 2.0
        let result = field.pairProduction(energy: energy)
        XCTAssertNotNil(result)
        if let (p1, p2) = result {
            XCTAssertEqual(p1.entangledWithID, p2.id)
            XCTAssertEqual(p2.entangledWithID, p1.id)
        }
        XCTAssertEqual(field.entangledPairs.count, 1)
    }

    func testAnnihilate() {
        let field = QuantumField()
        let energy = 2.0 * ParticleMass.electron * PhysicsConstants.c * PhysicsConstants.c * 10.0
        guard let (p1, p2) = field.pairProduction(energy: energy) else {
            XCTFail("Pair production failed")
            return
        }
        let initialCount = field.particles.count
        let releasedEnergy = field.annihilate(p1, p2)
        XCTAssertGreaterThan(releasedEnergy, 0.0)
        // Original pair removed, two photons added
        XCTAssertEqual(field.particles.count, initialCount - 2 + 2)
        XCTAssertEqual(field.totalAnnihilated, 2)
        // The remaining particles should be photons
        XCTAssertTrue(field.particles.allSatisfy { $0.particleType == .photon })
    }

    func testQuarkConfinementBelowThreshold() {
        let field = QuantumField(temperature: TemperatureScale.quarkHadron * 0.5)
        // Add quarks
        let u1 = Particle(particleType: .up)
        let u2 = Particle(particleType: .up)
        let d1 = Particle(particleType: .down)
        field.particles.append(contentsOf: [u1, u2, d1])

        let hadrons = field.quarkConfinement()
        // 2 ups + 1 down = 1 proton
        XCTAssertFalse(hadrons.isEmpty)
        let protons = hadrons.filter { $0.particleType == .proton }
        XCTAssertEqual(protons.count, 1)
    }

    func testQuarkConfinementAboveThreshold() {
        let field = QuantumField(temperature: TemperatureScale.quarkHadron * 2.0)
        let u1 = Particle(particleType: .up)
        let u2 = Particle(particleType: .up)
        let d1 = Particle(particleType: .down)
        field.particles.append(contentsOf: [u1, u2, d1])

        let hadrons = field.quarkConfinement()
        XCTAssertTrue(hadrons.isEmpty, "Should not confine above quark-hadron temperature")
    }

    func testQuarkConfinementNeutron() {
        let field = QuantumField(temperature: TemperatureScale.quarkHadron * 0.5)
        let u1 = Particle(particleType: .up)
        let d1 = Particle(particleType: .down)
        let d2 = Particle(particleType: .down)
        field.particles.append(contentsOf: [u1, d1, d2])

        let hadrons = field.quarkConfinement()
        let neutrons = hadrons.filter { $0.particleType == .neutron }
        XCTAssertEqual(neutrons.count, 1)
    }

    func testCool() {
        let field = QuantumField(temperature: 1000.0)
        field.cool(factor: 0.5)
        XCTAssertEqual(field.temperature, 500.0)
    }

    func testCoolDefaultFactor() {
        let field = QuantumField(temperature: 1000.0)
        field.cool()
        XCTAssertEqual(field.temperature, 999.0, accuracy: 0.1)
    }

    func testEvolve() {
        let field = QuantumField()
        let p = Particle(particleType: .electron, momentum: SIMD3<Double>(1.0, 0.0, 0.0))
        field.particles.append(p)
        let posBefore = p.position
        field.evolve(dt: 1.0)
        XCTAssertNotEqual(p.position, posBefore)
    }

    func testEvolvePhoton() {
        let field = QuantumField()
        let photon = Particle(particleType: .photon, momentum: SIMD3<Double>(1.0, 0.0, 0.0))
        field.particles.append(photon)
        field.evolve(dt: 1.0)
        // Photon should have moved
        XCTAssertNotEqual(photon.position, .zero)
    }

    func testDecohere() {
        let field = QuantumField(temperature: 1000.0)
        let p = Particle(particleType: .electron)
        XCTAssertTrue(p.waveFn.coherent)
        // With high temperature and coupling, decoherence should happen eventually
        for _ in 0..<100 {
            field.decohere(p, environmentCoupling: 1.0)
            if !p.waveFn.coherent { break }
        }
        // With coupling=1.0 and temperature=1000, decoherence rate is 1000, so very likely
        XCTAssertFalse(p.waveFn.coherent)
    }

    func testParticleCount() {
        let field = QuantumField()
        let e = Particle(particleType: .electron)
        let p = Particle(particleType: .proton)
        let photon = Particle(particleType: .photon)
        field.particles.append(contentsOf: [e, p, photon])

        let counts = field.particleCount()
        XCTAssertEqual(counts[.electron], 1)
        XCTAssertEqual(counts[.proton], 1)
        XCTAssertEqual(counts[.photon], 1)
    }

    func testTotalEnergy() {
        let field = QuantumField()
        XCTAssertEqual(field.totalEnergy(), 0.0)

        let p = Particle(particleType: .electron, momentum: SIMD3<Double>(1.0, 0.0, 0.0))
        field.particles.append(p)
        XCTAssertGreaterThan(field.totalEnergy(), 0.0)
    }

    func testTotalEnergyIncludesVacuum() {
        let field = QuantumField()
        field.vacuumEnergy = 100.0
        XCTAssertEqual(field.totalEnergy(), 100.0)
    }

    func testVacuumFluctuationAtHighTemp() {
        let field = QuantumField(temperature: TemperatureScale.planck)
        // Run many attempts; at Planck temperature probability should be ~0.5
        var produced = false
        for _ in 0..<100 {
            if field.vacuumFluctuation() != nil {
                produced = true
                break
            }
        }
        XCTAssertTrue(produced, "Should produce virtual pairs at Planck temperature")
    }
}
