package com.inthebeginning.simulator

import com.inthebeginning.simulator.Constants.COSMIC_RAY_MUTATION_RATE
import com.inthebeginning.simulator.Constants.K_B
import com.inthebeginning.simulator.Constants.RADIATION_DAMAGE_THRESHOLD
import com.inthebeginning.simulator.Constants.T_CMB
import com.inthebeginning.simulator.Constants.T_EARTH_SURFACE
import com.inthebeginning.simulator.Constants.T_PLANCK
import com.inthebeginning.simulator.Constants.THERMAL_FLUCTUATION
import com.inthebeginning.simulator.Constants.UV_MUTATION_RATE
import kotlin.math.exp
import kotlin.random.Random

/**
 * Atmospheric composition as gas fractions.
 */
data class Atmosphere(
    var nitrogen: Double = 0.0,
    var oxygen: Double = 0.0,
    var carbonDioxide: Double = 0.0,
    var methane: Double = 0.0,
    var water: Double = 0.0,
    var hydrogen: Double = 0.0,
    var helium: Double = 0.0,
    var ammonia: Double = 0.0
) {
    /** Total atmospheric pressure (arbitrary units). */
    val totalPressure: Double
        get() = nitrogen + oxygen + carbonDioxide + methane +
                water + hydrogen + helium + ammonia

    /** Whether this atmosphere is reducing (no free oxygen). */
    val isReducing: Boolean get() = oxygen < 0.01 && (hydrogen + methane + ammonia) > 0.1

    /** Whether this atmosphere is oxidizing (has free oxygen). */
    val isOxidizing: Boolean get() = oxygen > 0.01

    /** Greenhouse effect factor based on greenhouse gases. */
    val greenhouseEffect: Double
        get() = 1.0 + carbonDioxide * 30.0 + methane * 80.0 + water * 5.0
}

/**
 * Represents a body of liquid on the planetary surface.
 */
data class OceanState(
    var volume: Double = 0.0,
    var salinity: Double = 0.0,
    var pH: Double = 7.0,
    var dissolvedMinerals: Double = 0.0
) {
    val isPresent: Boolean get() = volume > 0.01
}

/**
 * Radiation type impinging on the environment.
 */
enum class RadiationType(val displayName: String) {
    STELLAR_UV("Stellar UV"),
    COSMIC_RAYS("Cosmic Rays"),
    RADIOACTIVE_DECAY("Radioactive Decay"),
    THERMAL_IR("Thermal IR");
}

/**
 * Represents a single radiation source.
 */
data class RadiationSource(
    val type: RadiationType,
    var intensity: Double,
    val mutagenicFactor: Double
)

/**
 * Environmental conditions for the simulation.
 * Models temperature, radiation, atmosphere, and geological activity
 * as they evolve through cosmic epochs.
 */
