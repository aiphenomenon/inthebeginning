package com.inthebeginning.simulator

import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

class BiosphereTest {

    @Before
    fun resetIds() {
        DNA.resetIds()
        Cell.resetIds()
    }

    // --- DNA tests ---

    @Test
    fun dnaRandomLength() {
        val dna = DNA.random(30)
        assertEquals(30, dna.length)
    }

    @Test
    fun dnaValidBases() {
        val dna = DNA.random(100)
        for (base in dna.sequence) {
            assertTrue("Invalid base: $base", base in Constants.NUCLEOTIDE_BASES)
        }
    }

    @Test
    fun dnaComplementary() {
        val dna = DNA(mutableListOf("A", "T", "G", "C"))
        val comp = dna.complementary
        assertEquals(listOf("T", "A", "C", "G"), comp)
    }

    @Test
    fun dnaTranscribe() {
        val dna = DNA(mutableListOf("A", "T", "G", "C", "T"))
        val rna = dna.transcribe()
        assertEquals(listOf("A", "U", "G", "C", "U"), rna)
    }

    @Test
    fun dnaTranslate() {
        // ATG -> AUG (Met), TTT -> UUU (Phe), TAA -> UAA (STOP)
        val dna = DNA(mutableListOf("A", "T", "G", "T", "T", "T", "T", "A", "A"))
        val protein = dna.translate()
        assertTrue(protein.isNotEmpty())
        assertEquals("Met", protein[0])
    }

    @Test
    fun dnaGcContent() {
        val dna = DNA(mutableListOf("G", "C", "G", "C"))
        assertEquals(1.0, dna.gcContent, 0.0)

        val dna2 = DNA(mutableListOf("A", "T", "A", "T"))
        assertEquals(0.0, dna2.gcContent, 0.0)

        val dna3 = DNA(mutableListOf("A", "G", "T", "C"))
        assertEquals(0.5, dna3.gcContent, 0.0)
    }

    @Test
    fun dnaMethylationMatchesLength() {
        val dna = DNA.random(30)
        assertEquals(dna.length, dna.methylation.size)
    }

    @Test
    fun dnaCopy() {
        val dna = DNA.random(30)
        val copy = dna.copy()
        assertEquals(dna.length, copy.length)
        assertEquals(dna.sequence, copy.sequence)
        // They are independent
        copy.sequence[0] = "X"
        assertNotEquals(dna.sequence[0], copy.sequence[0])
    }

    @Test
    fun dnaMethylationFraction() {
        val dna = DNA(mutableListOf("A", "T", "G", "C"))
        assertEquals(0.0, dna.methylationFraction, 0.0)
        dna.methylation[0] = true
        dna.methylation[1] = true
        assertEquals(0.5, dna.methylationFraction, 0.0)
    }

    // --- HistoneState tests ---

    @Test
    fun histoneOpenState() {
        val h = HistoneState(acetylated = true, methylated = false)
        assertTrue(h.isOpen)

        val h2 = HistoneState(acetylated = true, methylated = true)
        assertFalse(h2.isOpen)

        val h3 = HistoneState(acetylated = false, methylated = false)
        assertFalse(h3.isOpen)
    }

    // --- EpigeneticMark tests ---

    @Test
    fun epigeneticMarkSilencing() {
        // By default, histone not acetylated -> silenced
        val mark = EpigeneticMark(geneIndex = 0)
        assertTrue(mark.isSilenced)

        val mark2 = EpigeneticMark(
            geneIndex = 0,
            dnaMethylated = false,
            histone = HistoneState(acetylated = true, methylated = false)
        )
        assertFalse(mark2.isSilenced)
    }

    // --- Cell tests ---

    @Test
    fun cellCreation() {
        val dna = DNA.random(30)
        val cell = Cell(genome = dna, energy = 100.0)
        assertTrue(cell.alive)
        assertEquals(100.0, cell.energy, 0.0)
        assertEquals(0, cell.generation)
    }

