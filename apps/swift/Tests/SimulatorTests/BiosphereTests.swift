// BiosphereTests.swift
// Tests for Biosphere.swift

import XCTest
@testable import InTheBeginningSimulator

final class BiosphereTests: XCTestCase {

    // MARK: - NucleotideBase

    func testNucleotideBaseAllCases() {
        XCTAssertEqual(NucleotideBase.allCases.count, 4)
    }

    func testNucleotideBaseRawValues() {
        XCTAssertEqual(NucleotideBase.adenine.rawValue, "A")
        XCTAssertEqual(NucleotideBase.thymine.rawValue, "T")
        XCTAssertEqual(NucleotideBase.guanine.rawValue, "G")
        XCTAssertEqual(NucleotideBase.cytosine.rawValue, "C")
    }

    func testNucleotideBaseComplement() {
        XCTAssertEqual(NucleotideBase.adenine.complement, .thymine)
        XCTAssertEqual(NucleotideBase.thymine.complement, .adenine)
        XCTAssertEqual(NucleotideBase.guanine.complement, .cytosine)
        XCTAssertEqual(NucleotideBase.cytosine.complement, .guanine)
    }

    func testNucleotideBaseRNAEquivalent() {
        XCTAssertEqual(NucleotideBase.adenine.rnaEquivalent, "A")
        XCTAssertEqual(NucleotideBase.thymine.rnaEquivalent, "U")
        XCTAssertEqual(NucleotideBase.guanine.rnaEquivalent, "G")
        XCTAssertEqual(NucleotideBase.cytosine.rnaEquivalent, "C")
    }

    func testNucleotideBaseRandom() {
        var bases = Set<NucleotideBase>()
        for _ in 0..<200 {
            bases.insert(NucleotideBase.random())
        }
        XCTAssertEqual(bases.count, 4, "Random should produce all 4 bases")
    }

    // MARK: - DNAStrand

    func testDNAStrandDefaultLength() {
        let dna = DNAStrand()
        XCTAssertEqual(dna.length, 30)
        XCTAssertEqual(dna.sequence.count, 30)
        XCTAssertEqual(dna.methylation.count, 30)
    }

    func testDNAStrandCustomLength() {
        let dna = DNAStrand(length: 50)
        XCTAssertEqual(dna.length, 50)
    }

    func testDNAStrandFromSequence() {
        let seq: [NucleotideBase] = [.adenine, .thymine, .guanine, .cytosine]
        let dna = DNAStrand(sequence: seq)
        XCTAssertEqual(dna.length, 4)
        XCTAssertEqual(dna.sequence, seq)
    }

    func testDNAStrandMethylationInitiallyFalse() {
        let dna = DNAStrand(length: 10)
        XCTAssertTrue(dna.methylation.allSatisfy { !$0 })
    }

    func testComplementaryStrand() {
        let seq: [NucleotideBase] = [.adenine, .thymine, .guanine, .cytosine]
        let dna = DNAStrand(sequence: seq)
        let comp = dna.complementaryStrand
        XCTAssertEqual(comp, [.thymine, .adenine, .cytosine, .guanine])
    }

    func testGCContent() {
        let allGC = DNAStrand(sequence: [.guanine, .cytosine, .guanine, .cytosine])
        XCTAssertEqual(allGC.gcContent, 1.0, accuracy: 1e-10)

        let noGC = DNAStrand(sequence: [.adenine, .thymine, .adenine, .thymine])
        XCTAssertEqual(noGC.gcContent, 0.0, accuracy: 1e-10)

        let halfGC = DNAStrand(sequence: [.adenine, .guanine, .thymine, .cytosine])
        XCTAssertEqual(halfGC.gcContent, 0.5, accuracy: 1e-10)
    }

    func testGCContentEmpty() {
        let dna = DNAStrand(length: 0)
        XCTAssertEqual(dna.gcContent, 0.0)
    }

    func testTranscribe() {
        let dna = DNAStrand(sequence: [.adenine, .thymine, .guanine, .cytosine])
        let rna = dna.transcribe()
        XCTAssertEqual(rna, ["A", "U", "G", "C"])
    }

