package com.inthebeginning.simulator

import com.inthebeginning.simulator.Constants.AMINO_ACIDS
import com.inthebeginning.simulator.Constants.CODON_TABLE
import com.inthebeginning.simulator.Constants.DEMETHYLATION_PROBABILITY
import com.inthebeginning.simulator.Constants.HISTONE_ACETYLATION_PROB
import com.inthebeginning.simulator.Constants.HISTONE_DEACETYLATION_PROB
import com.inthebeginning.simulator.Constants.METHYLATION_PROBABILITY
import com.inthebeginning.simulator.Constants.NUCLEOTIDE_BASES
import kotlin.random.Random

/**
 * A strand of DNA represented as a sequence of nucleotide bases.
 */
data class DNA(
    val sequence: MutableList<String>,
    val methylation: MutableList<Boolean> = MutableList(0) { false },
    val dnaId: Int = nextId()
) {
    companion object {
        private var idCounter = 0
        fun nextId(): Int = ++idCounter
        fun resetIds() { idCounter = 0 }

        /** Generate a random DNA sequence of the given length. */
        fun random(length: Int, rng: Random = Random): DNA {
            val seq = MutableList(length) { NUCLEOTIDE_BASES[rng.nextInt(4)] }
            val meth = MutableList(length) { false }
            return DNA(seq, meth)
        }
    }

    init {
        // Ensure methylation list matches sequence length
        while (methylation.size < sequence.size) {
            methylation.add(false)
        }
    }

    val length: Int get() = sequence.size

    /** Complementary strand. */
    val complementary: List<String>
        get() = sequence.map { base ->
            when (base) {
                "A" -> "T"; "T" -> "A"; "G" -> "C"; "C" -> "G"; else -> "N"
            }
        }

    /** Transcribe DNA to mRNA (T -> U). */
    fun transcribe(): List<String> = sequence.map { base ->
        when (base) {
            "T" -> "U"
            else -> base
        }
    }

    /** Translate mRNA to amino acid sequence using the codon table. */
    fun translate(): List<String> {
        val mRNA = transcribe()
        val protein = mutableListOf<String>()

        // Find start codon
        var i = 0
        while (i + 2 < mRNA.size) {
            val codon = "${mRNA[i]}${mRNA[i + 1]}${mRNA[i + 2]}"
            if (codon == "AUG") break
            i++
        }

        // Translate from start codon
        while (i + 2 < mRNA.size) {
            val codon = "${mRNA[i]}${mRNA[i + 1]}${mRNA[i + 2]}"
            val aa = CODON_TABLE[codon] ?: break
            if (aa == "STOP") break
            protein.add(aa)
            i += 3
        }

        return protein
    }

    /** GC content ratio (indicator of thermal stability). */
    val gcContent: Double
        get() {
            if (sequence.isEmpty()) return 0.0
            val gcCount = sequence.count { it == "G" || it == "C" }
            return gcCount.toDouble() / sequence.size
        }

    /** Fraction of methylated bases (epigenetic silencing). */
    val methylationFraction: Double
        get() {
            if (methylation.isEmpty()) return 0.0
            return methylation.count { it }.toDouble() / methylation.size
        }

    /** Deep copy of this DNA. */
    fun copy(): DNA = DNA(
        sequence = sequence.toMutableList(),
        methylation = methylation.toMutableList()
    )
}

/**
 * Histone modification state affecting gene expression.
 */
data class HistoneState(
    var acetylated: Boolean = false,
    var methylated: Boolean = false
) {
    /** Whether the chromatin is in an open (active) state. */
    val isOpen: Boolean get() = acetylated && !methylated
}

/**
 * Epigenetic state of a gene region.
 */
data class EpigeneticMark(
    val geneIndex: Int,
    var dnaMethylated: Boolean = false,
    val histone: HistoneState = HistoneState()
) {
    /** Whether the gene is silenced by epigenetic marks. */
    val isSilenced: Boolean get() = dnaMethylated || !histone.isOpen
}