    @Test
    fun cellMetabolize() {
        val dna = DNA.random(30)
        val cell = Cell(genome = dna, energy = 100.0)
        val initialEnergy = cell.energy
        cell.metabolize()
        assertTrue(cell.energy < initialEnergy)
    }

    @Test
    fun cellDiesWhenEnergyDepleted() {
        val dna = DNA.random(30)
        val cell = Cell(genome = dna, energy = 0.01)
        cell.metabolize()
        assertFalse(cell.alive)
    }

    @Test
    fun cellFeed() {
        val dna = DNA.random(30)
        val cell = Cell(genome = dna, energy = 50.0)
        cell.expressGenome()
        val beforeFeed = cell.energy
        cell.feed(100.0)
        assertTrue(cell.energy > beforeFeed)
    }

    @Test
    fun cellCanReproduce() {
        val dna = DNA.random(30)
        val cell = Cell(genome = dna, energy = 150.0)
        assertTrue(cell.canReproduce)

        val lowEnergyCell = Cell(genome = dna, energy = 10.0)
        assertFalse(lowEnergyCell.canReproduce)
    }

    @Test
    fun cellExpressGenome() {
        val dna = DNA.random(30)
        val cell = Cell(genome = dna)
        val protein = cell.expressGenome()
        assertTrue(cell.fitness > 0)
    }

    // --- Biosphere tests ---

    @Test
    fun biosphereSeedLife() {
        val bio = Biosphere()
        val cells = bio.seedLife(5, 30)
        assertEquals(5, cells.size)
        assertEquals(5, bio.population.size)
    }

    @Test
    fun biosphereMutate() {
        val bio = Biosphere()
        val dna = DNA.random(30)
        val original = dna.sequence.toList()

        // With 100% mutation rate, mutation should definitely happen
        val mutation = bio.mutate(dna, 1.0)
        assertNotNull(mutation)
        assertTrue(bio.totalMutations > 0)
    }

    @Test
    fun biosphereReproduce() {
        val bio = Biosphere()
        val dna = DNA.random(30)
        val parent = Cell(genome = dna, energy = 150.0)
        parent.expressGenome()
        bio.population.add(parent)

        val child = bio.reproduce(parent)
        if (child != null) {
            assertEquals(1, child.generation)
            assertTrue(bio.population.size >= 2)
        }
    }

    @Test
    fun biosphereEvolveGeneration() {
        val bio = Biosphere()
        bio.seedLife(10, 30)
        val env = Environment(temperature = 300.0)
        env.ocean.volume = 10.0

        bio.evolveGeneration(env)
        assertEquals(1, bio.totalGenerations)
    }

    @Test
    fun biosphereAverageFitness() {
        val bio = Biosphere()
        bio.seedLife(5, 30)
        val avg = bio.averageFitness
        assertTrue(avg >= 0)
    }

    @Test
    fun biosphereSpeciesCount() {
        val bio = Biosphere()
        bio.seedLife(10, 30)
        assertTrue(bio.speciesCount >= 1)
    }

    @Test
    fun biosphereSummary() {
        val bio = Biosphere()
        bio.seedLife(5, 30)
        val summary = bio.summary()
        assertTrue(summary.containsKey("populationSize"))
        assertTrue(summary.containsKey("averageFitness"))
        assertTrue(summary.containsKey("totalMutations"))
        assertTrue(summary.containsKey("maxFitness"))
        assertTrue(summary.containsKey("speciesCount"))
        assertTrue(summary.containsKey("averageGenomeLength"))
        assertTrue(summary.containsKey("maxGeneration"))
        assertTrue(summary.containsKey("totalGenerations"))
    }

    // --- DNA additional tests ---

    @Test
    fun dnaGcContentEmptySequence() {
        val dna = DNA(mutableListOf())
        assertEquals(0.0, dna.gcContent, 0.0)
    }

