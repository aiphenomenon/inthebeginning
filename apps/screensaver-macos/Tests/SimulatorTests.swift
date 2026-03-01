// SimulatorTests.swift
// InTheBeginning -- macOS Screensaver
//
// Unit tests for the pure simulator logic (no UI/Metal dependencies).
// These tests cover Constants, QuantumField, AtomicSystem, ChemicalSystem,
// Biosphere, Environment, and Universe classes.
//
// NOTE: These tests require macOS and XCTest. They are not runnable in CI
// environments without macOS, but document the expected behavior of the
// simulation engine and can be run locally via:
//   swift test
// or from Xcode by adding this file to a test target.

import XCTest
@testable import InTheBeginning

// MARK: - Constants Tests

class ConstantsTests: XCTestCase {

    func testFundamentalConstants() {
        XCTAssertEqual(kSpeedOfLight, 1.0)
        XCTAssertEqual(kHBar, 0.01)
        XCTAssertEqual(kBoltzmann, 0.001)
        XCTAssertEqual(kFineStructure, 1.0 / 137.0, accuracy: 1e-10)
    }

    func testParticleMassOrdering() {
        // Electron is lightest massive particle
        XCTAssertLessThan(kMassElectron, kMassUpQuark)
        XCTAssertLessThan(kMassUpQuark, kMassDownQuark)
        XCTAssertLessThan(kMassDownQuark, kMassProton)
        XCTAssertLessThan(kMassProton, kMassNeutron)
        XCTAssertEqual(kMassPhoton, 0.0)
        XCTAssertEqual(kMassProton, 1836.0)
    }

    func testForceCouplingHierarchy() {
        // Strong > EM > Weak > Gravity
        XCTAssertGreaterThan(kStrongCoupling, kEMCoupling)
        XCTAssertGreaterThan(kEMCoupling, kWeakCoupling)
        XCTAssertGreaterThan(kWeakCoupling, kGravityCoupling)
    }

    func testEpochOrdering() {
        let epochs = Epoch.allCases
        for i in 1..<epochs.count {
            XCTAssertGreaterThan(epochs[i].rawValue, epochs[i - 1].rawValue,
                                 "\(epochs[i]) should come after \(epochs[i - 1])")
        }
    }

    func testEpochCurrentForTick() {
        XCTAssertEqual(Epoch.current(forTick: 1), .planck)
        XCTAssertEqual(Epoch.current(forTick: 5), .planck)
        XCTAssertEqual(Epoch.current(forTick: 10), .inflation)
        XCTAssertEqual(Epoch.current(forTick: 100), .electroweak)
        XCTAssertEqual(Epoch.current(forTick: 1000), .quark)
        XCTAssertEqual(Epoch.current(forTick: 5000), .hadron)
        XCTAssertEqual(Epoch.current(forTick: 10000), .nucleosynthesis)
        XCTAssertEqual(Epoch.current(forTick: 50000), .recombination)
        XCTAssertEqual(Epoch.current(forTick: 100000), .starFormation)
        XCTAssertEqual(Epoch.current(forTick: 200000), .solarSystem)
        XCTAssertEqual(Epoch.current(forTick: 210000), .earth)
        XCTAssertEqual(Epoch.current(forTick: 250000), .life)
        XCTAssertEqual(Epoch.current(forTick: 280000), .dna)
        XCTAssertEqual(Epoch.current(forTick: 300000), .present)
    }

    func testEpochNames() {
        XCTAssertEqual(Epoch.planck.name, "Planck")
        XCTAssertEqual(Epoch.present.name, "Present")
        XCTAssertEqual(Epoch.life.name, "Life")
    }

    func testEpochDescriptions() {
        XCTAssertTrue(Epoch.planck.description.contains("unified"))
        XCTAssertTrue(Epoch.life.description.contains("self-replicating"))
        XCTAssertTrue(Epoch.present.description.contains("intelligence"))
    }

    func testTemperatureOrdering() {
        XCTAssertGreaterThan(kTempPlanck, kTempElectroweak)
        XCTAssertGreaterThan(kTempElectroweak, kTempQuarkHadron)
        XCTAssertGreaterThan(kTempQuarkHadron, kTempNucleosynthesis)
        XCTAssertGreaterThan(kTempNucleosynthesis, kTempRecombination)
        XCTAssertGreaterThan(kTempRecombination, kTempCMB)
    }

    func testElectronShells() {
        XCTAssertEqual(kElectronShells[0], 2)   // 1s
        XCTAssertEqual(kElectronShells[1], 8)   // 2s2p
        XCTAssertEqual(kElectronShells.count, 7)
    }

    func testBondEnergyOrdering() {
        XCTAssertLessThan(kBondEnergyVanDerWaals, kBondEnergyHydrogen)
        XCTAssertLessThan(kBondEnergyHydrogen, kBondEnergyCovalent)
        XCTAssertLessThan(kBondEnergyCovalent, kBondEnergyIonic)
    }

    func testBiologyProbabilitiesValid() {
        XCTAssertGreaterThan(kMethylationProbability, 0.0)
        XCTAssertLessThan(kMethylationProbability, 1.0)
        XCTAssertGreaterThan(kDemethylationProbability, 0.0)
        XCTAssertLessThan(kDemethylationProbability, 1.0)
        XCTAssertGreaterThan(kUVMutationRate, 0.0)
        XCTAssertLessThan(kUVMutationRate, 1.0)
    }
}

// MARK: - Quantum Field Tests

class QuantumFieldTests: XCTestCase {

    func testParticleMassLookup() {
        XCTAssertEqual(particleMass(.photon), 0.0)
        XCTAssertEqual(particleMass(.electron), kMassElectron)
        XCTAssertEqual(particleMass(.proton), kMassProton)
        XCTAssertEqual(particleMass(.neutron), kMassNeutron)
        XCTAssertEqual(particleMass(.up), kMassUpQuark)
        XCTAssertEqual(particleMass(.down), kMassDownQuark)
    }

    func testParticleChargeLookup() {
        XCTAssertEqual(particleCharge(.electron), -1.0)
        XCTAssertEqual(particleCharge(.positron), 1.0)
        XCTAssertEqual(particleCharge(.proton), 1.0)
        XCTAssertEqual(particleCharge(.neutron), 0.0)
        XCTAssertEqual(particleCharge(.photon), 0.0)
        XCTAssertEqual(particleCharge(.up), 2.0 / 3.0, accuracy: 1e-10)
        XCTAssertEqual(particleCharge(.down), -1.0 / 3.0, accuracy: 1e-10)
    }

