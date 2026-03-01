package com.inthebeginning.simulator

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlin.math.cos
import kotlin.math.ln
import kotlin.math.sin
import kotlin.random.Random

/**
 * Lightweight entity for the renderer to draw.
 */
data class RenderableEntity(
    val x: Float,
    val y: Float,
    val radius: Float,
    val type: String
)

/**
 * Full snapshot of the universe state for rendering and display.
 */
data class Snapshot(
    val tick: Int,
    val epoch: EpochInfo,
    val epochIndex: Int,
    val temperature: Double,
    val scaleFactor: Double,
    val particleCount: Int,
    val atomCount: Int,
    val moleculeCount: Int,
    val cellCount: Int,
    val totalEnergy: Double,
    val elementCounts: Map<String, Int>,
    val moleculeCounts: Map<String, Int>,
    val particleCounts: Map<String, Int>,
    val populationFitness: Double,
    val speciesCount: Int,
    val maxGeneration: Int,
    val isHabitable: Boolean,
    val hasLiquidWater: Boolean,
    val atmospherePressure: Double,
    val atmosphereOxygen: Double,
    val events: List<String>,
    val renderableParticles: List<RenderableEntity>,
    val renderableAtoms: List<RenderableEntity>,
    val renderableMolecules: List<RenderableEntity>,
    val renderableCells: List<RenderableEntity>,
    val progress: Double,
    val cosmicAge: String
)

/**
 * Simulation state at any given tick, exposed as an immutable snapshot.
 */
data class SimulationState(
    val tick: Int = 0,
    val currentEpoch: EpochInfo = EPOCHS.first(),
    val temperature: Double = Constants.T_PLANCK,
    val particleCounts: Map<String, Int> = emptyMap(),
    val elementCounts: Map<String, Int> = emptyMap(),
    val moleculeCounts: Map<String, Int> = emptyMap(),
    val populationSize: Int = 0,
    val averageFitness: Double = 0.0,
    val maxFitness: Double = 0.0,
    val speciesCount: Int = 0,
    val totalEnergy: Double = 0.0,
    val hasLiquidWater: Boolean = false,
    val isHabitable: Boolean = false,
    val atmosphereOxygen: Double = 0.0,
    val events: List<String> = emptyList(),
    val running: Boolean = false,
    val completed: Boolean = false,
    val maxGeneration: Int = 0,
    val totalMutations: Int = 0
)

/**
 * The Universe orchestrates all simulation subsystems through 13 cosmic epochs,
 * from the Planck era through inflation, nucleosynthesis, stellar evolution,
 * planet formation, and the emergence of life.
 *
 * Exposes simulation state as a Kotlin Flow for reactive UI binding.
 */
class Universe {
    // === Subsystems ===
    val quantumField = QuantumField()
    val atomicSystem = AtomicSystem()
    val chemicalSystem = ChemicalSystem()
    val environment = Environment()
    val biosphere = Biosphere()

    // === State management ===
    private val _state = MutableStateFlow(SimulationState())
    val state: StateFlow<SimulationState> = _state.asStateFlow()

    var tick: Int = 0
        private set

    var running: Boolean = false
        private set

    var completed: Boolean = false
        private set

    private val recentEvents = mutableListOf<String>()
    private val rng = Random

    /** Speed multiplier: how many ticks to advance per step call. */
    var ticksPerStep: Int = 100

    /**
     * Determine the current epoch based on the tick counter.
     */
    private fun currentEpoch(): EpochInfo {
        var epoch = EPOCHS.first()
        for (e in EPOCHS) {
            if (tick >= e.startTick) epoch = e
        }
        return epoch
    }

    /**
     * Run a single simulation step (advancing by [ticksPerStep] ticks).
     * This is designed to be called from a coroutine on a background thread.
     */
    fun step() {
        if (completed) return
        running = true

        repeat(ticksPerStep) {
            tick++
            advanceTick()

            if (tick >= Constants.PRESENT_EPOCH) {
                completed = true
                recentEvents.add("Simulation complete: the present epoch reached.")
                return@repeat
            }
        }

        emitState()
    }