    @Test
    fun dnaMethylationFractionEmpty() {
        val dna = DNA(mutableListOf())
        assertEquals(0.0, dna.methylationFraction, 0.0)
    }

    @Test
    fun dnaTranslateNoStartCodon() {
        // No ATG -> no protein
        val dna = DNA(mutableListOf("T", "T", "T", "C", "C", "C", "G", "G", "G"))
        val protein = dna.translate()
        assertTrue(protein.isEmpty())
    }

    @Test
    fun dnaTranslateMultipleCodons() {
        // ATG (Met) TTT (Phe) GCU->GCA... actually we need DNA bases
        // ATG -> AUG (Met), GCT -> GCU (Ala), TAA -> UAA (STOP)
        val dna = DNA(mutableListOf("A", "T", "G", "G", "C", "T", "T", "A", "A"))
        val protein = dna.translate()
        assertEquals(2, protein.size)
        assertEquals("Met", protein[0])
        assertEquals("Ala", protein[1])
    }

    @Test
    fun dnaComplementaryUnknownBase() {
        val dna = DNA(mutableListOf("X"))
        val comp = dna.complementary
        assertEquals(listOf("N"), comp)
    }

    @Test
    fun dnaUniqueIds() {
        val d1 = DNA.random(10)
        val d2 = DNA.random(10)
        assertNotEquals(d1.dnaId, d2.dnaId)
    }

    @Test
    fun dnaMethylationInitMatchesSequence() {
        // When methylation list is shorter than sequence, init fills it
        val seq = mutableListOf("A", "T", "G", "C", "A")
        val meth = mutableListOf(false, false) // Only 2, should be extended to 5
        val dna = DNA(seq, meth)
        assertEquals(5, dna.methylation.size)
    }

    // --- Cell additional tests ---

    @Test
    fun cellToString() {
        val dna = DNA.random(30)
        val cell = Cell(genome = dna, energy = 100.0)
        val str = cell.toString()
        assertTrue(str.contains("Cell"))
        assertTrue(str.contains("gen="))
        assertTrue(str.contains("fitness="))
        assertTrue(str.contains("energy="))
    }

    @Test
    fun cellCanReproduceDeadCell() {
        val dna = DNA.random(30)
        val cell = Cell(genome = dna, energy = 150.0)
        cell.alive = false
        assertFalse(cell.canReproduce)
    }

    @Test
    fun cellCanReproduceShortGenome() {
        // Genome shorter than 9 bases
        val dna = DNA(mutableListOf("A", "T", "G"))
        val cell = Cell(genome = dna, energy = 150.0)
        assertFalse(cell.canReproduce)
    }

    @Test
    fun cellFeedCappedAt200() {
        val dna = DNA.random(30)
        val cell = Cell(genome = dna, energy = 195.0, fitness = 1.0)
        cell.expressGenome()
        cell.feed(10000.0) // Feed a huge amount
        assertTrue(cell.energy <= 200.0)
    }

    @Test
    fun cellMetabolizeIncreasesAge() {
        val dna = DNA.random(30)
        val cell = Cell(genome = dna, energy = 100.0)
        assertEquals(0, cell.age)
        cell.metabolize()
        assertEquals(1, cell.age)
    }

    @Test
    fun cellUniqueIds() {
        val c1 = Cell(genome = DNA.random(10))
        val c2 = Cell(genome = DNA.random(10))
        assertNotEquals(c1.cellId, c2.cellId)
    }

    @Test
    fun cellInitialState() {
        val dna = DNA.random(30)
        val cell = Cell(genome = dna)
        assertTrue(cell.alive)
        assertEquals(0, cell.age)
        assertEquals(0, cell.mutationCount)
        assertEquals(0, cell.generation)
    }

    // --- Mutation sealed class tests ---