    func testWaveFunctionInit() {
        let wf = WaveFunction()
        XCTAssertEqual(wf.amplitude, 1.0)
        XCTAssertEqual(wf.phase, 0.0)
        XCTAssertTrue(wf.coherent)
        XCTAssertEqual(wf.probability, 1.0)
    }

    func testWaveFunctionEvolve() {
        var wf = WaveFunction()
        wf.evolve(dt: 1.0, energy: 1.0)
        // Phase should change: phase += energy * dt / hbar = 1.0 / 0.01 = 100
        XCTAssertNotEqual(wf.phase, 0.0)
        XCTAssertTrue(wf.coherent)
    }

    func testWaveFunctionEvolveIncoherent() {
        var wf = WaveFunction()
        wf.coherent = false
        wf.evolve(dt: 1.0, energy: 1.0)
        // Incoherent: phase should not change
        XCTAssertEqual(wf.phase, 0.0)
    }

    func testParticleCreation() {
        let p = Particle(type: .electron,
                         position: SIMD3(1.0, 2.0, 3.0),
                         momentum: SIMD3(0.1, 0.2, 0.3))
        XCTAssertEqual(p.particleType, .electron)
        XCTAssertEqual(p.position.x, 1.0)
        XCTAssertEqual(p.position.y, 2.0)
        XCTAssertEqual(p.position.z, 3.0)
        XCTAssertEqual(p.mass, kMassElectron)
        XCTAssertEqual(p.charge, -1.0)
    }

    func testParticleEnergyAtRest() {
        let p = Particle(type: .electron,
                         position: .zero,
                         momentum: .zero)
        // E = mc^2 when at rest
        let expected = kMassElectron * kSpeedOfLight * kSpeedOfLight
        XCTAssertEqual(p.energy, expected, accuracy: 1e-10)
    }

    func testParticleEnergyPhoton() {
        let p = Particle(type: .photon,
                         momentum: SIMD3(1.0, 0.0, 0.0))
        // E = |p|c for massless particle
        XCTAssertEqual(p.energy, 1.0 * kSpeedOfLight, accuracy: 1e-10)
    }

    func testQuantumFieldInit() {
        let qf = QuantumField(temperature: 1e6)
        XCTAssertEqual(qf.temperature, 1e6)
        XCTAssertTrue(qf.particles.isEmpty)
        XCTAssertEqual(qf.totalCreated, 0)
        XCTAssertEqual(qf.totalAnnihilated, 0)
    }

    func testPairProductionBelowThreshold() {
        let qf = QuantumField(temperature: 1e6)
        // Energy below 2 * m_e * c^2 should fail
        let result = qf.pairProduction(energy: 0.5)
        XCTAssertNil(result)
        XCTAssertTrue(qf.particles.isEmpty)
    }

    func testPairProductionAboveThreshold() {
        let qf = QuantumField(temperature: 1e6)
        let energy = 2.0 * kMassElectron * kSpeedOfLight * kSpeedOfLight + 10.0
        let result = qf.pairProduction(energy: energy)
        XCTAssertNotNil(result)
        XCTAssertEqual(qf.particles.count, 2)
        XCTAssertEqual(qf.totalCreated, 2)
    }

    func testAnnihilation() {
        let qf = QuantumField(temperature: 1e6)
        let p1 = Particle(type: .electron, momentum: SIMD3(1.0, 0, 0))
        let p2 = Particle(type: .positron, momentum: SIMD3(-1.0, 0, 0))
        qf.particles.append(p1)
        qf.particles.append(p2)

        let energy = qf.annihilate(p1, p2)
        XCTAssertGreaterThan(energy, 0.0)
        XCTAssertEqual(qf.totalAnnihilated, 2)
        // Should have 2 photons remaining
        let photons = qf.particles.filter { $0.particleType == .photon }
        XCTAssertEqual(photons.count, 2)
    }

    func testQuarkConfinementAboveThreshold() {
        let qf = QuantumField(temperature: kTempQuarkHadron * 2.0)
        // Temperature too high: no confinement
        let hadrons = qf.quarkConfinement()
        XCTAssertTrue(hadrons.isEmpty)
    }

    func testQuarkConfinementBelowThreshold() {
        let qf = QuantumField(temperature: kTempQuarkHadron * 0.5)
        // Add quarks manually
        for _ in 0..<6 {
            qf.particles.append(Particle(type: .up))
        }
        for _ in 0..<4 {
            qf.particles.append(Particle(type: .down))
        }

        let hadrons = qf.quarkConfinement()
        XCTAssertFalse(hadrons.isEmpty)

        let protons = hadrons.filter { $0.particleType == .proton }
        let neutrons = hadrons.filter { $0.particleType == .neutron }
        XCTAssertTrue(protons.count > 0 || neutrons.count > 0)
    }

    func testEvolveMassiveParticle() {
        let qf = QuantumField(temperature: 1e6)
        let p = Particle(type: .electron,
                         position: .zero,
                         momentum: SIMD3(1.0, 0.0, 0.0))
        qf.particles.append(p)

        qf.evolve(dt: 1.0)
        // position += momentum / mass * dt = 1.0 / 1.0 * 1.0 = 1.0
        XCTAssertEqual(p.position.x, 1.0, accuracy: 1e-10)
    }

    func testEvolvePhoton() {
        let qf = QuantumField(temperature: 1e6)
        let p = Particle(type: .photon,
                         position: .zero,
                         momentum: SIMD3(1.0, 0.0, 0.0))
        qf.particles.append(p)

        qf.evolve(dt: 1.0)
        // Photon moves at c in direction of momentum
        XCTAssertEqual(p.position.x, kSpeedOfLight, accuracy: 1e-10)
    }

    func testParticleCount() {
        let qf = QuantumField()
        qf.particles.append(Particle(type: .electron))
        qf.particles.append(Particle(type: .electron))
        qf.particles.append(Particle(type: .proton))

        let counts = qf.particleCount()
        XCTAssertEqual(counts[.electron], 2)
        XCTAssertEqual(counts[.proton], 1)
    }

