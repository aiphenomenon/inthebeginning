// Biosphere.swift
// InTheBeginning – macOS Screensaver
//
// Biological systems simulation.
// Models DNA, cells, metabolism, mutation, and natural selection.
// Life emerges from the chemical substrate when conditions are right.

import Foundation

// MARK: - Nucleotide

enum Nucleotide: Character, CaseIterable {
    case adenine  = "A"
    case thymine  = "T"
    case guanine  = "G"
    case cytosine = "C"

    var complement: Nucleotide {
        switch self {
        case .adenine:  return .thymine
        case .thymine:  return .adenine
        case .guanine:  return .cytosine
        case .cytosine: return .guanine
        }
    }

    /// Convert DNA base to RNA base for transcription.
    var rnaBase: Character {
        switch self {
        case .adenine:  return "A"
        case .thymine:  return "U"   // T -> U in RNA
        case .guanine:  return "G"
        case .cytosine: return "C"
        }
    }
}

// MARK: - Gene

struct Gene {
    var name: String
    var startIndex: Int
    var length: Int
    var isActive: Bool
    var methylated: Bool

    /// Expression level: 0.0 (silenced) to 1.0 (fully active).
    var expressionLevel: Double {
        if !isActive { return 0.0 }
        return methylated ? 0.1 : 1.0
    }
}

// MARK: - DNA Strand

struct DNAStrand {
    var sequence: [Nucleotide]
    var genes: [Gene]
    var methylationMap: [Bool]
    var mutationCount: Int = 0

    var length: Int { sequence.count }

    init(length: Int = 100) {
        sequence = (0..<length).map { _ in Nucleotide.allCases.randomElement()! }
        methylationMap = [Bool](repeating: false, count: length)
        genes = DNAStrand.identifyGenes(in: sequence)
    }

    init(sequence: [Nucleotide], genes: [Gene] = [], methylationMap: [Bool] = []) {
        self.sequence = sequence
        self.methylationMap = methylationMap.isEmpty
            ? [Bool](repeating: false, count: sequence.count)
            : methylationMap
        self.genes = genes.isEmpty
            ? DNAStrand.identifyGenes(in: sequence)
            : genes
    }

    // MARK: Gene Identification

    /// Scan sequence for start codons (ATG) and stop codons to define genes.
    static func identifyGenes(in seq: [Nucleotide]) -> [Gene] {
        var genes: [Gene] = []
        var geneIndex = 0
        var i = 0
        while i + 2 < seq.count {
            // Look for ATG start codon
            if seq[i] == .adenine && seq[i + 1] == .thymine && seq[i + 2] == .guanine {
                let start = i
                var j = i + 3
                // Scan for stop codon (TAA, TAG, TGA)
                while j + 2 < seq.count {
                    let isStop =
                        (seq[j] == .thymine && seq[j + 1] == .adenine && seq[j + 2] == .adenine) ||
                        (seq[j] == .thymine && seq[j + 1] == .adenine && seq[j + 2] == .guanine) ||
                        (seq[j] == .thymine && seq[j + 1] == .guanine && seq[j + 2] == .adenine)
                    if isStop {
                        let len = j + 3 - start
                        if len >= 9 {   // Minimum gene length: start + 1 codon + stop
                            genes.append(Gene(
                                name: "gene_\(geneIndex)",
                                startIndex: start,
                                length: len,
                                isActive: true,
                                methylated: false
                            ))
                            geneIndex += 1
                        }
                        i = j + 3
                        break
                    }
                    j += 3
                }
                if j + 2 >= seq.count { break }
            } else {
                i += 1
            }
        }
        return genes
    }

    // MARK: Transcription

    /// Transcribe a gene to mRNA (as Character array).
    func transcribe(gene: Gene) -> [Character] {
        guard gene.isActive else { return [] }
        let end = min(gene.startIndex + gene.length, sequence.count)
        return (gene.startIndex..<end).map { sequence[$0].rnaBase }
    }

    /// Translate mRNA to amino acid sequence using the codon table.
    static func translate(mRNA: [Character]) -> [String] {
        var proteins: [String] = []
        var i = 0
        // Skip to AUG start codon
        while i + 2 < mRNA.count {
            let codon = String([mRNA[i], mRNA[i + 1], mRNA[i + 2]])
            if codon == "AUG" { break }
            i += 3
        }
        while i + 2 < mRNA.count {
            let codon = String([mRNA[i], mRNA[i + 1], mRNA[i + 2]])
            if let aa = kCodonTable[codon] {
                if aa == "STOP" { break }
                proteins.append(aa)
            }
            i += 3
        }
        return proteins
    }