    @Test
    fun mutationPointMutation() {
        val m = Mutation.PointMutation(5, "A", "G")
        assertEquals("point", m.name)
        assertEquals(5, m.position)
        assertEquals("A", m.oldBase)
        assertEquals("G", m.newBase)
    }

    @Test
    fun mutationInsertion() {
        val m = Mutation.Insertion(3, listOf("A", "T"))
        assertEquals("insertion", m.name)
        assertEquals(3, m.position)
        assertEquals(listOf("A", "T"), m.bases)
    }

    @Test
    fun mutationDeletion() {
        val m = Mutation.Deletion(2, 3)
        assertEquals("deletion", m.name)
        assertEquals(2, m.position)
        assertEquals(3, m.count)
    }

    @Test
    fun mutationDuplication() {
        val m = Mutation.Duplication(0, 5)
        assertEquals("duplication", m.name)
        assertEquals(0, m.start)
        assertEquals(5, m.end)
    }

    @Test
    fun mutationInversion() {
        val m = Mutation.Inversion(1, 4)
        assertEquals("inversion", m.name)
        assertEquals(1, m.start)
        assertEquals(4, m.end)
    }

    // --- Biosphere additional tests ---

    @Test
    fun biosphereMutateZeroLengthDNA() {
        val bio = Biosphere()
        val dna = DNA(mutableListOf())
        val mutation = bio.mutate(dna, 1.0)
        assertNull(mutation) // Zero-length DNA cannot be mutated
    }

    @Test
    fun biosphereMutateZeroRate() {
        val bio = Biosphere()
        val dna = DNA.random(30)
        val original = dna.sequence.toList()
        val mutation = bio.mutate(dna, 0.0)
        assertNull(mutation)
        assertEquals(original, dna.sequence)
    }

    @Test
    fun biosphereReproduceCannotReproduce() {
        val bio = Biosphere()
        val dna = DNA.random(30)
        val parent = Cell(genome = dna, energy = 10.0) // Too low energy
        bio.population.add(parent)
        val child = bio.reproduce(parent)
        assertNull(child)
    }

    @Test
    fun biosphereEvolveGenerationEmptyPopulation() {
        val bio = Biosphere()
        val env = Environment(temperature = 300.0)
        bio.evolveGeneration(env) // Should not crash
        assertEquals(0, bio.totalGenerations)
    }

    @Test
    fun biosphereUpdateEpigenetics() {
        val bio = Biosphere()
        val dna = DNA.random(30)
        val cell = Cell(genome = dna)
        cell.epigeneticMarks.add(EpigeneticMark(geneIndex = 0))
        cell.epigeneticMarks.add(EpigeneticMark(geneIndex = 1))
        // Call updateEpigenetics many times, checking it doesn't crash
        repeat(100) {
            bio.updateEpigenetics(cell)
        }
        // Epigenetic marks should still be valid
        assertEquals(2, cell.epigeneticMarks.size)
    }

    @Test
    fun biosphereNaturalSelectionRemovesDead() {
        val bio = Biosphere()
        bio.seedLife(5, 30)
        val env = Environment(temperature = 300.0)
        env.ocean.volume = 10.0
        // Kill two cells
        bio.population[0].alive = false
        bio.population[1].alive = false
        bio.naturalSelection(env)
        assertEquals(3, bio.population.size)
    }

    @Test
    fun biosphereNaturalSelectionCarryingCapacity() {
        val bio = Biosphere()
        bio.carryingCapacity = 3
        bio.seedLife(10, 30)
        val env = Environment(temperature = 300.0)
        env.ocean.volume = 10.0
        bio.naturalSelection(env)
        assertTrue(bio.population.size <= 3)
    }

    @Test
    fun biosphereMaxFitness() {
        val bio = Biosphere()
        bio.seedLife(5, 30)
        assertTrue(bio.maxFitness > 0)
        assertTrue(bio.maxFitness >= bio.averageFitness)
    }