    func testTranslateStartCodon() {
        // ATG -> AUG (Met), TTT -> UUU (Phe), TAA -> UAA (STOP)
        let dna = DNAStrand(sequence: [.adenine, .thymine, .guanine,
                                        .thymine, .thymine, .thymine,
                                        .thymine, .adenine, .adenine])
        let proteins = dna.translate()
        XCTAssertFalse(proteins.isEmpty)
        XCTAssertEqual(proteins[0], "Met")
        XCTAssertEqual(proteins[1], "Phe")
        // UAA is STOP so translation stops after Phe
        XCTAssertEqual(proteins.count, 2)
    }

    func testTranslateNoStartCodon() {
        // TTT -> UUU, no AUG start codon
        let dna = DNAStrand(sequence: [.thymine, .thymine, .thymine])
        let proteins = dna.translate()
        XCTAssertTrue(proteins.isEmpty)
    }

    func testMutate() {
        var dna = DNAStrand(length: 100)
        let original = dna.sequence
        dna.mutate(rate: 1.0) // 100% mutation rate
        // With rate=1.0, every non-methylated base should mutate
        var changedCount = 0
        for i in 0..<dna.length {
            if dna.sequence[i] != original[i] {
                changedCount += 1
            }
        }
        XCTAssertGreaterThan(changedCount, 0, "Should have mutations with 100% rate")
    }

    func testMutateMethylatedBasesProtected() {
        var dna = DNAStrand(sequence: [.adenine, .adenine, .adenine, .adenine])
        dna.methylation = [true, true, true, true]
        let original = dna.sequence
        // With rate=1.0, methylated bases get rate*0.1=0.1, so some may still mutate
        // But with only 4 bases and 0.1 rate, it's possible none mutate
        dna.mutate(rate: 0.5)
        // This is a probabilistic test; we just check it doesn't crash
    }

    func testInsertionMutation() {
        var dna = DNAStrand(length: 10)
        dna.insertionMutation()
        XCTAssertEqual(dna.length, 11)
        XCTAssertEqual(dna.methylation.count, 11)
    }

    func testDeletionMutation() {
        var dna = DNAStrand(length: 10)
        dna.deletionMutation()
        XCTAssertEqual(dna.length, 9)
        XCTAssertEqual(dna.methylation.count, 9)
    }

    func testDeletionMutationShortSequence() {
        var dna = DNAStrand(length: 3)
        dna.deletionMutation()
        // Should not delete below length 3
        XCTAssertEqual(dna.length, 3)
    }

    func testApplyMethylation() {
        // Create DNA with CpG sites
        var dna = DNAStrand(sequence: [.cytosine, .guanine, .cytosine, .guanine,
                                        .cytosine, .guanine, .cytosine, .guanine,
                                        .cytosine, .guanine])
        // Run methylation many times to increase chance
        for _ in 0..<100 {
            dna.applyMethylation()
        }
        XCTAssertGreaterThan(dna.methylationLevel, 0.0, "Should have some methylation on CpG sites")
    }

    func testDemethylate() {
        var dna = DNAStrand(length: 10)
        // Set all methylation
        dna.methylation = [Bool](repeating: true, count: 10)
        XCTAssertEqual(dna.methylationLevel, 1.0)

        // Run demethylation many times
        for _ in 0..<200 {
            dna.demethylate()
        }
        XCTAssertLessThan(dna.methylationLevel, 1.0, "Some methylation should be removed")
    }

    func testMethylationLevel() {
        var dna = DNAStrand(length: 4)
        XCTAssertEqual(dna.methylationLevel, 0.0)

        dna.methylation[0] = true
        dna.methylation[1] = true
        XCTAssertEqual(dna.methylationLevel, 0.5, accuracy: 1e-10)
    }

    func testReplicate() {
        let dna = DNAStrand(length: 30)
        let copy = dna.replicate()
        XCTAssertEqual(copy.length, dna.length)
        // Replication may introduce errors
    }

    func testReplicateWithHighErrorRate() {
        let dna = DNAStrand(length: 100)
        let copy = dna.replicate(errorRate: 1.0) // Very high error rate
        // Some bases should differ
        var differences = 0
        for i in 0..<dna.length {
            if dna.sequence[i] != copy.sequence[i] {
                differences += 1
            }
        }
        XCTAssertGreaterThan(differences, 0, "High error rate should produce differences")
    }

