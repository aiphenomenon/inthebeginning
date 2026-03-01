// Biosphere.swift
// InTheBeginning
//
// Biological system simulation.
// Models DNA, RNA, proteins, cells, mutation, natural selection,
// and epigenetic regulation. Cells compete for resources, replicate
// with heritable mutations, and undergo selection pressure.

import Foundation

// MARK: - Nucleotide Base

enum NucleotideBase: Character, CaseIterable, Sendable {
    case adenine = "A"
    case thymine = "T"
    case guanine = "G"
    case cytosine = "C"

    var complement: NucleotideBase {
        switch self {
        case .adenine:  return .thymine
        case .thymine:  return .adenine
        case .guanine:  return .cytosine
        case .cytosine: return .guanine
        }
    }

    var rnaEquivalent: Character {
        switch self {
        case .adenine:  return "A"
        case .thymine:  return "U"
        case .guanine:  return "G"
        case .cytosine: return "C"
        }
    }

    static func random() -> NucleotideBase {
        allCases.randomElement()!
    }
}

// MARK: - DNA Strand

struct DNAStrand: Sendable {
    var sequence: [NucleotideBase]
    var methylation: [Bool]  // Epigenetic methylation marks

    var length: Int { sequence.count }

    var complementaryStrand: [NucleotideBase] {
        sequence.map(\.complement)
    }

    var gcContent: Double {
        guard !sequence.isEmpty else { return 0.0 }
        let gcCount = sequence.filter { $0 == .guanine || $0 == .cytosine }.count
        return Double(gcCount) / Double(sequence.count)
    }

    init(length: Int = 30) {
        sequence = (0..<length).map { _ in NucleotideBase.random() }
        methylation = [Bool](repeating: false, count: length)
    }

    init(sequence: [NucleotideBase]) {
        self.sequence = sequence
        self.methylation = [Bool](repeating: false, count: sequence.count)
    }

    // MARK: - Transcription

    /// Transcribe DNA to RNA (replace T with U).
    func transcribe() -> [Character] {
        sequence.map(\.rnaEquivalent)
    }

    // MARK: - Translation

    /// Translate RNA codons into amino acid sequence.
    func translate() -> [String] {
        let rna = transcribe()
        var proteins: [String] = []
        var i = 0
        var translating = false

        while i + 2 < rna.count {
            let codon = String([rna[i], rna[i + 1], rna[i + 2]])

            if codon == "AUG" {
                translating = true
            }

            if translating {
                if let aa = BiologyParams.codonTable[codon] {
                    if aa == "STOP" {
                        break
                    }
                    proteins.append(aa)
                }
            }
            i += 3
        }

        return proteins
    }

    // MARK: - Mutation

    /// Apply point mutations at given rate.
    mutating func mutate(rate: Double) {
        for i in sequence.indices {
            // Methylated bases have lower mutation rate
            let effectiveRate = methylation[i] ? rate * 0.1 : rate
            if Double.random(in: 0...1) < effectiveRate {
                let currentBase = sequence[i]
                var newBase = NucleotideBase.random()
                while newBase == currentBase {
                    newBase = NucleotideBase.random()
                }
                sequence[i] = newBase
            }
        }
    }

    /// Insert a random base at a random position.
    mutating func insertionMutation() {
        guard !sequence.isEmpty else { return }
        let pos = Int.random(in: 0...sequence.count)
        sequence.insert(NucleotideBase.random(), at: pos)
        methylation.insert(false, at: pos)
    }

    /// Delete a random base.
    mutating func deletionMutation() {
        guard sequence.count > 3 else { return }
        let pos = Int.random(in: 0..<sequence.count)
        sequence.remove(at: pos)
        methylation.remove(at: pos)
    }

    // MARK: - Epigenetics

    /// Apply methylation at CpG sites.
    mutating func applyMethylation() {
        for i in 0..<(sequence.count - 1) {
            if sequence[i] == .cytosine && sequence[i + 1] == .guanine {
                if Double.random(in: 0...1) < EpigeneticParams.methylationProbability {
                    methylation[i] = true
                }
            }
        }
    }

    /// Remove methylation marks stochastically.
    mutating func demethylate() {
        for i in methylation.indices {
            if methylation[i] && Double.random(in: 0...1) < EpigeneticParams.demethylationProbability {
                methylation[i] = false
            }
        }
    }

    var methylationLevel: Double {
        guard !methylation.isEmpty else { return 0.0 }
        let methylatedCount = methylation.filter { $0 }.count
        return Double(methylatedCount) / Double(methylation.count)
    }

    // MARK: - Replication