    func testTotalEnergy() {
        let qf = QuantumField()
        qf.particles.append(Particle(type: .electron, momentum: .zero))
        qf.vacuumEnergy = 5.0

        let total = qf.totalEnergy()
        // At least mass-energy + vacuum energy
        XCTAssertGreaterThan(total, 5.0)
    }
}

// MARK: - Atomic System Tests

class AtomicSystemTests: XCTestCase {

    func testAtomCreation() {
        let atom = Atom(atomicNumber: 1, massNumber: 1)
        XCTAssertEqual(atom.atomicNumber, 1)
        XCTAssertEqual(atom.massNumber, 1)
        XCTAssertEqual(atom.electronCount, 1)
        XCTAssertEqual(atom.symbol, "H")
        XCTAssertEqual(atom.name, "Hydrogen")
        XCTAssertTrue(atom.bonds.isEmpty)
    }

    func testAtomDefaultMassNumber() {
        let carbon = Atom(atomicNumber: 6)
        XCTAssertEqual(carbon.massNumber, 12) // z * 2 for non-hydrogen

        let hydrogen = Atom(atomicNumber: 1)
        XCTAssertEqual(hydrogen.massNumber, 1) // Special case for hydrogen
    }

    func testAtomElectronegativity() {
        let h = Atom(atomicNumber: 1)
        XCTAssertEqual(h.electronegativity, 2.20, accuracy: 0.01)

        let o = Atom(atomicNumber: 8)
        XCTAssertEqual(o.electronegativity, 3.44, accuracy: 0.01)
    }

    func testAtomCharge() {
        let neutral = Atom(atomicNumber: 6, electronCount: 6)
        XCTAssertEqual(neutral.charge, 0)

        let ion = Atom(atomicNumber: 11, electronCount: 10)
        XCTAssertEqual(ion.charge, 1) // Na+
    }

    func testAtomNobleGas() {
        let he = Atom(atomicNumber: 2) // He: 2 electrons, first shell full
        XCTAssertTrue(he.isNobleGas)

        let c = Atom(atomicNumber: 6) // C: not noble
        XCTAssertFalse(c.isNobleGas)
    }

    func testAtomCanBondWith() {
        let h1 = Atom(atomicNumber: 1)
        let h2 = Atom(atomicNumber: 1)
        XCTAssertTrue(h1.canBondWith(h2))

        let he = Atom(atomicNumber: 2)
        XCTAssertFalse(h1.canBondWith(he)) // Noble gas cannot bond
    }

    func testAtomBondType() {
        let na = Atom(atomicNumber: 11) // EN = 0.93
        let cl = Atom(atomicNumber: 17) // EN = 3.16
        XCTAssertEqual(na.bondType(with: cl), "ionic") // diff > 1.7

        let c = Atom(atomicNumber: 6)  // EN = 2.55
        let h = Atom(atomicNumber: 1)  // EN = 2.20
        XCTAssertEqual(c.bondType(with: h), "covalent") // diff < 0.4
    }

    func testAtomicSystemInit() {
        let sys = AtomicSystem()
        XCTAssertTrue(sys.atoms.isEmpty)
        XCTAssertEqual(sys.temperature, kTempRecombination)
    }

    func testNucleosynthesis() {
        let sys = AtomicSystem()
        let newAtoms = sys.nucleosynthesis(protons: 4, neutrons: 4)
        // 4p + 4n -> 2 He-4
        XCTAssertEqual(newAtoms.count, 2)
        XCTAssertTrue(newAtoms.allSatisfy { $0.atomicNumber == 2 })
    }

    func testNucleosynthesisMixed() {
        let sys = AtomicSystem()
        let newAtoms = sys.nucleosynthesis(protons: 5, neutrons: 2)
        // 2p + 2n -> 1 He-4, remaining 3p -> 3 H
        XCTAssertEqual(newAtoms.count, 4)
        let he = newAtoms.filter { $0.atomicNumber == 2 }
        let h = newAtoms.filter { $0.atomicNumber == 1 }
        XCTAssertEqual(he.count, 1)
        XCTAssertEqual(h.count, 3)
    }

    func testElementCounts() {
        let sys = AtomicSystem()
        _ = sys.nucleosynthesis(protons: 6, neutrons: 4)
        let counts = sys.elementCounts()
        XCTAssertEqual(counts["He"], 2)
        XCTAssertEqual(counts["H"], 2)
    }
}

// MARK: - Chemical System Tests

class ChemicalSystemTests: XCTestCase {

    private func makeAtomicSystem(elements: [(Int, Int)]) -> AtomicSystem {
        let sys = AtomicSystem()
        for (z, count) in elements {
            for _ in 0..<count {
                let atom = Atom(atomicNumber: z,
                                position: SIMD3(
                                    Double.random(in: -5...5),
                                    Double.random(in: -5...5),
                                    Double.random(in: -5...5)
                                ))
                sys.atoms.append(atom)
            }
        }
        return sys
    }

    func testChemicalSystemInit() {
        let atomic = AtomicSystem()
        let chem = ChemicalSystem(atomicSystem: atomic)
        XCTAssertTrue(chem.molecules.isEmpty)
        XCTAssertEqual(chem.waterCount, 0)
        XCTAssertEqual(chem.aminoAcidCount, 0)
        XCTAssertEqual(chem.nucleotideCount, 0)
    }

    func testFormWater() {
        let atomic = makeAtomicSystem(elements: [(1, 4), (8, 2)])
        let chem = ChemicalSystem(atomicSystem: atomic)

        let waters = chem.formWater()
        XCTAssertEqual(waters.count, 2)
        XCTAssertEqual(chem.waterCount, 2)
        XCTAssertEqual(chem.molecules.count, 2)
        XCTAssertTrue(waters.allSatisfy { $0.name == "water" })
    }

    func testFormWaterInsufficient() {
        let atomic = makeAtomicSystem(elements: [(1, 1), (8, 1)])
        let chem = ChemicalSystem(atomicSystem: atomic)

        let waters = chem.formWater()
        XCTAssertEqual(waters.count, 0) // Need 2 H for 1 water
    }