    @Test
    fun biosphereMaxFitnessEmptyPopulation() {
        val bio = Biosphere()
        assertEquals(0.0, bio.maxFitness, 0.0)
    }

    @Test
    fun biosphereAverageGenomeLength() {
        val bio = Biosphere()
        bio.seedLife(5, 30)
        assertEquals(30.0, bio.averageGenomeLength, 5.0)
    }

    @Test
    fun biosphereAverageGenomeLengthEmpty() {
        val bio = Biosphere()
        assertEquals(0.0, bio.averageGenomeLength, 0.0)
    }

    @Test
    fun biosphereMaxGeneration() {
        val bio = Biosphere()
        bio.seedLife(5, 30)
        assertEquals(0, bio.maxGeneration) // All cells are generation 0
    }

    @Test
    fun biosphereMaxGenerationEmpty() {
        val bio = Biosphere()
        assertEquals(0, bio.maxGeneration)
    }

    @Test
    fun biosphereSpeciesCountSingleCell() {
        val bio = Biosphere()
        bio.seedLife(1, 30)
        assertEquals(1, bio.speciesCount)
    }

    @Test
    fun biosphereSpeciesCountEmpty() {
        val bio = Biosphere()
        assertEquals(0, bio.speciesCount)
    }

    @Test
    fun biosphereAverageFitnessEmpty() {
        val bio = Biosphere()
        assertEquals(0.0, bio.averageFitness, 0.0)
    }

    @Test
    fun biosphereReproduceChildGeneration() {
        val bio = Biosphere()
        val dna = DNA.random(30)
        val parent = Cell(genome = dna, energy = 150.0, generation = 3)
        parent.expressGenome()
        bio.population.add(parent)
        val child = bio.reproduce(parent)
        if (child != null) {
            assertEquals(4, child.generation)
        }
    }

    @Test
    fun biosphereReproduceReducesParentEnergy() {
        val bio = Biosphere()
        val dna = DNA.random(30)
        val parent = Cell(genome = dna, energy = 150.0)
        parent.expressGenome()
        bio.population.add(parent)
        val initialEnergy = parent.energy
        val child = bio.reproduce(parent)
        if (child != null) {
            assertTrue(parent.energy < initialEnergy)
        }
    }

    @Test
    fun biosphereNaturalSelectionStress() {
        val bio = Biosphere()
        bio.seedLife(5, 30)
        // High stress environment
        val env = Environment(temperature = 600.0) // High temp
        env.radiation = 8.0
        bio.naturalSelection(env)
        // Some cells may die from stress
        for (cell in bio.population) {
            assertTrue(cell.alive)
        }
    }

    @Test
    fun biosphereSeedLifeEpigeneticMarks() {
        val bio = Biosphere()
        val cells = bio.seedLife(5, 30)
        for (cell in cells) {
            assertTrue(cell.epigeneticMarks.isNotEmpty())
        }
    }

    @Test
    fun biosphereMutateAllTypes() {
        val bio = Biosphere()
        var hasPoint = false
        var hasInsertion = false
        var hasDeletion = false
        var hasDuplication = false
        var hasInversion = false

        repeat(1000) {
            val dna = DNA.random(100)
            val mutation = bio.mutate(dna, 1.0)
            when (mutation) {
                is Mutation.PointMutation -> hasPoint = true
                is Mutation.Insertion -> hasInsertion = true
                is Mutation.Deletion -> hasDeletion = true
                is Mutation.Duplication -> hasDuplication = true
                is Mutation.Inversion -> hasInversion = true
                null -> {}
            }
        }

        assertTrue("Expected point mutations", hasPoint)
        assertTrue("Expected insertions", hasInsertion)
        assertTrue("Expected deletions", hasDeletion)
        assertTrue("Expected duplications", hasDuplication)
        assertTrue("Expected inversions", hasInversion)
    }
}