    // MARK: Mutation

    /// Point mutation: change a single nucleotide at random.
    mutating func pointMutation(rate: Double = kUVMutationRate) {
        for i in 0..<sequence.count {
            if Double.random(in: 0..<1) < rate {
                let original = sequence[i]
                var choices = Nucleotide.allCases.filter { $0 != original }
                sequence[i] = choices.randomElement()!
                mutationCount += 1
            }
        }
        genes = DNAStrand.identifyGenes(in: sequence)
    }

    /// Insertion mutation: insert a random nucleotide.
    mutating func insertionMutation() {
        guard sequence.count < 10000 else { return }
        let pos = Int.random(in: 0...sequence.count)
        let base = Nucleotide.allCases.randomElement()!
        sequence.insert(base, at: pos)
        methylationMap.insert(false, at: pos)
        mutationCount += 1
        genes = DNAStrand.identifyGenes(in: sequence)
    }

    /// Deletion mutation: remove a nucleotide.
    mutating func deletionMutation() {
        guard sequence.count > 10 else { return }
        let pos = Int.random(in: 0..<sequence.count)
        sequence.remove(at: pos)
        methylationMap.remove(at: pos)
        mutationCount += 1
        genes = DNAStrand.identifyGenes(in: sequence)
    }

    // MARK: Epigenetics

    /// Apply methylation/demethylation stochastically.
    mutating func updateMethylation() {
        for i in 0..<methylationMap.count {
            if methylationMap[i] {
                if Double.random(in: 0..<1) < kDemethylationProbability {
                    methylationMap[i] = false
                }
            } else {
                if Double.random(in: 0..<1) < kMethylationProbability {
                    methylationMap[i] = true
                }
            }
        }
        // Update gene methylation status
        for j in 0..<genes.count {
            let start = genes[j].startIndex
            let end = min(start + genes[j].length, methylationMap.count)
            guard start < end else { continue }
            let methylCount = methylationMap[start..<end].filter { $0 }.count
            genes[j].methylated = Double(methylCount) / Double(end - start) > 0.5
        }
    }

    // MARK: Replication

    /// Replicate this DNA strand (with potential copy errors).
    func replicate(errorRate: Double = 1e-5) -> DNAStrand {
        var newSeq = sequence
        for i in 0..<newSeq.count {
            if Double.random(in: 0..<1) < errorRate {
                newSeq[i] = Nucleotide.allCases.randomElement()!
            }
        }
        return DNAStrand(sequence: newSeq, methylationMap: methylationMap)
    }

    // MARK: Complementary Strand

    var complementary: [Nucleotide] {
        sequence.map { $0.complement }
    }
}

// MARK: - Cell

private var _cellIDCounter: Int = 0

struct Cell {
    let cellID: Int
    var dna: DNAStrand
    var fitness: Double
    var energy: Double
    var metabolismRate: Double
    var age: Int = 0
    var generation: Int = 0
    var position: SIMD3<Double>
    var isDead: Bool = false

    /// Proteins expressed by active genes.
    var expressedProteins: [String] = []

    var canDivide: Bool {
        energy >= 2.0 && age >= 10 && !isDead
    }

    init(dna: DNAStrand = DNAStrand(length: 100),
         fitness: Double = 1.0,
         energy: Double = 5.0,
         metabolismRate: Double = 0.1,
         generation: Int = 0,
         position: SIMD3<Double> = .zero) {
        _cellIDCounter += 1
        self.cellID = _cellIDCounter
        self.dna = dna
        self.fitness = fitness
        self.energy = energy
        self.metabolismRate = metabolismRate
        self.generation = generation
        self.position = position
    }

    // MARK: Metabolism

    /// One metabolic tick: consume energy, express genes, update fitness.
    mutating func metabolize(environmentalEnergy: Double) {
        guard !isDead else { return }
        age += 1

        // Energy intake from environment (proportional to fitness)
        energy += environmentalEnergy * fitness * metabolismRate

        // Basal metabolic cost
        let cost = metabolismRate * (1.0 + Double(dna.length) * 0.001)
        energy -= cost

        // Express proteins from active genes
        expressedProteins = []
        for gene in dna.genes where gene.expressionLevel > 0.5 {
            let mRNA = dna.transcribe(gene: gene)
            let proteins = DNAStrand.translate(mRNA: mRNA)
            expressedProteins.append(contentsOf: proteins)
        }

        // Fitness based on protein diversity and energy
        let proteinDiversity = Double(Set(expressedProteins).count)
        fitness = min(2.0, 0.5 + proteinDiversity * 0.1 + energy * 0.05)

        // Death check
        if energy <= 0 {
            isDead = true
            energy = 0
        }
    }