    /**
     * Advance the simulation by a single tick.
     */
    private fun advanceTick() {
        val epoch = currentEpoch()

        when {
            // === PLANCK EPOCH ===
            tick <= Constants.INFLATION_EPOCH -> planckPhase()

            // === INFLATION EPOCH ===
            tick <= Constants.ELECTROWEAK_EPOCH -> inflationPhase()

            // === ELECTROWEAK EPOCH ===
            tick <= Constants.QUARK_EPOCH -> electroweakPhase()

            // === QUARK EPOCH ===
            tick <= Constants.HADRON_EPOCH -> quarkPhase()

            // === HADRON EPOCH ===
            tick <= Constants.NUCLEOSYNTHESIS_EPOCH -> hadronPhase()

            // === NUCLEOSYNTHESIS ===
            tick <= Constants.RECOMBINATION_EPOCH -> nucleosynthesisPhase()

            // === RECOMBINATION ===
            tick <= Constants.STAR_FORMATION_EPOCH -> recombinationPhase()

            // === STAR FORMATION ===
            tick <= Constants.SOLAR_SYSTEM_EPOCH -> starFormationPhase()

            // === SOLAR SYSTEM ===
            tick <= Constants.EARTH_EPOCH -> solarSystemPhase()

            // === EARTH FORMATION ===
            tick <= Constants.LIFE_EPOCH -> earthPhase()

            // === ORIGIN OF LIFE ===
            tick <= Constants.DNA_EPOCH -> lifePhase()

            // === DNA ERA ===
            tick <= Constants.PRESENT_EPOCH -> dnaPhase()
        }

        // Evolve environment every tick
        environment.evolve(tick)

        // Cool the quantum field
        if (tick < Constants.RECOMBINATION_EPOCH) {
            quantumField.cool()
        }
    }

    // ==================== Epoch Phase Handlers ====================

    private fun planckPhase() {
        // All forces unified; vacuum fluctuations create first particles
        quantumField.temperature = Constants.T_PLANCK
        quantumField.vacuumFluctuation()

        if (tick == Constants.PLANCK_EPOCH) {
            recentEvents.add("Planck epoch: all forces unified at T ~ 10^32 K")
        }
    }

    private fun inflationPhase() {
        // Exponential expansion; massive particle production
        val inflationEnergy = Constants.T_PLANCK * Constants.K_B * 0.1
        repeat(5) {
            quantumField.pairProduction(inflationEnergy)
        }
        quantumField.cool(0.99)

        if (tick == Constants.INFLATION_EPOCH) {
            recentEvents.add("Inflation begins: universe expands exponentially")
        }
    }

    private fun electroweakPhase() {
        // Electroweak symmetry breaking; W/Z bosons acquire mass
        quantumField.cool(0.995)

        // Continue pair production at lower energies
        val energy = quantumField.temperature * Constants.K_B
        if (rng.nextDouble() < 0.3) {
            quantumField.pairProduction(energy)
        }

        // Some annihilation occurs (matter-antimatter asymmetry leaves net matter)
        val electrons = quantumField.particles.filter { it.particleType == ParticleType.ELECTRON }
        val positrons = quantumField.particles.filter { it.particleType == ParticleType.POSITRON }
        if (electrons.isNotEmpty() && positrons.isNotEmpty() && rng.nextDouble() < 0.4) {
            quantumField.annihilate(electrons.first(), positrons.first())
        }

        if (tick == Constants.ELECTROWEAK_EPOCH) {
            recentEvents.add("Electroweak symmetry breaking: EM and weak forces separate")
        }
    }

    private fun quarkPhase() {
        // Quark-gluon plasma; free quarks
        quantumField.cool(0.998)

        // Ongoing pair production
        val energy = quantumField.temperature * Constants.K_B * 0.5
        if (rng.nextDouble() < 0.1) {
            quantumField.pairProduction(energy)
        }

        if (tick == Constants.QUARK_EPOCH) {
            recentEvents.add("Quark epoch: quark-gluon plasma fills the universe")
        }
    }