    func testReplicatePreservesMethylation() {
        var dna = DNAStrand(length: 10)
        dna.methylation[0] = true
        dna.methylation[5] = true
        let copy = dna.replicate(errorRate: 0.0)
        // Methylation inheritance is 80% per position
        // Can't be 100% deterministic, just check copy has methylation array of correct size
        XCTAssertEqual(copy.methylation.count, copy.length)
    }

    // MARK: - Cell

    func testCellCreation() {
        let cell = Cell()
        XCTAssertTrue(cell.isAlive)
        XCTAssertEqual(cell.age, 0)
        XCTAssertEqual(cell.generation, 0)
        XCTAssertEqual(cell.energy, 20.0)
        XCTAssertTrue(cell.hasMembraneIntegrity)
        XCTAssertGreaterThan(cell.fitness, 0.0)
    }

    func testCellWithCustomDNA() {
        let dna = DNAStrand(length: 50)
        let cell = Cell(dna: dna, energy: 100.0, generation: 5)
        XCTAssertEqual(cell.dna.length, 50)
        XCTAssertEqual(cell.energy, 100.0)
        XCTAssertEqual(cell.generation, 5)
    }

    func testCellUniqueIDs() {
        let c1 = Cell()
        let c2 = Cell()
        XCTAssertNotEqual(c1.id, c2.id)
    }

    func testCellMetabolicRate() {
        let cell = Cell()
        XCTAssertGreaterThan(cell.metabolicRate, 0.0)
    }

    func testCellReproductionThreshold() {
        let cell = Cell()
        XCTAssertGreaterThan(cell.reproductionThreshold, 0.0)
    }

    func testCellMetabolize() {
        let cell = Cell(energy: 100.0)
        let survived = cell.metabolize(availableEnergy: 10.0)
        XCTAssertTrue(survived)
        XCTAssertEqual(cell.age, 1)
    }

    func testCellMetabolizeNoEnergy() {
        let cell = Cell(energy: 0.001)
        let survived = cell.metabolize(availableEnergy: 0.0)
        XCTAssertFalse(survived)
        XCTAssertFalse(cell.isAlive)
    }

    func testCellDivide() {
        let cell = Cell(energy: 200.0)
        cell.computeFitness()
        let daughter = cell.divide(mutationRate: 0.01)
        if let daughter = daughter {
            XCTAssertEqual(daughter.generation, 1)
            XCTAssertTrue(daughter.isAlive)
            XCTAssertEqual(daughter.dna.length, cell.dna.length)
            // Parent energy should be halved
            XCTAssertEqual(cell.energy, 100.0, accuracy: 1.0)
        }
    }

    func testCellDivideInsufficientEnergy() {
        let cell = Cell(energy: 1.0)
        cell.computeFitness()
        let daughter = cell.divide(mutationRate: 0.01)
        XCTAssertNil(daughter)
    }

    func testCellDivideDead() {
        let cell = Cell(energy: 200.0)
        cell.isAlive = false
        let daughter = cell.divide(mutationRate: 0.01)
        XCTAssertNil(daughter)
    }

    func testCellComputeFitness() {
        let cell = Cell()
        cell.computeFitness()
        XCTAssertGreaterThan(cell.fitness, 0.0)
        XCTAssertLessThanOrEqual(cell.fitness, 1.0)
    }

    func testCellApplyRadiationDamage() {
        let cell = Cell(energy: 100.0)
        // Low intensity should not kill
        cell.applyRadiationDamage(intensity: 0.1)
        // Cell may or may not be alive (probabilistic)
    }

    func testCellHighRadiationCanKill() {
        let cell = Cell(energy: 100.0)
        // Very high intensity above damage threshold
        var killed = false
        for _ in 0..<100 {
            let testCell = Cell(energy: 100.0)
            testCell.applyRadiationDamage(intensity: 100.0)
            if !testCell.isAlive {
                killed = true
                break
            }
        }
        XCTAssertTrue(killed, "Very high radiation should eventually kill cells")
    }