/**
 * Represents a single-celled organism with DNA and metabolic state.
 */
class Cell(
    val genome: DNA,
    var energy: Double = 100.0,
    var fitness: Double = 1.0,
    var generation: Int = 0,
    val epigeneticMarks: MutableList<EpigeneticMark> = mutableListOf(),
    val cellId: Int = nextCellId()
) {
    companion object {
        private var idCounter = 0
        fun nextCellId(): Int = ++idCounter
        fun resetIds() { idCounter = 0 }
    }

    var alive: Boolean = true
    var age: Int = 0
    var mutationCount: Int = 0

    /** Express genome: translate to protein, assess fitness. */
    fun expressGenome(): List<String> {
        val protein = genome.translate()
        // Fitness based on protein diversity and length
        val diversity = protein.distinct().size.toDouble()
        val lengthFactor = (protein.size.toDouble() / genome.length * 3.0).coerceIn(0.1, 2.0)
        fitness = (diversity / AMINO_ACIDS.size * lengthFactor).coerceIn(0.01, 10.0)

        // Epigenetic silencing reduces fitness moderately
        val silencedFraction = epigeneticMarks.count { it.isSilenced }.toDouble() /
                epigeneticMarks.size.coerceAtLeast(1)
        fitness *= (1.0 - silencedFraction * 0.3)

        return protein
    }

    /** Metabolize: consume energy proportional to genome size. */
    fun metabolize() {
        val cost = genome.length * 0.001 + 0.5
        energy -= cost
        age++
        if (energy <= 0.0) alive = false
    }

    /** Feed: gain energy from the environment. */
    fun feed(availableEnergy: Double) {
        energy += availableEnergy * fitness * 0.1
        energy = energy.coerceAtMost(200.0)
    }

    /** Is the cell ready to reproduce? */
    val canReproduce: Boolean
        get() = alive && energy > 80.0 && genome.length >= 9

    override fun toString(): String =
        "Cell(id=$cellId, gen=$generation, fitness=${String.format("%.3f", fitness)}, energy=${String.format("%.1f", energy)})"
}

/**
 * Mutation types that can affect DNA.
 */
sealed class Mutation(val name: String) {
    /** Single base substitution. */
    data class PointMutation(val position: Int, val oldBase: String, val newBase: String) :
        Mutation("point")

    /** Insertion of one or more bases. */
    data class Insertion(val position: Int, val bases: List<String>) :
        Mutation("insertion")

    /** Deletion of one or more bases. */
    data class Deletion(val position: Int, val count: Int) :
        Mutation("deletion")

    /** Duplication of a segment. */
    data class Duplication(val start: Int, val end: Int) :
        Mutation("duplication")

    /** Inversion of a segment. */
    data class Inversion(val start: Int, val end: Int) :
        Mutation("inversion")
}

/**
 * The biosphere manages populations of cells, mutation, reproduction,
 * and natural selection.
 */
class Biosphere {
    val population: MutableList<Cell> = mutableListOf()
    var totalGenerations: Int = 0
    var totalMutations: Int = 0
    var totalExtinctions: Int = 0
    var totalSpeciations: Int = 0

    private val rng = Random

    /** Maximum population size to prevent unbounded growth. */
    var carryingCapacity: Int = 500

    /**
     * Seed the biosphere with initial cells from RNA world.
     * Creates primitive cells with short random genomes.
     */
    fun seedLife(count: Int = 10, genomeLength: Int = 30): List<Cell> {
        val cells = mutableListOf<Cell>()
        repeat(count) {
            val dna = DNA.random(genomeLength, rng)
            val cell = Cell(
                genome = dna,
                energy = 100.0,
                generation = 0
            )
            // Initialize epigenetic marks
            for (i in 0 until (genomeLength / 10).coerceAtLeast(1)) {
                cell.epigeneticMarks.add(EpigeneticMark(geneIndex = i))
            }
            cell.expressGenome()
            cells.add(cell)
            population.add(cell)
        }
        return cells
    }