    private fun hadronPhase() {
        // Quarks confine into protons and neutrons
        quantumField.cool(0.999)

        // Confinement occurs as temperature drops below QCD transition
        quantumField.temperature = quantumField.temperature.coerceAtMost(Constants.T_QUARK_HADRON)
        val hadrons = quantumField.quarkConfinement()

        if (hadrons.isNotEmpty() && tick % 500 == 0) {
            recentEvents.add("Quark confinement: ${hadrons.size} hadrons formed")
        }

        if (tick == Constants.HADRON_EPOCH) {
            recentEvents.add("Hadron epoch: quarks confined into protons and neutrons")
        }
    }

    private fun nucleosynthesisPhase() {
        // Big Bang nucleosynthesis: H, He, Li
        quantumField.cool(0.9995)

        // Count available protons and neutrons
        val protons = quantumField.particles.count { it.particleType == ParticleType.PROTON }
        val neutrons = quantumField.particles.count { it.particleType == ParticleType.NEUTRON }

        if (protons >= 2 && neutrons >= 2 && tick % 100 == 0) {
            // Transfer some particles to atomic system for fusion
            val pToFuse = (protons / 10).coerceAtLeast(2)
            val nToFuse = (neutrons / 10).coerceAtLeast(2)
            atomicSystem.nucleosynthesis(pToFuse, nToFuse)

            // Remove fused particles from quantum field
            var pRemoved = 0
            var nRemoved = 0
            quantumField.particles.removeAll {
                when {
                    it.particleType == ParticleType.PROTON && pRemoved < pToFuse -> {
                        pRemoved++; true
                    }
                    it.particleType == ParticleType.NEUTRON && nRemoved < nToFuse -> {
                        nRemoved++; true
                    }
                    else -> false
                }
            }
        }

        if (tick == Constants.NUCLEOSYNTHESIS_EPOCH) {
            recentEvents.add("Nucleosynthesis: light nuclei formed (H, He, Li)")
        }
    }

    private fun recombinationPhase() {
        // Electrons captured by nuclei; universe becomes transparent
        atomicSystem.temperature = environment.temperature
        quantumField.temperature = environment.temperature

        if (tick % 500 == 0) {
            val newAtoms = atomicSystem.recombination(quantumField)
            if (newAtoms.isNotEmpty()) {
                recentEvents.add("Recombination: ${newAtoms.size} atoms formed")
            }
        }

        // Decoherence of remaining quantum particles
        for (p in quantumField.particles) {
            quantumField.decohere(p, 0.01)
        }

        if (tick == Constants.RECOMBINATION_EPOCH) {
            recentEvents.add("Recombination: atoms form, CMB released")
        }
    }

    private fun starFormationPhase() {
        // First stars form; stellar nucleosynthesis creates heavier elements
        if (tick % 1000 == 0) {
            val stellarTemp = Constants.T_STELLAR_CORE
            val newElements = atomicSystem.stellarNucleosynthesis(stellarTemp)
            if (newElements.isNotEmpty()) {
                val names = newElements.map { it.symbol }.distinct().joinToString(", ")
                recentEvents.add("Stellar forge: created $names")
            }
        }

        // Supernovae scatter heavy elements (rare events)
        if (rng.nextDouble() < 0.0005) {
            // Create some heavier atoms directly
            val heavyElements = listOf(7, 8, 14, 15, 16, 26) // N, O, Si, P, S, Fe
            val element = heavyElements.random(rng)
            val atom = Atom(
                atomicNumber = element,
                position = doubleArrayOf(
                    rng.nextGaussian() * 20.0,
                    rng.nextGaussian() * 20.0,
                    rng.nextGaussian() * 20.0
                )
            )
            atomicSystem.atoms.add(atom)
            recentEvents.add("Supernova: scattered ${atom.symbol}")
        }

        if (tick == Constants.STAR_FORMATION_EPOCH) {
            recentEvents.add("First stars ignite, forging heavier elements")
        }
    }