    func testFormMethane() {
        let atomic = makeAtomicSystem(elements: [(6, 1), (1, 4)])
        let chem = ChemicalSystem(atomicSystem: atomic)

        let methanes = chem.formMethane()
        XCTAssertEqual(methanes.count, 1)
        XCTAssertEqual(methanes[0].name, "methane")
    }

    func testFormAmmonia() {
        let atomic = makeAtomicSystem(elements: [(7, 1), (1, 3)])
        let chem = ChemicalSystem(atomicSystem: atomic)

        let ammonias = chem.formAmmonia()
        XCTAssertEqual(ammonias.count, 1)
        XCTAssertEqual(ammonias[0].name, "ammonia")
    }

    func testFormAminoAcid() {
        // Needs: 2C + 5H + 2O + 1N
        let atomic = makeAtomicSystem(elements: [(6, 2), (1, 5), (8, 2), (7, 1)])
        let chem = ChemicalSystem(atomicSystem: atomic)

        let aa = chem.formAminoAcid(type: "Gly")
        XCTAssertNotNil(aa)
        XCTAssertEqual(chem.aminoAcidCount, 1)
        XCTAssertTrue(aa!.isOrganic)
    }

    func testFormNucleotide() {
        // Needs: 5C + 8H + 4O + 2N
        let atomic = makeAtomicSystem(elements: [(6, 5), (1, 8), (8, 4), (7, 2)])
        let chem = ChemicalSystem(atomicSystem: atomic)

        let nuc = chem.formNucleotide(base: "A")
        XCTAssertNotNil(nuc)
        XCTAssertEqual(chem.nucleotideCount, 1)
        XCTAssertTrue(nuc!.isOrganic)
        XCTAssertTrue(nuc!.name.contains("nucleotide"))
    }

    func testMoleculeFormula() {
        let h1 = Atom(atomicNumber: 1)
        let h2 = Atom(atomicNumber: 1)
        let o = Atom(atomicNumber: 8)

        let formula = Molecule.computeFormula(atoms: [h1, h2, o])
        XCTAssertEqual(formula, "H2O")
    }

    func testMoleculeCensus() {
        let atomic = makeAtomicSystem(elements: [(1, 8), (8, 2), (6, 1)])
        let chem = ChemicalSystem(atomicSystem: atomic)
        _ = chem.formWater()
        _ = chem.formMethane()

        let census = chem.moleculeCensus()
        XCTAssertEqual(census["water"], 2)
        XCTAssertEqual(census["methane"], 1)
    }
}

// MARK: - Biology Tests

class BiologyTests: XCTestCase {

    func testNucleotideComplement() {
        XCTAssertEqual(Nucleotide.adenine.complement, .thymine)
        XCTAssertEqual(Nucleotide.thymine.complement, .adenine)
        XCTAssertEqual(Nucleotide.guanine.complement, .cytosine)
        XCTAssertEqual(Nucleotide.cytosine.complement, .guanine)
    }

    func testNucleotideRNABase() {
        XCTAssertEqual(Nucleotide.adenine.rnaBase, "A" as Character)
        XCTAssertEqual(Nucleotide.thymine.rnaBase, "U" as Character) // T -> U in RNA
        XCTAssertEqual(Nucleotide.guanine.rnaBase, "G" as Character)
        XCTAssertEqual(Nucleotide.cytosine.rnaBase, "C" as Character)
    }

    func testGeneExpressionLevel() {
        var gene = Gene(name: "test", startIndex: 0, length: 10,
                        isActive: true, methylated: false)
        XCTAssertEqual(gene.expressionLevel, 1.0)

        gene.methylated = true
        XCTAssertEqual(gene.expressionLevel, 0.1) // Methylated: suppressed

        gene.isActive = false
        XCTAssertEqual(gene.expressionLevel, 0.0) // Inactive: silenced
    }

    func testDNAStrandInit() {
        let dna = DNAStrand(length: 50)
        XCTAssertEqual(dna.length, 50)
        XCTAssertEqual(dna.sequence.count, 50)
        XCTAssertEqual(dna.methylationMap.count, 50)
        XCTAssertEqual(dna.mutationCount, 0)
    }

    func testDNAComplementary() {
        let seq: [Nucleotide] = [.adenine, .thymine, .guanine, .cytosine]
        let dna = DNAStrand(sequence: seq)
        let comp = dna.complementary

        XCTAssertEqual(comp[0], .thymine)   // A -> T
        XCTAssertEqual(comp[1], .adenine)   // T -> A
        XCTAssertEqual(comp[2], .cytosine)  // G -> C
        XCTAssertEqual(comp[3], .guanine)   // C -> G
    }

    func testDNAPointMutation() {
        var dna = DNAStrand(length: 100)
        let original = dna.sequence

        dna.pointMutation(rate: 1.0) // 100% mutation rate
        // Every position should have changed
        var changed = 0
        for i in 0..<dna.length {
            if dna.sequence[i] != original[i] { changed += 1 }
        }
        XCTAssertGreaterThan(changed, 0)
        XCTAssertGreaterThan(dna.mutationCount, 0)
    }

    func testDNAInsertionMutation() {
        var dna = DNAStrand(length: 50)
        let originalLength = dna.length

        dna.insertionMutation()
        XCTAssertEqual(dna.length, originalLength + 1)
        XCTAssertEqual(dna.mutationCount, 1)
    }

    func testDNADeletionMutation() {
        var dna = DNAStrand(length: 50)
        let originalLength = dna.length

        dna.deletionMutation()
        XCTAssertEqual(dna.length, originalLength - 1)
        XCTAssertEqual(dna.mutationCount, 1)
    }

    func testDNAReplication() {
        let dna = DNAStrand(length: 100)
        let copy = dna.replicate(errorRate: 0.0) // Perfect copy

        XCTAssertEqual(copy.length, dna.length)
        XCTAssertEqual(copy.sequence, dna.sequence)
    }

    func testDNAReplicationWithErrors() {
        let dna = DNAStrand(length: 100)
        let copy = dna.replicate(errorRate: 1.0) // 100% error rate

        XCTAssertEqual(copy.length, dna.length)
        // Sequences should differ due to errors
        XCTAssertNotEqual(copy.sequence, dna.sequence)
    }