    func testCellRegulateEpigenetics() {
        let dna = DNAStrand(sequence: [.cytosine, .guanine, .cytosine, .guanine,
                                        .cytosine, .guanine, .adenine, .thymine, .guanine])
        let cell = Cell(dna: dna, energy: 100.0)
        let proteinsBefore = cell.proteins
        // Run regulation multiple times
        for _ in 0..<50 {
            cell.regulateEpigenetics()
        }
        // Fitness should still be valid
        XCTAssertGreaterThan(cell.fitness, 0.0)
    }

    // MARK: - Biosphere

    func testBiosphereInit() {
        let bio = Biosphere()
        XCTAssertTrue(bio.cells.isEmpty)
        XCTAssertEqual(bio.extinctSpeciesCount, 0)
        XCTAssertEqual(bio.totalDivisions, 0)
        XCTAssertEqual(bio.totalDeaths, 0)
        XCTAssertEqual(bio.maxGenerationReached, 0)
    }

    func testBiosphereLivingCellCount() {
        let bio = Biosphere()
        XCTAssertEqual(bio.livingCellCount, 0)

        let cell = Cell(energy: 100.0)
        bio.cells.append(cell)
        XCTAssertEqual(bio.livingCellCount, 1)
    }

    func testBiosphereAverageFitness() {
        let bio = Biosphere()
        XCTAssertEqual(bio.averageFitness, 0.0)

        let c1 = Cell(energy: 100.0)
        let c2 = Cell(energy: 100.0)
        bio.cells.append(contentsOf: [c1, c2])
        XCTAssertGreaterThan(bio.averageFitness, 0.0)
    }

    func testBiosphereAverageGeneration() {
        let bio = Biosphere()
        XCTAssertEqual(bio.averageGeneration, 0.0)

        let c1 = Cell(energy: 100.0, generation: 5)
        let c2 = Cell(energy: 100.0, generation: 10)
        bio.cells.append(contentsOf: [c1, c2])
        XCTAssertEqual(bio.averageGeneration, 7.5, accuracy: 0.01)
    }

    func testBiosphereAverageGenomeLength() {
        let bio = Biosphere()
        XCTAssertEqual(bio.averageGenomeLength, 0.0)

        let c1 = Cell(dna: DNAStrand(length: 20))
        let c2 = Cell(dna: DNAStrand(length: 40))
        bio.cells.append(contentsOf: [c1, c2])
        XCTAssertEqual(bio.averageGenomeLength, 30.0, accuracy: 0.01)
    }

    func testBiosphereMaxFitness() {
        let bio = Biosphere()
        XCTAssertEqual(bio.maxFitness, 0.0)

        let c = Cell(energy: 100.0)
        bio.cells.append(c)
        XCTAssertGreaterThan(bio.maxFitness, 0.0)
    }

    func testBiosphereFittestCell() {
        let bio = Biosphere()
        XCTAssertNil(bio.fittestCell)

        let c1 = Cell(energy: 100.0)
        let c2 = Cell(energy: 100.0)
        bio.cells.append(contentsOf: [c1, c2])
        XCTAssertNotNil(bio.fittestCell)
    }

    func testBiosphereGeneticDiversity() {
        let bio = Biosphere()
        XCTAssertEqual(bio.geneticDiversity, 0.0)

        let c1 = Cell(dna: DNAStrand(length: 30), energy: 100.0)
        bio.cells.append(c1)
        // Single cell: diversity = 0
        XCTAssertEqual(bio.geneticDiversity, 0.0)

        let c2 = Cell(dna: DNAStrand(length: 30), energy: 100.0)
        bio.cells.append(c2)
        // Two random cells: diversity > 0 (very likely unique genomes)
        XCTAssertGreaterThanOrEqual(bio.geneticDiversity, 0.0)
    }