    private fun solarSystemPhase() {
        // Solar system coalesces from interstellar debris
        // Add more diverse elements from the protoplanetary disk
        if (tick % 500 == 0) {
            val diskElements = listOf(1, 6, 7, 8, 11, 12, 14, 15, 16, 19, 20, 26)
            for (z in diskElements) {
                if (rng.nextDouble() < 0.3) {
                    val atom = Atom(
                        atomicNumber = z,
                        position = doubleArrayOf(
                            rng.nextGaussian() * 5.0,
                            rng.nextGaussian() * 5.0,
                            rng.nextGaussian() * 5.0
                        )
                    )
                    atomicSystem.atoms.add(atom)
                }
            }
        }

        if (tick == Constants.SOLAR_SYSTEM_EPOCH) {
            recentEvents.add("Solar system forms from stellar debris")
        }
    }

    private fun earthPhase() {
        // Earth forms, cools, oceans appear
        environment.initEarlyEarth()
        chemicalSystem.temperature = environment.temperature

        // Form water and simple molecules
        if (tick % 200 == 0) {
            val water = chemicalSystem.formWater(atomicSystem)
            if (water.isNotEmpty()) {
                recentEvents.add("Water formed: ${water.size} molecules")
            }
        }

        // Prebiotic chemistry on cooling Earth
        if (environment.temperature < 400.0 && tick % 500 == 0) {
            val prebiotic = chemicalSystem.prebioticSynthesis(atomicSystem)
            if (prebiotic.isNotEmpty()) {
                val names = prebiotic.map { it.name }.joinToString(", ")
                recentEvents.add("Prebiotic molecules: $names")
            }
        }

        if (tick == Constants.EARTH_EPOCH) {
            recentEvents.add("Earth formed: volcanic world with reducing atmosphere")
        }
    }

    private fun lifePhase() {
        // First self-replicating molecules -> cells
        chemicalSystem.temperature = environment.temperature

        // Amino acid synthesis
        if (tick % 300 == 0) {
            val aa = chemicalSystem.aminoAcidSynthesis(environment)
            if (aa.isNotEmpty()) {
                recentEvents.add("Amino acids synthesized: ${aa.joinToString(", ")}")
            }
        }

        // Nucleotide synthesis
        if (tick % 400 == 0) {
            val nts = chemicalSystem.nucleotideSynthesis(environment)
            if (nts.isNotEmpty()) {
                recentEvents.add("Nucleotides formed: ${nts.map { it.base }.joinToString("")}")
            }
        }

        // RNA polymerization
        if (tick % 500 == 0) {
            val chainLen = chemicalSystem.polymerizeRNA()
            if (chainLen > 0) {
                recentEvents.add("RNA chain polymerized: length $chainLen")
            }
        }

        // Seed life once conditions are right
        if (biosphere.population.isEmpty() && environment.isHabitable &&
            chemicalSystem.aminoAcids.size >= 5
        ) {
            val cells = biosphere.seedLife()
            recentEvents.add("LIFE EMERGES: ${cells.size} primitive cells!")
        }

        // Evolve existing life
        if (biosphere.population.isNotEmpty() && tick % 100 == 0) {
            biosphere.evolveGeneration(environment)
        }

        if (tick == Constants.LIFE_EPOCH) {
            recentEvents.add("Life epoch: first self-replicating molecules")
        }
    }

    private fun dnaPhase() {
        // DNA-based life, complex cells, epigenetics
        chemicalSystem.temperature = environment.temperature

        // Continued evolution with increasing complexity
        if (tick % 50 == 0) {
            biosphere.evolveGeneration(environment)
        }

        // Great Oxidation Event (photosynthesis produces oxygen)
        if (biosphere.population.size > 50 && tick % 200 == 0) {
            val oxygenOutput = biosphere.population.size * 0.01
            environment.greatOxidationEvent(oxygenOutput)
        }

        // Increase carrying capacity over time (more niches available)
        biosphere.carryingCapacity = (300 + (tick - Constants.DNA_EPOCH) / 100)
            .coerceAtMost(1000)

        if (tick == Constants.DNA_EPOCH) {
            recentEvents.add("DNA Era: DNA-based replication, epigenetics emerge")
        }
    }