    /// Replicate DNA with possible errors.
    func replicate(errorRate: Double = 1e-4) -> DNAStrand {
        var copy = DNAStrand(sequence: sequence)
        copy.methylation = methylation
        copy.mutate(rate: errorRate)

        // Occasionally inherit methylation patterns (epigenetic inheritance)
        for i in copy.methylation.indices where i < methylation.count {
            if methylation[i] && Double.random(in: 0...1) < 0.8 {
                copy.methylation[i] = true
            }
        }

        return copy
    }
}

// MARK: - Cell

final class Cell: Identifiable {
    static let idGenerator = IDGenerator()

    let id: Int
    var dna: DNAStrand
    var proteins: [String]
    var energy: Double
    var age: Int
    var generation: Int
    var position: SIMD3<Double>
    var fitness: Double
    var isAlive: Bool
    var hasMembraneIntegrity: Bool

    /// Derived traits from DNA/proteins
    var metabolicRate: Double {
        max(0.1, fitness * 0.5 + dna.gcContent * 0.3)
    }

    var reproductionThreshold: Double {
        50.0 / max(0.1, fitness)
    }

    /// Color for rendering based on fitness
    var displayColor: SIMD4<Float> {
        let g = Float(min(1.0, fitness))
        let r = Float(1.0 - min(1.0, fitness))
        return SIMD4<Float>(r, g, 0.3, 1.0)
    }

    init(
        dna: DNAStrand = DNAStrand(),
        energy: Double = 20.0,
        generation: Int = 0,
        position: SIMD3<Double> = .zero
    ) {
        self.id = Cell.idGenerator.next()
        self.dna = dna
        self.proteins = dna.translate()
        self.energy = energy
        self.age = 0
        self.generation = generation
        self.position = position
        self.fitness = 0.5
        self.isAlive = true
        self.hasMembraneIntegrity = true

        computeFitness()
    }

    // MARK: - Fitness

    /// Compute fitness from protein expression and DNA properties.
    func computeFitness() {
        var score = 0.5

        // Protein diversity contributes to fitness
        let uniqueProteins = Set(proteins)
        score += min(0.3, Double(uniqueProteins.count) * 0.03)

        // GC content stability (prefer moderate GC)
        let gcOpt = abs(dna.gcContent - 0.5)
        score -= gcOpt * 0.2

        // Longer functional sequences are beneficial
        score += min(0.2, Double(proteins.count) * 0.02)

        // Methylation provides regulatory flexibility
        score += dna.methylationLevel * 0.1

        fitness = max(0.01, min(1.0, score))
    }

    // MARK: - Metabolism

    /// Consume energy for survival; returns false if cell dies.
    @discardableResult
    func metabolize(availableEnergy: Double) -> Bool {
        let consumption = metabolicRate * 0.1
        let absorbed = min(availableEnergy, consumption * 2.0)
        energy += absorbed - consumption

        age += 1

        if energy <= 0 {
            isAlive = false
            return false
        }

        // Age-related death probability
        let ageFactor = Double(age) / 1000.0
        if Double.random(in: 0...1) < ageFactor * 0.01 {
            isAlive = false
            return false
        }

        return true
    }

    // MARK: - Division

    /// Attempt cell division. Returns daughter cell if successful.
    func divide(mutationRate: Double) -> Cell? {
        guard isAlive && energy >= reproductionThreshold else { return nil }

        let daughterDNA = dna.replicate(errorRate: mutationRate)

        // Frameshift mutations (rare)
        if Double.random(in: 0...1) < mutationRate * 10.0 {
            var mutatedDNA = daughterDNA
            if Bool.random() {
                mutatedDNA.insertionMutation()
            } else {
                mutatedDNA.deletionMutation()
            }
            let daughter = Cell(
                dna: mutatedDNA,
                energy: energy / 2.0,
                generation: generation + 1,
                position: position + SIMD3<Double>.randomGaussian(sigma: 1.0)
            )
            energy /= 2.0
            return daughter
        }

        let daughter = Cell(
            dna: daughterDNA,
            energy: energy / 2.0,
            generation: generation + 1,
            position: position + SIMD3<Double>.randomGaussian(sigma: 1.0)
        )
        energy /= 2.0
        return daughter
    }

    // MARK: - Damage

    /// Apply radiation damage.
    func applyRadiationDamage(intensity: Double) {
        let damageProb = intensity * EnvironmentParams.uvMutationRate
        if Double.random(in: 0...1) < damageProb {
            dna.mutate(rate: intensity * 0.01)
            proteins = dna.translate()
            computeFitness()
        }

        if intensity > EnvironmentParams.radiationDamageThreshold {
            let lethalProb = (intensity - EnvironmentParams.radiationDamageThreshold) * 0.01
            if Double.random(in: 0...1) < lethalProb {
                isAlive = false
            }
        }
    }

    // MARK: - Epigenetic Regulation