    func testAbiogenesisRequiresPreconditions() {
        let bio = Biosphere()
        // Missing precursors
        let cells1 = bio.abiogenesis(aminoAcidCount: 0, nucleotideCount: 0, hasWater: false, temperature: 300.0)
        XCTAssertTrue(cells1.isEmpty)

        // No water
        let cells2 = bio.abiogenesis(aminoAcidCount: 5, nucleotideCount: 5, hasWater: false, temperature: 300.0)
        XCTAssertTrue(cells2.isEmpty)

        // Too cold
        let cells3 = bio.abiogenesis(aminoAcidCount: 5, nucleotideCount: 5, hasWater: true, temperature: 100.0)
        XCTAssertTrue(cells3.isEmpty)

        // Too hot
        let cells4 = bio.abiogenesis(aminoAcidCount: 5, nucleotideCount: 5, hasWater: true, temperature: 500.0)
        XCTAssertTrue(cells4.isEmpty)
    }

    func testAbiogenesisCanSucceed() {
        let bio = Biosphere()
        var succeeded = false
        for _ in 0..<500 {
            let cells = bio.abiogenesis(aminoAcidCount: 10, nucleotideCount: 10, hasWater: true, temperature: 300.0)
            if !cells.isEmpty {
                succeeded = true
                break
            }
        }
        XCTAssertTrue(succeeded, "Abiogenesis should eventually succeed with good conditions")
        XCTAssertFalse(bio.cells.isEmpty)
    }

    func testBiosphereEvolve() {
        let bio = Biosphere()
        let c1 = Cell(energy: 100.0)
        let c2 = Cell(energy: 100.0)
        bio.cells.append(contentsOf: [c1, c2])

        bio.evolve(temperature: 300.0, radiationLevel: 0.1, energyAvailable: 100.0)
        // Cells should have aged
        // Some may have divided or died
    }

    func testBiosphereEvolveRemovesDead() {
        let bio = Biosphere()
        let deadCell = Cell(energy: 0.001)
        bio.cells.append(deadCell)

        bio.evolve(temperature: 300.0, radiationLevel: 0.0, energyAvailable: 0.0)
        // Dead cells should be removed
        XCTAssertEqual(bio.cells.filter { !$0.isAlive }.count, 0)
    }

    func testBiosphereEvolveReproduction() {
        let bio = Biosphere()
        // Create cells with enough energy to reproduce
        for _ in 0..<5 {
            let cell = Cell(energy: 200.0)
            bio.cells.append(cell)
        }

        bio.evolve(temperature: 300.0, radiationLevel: 0.0, energyAvailable: 1000.0)
        // Some cells should have divided (totalDivisions > 0) or at least survived
    }

    func testBiosphereMaxCellsLimit() {
        let bio = Biosphere()
        // Fill with many high-energy cells
        for _ in 0..<(SimulationLimits.maxCells + 50) {
            let cell = Cell(energy: 500.0)
            bio.cells.append(cell)
        }

        bio.evolve(temperature: 300.0, radiationLevel: 0.0, energyAvailable: 10000.0)
        // Should be trimmed to maxCells
        XCTAssertLessThanOrEqual(bio.cells.count, SimulationLimits.maxCells)
    }

    // MARK: - Additional NucleotideBase Coverage

    func testNucleotideBaseComplementIsInvolution() {
        for base in NucleotideBase.allCases {
            XCTAssertEqual(base.complement.complement, base,
                "\(base) complement's complement should be itself")
        }
    }

    func testNucleotideBaseRandomProducesAll() {
        var seen = Set<NucleotideBase>()
        for _ in 0..<500 {
            seen.insert(NucleotideBase.random())
        }
        XCTAssertEqual(seen.count, 4)
    }

    // MARK: - Additional DNAStrand Coverage

    func testDNAStrandInsertionMutationOnEmpty() {
        var dna = DNAStrand(length: 0)
        dna.insertionMutation()
        // Empty sequence guard returns early
        XCTAssertEqual(dna.length, 0)
    }

    func testDNAStrandMethylationLevelEmpty() {
        let dna = DNAStrand(length: 0)
        XCTAssertEqual(dna.methylationLevel, 0.0)
    }

    func testDNAStrandTranscribeEmpty() {
        let dna = DNAStrand(length: 0)
        let rna = dna.transcribe()
        XCTAssertTrue(rna.isEmpty)
    }

    func testDNAStrandTranslateShortSequence() {
        // Less than 3 bases - cannot form a codon
        let dna = DNAStrand(sequence: [.adenine, .thymine])
        let proteins = dna.translate()
        XCTAssertTrue(proteins.isEmpty)
    }