    /**
     * Apply a random mutation to a DNA strand.
     * Returns the mutation applied, or null if none occurred.
     */
    fun mutate(dna: DNA, mutationRate: Double = 0.01): Mutation? {
        if (rng.nextDouble() > mutationRate) return null
        if (dna.length == 0) return null

        val roll = rng.nextDouble()
        val mutation: Mutation = when {
            // Point mutation (most common)
            roll < 0.6 -> {
                val pos = rng.nextInt(dna.length)
                val oldBase = dna.sequence[pos]
                val newBase = NUCLEOTIDE_BASES.filter { it != oldBase }.random(rng)
                dna.sequence[pos] = newBase
                Mutation.PointMutation(pos, oldBase, newBase)
            }
            // Insertion
            roll < 0.75 -> {
                val pos = rng.nextInt(dna.length)
                val insertLen = rng.nextInt(1, 4)
                val bases = List(insertLen) { NUCLEOTIDE_BASES.random(rng) }
                dna.sequence.addAll(pos, bases)
                // Extend methylation list
                repeat(insertLen) { dna.methylation.add(pos, false) }
                Mutation.Insertion(pos, bases)
            }
            // Deletion
            roll < 0.9 -> {
                val count = rng.nextInt(1, 4).coerceAtMost(dna.length)
                val pos = rng.nextInt(dna.length - count + 1)
                repeat(count) {
                    dna.sequence.removeAt(pos)
                    if (pos < dna.methylation.size) dna.methylation.removeAt(pos)
                }
                Mutation.Deletion(pos, count)
            }
            // Duplication
            roll < 0.95 -> {
                val segLen = rng.nextInt(1, (dna.length / 4).coerceAtLeast(2))
                val start = rng.nextInt(dna.length - segLen + 1)
                val segment = dna.sequence.subList(start, start + segLen).toList()
                dna.sequence.addAll(start + segLen, segment)
                repeat(segLen) { dna.methylation.add(false) }
                Mutation.Duplication(start, start + segLen)
            }
            // Inversion
            else -> {
                val segLen = rng.nextInt(2, (dna.length / 3).coerceAtLeast(3))
                val start = rng.nextInt(dna.length - segLen + 1)
                val end = start + segLen
                val segment = dna.sequence.subList(start, end).reversed()
                for (i in segment.indices) {
                    dna.sequence[start + i] = segment[i]
                }
                Mutation.Inversion(start, end)
            }
        }

        totalMutations++
        return mutation
    }

    /**
     * Update epigenetic marks on a cell's genome.
     */
    fun updateEpigenetics(cell: Cell) {
        for (mark in cell.epigeneticMarks) {
            // DNA methylation
            if (!mark.dnaMethylated && rng.nextDouble() < METHYLATION_PROBABILITY) {
                mark.dnaMethylated = true
                // Also methylate the corresponding genome position
                val genomePos = (mark.geneIndex * 10).coerceAtMost(cell.genome.length - 1)
                if (genomePos >= 0) cell.genome.methylation[genomePos] = true
            } else if (mark.dnaMethylated && rng.nextDouble() < DEMETHYLATION_PROBABILITY) {
                mark.dnaMethylated = false
            }

            // Histone acetylation
            if (!mark.histone.acetylated && rng.nextDouble() < HISTONE_ACETYLATION_PROB) {
                mark.histone.acetylated = true
            } else if (mark.histone.acetylated && rng.nextDouble() < HISTONE_DEACETYLATION_PROB) {
                mark.histone.acetylated = false
            }
        }
    }