    // MARK: Division

    /// Divide this cell into two daughter cells.
    mutating func divide() -> Cell? {
        guard canDivide else { return nil }

        energy /= 2.0

        var daughterDNA = dna.replicate(errorRate: 1e-4)
        // Occasional mutations in the daughter
        if Double.random(in: 0..<1) < 0.1 {
            daughterDNA.pointMutation(rate: kUVMutationRate)
        }
        if Double.random(in: 0..<1) < 0.01 {
            daughterDNA.insertionMutation()
        }
        if Double.random(in: 0..<1) < 0.01 {
            daughterDNA.deletionMutation()
        }

        let offset = SIMD3<Double>(
            Double.random(in: -1...1),
            Double.random(in: -1...1),
            Double.random(in: -1...1)
        )

        var daughter = Cell(
            dna: daughterDNA,
            fitness: fitness * 0.9,
            energy: energy,
            metabolismRate: metabolismRate * Double.random(in: 0.95...1.05),
            generation: generation + 1,
            position: position + offset
        )
        daughter.isDead = false
        return daughter
    }
}

// MARK: - Biosphere

final class Biosphere {
    var cells: [Cell] = []
    var totalBorn: Int = 0
    var totalDied: Int = 0
    var generationMax: Int = 0
    var carryingCapacity: Int

    init(carryingCapacity: Int = kMaxRenderableCells) {
        self.carryingCapacity = carryingCapacity
    }

    // MARK: Seeding

    /// Seed the biosphere with initial protocells.
    func seed(count: Int, at position: SIMD3<Double> = .zero) {
        for _ in 0..<count {
            let offset = SIMD3<Double>(
                Double.random(in: -5...5),
                Double.random(in: -5...5),
                Double.random(in: -5...5)
            )
            let cell = Cell(
                dna: DNAStrand(length: Int.random(in: 50...200)),
                fitness: Double.random(in: 0.5...1.5),
                energy: Double.random(in: 3.0...8.0),
                position: position + offset
            )
            cells.append(cell)
            totalBorn += 1
        }
    }

    // MARK: Step

    /// Advance the biosphere by one tick.
    func step(environmentalEnergy: Double, mutationModifier: Double = 1.0) {
        // Metabolize
        for i in 0..<cells.count {
            cells[i].metabolize(environmentalEnergy: environmentalEnergy)
        }

        // Epigenetic updates
        for i in 0..<cells.count where !cells[i].isDead {
            cells[i].dna.updateMethylation()
        }

        // Environmental mutations
        if mutationModifier > 1.0 {
            for i in 0..<cells.count where !cells[i].isDead {
                let rate = kUVMutationRate * mutationModifier
                cells[i].dna.pointMutation(rate: rate)
            }
        }

        // Division
        var newCells: [Cell] = []
        for i in 0..<cells.count {
            if cells[i].canDivide && cells.count + newCells.count < carryingCapacity {
                if Double.random(in: 0..<1) < cells[i].fitness * 0.1 {
                    if var daughter = cells[i].divide() {
                        newCells.append(daughter)
                        totalBorn += 1
                    }
                }
            }
        }
        cells.append(contentsOf: newCells)

        // Remove dead cells
        let beforeCount = cells.count
        cells.removeAll { $0.isDead }
        totalDied += beforeCount - cells.count

        // Track max generation
        for cell in cells {
            if cell.generation > generationMax {
                generationMax = cell.generation
            }
        }
    }

    // MARK: Natural Selection

    /// Apply selection pressure: cull the weakest cells if over capacity.
    func naturalSelection() {
        guard cells.count > carryingCapacity else { return }
        cells.sort { $0.fitness > $1.fitness }
        let culled = cells.count - carryingCapacity
        cells.removeLast(culled)
        totalDied += culled
    }

    // MARK: Census

    func averageFitness() -> Double {
        guard !cells.isEmpty else { return 0.0 }
        return cells.reduce(0.0) { $0 + $1.fitness } / Double(cells.count)
    }

    func averageGenomeLength() -> Double {
        guard !cells.isEmpty else { return 0.0 }
        return cells.reduce(0.0) { $0 + Double($1.dna.length) } / Double(cells.count)
    }

    func populationCount() -> Int {
        cells.count
    }
}