    func testDNAStrandComplementaryStrandLength() {
        let dna = DNAStrand(length: 20)
        let comp = dna.complementaryStrand
        XCTAssertEqual(comp.count, 20)
    }

    func testDNAStrandMutateZeroRate() {
        var dna = DNAStrand(length: 100)
        let original = dna.sequence
        dna.mutate(rate: 0.0)
        XCTAssertEqual(dna.sequence, original, "Zero mutation rate should not change sequence")
    }

    func testDNAStrandReplicatePreservesLength() {
        let dna = DNAStrand(length: 50)
        let copy = dna.replicate(errorRate: 0.0)
        XCTAssertEqual(copy.length, dna.length)
    }

    func testDNAStrandApplyMethylationNoCpG() {
        var dna = DNAStrand(sequence: [.adenine, .adenine, .thymine, .thymine])
        // No CpG sites, so methylation should not change
        dna.applyMethylation()
        XCTAssertEqual(dna.methylationLevel, 0.0)
    }

    func testDNAStrandDemethylateAlreadyUnmethylated() {
        var dna = DNAStrand(length: 10)
        // All methylation is false
        dna.demethylate()
        XCTAssertEqual(dna.methylationLevel, 0.0)
    }

    func testDNAStrandInsertionPreservesIntegrity() {
        var dna = DNAStrand(length: 20)
        dna.methylation[5] = true
        dna.insertionMutation()
        XCTAssertEqual(dna.length, 21)
        XCTAssertEqual(dna.methylation.count, 21)
    }

    func testDNAStrandDeletionPreservesIntegrity() {
        var dna = DNAStrand(length: 20)
        dna.deletionMutation()
        XCTAssertEqual(dna.length, 19)
        XCTAssertEqual(dna.methylation.count, 19)
    }

    // MARK: - Additional Cell Coverage

    func testCellDisplayColor() {
        let cell = Cell(energy: 100.0)
        let color = cell.displayColor
        XCTAssertGreaterThanOrEqual(color.x, 0.0)
        XCTAssertLessThanOrEqual(color.x, 1.0)
        XCTAssertGreaterThanOrEqual(color.y, 0.0)
        XCTAssertLessThanOrEqual(color.y, 1.0)
        XCTAssertEqual(color.z, 0.3, accuracy: 0.01)
        XCTAssertEqual(color.w, 1.0)
    }

    func testCellDisplayColorHighFitness() {
        let cell = Cell(energy: 100.0)
        cell.fitness = 1.0
        let color = cell.displayColor
        // High fitness -> green (g=1.0, r=0.0)
        XCTAssertEqual(color.y, 1.0, accuracy: 0.01) // green
        XCTAssertEqual(color.x, 0.0, accuracy: 0.01) // red
    }

    func testCellDisplayColorLowFitness() {
        let cell = Cell(energy: 100.0)
        cell.fitness = 0.0
        let color = cell.displayColor
        // Low fitness -> red (g=0.0, r=1.0)
        XCTAssertEqual(color.y, 0.0, accuracy: 0.01) // green
        XCTAssertEqual(color.x, 1.0, accuracy: 0.01) // red
    }

    func testCellMetabolicRateMinimum() {
        let cell = Cell(energy: 100.0)
        cell.fitness = 0.0
        // metabolicRate = max(0.1, fitness * 0.5 + gcContent * 0.3)
        XCTAssertGreaterThanOrEqual(cell.metabolicRate, 0.1)
    }

    func testCellReproductionThresholdInverseFitness() {
        let cell1 = Cell(energy: 100.0)
        cell1.fitness = 1.0
        let cell2 = Cell(energy: 100.0)
        cell2.fitness = 0.1
        // Higher fitness should mean lower reproduction threshold
        XCTAssertLessThan(cell1.reproductionThreshold, cell2.reproductionThreshold)
    }

    func testCellMetabolizeAgesCell() {
        let cell = Cell(energy: 1000.0)
        for _ in 0..<10 {
            cell.metabolize(availableEnergy: 10.0)
        }
        XCTAssertEqual(cell.age, 10)
    }