    /**
     * Reproduce a cell asexually (binary fission with possible mutations).
     */
    fun reproduce(parent: Cell, mutationRate: Double = 0.01): Cell? {
        if (!parent.canReproduce) return null

        // Copy genome with possible mutations
        val childGenome = parent.genome.copy()
        mutate(childGenome, mutationRate)

        // Daughter cell
        val child = Cell(
            genome = childGenome,
            energy = parent.energy * 0.45,
            generation = parent.generation + 1
        )

        // Inherit some epigenetic marks
        for (mark in parent.epigeneticMarks) {
            val inherited = EpigeneticMark(
                geneIndex = mark.geneIndex,
                dnaMethylated = mark.dnaMethylated && rng.nextDouble() < 0.8,
                histone = HistoneState(
                    acetylated = mark.histone.acetylated,
                    methylated = mark.histone.methylated
                )
            )
            child.epigeneticMarks.add(inherited)
        }

        child.expressGenome()

        // Parent loses energy from reproduction
        parent.energy *= 0.45

        population.add(child)
        parent.mutationCount += if (totalMutations > 0) 1 else 0

        return child
    }

    /**
     * Natural selection: remove unfit cells, capped by carrying capacity.
     */
    fun naturalSelection(environment: Environment) {
        // Remove dead cells
        population.removeAll { !it.alive }

        // Environmental stress reduces energy
        val stress = environment.stressFactor
        for (cell in population) {
            cell.energy -= stress * 0.5
            if (cell.energy <= 0.0) cell.alive = false
        }
        population.removeAll { !it.alive }

        // If over carrying capacity, remove least fit
        if (population.size > carryingCapacity) {
            population.sortByDescending { it.fitness }
            val toRemove = population.size - carryingCapacity
            repeat(toRemove) {
                population.removeAt(population.lastIndex)
            }
            totalExtinctions += toRemove
        }
    }

    /**
     * Evolve one generation: metabolize, feed, mutate, reproduce, select.
     */
    fun evolveGeneration(environment: Environment) {
        if (population.isEmpty()) return
        totalGenerations++

        val mutationRate = 0.01 + environment.mutationRate

        // Metabolize and feed
        val energyPerCell = if (environment.isHabitable) 5.0 else 1.0
        for (cell in population.toList()) {
            cell.metabolize()
            cell.feed(energyPerCell)
            updateEpigenetics(cell)
        }

        // Reproduction
        val parents = population.filter { it.canReproduce }.toList()
        for (parent in parents) {
            if (population.size < carryingCapacity) {
                reproduce(parent, mutationRate)
            }
        }

        // Natural selection
        naturalSelection(environment)

        // Random catastrophe
        environment.randomCatastrophe()
    }

    /** Average fitness of the population. */
    val averageFitness: Double
        get() = if (population.isEmpty()) 0.0
        else population.sumOf { it.fitness } / population.size

    /** Maximum fitness in the population. */
    val maxFitness: Double
        get() = population.maxOfOrNull { it.fitness } ?: 0.0

    /** Average genome length. */
    val averageGenomeLength: Double
        get() = if (population.isEmpty()) 0.0
        else population.sumOf { it.genome.length.toDouble() } / population.size

    /** Number of distinct "species" (based on genome similarity clustering). */
    val speciesCount: Int
        get() {
            if (population.size <= 1) return population.size
            // Simple diversity measure: count distinct GC content buckets
            val buckets = population.map { (it.genome.gcContent * 10).toInt() }.distinct()
            return buckets.size.coerceAtLeast(1)
        }

    /** Maximum generation reached. */
    val maxGeneration: Int
        get() = population.maxOfOrNull { it.generation } ?: 0

    /** Summary statistics. */
    fun summary(): Map<String, Any> = mapOf(
        "populationSize" to population.size,
        "averageFitness" to averageFitness,
        "maxFitness" to maxFitness,
        "totalGenerations" to totalGenerations,
        "totalMutations" to totalMutations,
        "speciesCount" to speciesCount,
        "averageGenomeLength" to averageGenomeLength,
        "maxGeneration" to maxGeneration,
    )
}