    func testTranslation() {
        // AUG (start) -> Met, then some codons, then UAA (stop)
        let mRNA: [Character] = ["A", "U", "G", "G", "C", "U", "U", "A", "A"]
        let proteins = DNAStrand.translate(mRNA: mRNA)
        // AUG -> Met, GCU -> Ala, UAA -> STOP
        XCTAssertEqual(proteins.count, 2)
        XCTAssertEqual(proteins[0], "Met")
        XCTAssertEqual(proteins[1], "Ala")
    }

    func testCellInit() {
        let cell = Cell(energy: 5.0, position: .zero)
        XCTAssertFalse(cell.isDead)
        XCTAssertEqual(cell.energy, 5.0)
        XCTAssertEqual(cell.age, 0)
    }

    func testCellMetabolize() {
        var cell = Cell(energy: 5.0, metabolismRate: 0.1, position: .zero)
        cell.metabolize(environmentalEnergy: 10.0)
        XCTAssertEqual(cell.age, 1)
        XCTAssertFalse(cell.isDead)
    }

    func testCellDeath() {
        var cell = Cell(energy: 0.01, metabolismRate: 0.5, position: .zero)
        cell.metabolize(environmentalEnergy: 0.0)
        XCTAssertTrue(cell.isDead)
        XCTAssertEqual(cell.energy, 0)
    }

    func testCellCanDivide() {
        var cell = Cell(energy: 5.0, position: .zero)
        // Need age >= 10
        for _ in 0..<10 {
            cell.metabolize(environmentalEnergy: 10.0)
        }
        XCTAssertTrue(cell.canDivide)
    }

    func testCellCannotDivideInsufficientEnergy() {
        var cell = Cell(energy: 1.0, position: .zero)
        for _ in 0..<10 {
            cell.metabolize(environmentalEnergy: 0.5)
        }
        // Energy should be < 2.0
        XCTAssertFalse(cell.canDivide)
    }

    func testCellDivide() {
        var cell = Cell(energy: 10.0, position: .zero)
        for _ in 0..<10 {
            cell.metabolize(environmentalEnergy: 5.0)
        }

        let daughter = cell.divide()
        XCTAssertNotNil(daughter)
        if let daughter = daughter {
            XCTAssertEqual(daughter.generation, cell.generation + 1)
            XCTAssertFalse(daughter.isDead)
        }
    }

    func testBiosphereInit() {
        let bio = Biosphere(carryingCapacity: 50)
        XCTAssertTrue(bio.cells.isEmpty)
        XCTAssertEqual(bio.totalBorn, 0)
        XCTAssertEqual(bio.totalDied, 0)
    }

    func testBiosphereSeed() {
        let bio = Biosphere(carryingCapacity: 50)
        bio.seed(count: 10)
        XCTAssertEqual(bio.cells.count, 10)
        XCTAssertEqual(bio.totalBorn, 10)
    }

    func testBiosphereStep() {
        let bio = Biosphere(carryingCapacity: 50)
        bio.seed(count: 5)
        bio.step(environmentalEnergy: 10.0, mutationModifier: 1.0)
        // Cells should still exist
        XCTAssertGreaterThan(bio.cells.count, 0)
    }

    func testBiosphereAverageFitness() {
        let bio = Biosphere()
        XCTAssertEqual(bio.averageFitness(), 0.0) // No cells

        bio.seed(count: 5)
        XCTAssertGreaterThan(bio.averageFitness(), 0.0)
    }

    func testBiosphereNaturalSelection() {
        let bio = Biosphere(carryingCapacity: 5)
        bio.seed(count: 10)
        bio.naturalSelection()
        XCTAssertLessThanOrEqual(bio.cells.count, 5)
    }

    func testBiospherePopulationCount() {
        let bio = Biosphere()
        bio.seed(count: 7)
        XCTAssertEqual(bio.populationCount(), 7)
    }
}

// MARK: - Environment Tests

class EnvironmentTests: XCTestCase {

    func testEnvironmentInit() {
        let env = Environment(temperature: kTempPlanck)
        XCTAssertEqual(env.temperature, kTempPlanck)
        XCTAssertEqual(env.surfaceType, .plasma)
        XCTAssertFalse(env.waterPresent)
    }

    func testEnvironmentIsHabitable() {
        let env = Environment()
        env.temperature = 300.0
        env.waterPresent = true
        env.radiation = 0.5
        XCTAssertTrue(env.isHabitable)
    }

    func testEnvironmentNotHabitableTooHot() {
        let env = Environment()
        env.temperature = 500.0
        env.waterPresent = true
        env.radiation = 0.5
        XCTAssertFalse(env.isHabitable)
    }

    func testEnvironmentNotHabitableNoWater() {
        let env = Environment()
        env.temperature = 300.0
        env.waterPresent = false
        env.radiation = 0.5
        XCTAssertFalse(env.isHabitable)
    }

    func testEnvironmentIsChemicallyActive() {
        let env = Environment()
        env.temperature = 1000.0
        XCTAssertTrue(env.isChemicallyActive)

        env.temperature = 50.0
        XCTAssertFalse(env.isChemicallyActive)
    }

    func testEnvironmentMutationModifier() {
        let env = Environment()
        env.uvFlux = 2.0
        env.cosmicRayFlux = 5.0
        let modifier = env.mutationModifier
        XCTAssertGreaterThan(modifier, 1.0)
    }

    func testEnvironmentBiologicalEnergy() {
        let env = Environment()
        env.temperature = 300.0
        env.waterPresent = true
        env.radiation = 0.5
        env.uvFlux = 1.0

        let energy = env.biologicalEnergy
        XCTAssertGreaterThan(energy, 0.0)
    }

    func testEnvironmentBiologicalEnergyNotHabitable() {
        let env = Environment()
        env.temperature = 5000.0 // Not habitable
        env.waterPresent = false

        XCTAssertEqual(env.biologicalEnergy, 0.0)
    }

    func testEnvironmentStepEarlyEpochs() {
        let env = Environment()
        let initialTemp = env.temperature

        env.step(epoch: .planck)
        XCTAssertLessThan(env.temperature, initialTemp)
        XCTAssertEqual(env.surfaceType, .plasma)
    }

    func testEnvironmentStepPresent() {
        let env = Environment()
        env.step(epoch: .present)
        XCTAssertEqual(env.temperature, kTempEarthSurface)
        XCTAssertTrue(env.waterPresent)
        XCTAssertEqual(env.surfaceType, .land)
    }