    /// Perform epigenetic updates.
    func regulateEpigenetics() {
        dna.applyMethylation()
        dna.demethylate()
        proteins = dna.translate()
        computeFitness()
    }
}

// MARK: - Biosphere

final class Biosphere {
    var cells: [Cell] = []
    var extinctSpeciesCount: Int = 0
    var totalDivisions: Int = 0
    var totalDeaths: Int = 0
    var maxGenerationReached: Int = 0
    var mutationRate: Double = 1e-4

    /// The available energy pool for cells to draw from.
    var availableEnergy: Double = 100.0

    // MARK: - Abiogenesis

    /// Spontaneously generate the first cells from precursor molecules.
    /// This models the origin of life from chemical building blocks.
    func abiogenesis(
        aminoAcidCount: Int,
        nucleotideCount: Int,
        hasWater: Bool,
        temperature: Double
    ) -> [Cell] {
        var newCells: [Cell] = []

        // Require preconditions for life
        guard aminoAcidCount >= 3 && nucleotideCount >= 2 && hasWater else {
            return newCells
        }

        // Goldilocks temperature zone
        guard temperature > 250.0 && temperature < 400.0 else {
            return newCells
        }

        // Very low probability per tick, increasing with more precursors
        let baseProbability = 0.001
        let boost = Double(aminoAcidCount + nucleotideCount) * 0.0001
        let prob = min(0.05, baseProbability + boost)

        guard Double.random(in: 0...1) < prob else {
            return newCells
        }

        // Create a protocell with a short random genome
        let genomeLength = min(30, nucleotideCount * 3)
        let dna = DNAStrand(length: genomeLength)
        let cell = Cell(
            dna: dna,
            energy: 30.0,
            generation: 0,
            position: SIMD3<Double>.randomGaussian(sigma: 20.0)
        )
        newCells.append(cell)
        cells.append(cell)

        return newCells
    }

    // MARK: - Evolution Tick

    /// Run one tick of evolution: metabolism, selection, reproduction, epigenetics.
    func evolve(temperature: Double, radiationLevel: Double, energyAvailable: Double) {
        availableEnergy = energyAvailable

        // Per-cell energy share
        let energyPerCell = cells.isEmpty ? 0.0 : availableEnergy / Double(cells.count)

        // Metabolism and survival
        for cell in cells {
            cell.metabolize(availableEnergy: energyPerCell)

            // Radiation damage
            cell.applyRadiationDamage(intensity: radiationLevel)

            // Epigenetic regulation (occasional)
            if Int.random(in: 0..<10) == 0 {
                cell.regulateEpigenetics()
            }
        }

        // Remove dead cells
        let deadCount = cells.filter { !$0.isAlive }.count
        totalDeaths += deadCount
        cells.removeAll { !$0.isAlive }

        // Reproduction
        var newCells: [Cell] = []
        for cell in cells {
            guard cells.count + newCells.count < SimulationLimits.maxCells else { break }
            if let daughter = cell.divide(mutationRate: mutationRate) {
                newCells.append(daughter)
                totalDivisions += 1
                maxGenerationReached = max(maxGenerationReached, daughter.generation)
            }
        }
        cells.append(contentsOf: newCells)

        // Natural selection pressure: if overpopulated, remove least fit
        if cells.count > SimulationLimits.maxCells {
            cells.sort { $0.fitness > $1.fitness }
            let excess = cells.count - SimulationLimits.maxCells
            let removed = cells.suffix(excess)
            totalDeaths += removed.count
            cells.removeLast(excess)
        }
    }

    // MARK: - Statistics

    var livingCellCount: Int { cells.count }

    var averageFitness: Double {
        guard !cells.isEmpty else { return 0.0 }
        return cells.reduce(0.0) { $0 + $1.fitness } / Double(cells.count)
    }

    var averageGeneration: Double {
        guard !cells.isEmpty else { return 0.0 }
        return Double(cells.reduce(0) { $0 + $1.generation }) / Double(cells.count)
    }

    var averageGenomeLength: Double {
        guard !cells.isEmpty else { return 0.0 }
        return Double(cells.reduce(0) { $0 + $1.dna.length }) / Double(cells.count)
    }

    var maxFitness: Double {
        cells.map(\.fitness).max() ?? 0.0
    }

    /// Return the fittest cell, if any.
    var fittestCell: Cell? {
        cells.max(by: { $0.fitness < $1.fitness })
    }

    /// Diversity metric: unique protein sets across population.
    var geneticDiversity: Double {
        guard cells.count > 1 else { return 0.0 }
        let uniqueGenomes = Set(cells.map { $0.dna.sequence.map(\.rawValue) })
        return Double(uniqueGenomes.count) / Double(cells.count)
    }
}