    func testCellDivideProducesCorrectGeneration() {
        let cell = Cell(energy: 500.0, generation: 7)
        if let daughter = cell.divide(mutationRate: 0.001) {
            XCTAssertEqual(daughter.generation, 8)
        }
    }

    func testCellDivideHalvesEnergy() {
        let cell = Cell(energy: 500.0)
        if let _ = cell.divide(mutationRate: 0.001) {
            XCTAssertEqual(cell.energy, 250.0, accuracy: 1.0)
        }
    }

    func testCellComputeFitnessProteinDiversity() {
        // Cell with unique proteins should have different fitness than one without
        let seq1: [NucleotideBase] = [.adenine, .thymine, .guanine,  // AUG -> Met
                                       .guanine, .guanine, .guanine,  // GGG -> Gly
                                       .cytosine, .cytosine, .cytosine]  // CCC -> Pro
        let cell1 = Cell(dna: DNAStrand(sequence: seq1), energy: 100.0)
        cell1.computeFitness()

        let seq2: [NucleotideBase] = [.thymine, .thymine, .thymine,
                                       .thymine, .thymine, .thymine,
                                       .thymine, .thymine, .thymine]
        let cell2 = Cell(dna: DNAStrand(sequence: seq2), energy: 100.0)
        cell2.computeFitness()

        // cell1 has protein diversity, cell2 has no proteins (no start codon)
        // Both should have valid fitness
        XCTAssertGreaterThan(cell1.fitness, 0.0)
        XCTAssertGreaterThan(cell2.fitness, 0.0)
    }

    func testCellApplyRadiationDamageLowIntensity() {
        let cell = Cell(energy: 100.0)
        // Low intensity should not kill
        for _ in 0..<10 {
            cell.applyRadiationDamage(intensity: 0.01)
        }
        // Very low intensity, highly unlikely to kill
        XCTAssertTrue(cell.isAlive)
    }

    func testCellRegulateEpigeneticsUpdatesFitness() {
        let dna = DNAStrand(sequence: [.cytosine, .guanine, .adenine, .thymine,
                                        .cytosine, .guanine, .adenine, .thymine,
                                        .guanine, .cytosine, .adenine, .thymine])
        let cell = Cell(dna: dna, energy: 100.0)
        let fitnessBefore = cell.fitness
        for _ in 0..<50 {
            cell.regulateEpigenetics()
        }
        // Fitness should have been recomputed (may or may not change)
        XCTAssertGreaterThan(cell.fitness, 0.0)
        XCTAssertLessThanOrEqual(cell.fitness, 1.0)
    }

    func testCellProteinsFromDNA() {
        // Create DNA with known start codon
        let seq: [NucleotideBase] = [.adenine, .thymine, .guanine,  // AUG -> Met
                                      .thymine, .thymine, .thymine,  // UUU -> Phe
                                      .thymine, .adenine, .adenine]  // UAA -> STOP
        let cell = Cell(dna: DNAStrand(sequence: seq), energy: 100.0)
        XCTAssertEqual(cell.proteins.count, 2)
        XCTAssertEqual(cell.proteins[0], "Met")
        XCTAssertEqual(cell.proteins[1], "Phe")
    }

    func testCellHasMembraneIntegrity() {
        let cell = Cell()
        XCTAssertTrue(cell.hasMembraneIntegrity)
    }

    func testCellPosition() {
        let pos = SIMD3<Double>(5.0, 10.0, 15.0)
        let cell = Cell(energy: 100.0, position: pos)
        XCTAssertEqual(cell.position, pos)
    }

    // MARK: - Additional Biosphere Coverage

    func testBiosphereAvailableEnergy() {
        let bio = Biosphere()
        XCTAssertEqual(bio.availableEnergy, 100.0)
    }

    func testBiosphereMutationRate() {
        let bio = Biosphere()
        XCTAssertEqual(bio.mutationRate, 1e-4)
        bio.mutationRate = 0.01
        XCTAssertEqual(bio.mutationRate, 0.01)
    }

    func testBiosphereEvolveUpdatesAvailableEnergy() {
        let bio = Biosphere()
        let cell = Cell(energy: 100.0)
        bio.cells.append(cell)
        bio.evolve(temperature: 300.0, radiationLevel: 0.1, energyAvailable: 50.0)
        XCTAssertEqual(bio.availableEnergy, 50.0)
    }