    func testEnvironmentSummary() {
        let env = Environment()
        env.step(epoch: .present)
        let summary = env.summary()
        XCTAssertTrue(summary.contains("T="))
        XCTAssertTrue(summary.contains("habitable="))
    }

    func testAtmosphericGasValues() {
        // Verify all gas enum cases have non-empty raw values
        for gas in AtmosphericGas.allCases {
            XCTAssertFalse(gas.rawValue.isEmpty)
        }
    }
}

// MARK: - Universe Tests

class UniverseTests: XCTestCase {

    func testUniverseInit() {
        let u = Universe(seed: 42)
        XCTAssertEqual(u.tick, 0)
        XCTAssertEqual(u.seed, 42)
        XCTAssertTrue(u.quantumField.particles.isEmpty)
        XCTAssertTrue(u.atomicSystem.atoms.isEmpty)
        XCTAssertTrue(u.chemicalSystem.molecules.isEmpty)
        XCTAssertTrue(u.biosphere.cells.isEmpty)
    }

    func testUniverseStep() {
        let u = Universe(seed: 42)
        u.step()
        XCTAssertEqual(u.tick, 1)
        XCTAssertEqual(u.currentEpoch, .planck)
    }

    func testUniverseEpochTransitions() {
        let u = Universe(seed: 42)
        while u.tick < Epoch.inflation.rawValue {
            u.step()
        }
        XCTAssertEqual(u.currentEpoch, .inflation)

        while u.tick < Epoch.quark.rawValue {
            u.step()
        }
        XCTAssertEqual(u.currentEpoch, .quark)
    }

    func testUniverseSnapshot() {
        let u = Universe(seed: 42)
        let snap = u.snapshot()
        XCTAssertEqual(snap.tick, 0)
        XCTAssertEqual(snap.epoch, .planck)
        XCTAssertEqual(snap.particleCount, 0)
        XCTAssertEqual(snap.atomCount, 0)
        XCTAssertEqual(snap.moleculeCount, 0)
        XCTAssertEqual(snap.cellCount, 0)
    }

    func testUniverseSnapshotAfterSteps() {
        let u = Universe(seed: 42)
        for _ in 0..<50 {
            u.step()
        }
        let snap = u.snapshot()
        XCTAssertEqual(snap.tick, 50)
        XCTAssertGreaterThan(snap.particleCount, 0)
    }

    func testUniverseSnapshotContent() {
        let u = Universe(seed: 42)
        for _ in 0..<50 {
            u.step()
        }
        let snap = u.snapshot()
        XCTAssertFalse(snap.epochName.isEmpty)
        XCTAssertFalse(snap.epochDescription.isEmpty)
        XCTAssertFalse(snap.entities.isEmpty)
    }

    func testRenderableEntity() {
        let entity = RenderableEntity(
            position: SIMD3(1.0, 2.0, 3.0),
            size: 5.0,
            red: 0.5, green: 0.6, blue: 0.7,
            alpha: 0.9
        )
        XCTAssertEqual(entity.position.x, 1.0)
        XCTAssertEqual(entity.size, 5.0)
        XCTAssertEqual(entity.red, 0.5)
        XCTAssertEqual(entity.alpha, 0.9)
    }
}

// MARK: - Additional Quantum Field Tests

class QuantumFieldAdditionalTests: XCTestCase {

    func testVacuumFluctuationHighTemperature() {
        let qf = QuantumField(temperature: kTempPlanck)
        var produced = false
        for _ in 0..<100 {
            qf.vacuumFluctuation()
            if !qf.particles.isEmpty {
                produced = true
                break
            }
        }
        XCTAssertTrue(produced, "Vacuum fluctuation should produce pairs at Planck temperature")
    }

    func testWaveFunctionCollapse() {
        var wf = WaveFunction(amplitude: 1.0, phase: 0.0, coherent: true)
        let _ = wf.collapse()
        XCTAssertFalse(wf.coherent)
        XCTAssertTrue(wf.amplitude == 0.0 || wf.amplitude == 1.0)
    }

    func testWaveFunctionProbability() {
        let wf = WaveFunction(amplitude: 0.5, phase: 0.0, coherent: true)
        XCTAssertEqual(wf.probability, 0.25, accuracy: 1e-10)
    }
}

// MARK: - Additional Atomic System Tests

class AtomicSystemAdditionalTests: XCTestCase {

    func testAtomValenceElectrons() {
        let h = Atom(atomicNumber: 1)
        XCTAssertEqual(h.valenceElectrons, 1)

        let c = Atom(atomicNumber: 6)
        XCTAssertEqual(c.valenceElectrons, 4)

        let he = Atom(atomicNumber: 2)
        XCTAssertEqual(he.valenceElectrons, 2)
    }

    func testAtomNeedsElectrons() {
        let h = Atom(atomicNumber: 1)
        XCTAssertEqual(h.needsElectrons, 1) // needs 1 to fill first shell

        let he = Atom(atomicNumber: 2)
        XCTAssertEqual(he.needsElectrons, 0) // shell full
    }

    func testAtomBondEnergy() {
        let na = Atom(atomicNumber: 11) // EN = 0.93
        let cl = Atom(atomicNumber: 17) // EN = 3.16
        XCTAssertEqual(na.bondEnergy(with: cl), kBondEnergyIonic)

        let c = Atom(atomicNumber: 6)  // EN = 2.55
        let h = Atom(atomicNumber: 1)  // EN = 2.20
        XCTAssertEqual(c.bondEnergy(with: h), kBondEnergyCovalent)

        let o = Atom(atomicNumber: 8)  // EN = 3.44
        let hh = Atom(atomicNumber: 1) // EN = 2.20
        let expected = (kBondEnergyCovalent + kBondEnergyIonic) / 2.0
        XCTAssertEqual(o.bondEnergy(with: hh), expected)
    }

    func testAtomDistanceTo() {
        let a1 = Atom(atomicNumber: 1, position: SIMD3(0, 0, 0))
        let a2 = Atom(atomicNumber: 1, position: SIMD3(3, 4, 0))
        XCTAssertEqual(a1.distanceTo(a2), 5.0, accuracy: 1e-10)
    }