    // ==================== State Emission ====================

    /**
     * Build and emit the current simulation state as an immutable snapshot.
     */
    private fun emitState() {
        val epoch = currentEpoch()

        _state.value = SimulationState(
            tick = tick,
            currentEpoch = epoch,
            temperature = environment.temperature,
            particleCounts = quantumField.particleCount(),
            elementCounts = atomicSystem.elementCounts(),
            moleculeCounts = chemicalSystem.moleculeCounts(),
            populationSize = biosphere.population.size,
            averageFitness = biosphere.averageFitness,
            maxFitness = biosphere.maxFitness,
            speciesCount = biosphere.speciesCount,
            totalEnergy = quantumField.totalEnergy(),
            hasLiquidWater = environment.hasLiquidWater,
            isHabitable = environment.isHabitable,
            atmosphereOxygen = environment.atmosphere.oxygen,
            events = recentEvents.takeLast(20).toList(),
            running = running,
            completed = completed,
            maxGeneration = biosphere.maxGeneration,
            totalMutations = biosphere.totalMutations
        )
    }

    /**
     * Reset the simulation to initial conditions.
     */
    fun reset() {
        tick = 0
        running = false
        completed = false

        quantumField.particles.clear()
        quantumField.entangledPairs.clear()
        quantumField.temperature = Constants.T_PLANCK
        quantumField.vacuumEnergy = 0.0
        quantumField.totalCreated = 0
        quantumField.totalAnnihilated = 0

        atomicSystem.atoms.clear()
        atomicSystem.freeElectrons.clear()
        atomicSystem.temperature = Constants.T_RECOMBINATION
        atomicSystem.bondsFormed = 0
        atomicSystem.bondsBroken = 0

        chemicalSystem.molecules.clear()
        chemicalSystem.aminoAcids.clear()
        chemicalSystem.nucleotides.clear()
        chemicalSystem.reactionsPerformed = 0
        chemicalSystem.temperature = Constants.T_EARTH_SURFACE

        environment.temperature = Constants.T_PLANCK
        environment.radiation = 0.0
        environment.cosmicAge = 0.0
        environment.radiationSources.clear()
        environment.events.clear()

        biosphere.population.clear()
        biosphere.totalGenerations = 0
        biosphere.totalMutations = 0
        biosphere.totalExtinctions = 0
        biosphere.carryingCapacity = 500

        Particle.resetIds()
        Atom.resetIds()
        Molecule.resetIds()
        DNA.resetIds()
        Cell.resetIds()

        recentEvents.clear()
        recentEvents.add("Universe reset. Ready for the Big Bang.")

        emitState()
    }

    /**
     * Pause the simulation.
     */
    fun pause() {
        running = false
        emitState()
    }

    /**
     * Get the progress through the simulation as a fraction [0, 1].
     */
    val progress: Double
        get() = (tick.toDouble() / Constants.PRESENT_EPOCH).coerceIn(0.0, 1.0)

    /**
     * Formatted cosmic age string.
     */
    val cosmicAgeDisplay: String
        get() {
            val fraction = progress
            return when {
                fraction < 0.001 -> "< 1 second"
                fraction < 0.01 -> "${(fraction * 380000).toInt()} years"
                fraction < 0.1 -> "${(fraction * 13.8).toInt()} billion years"
                else -> "${String.format("%.1f", fraction * 13.8)} billion years"
            }
        }

    /**
     * The current epoch index (0..12).
     */
    val epochIndex: Int
        get() {
            var idx = 0
            for (i in EPOCHS.indices) {
                if (tick >= EPOCHS[i].startTick) idx = i
            }
            return idx
        }

