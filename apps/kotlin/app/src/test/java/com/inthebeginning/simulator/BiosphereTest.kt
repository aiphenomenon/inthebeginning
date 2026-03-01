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
    }
}