    func testAtomDistanceToSelf() {
        let a = Atom(atomicNumber: 1, position: SIMD3(1, 2, 3))
        XCTAssertEqual(a.distanceTo(a), 0.0, accuracy: 1e-10)
    }

    func testAtomIsIon() {
        let neutral = Atom(atomicNumber: 6, electronCount: 6)
        XCTAssertFalse(neutral.isIon)

        let ion = Atom(atomicNumber: 11, electronCount: 10)
        XCTAssertTrue(ion.isIon)
    }

    func testElectronShellAddRemove() {
        var shell = ElectronShell(n: 1, maxElectrons: 2, electrons: 0)
        XCTAssertTrue(shell.isEmpty)
        XCTAssertTrue(shell.addElectron())
        XCTAssertEqual(shell.electrons, 1)
        XCTAssertTrue(shell.addElectron())
        XCTAssertTrue(shell.isFull)
        XCTAssertFalse(shell.addElectron()) // Full, cannot add
        XCTAssertTrue(shell.removeElectron())
        XCTAssertEqual(shell.electrons, 1)
    }

    func testStellarNucleosynthesisProducesHeavierElements() {
        let sys = AtomicSystem()
        // Add many helium atoms
        for _ in 0..<30 {
            sys.atoms.append(Atom(atomicNumber: 2, massNumber: 4))
        }
        var produced = false
        for _ in 0..<200 {
            let newAtoms = sys.stellarNucleosynthesis(temperature: kTempStellarCore)
            if newAtoms.contains(where: { $0.atomicNumber == 6 }) {
                produced = true
                break
            }
            // Re-add helium to keep the pool fresh
            if sys.atoms.filter({ $0.atomicNumber == 2 }).count < 10 {
                for _ in 0..<15 {
                    sys.atoms.append(Atom(atomicNumber: 2, massNumber: 4))
                }
            }
        }
        XCTAssertTrue(produced, "Stellar nucleosynthesis should eventually produce carbon")
    }

    func testRecombinationAboveThreshold() {
        let sys = AtomicSystem(temperature: kTempRecombination * 2.0) // Too hot
        let qf = QuantumField(temperature: 1e6)
        qf.particles.append(Particle(type: .proton))
        qf.particles.append(Particle(type: .electron))
        let newAtoms = sys.recombination(field: qf)
        XCTAssertTrue(newAtoms.isEmpty)
    }

    func testRecombinationBelowThreshold() {
        let sys = AtomicSystem(temperature: kTempRecombination * 0.5) // Cold enough
        let qf = QuantumField(temperature: 1e3)
        for _ in 0..<3 {
            qf.particles.append(Particle(type: .proton))
            qf.particles.append(Particle(type: .electron))
        }
        let newAtoms = sys.recombination(field: qf)
        XCTAssertEqual(newAtoms.count, 3)
        XCTAssertTrue(newAtoms.allSatisfy { $0.atomicNumber == 1 })
    }
}

// MARK: - Additional Chemical System Tests

class ChemicalSystemAdditionalTests: XCTestCase {

    private func makeAtomicSystem(elements: [(Int, Int)]) -> AtomicSystem {
        let sys = AtomicSystem()
        for (z, count) in elements {
            for _ in 0..<count {
                let atom = Atom(atomicNumber: z,
                                position: SIMD3(
                                    Double.random(in: -5...5),
                                    Double.random(in: -5...5),
                                    Double.random(in: -5...5)
                                ))
                sys.atoms.append(atom)
            }
        }
        return sys
    }

    func testCatalyzedReaction() {
        // Needs sufficient atoms for amino acid or nucleotide formation
        let atomic = makeAtomicSystem(elements: [(6, 20), (1, 40), (8, 20), (7, 10)])
        let chem = ChemicalSystem(atomicSystem: atomic)

        var totalFormed = 0
        for _ in 0..<200 {
            totalFormed += chem.catalyzedReaction(temperature: 5000.0, catalystPresent: true)
        }
        XCTAssertGreaterThan(totalFormed, 0, "Catalyzed reaction should form products with catalyst and high temp")
    }

    func testMoleculeFormula() {
        let h1 = Atom(atomicNumber: 1)
        let h2 = Atom(atomicNumber: 1)
        let o = Atom(atomicNumber: 8)
        let formula = Molecule.computeFormula(atoms: [h1, h2, o])
        XCTAssertEqual(formula, "H2O")
    }

    func testMoleculeIsOrganic() {
        let atomic = makeAtomicSystem(elements: [(6, 1), (1, 4)])
        let chem = ChemicalSystem(atomicSystem: atomic)
        let methanes = chem.formMethane()
        XCTAssertEqual(methanes.count, 1)
        XCTAssertTrue(methanes[0].isOrganic)
    }

    func testMoleculeNotOrganic() {
        let atomic = makeAtomicSystem(elements: [(1, 4), (8, 2)])
        let chem = ChemicalSystem(atomicSystem: atomic)
        let waters = chem.formWater()
        XCTAssertEqual(waters.count, 2)
        XCTAssertFalse(waters[0].isOrganic) // Water is not organic
    }
}

// MARK: - Additional Biology Tests

class BiologyAdditionalTests: XCTestCase {

    func testDNATranscribe() {
        let seq: [Nucleotide] = [.adenine, .thymine, .guanine, .cytosine, .adenine, .thymine]
        let dna = DNAStrand(sequence: seq)
        // Create a simple gene covering all positions
        let gene = Gene(name: "test", startIndex: 0, length: 6, isActive: true, methylated: false)
        let mrna = dna.transcribe(gene: gene)
        // T -> U in RNA, others stay same
        XCTAssertEqual(mrna, ["A", "U", "G", "C", "A", "U"] as [Character])
    }

    func testDNATranscribeInactiveGene() {
        let seq: [Nucleotide] = [.adenine, .thymine, .guanine]
        let dna = DNAStrand(sequence: seq)
        let gene = Gene(name: "test", startIndex: 0, length: 3, isActive: false, methylated: false)
        let mrna = dna.transcribe(gene: gene)
        XCTAssertTrue(mrna.isEmpty)
    }