    /**
     * Scale factor for the universe expansion (simplified).
     */
    val scaleFactor: Double
        get() = when {
            tick < Constants.INFLATION_EPOCH -> 1.0
            tick < Constants.ELECTROWEAK_EPOCH ->
                kotlin.math.exp((tick - Constants.INFLATION_EPOCH).toDouble() * 0.01)
            else -> {
                val base = (tick.toDouble() / Constants.ELECTROWEAK_EPOCH.toDouble())
                    .coerceAtLeast(1.0)
                val matterDominated = Math.pow(base, 2.0 / 3.0)
                val inflationFactor = kotlin.math.exp(
                    (Constants.ELECTROWEAK_EPOCH - Constants.INFLATION_EPOCH).toDouble() * 0.01
                )
                matterDominated * inflationFactor
            }
        }

    /**
     * Create a full renderable snapshot of the universe for the UI.
     */
    fun snapshot(): Snapshot {
        val particles = quantumField.particles
        val atoms = atomicSystem.atoms
        val molecules = chemicalSystem.molecules
        val cells = biosphere.population
        val epoch = currentEpoch()
        val ei = epochIndex

        val renderableParticles = particles.map { p ->
            RenderableEntity(
                x = p.position[0].toFloat(),
                y = p.position[1].toFloat(),
                radius = when (p.particleType) {
                    ParticleType.PHOTON -> 1.5f
                    ParticleType.ELECTRON, ParticleType.POSITRON -> 2.0f
                    ParticleType.PROTON, ParticleType.NEUTRON -> 3.0f
                    else -> 2.5f
                },
                type = p.particleType.displayName
            )
        }

        val renderableAtoms = atoms.map { a ->
            RenderableEntity(
                x = a.position[0].toFloat(),
                y = a.position[1].toFloat(),
                radius = (2.0f + a.atomicNumber * 0.3f).coerceAtMost(8.0f),
                type = a.symbol
            )
        }

        val renderableMolecules = molecules.map { m ->
            val cx = m.atoms.map { it.position[0] }.average().toFloat()
            val cy = m.atoms.map { it.position[1] }.average().toFloat()
            RenderableEntity(
                x = cx,
                y = cy,
                radius = (3.0f + m.size * 0.5f).coerceAtMost(12.0f),
                type = m.formula
            )
        }

        val renderableCells = cells.mapIndexed { i, c ->
            val angle = i * 2.3998 // golden angle for spiral distribution
            val r = 5.0 + i * 0.5
            RenderableEntity(
                x = (r * cos(angle)).toFloat(),
                y = (r * sin(angle)).toFloat(),
                radius = (4.0f + c.fitness.toFloat() * 2.0f).coerceAtMost(15.0f),
                type = "cell"
            )
        }

        return Snapshot(
            tick = tick,
            epoch = epoch,
            epochIndex = ei,
            temperature = environment.temperature,
            scaleFactor = scaleFactor,
            particleCount = particles.size,
            atomCount = atoms.size,
            moleculeCount = molecules.size,
            cellCount = cells.size,
            totalEnergy = quantumField.totalEnergy(),
            elementCounts = atomicSystem.elementCounts(),
            moleculeCounts = chemicalSystem.moleculeCounts(),
            particleCounts = quantumField.particleCount(),
            populationFitness = biosphere.averageFitness,
            speciesCount = biosphere.speciesCount,
            maxGeneration = biosphere.maxGeneration,
            isHabitable = environment.isHabitable,
            hasLiquidWater = environment.hasLiquidWater,
            atmospherePressure = environment.atmosphere.totalPressure,
            atmosphereOxygen = environment.atmosphere.oxygen,
            events = recentEvents.takeLast(20).toList(),
            renderableParticles = renderableParticles,
            renderableAtoms = renderableAtoms,
            renderableMolecules = renderableMolecules,
            renderableCells = renderableCells,
            progress = progress,
            cosmicAge = cosmicAgeDisplay
        )
    }
}