class Environment(
    var temperature: Double = T_PLANCK
) {
    var radiation: Double = 0.0
    var cosmicAge: Double = 0.0
    var magneticFieldStrength: Double = 0.0
    var tectonicActivity: Double = 0.0

    val atmosphere: Atmosphere = Atmosphere()
    val ocean: OceanState = OceanState()

    val radiationSources: MutableList<RadiationSource> = mutableListOf()
    val events: MutableList<String> = mutableListOf()

    private val rng = Random

    /** Whether the environment has liquid water. */
    val hasLiquidWater: Boolean
        get() = temperature in 273.0..373.0 && ocean.isPresent

    /** Whether lightning is occurring (requires atmosphere and thermal gradient). */
    val hasLightning: Boolean
        get() = atmosphere.totalPressure > 0.5 &&
                temperature in 250.0..400.0 &&
                rng.nextDouble() < 0.1

    /** UV radiation level at the surface. */
    val uvLevel: Double
        get() {
            val stellarUV = radiationSources
                .filter { it.type == RadiationType.STELLAR_UV }
                .sumOf { it.intensity }
            // Ozone layer reduces UV (oxygen in atmosphere)
            val ozoneShielding = 1.0 - (atmosphere.oxygen * 5.0).coerceIn(0.0, 0.95)
            return stellarUV * ozoneShielding
        }

    /** Cosmic ray flux at the surface. */
    val cosmicRayFlux: Double
        get() {
            val crSources = radiationSources
                .filter { it.type == RadiationType.COSMIC_RAYS }
                .sumOf { it.intensity }
            // Magnetic field deflects cosmic rays
            val shielding = 1.0 - (magneticFieldStrength * 0.8).coerceIn(0.0, 0.95)
            return crSources * shielding
        }

    /** Effective mutation rate from all radiation sources. */
    val mutationRate: Double
        get() = uvLevel * UV_MUTATION_RATE + cosmicRayFlux * COSMIC_RAY_MUTATION_RATE

    /**
     * Initialize as the early universe (pre-stellar).
     */
    fun initEarlyUniverse() {
        temperature = T_PLANCK
        radiation = T_PLANCK * K_B
        atmosphere.hydrogen = 0.75
        atmosphere.helium = 0.25
        magneticFieldStrength = 0.0
        tectonicActivity = 0.0
        events.add("Environment initialized: early universe")
    }

    /**
     * Set conditions for early Earth (~4.5 Ga).
     */
    fun initEarlyEarth() {
        temperature = 500.0 // Hot, volcanic
        radiation = 5.0
        magneticFieldStrength = 0.5
        tectonicActivity = 0.8

        atmosphere.nitrogen = 0.0
        atmosphere.oxygen = 0.0
        atmosphere.carbonDioxide = 0.7
        atmosphere.methane = 0.1
        atmosphere.water = 0.1
        atmosphere.hydrogen = 0.05
        atmosphere.ammonia = 0.05

        radiationSources.clear()
        radiationSources.add(RadiationSource(RadiationType.STELLAR_UV, 3.0, UV_MUTATION_RATE))
        radiationSources.add(RadiationSource(RadiationType.COSMIC_RAYS, 1.0, COSMIC_RAY_MUTATION_RATE))
        radiationSources.add(RadiationSource(RadiationType.RADIOACTIVE_DECAY, 2.0, UV_MUTATION_RATE * 0.5))

        events.add("Early Earth conditions set: reducing atmosphere")
    }

    /**
     * Cool Earth and form oceans.
     */
    fun formOceans() {
        if (temperature > 373.0) return

        ocean.volume = atmosphere.water * 100.0
        atmosphere.water *= 0.1 // Most water condenses
        ocean.pH = 5.5 // Slightly acidic early ocean
        ocean.salinity = 0.1
        ocean.dissolvedMinerals = 0.5

        events.add("Oceans formed: liquid water present")
    }

    /**
     * Great Oxidation Event: oxygen from photosynthesis accumulates.
     */
    fun greatOxidationEvent(oxygenProduction: Double) {
        val freeOxygen = oxygenProduction * 0.01
        atmosphere.oxygen += freeOxygen

        // Methane reacts with oxygen
        val methaneOxidized = (atmosphere.methane * atmosphere.oxygen * 0.1)
            .coerceAtMost(atmosphere.methane)
        atmosphere.methane -= methaneOxidized
        atmosphere.carbonDioxide += methaneOxidized * 0.5

        if (atmosphere.oxygen > 0.01) {
            events.add("Great Oxidation Event: O2 = ${String.format("%.4f", atmosphere.oxygen)}")
        }
    }

    /**
     * Evolve environmental conditions by one time step.
     */
    fun evolve(tick: Int) {
        cosmicAge = tick.toDouble()

        // Universal cooling
        when {
            tick < Constants.RECOMBINATION_EPOCH -> {
                temperature = T_PLANCK * exp(-tick.toDouble() / 10000.0)
            }
            tick < Constants.STAR_FORMATION_EPOCH -> {
                temperature = (T_CMB + (3000.0 - T_CMB) *
                        exp(-(tick - Constants.RECOMBINATION_EPOCH).toDouble() / 50000.0))
            }
            tick < Constants.EARTH_EPOCH -> {
                // Background stays at CMB temperature
                temperature = T_CMB
            }
            tick < Constants.LIFE_EPOCH -> {
                // Earth surface temperature
                val cooling = exp(-(tick - Constants.EARTH_EPOCH).toDouble() / 20000.0)
                temperature = T_EARTH_SURFACE + 200.0 * cooling
                if (temperature < 373.0 && !ocean.isPresent) {
                    formOceans()
                }
            }
            else -> {
                // Stabilize near modern Earth temperature
                temperature = T_EARTH_SURFACE + rng.nextGaussian() * THERMAL_FLUCTUATION * 10.0
            }
        }

        // Thermal fluctuation
        temperature += rng.nextGaussian() * THERMAL_FLUCTUATION

        // Radiation decay
        for (source in radiationSources) {
            source.intensity *= 0.99999
        }

        // Update radiation total
        radiation = radiationSources.sumOf { it.intensity }

        // Tectonic activity slowly decreases
        tectonicActivity *= 0.99999

        // Nitrogen slowly builds up from volcanic outgassing
        if (tick > Constants.EARTH_EPOCH && atmosphere.nitrogen < 0.78) {
            atmosphere.nitrogen += tectonicActivity * 0.00001
        }
    }

    /**
     * Check if conditions are suitable for life.
     */
    val isHabitable: Boolean
        get() = hasLiquidWater &&
                temperature in 250.0..400.0 &&
                radiation < RADIATION_DAMAGE_THRESHOLD

    /**
     * Environmental stress factor (0 = ideal, higher = more stressful).
     */
    val stressFactor: Double
        get() {
            var stress = 0.0
            if (temperature !in 273.0..330.0) {
                stress += kotlin.math.abs(temperature - 300.0) / 100.0
            }
            stress += radiation * 0.1
            stress += uvLevel * 0.5
            return stress.coerceAtLeast(0.0)
        }

    /**
     * Apply a random catastrophic event with low probability.
     */
    fun randomCatastrophe(): String? {
        val roll = rng.nextDouble()
        return when {
            roll < 0.0001 -> {
                // Asteroid impact
                temperature += 50.0
                radiation += 5.0
                events.add("Asteroid impact!")
                "Asteroid impact"
            }
            roll < 0.0003 -> {
                // Supervolcano
                atmosphere.carbonDioxide += 0.05
                temperature += 10.0
                events.add("Supervolcano eruption!")
                "Supervolcano eruption"
            }
            roll < 0.0005 -> {
                // Solar flare
                radiation += 3.0
                events.add("Massive solar flare!")
                "Massive solar flare"
            }
            else -> null
        }
    }

    /** Summary of current environmental conditions. */
    fun summary(): Map<String, Any> = mapOf(
        "temperature" to temperature,
        "radiation" to radiation,
        "hasLiquidWater" to hasLiquidWater,
        "isHabitable" to isHabitable,
        "atmospherePressure" to atmosphere.totalPressure,
        "oceanVolume" to ocean.volume,
        "uvLevel" to uvLevel,
        "cosmicRayFlux" to cosmicRayFlux,
        "magneticField" to magneticFieldStrength,
    )
}