    func testDNAUpdateMethylation() {
        var dna = DNAStrand(length: 100)
        // Run many methylation cycles
        for _ in 0..<50 {
            dna.updateMethylation()
        }
        // Some positions should now be methylated
        let methylatedCount = dna.methylationMap.filter { $0 }.count
        XCTAssertGreaterThan(methylatedCount, 0, "Some positions should be methylated after 50 rounds")
    }

    func testDNAIdentifyGenes() {
        // Create ATG...TAA pattern (start codon + padding + stop codon)
        // ATG + GCU + GCU + TAA = 12 bases, which is >= 9 minimum
        let seq: [Nucleotide] = [
            .adenine, .thymine, .guanine, // ATG (start)
            .guanine, .cytosine, .thymine, // GCT
            .guanine, .cytosine, .thymine, // GCT
            .thymine, .adenine, .adenine, // TAA (stop)
        ]
        let genes = DNAStrand.identifyGenes(in: seq)
        XCTAssertEqual(genes.count, 1)
        XCTAssertEqual(genes[0].startIndex, 0)
        XCTAssertEqual(genes[0].length, 12)
    }

    func testDNADeletionMinLength() {
        var dna = DNAStrand(length: 10)
        // Should be able to delete when length > 10
        dna.deletionMutation()
        // At 10, one deletion should succeed
        XCTAssertEqual(dna.length, 9)
        // But at 10 before mutation, it was on the boundary
    }

    func testDNAInsertionMaxLength() {
        var dna = DNAStrand(length: 50)
        dna.insertionMutation()
        XCTAssertEqual(dna.length, 51)
    }

    func testBiosphereAverageGenomeLength() {
        let bio = Biosphere()
        XCTAssertEqual(bio.averageGenomeLength(), 0.0) // No cells

        bio.seed(count: 5)
        let avg = bio.averageGenomeLength()
        XCTAssertGreaterThan(avg, 0.0)
    }

    func testCellExpressProteins() {
        var cell = Cell(dna: DNAStrand(length: 200), energy: 10.0, position: .zero)
        cell.metabolize(environmentalEnergy: 5.0)
        // After metabolize, should have attempted protein expression
        XCTAssertEqual(cell.age, 1)
    }

    func testBiosphereStepMutationModifier() {
        let bio = Biosphere(carryingCapacity: 50)
        bio.seed(count: 5)
        // High mutation modifier should cause more mutations
        bio.step(environmentalEnergy: 10.0, mutationModifier: 5.0)
        XCTAssertGreaterThan(bio.cells.count, 0)
    }
}

// MARK: - Additional Environment Tests

class EnvironmentAdditionalTests: XCTestCase {

    func testAtmosphereDescription() {
        let env = Environment()
        env.step(epoch: .present)
        let desc = env.atmosphereDescription()
        XCTAssertTrue(desc.contains("N2"))
        XCTAssertTrue(desc.contains("O2"))
    }

    func testEnvironmentStepNucleosynthesis() {
        let env = Environment()
        env.step(epoch: .nucleosynthesis)
        XCTAssertEqual(env.surfaceType, .gas)
        XCTAssertEqual(env.atmosphere[.hydrogen], 0.75)
        XCTAssertEqual(env.atmosphere[.helium], 0.25)
    }

    func testEnvironmentStepRecombination() {
        let env = Environment()
        env.step(epoch: .recombination)
        XCTAssertEqual(env.surfaceType, .gas)
    }

    func testEnvironmentStepStarFormation() {
        let env = Environment()
        env.step(epoch: .starFormation)
        XCTAssertEqual(env.surfaceType, .gas)
        XCTAssertEqual(env.atmosphere[.hydrogen], 0.90)
    }

    func testEnvironmentStepSolarSystem() {
        let env = Environment()
        env.step(epoch: .solarSystem)
        XCTAssertEqual(env.surfaceType, .moltenRock)
        XCTAssertNotNil(env.atmosphere[.water])
    }

    func testEnvironmentStepEarth() {
        let env = Environment()
        env.temperature = 300.0 // Below 373
        env.step(epoch: .earth)
        XCTAssertTrue(env.waterPresent)
        XCTAssertEqual(env.surfaceType, .ocean)
    }

    func testEnvironmentStepLife() {
        let env = Environment()
        env.temperature = 400.0
        env.waterPresent = true
        env.radiation = 2.0
        env.step(epoch: .life)
        XCTAssertTrue(env.waterPresent)
        XCTAssertEqual(env.surfaceType, .ocean)
    }

    func testEnvironmentStepDNA() {
        let env = Environment()
        env.temperature = 350.0
        env.step(epoch: .dna)
        XCTAssertTrue(env.waterPresent)
        XCTAssertNotNil(env.atmosphere[.oxygen])
    }

    func testSurfaceTypeRawValues() {
        for st in SurfaceType.allCases {
            XCTAssertFalse(st.rawValue.isEmpty)
        }
    }
}

// MARK: - Additional Universe Tests

class UniverseAdditionalTests: XCTestCase {

    func testUniverseDifferentSeeds() {
        let u1 = Universe(seed: 42)
        let u2 = Universe(seed: 99)
        for _ in 0..<50 {
            u1.step()
            u2.step()
        }
        XCTAssertEqual(u1.tick, u2.tick)
        XCTAssertEqual(u1.tick, 50)
    }

    func testUniverseSnapshotEntities() {
        let u = Universe(seed: 42)
        for _ in 0..<50 {
            u.step()
        }
        let snap = u.snapshot()
        // All entities should have valid colors and size
        for entity in snap.entities {
            XCTAssertGreaterThanOrEqual(entity.red, 0.0)
            XCTAssertLessThanOrEqual(entity.red, 1.0)
            XCTAssertGreaterThanOrEqual(entity.green, 0.0)
            XCTAssertLessThanOrEqual(entity.green, 1.0)
            XCTAssertGreaterThanOrEqual(entity.blue, 0.0)
            XCTAssertLessThanOrEqual(entity.blue, 1.0)
            XCTAssertGreaterThan(entity.size, 0.0)
        }
    }

    func testUniverseFullRun() {
        let u = Universe(seed: 42)
        // Run through a significant portion of epochs
        for _ in 0..<500 {
            u.step()
        }
        let snap = u.snapshot()
        XCTAssertEqual(snap.tick, 500)
        XCTAssertGreaterThan(snap.particleCount, 0)
    }
}