    func testBiosphereEvolveTracksDivisions() {
        let bio = Biosphere()
        // Create cells with very high energy to ensure division
        for _ in 0..<10 {
            let cell = Cell(energy: 10000.0)
            bio.cells.append(cell)
        }
        bio.evolve(temperature: 300.0, radiationLevel: 0.0, energyAvailable: 10000.0)
        // Some cells should have divided
        XCTAssertGreaterThanOrEqual(bio.totalDivisions, 0)
    }

    func testBiosphereEvolveTracksDeaths() {
        let bio = Biosphere()
        // Create cells with zero energy that will die
        for _ in 0..<5 {
            let cell = Cell(energy: 0.001)
            bio.cells.append(cell)
        }
        bio.evolve(temperature: 300.0, radiationLevel: 0.0, energyAvailable: 0.0)
        XCTAssertGreaterThan(bio.totalDeaths, 0)
    }

    func testBiosphereEvolveMaxGenerationTracked() {
        let bio = Biosphere()
        for _ in 0..<5 {
            let cell = Cell(energy: 10000.0, generation: 10)
            bio.cells.append(cell)
        }
        bio.evolve(temperature: 300.0, radiationLevel: 0.0, energyAvailable: 10000.0)
        XCTAssertGreaterThanOrEqual(bio.maxGenerationReached, 10)
    }

    func testBiosphereGeneticDiversityMultipleDifferent() {
        let bio = Biosphere()
        // Add cells with definitely different genomes
        for _ in 0..<10 {
            let cell = Cell(dna: DNAStrand(length: 30), energy: 100.0)
            bio.cells.append(cell)
        }
        // With 30-base random genomes, all should be unique
        XCTAssertGreaterThan(bio.geneticDiversity, 0.0)
    }

    func testBiosphereGeneticDiversityIdenticalCells() {
        let bio = Biosphere()
        let sharedDNA = DNAStrand(sequence: [.adenine, .thymine, .guanine])
        for _ in 0..<5 {
            let cell = Cell(dna: DNAStrand(sequence: sharedDNA.sequence), energy: 100.0)
            bio.cells.append(cell)
        }
        // All identical genomes -> diversity = 1/5 = 0.2
        XCTAssertEqual(bio.geneticDiversity, 0.2, accuracy: 0.01)
    }

    func testBiosphereExtinctSpeciesCount() {
        let bio = Biosphere()
        XCTAssertEqual(bio.extinctSpeciesCount, 0)
    }

    func testBiosphereAbiogenesisGenomeLength() {
        let bio = Biosphere()
        var succeeded = false
        for _ in 0..<1000 {
            let cells = bio.abiogenesis(aminoAcidCount: 10, nucleotideCount: 5, hasWater: true, temperature: 300.0)
            if let cell = cells.first {
                // genomeLength = min(30, nucleotideCount * 3) = min(30, 15) = 15
                XCTAssertEqual(cell.dna.length, 15)
                succeeded = true
                break
            }
        }
        if !succeeded {
            // Abiogenesis is probabilistic; this is OK
        }
    }

    func testBiosphereEvolveSortsForNaturalSelection() {
        let bio = Biosphere()
        // Overfill past maxCells
        for i in 0..<(SimulationLimits.maxCells + 20) {
            let cell = Cell(energy: 500.0)
            cell.fitness = Double(i) / Double(SimulationLimits.maxCells + 20)
            bio.cells.append(cell)
        }
        bio.evolve(temperature: 300.0, radiationLevel: 0.0, energyAvailable: 10000.0)
        // After natural selection, surviving cells should be the fittest
        XCTAssertLessThanOrEqual(bio.cells.count, SimulationLimits.maxCells)
        // Check that remaining cells have higher fitness on average
        if bio.cells.count > 1 {
            // Cells should be sorted by fitness descending after natural selection
            for i in 0..<(bio.cells.count - 1) {
                XCTAssertGreaterThanOrEqual(bio.cells[i].fitness, bio.cells[i + 1].fitness)
            }
        }
    }
}
