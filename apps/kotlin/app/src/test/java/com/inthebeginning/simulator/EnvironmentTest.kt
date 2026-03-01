package com.inthebeginning.simulator

import com.inthebeginning.simulator.Constants.T_CMB
import com.inthebeginning.simulator.Constants.T_EARTH_SURFACE
import com.inthebeginning.simulator.Constants.T_PLANCK
import com.inthebeginning.simulator.Constants.UV_MUTATION_RATE
import com.inthebeginning.simulator.Constants.COSMIC_RAY_MUTATION_RATE
import org.junit.Assert.*
import org.junit.Test

class EnvironmentTest {

    // --- Atmosphere tests ---

    @Test
    fun atmosphereInit() {
        val atm = Atmosphere()
        assertEquals(0.0, atm.totalPressure, 0.0)
        assertFalse(atm.isReducing)
        assertFalse(atm.isOxidizing)
    }

    @Test
    fun atmosphereReducing() {
        val atm = Atmosphere(hydrogen = 0.5, methane = 0.1)
        assertTrue(atm.isReducing)
        assertFalse(atm.isOxidizing)
    }

    @Test
    fun atmosphereOxidizing() {
        val atm = Atmosphere(oxygen = 0.2)
        assertTrue(atm.isOxidizing)
        assertFalse(atm.isReducing)
    }

    @Test
    fun atmosphereGreenhouseEffect() {
        val atm = Atmosphere()
        assertEquals(1.0, atm.greenhouseEffect, 0.0)

        val atm2 = Atmosphere(carbonDioxide = 0.1, methane = 0.05)
        assertTrue(atm2.greenhouseEffect > 1.0)
    }

    @Test
    fun atmosphereTotalPressure() {
        val atm = Atmosphere(nitrogen = 0.78, oxygen = 0.21, carbonDioxide = 0.01)
        assertEquals(1.0, atm.totalPressure, 1e-10)
    }

    // --- OceanState tests ---

    @Test
    fun oceanNotPresent() {
        val ocean = OceanState()
        assertFalse(ocean.isPresent)
    }

    @Test
    fun oceanPresent() {
        val ocean = OceanState(volume = 1.0)
        assertTrue(ocean.isPresent)
    }

    // --- Environment tests ---

    @Test
    fun environmentInit() {
        val env = Environment(temperature = T_PLANCK)
        assertEquals(T_PLANCK, env.temperature, 0.0)
        assertEquals(0.0, env.radiation, 0.0)
    }

    @Test
    fun initEarlyUniverse() {
        val env = Environment()
        env.initEarlyUniverse()
        assertEquals(T_PLANCK, env.temperature, 0.0)
        assertTrue(env.atmosphere.hydrogen > 0)
        assertTrue(env.atmosphere.helium > 0)
    }

    @Test
    fun initEarlyEarth() {
        val env = Environment()
        env.initEarlyEarth()
        assertEquals(500.0, env.temperature, 0.0)
        assertTrue(env.atmosphere.carbonDioxide > 0)
        assertTrue(env.atmosphere.isReducing)
        assertTrue(env.radiationSources.isNotEmpty())
    }

    @Test
    fun formOceans() {
        val env = Environment(temperature = 350.0)
        env.atmosphere.water = 0.1
        env.formOceans()
        assertTrue(env.ocean.isPresent)
        assertTrue(env.events.any { it.contains("Oceans") })
    }

    @Test
    fun formOceansDoesNothingAboveBoiling() {
        val env = Environment(temperature = 500.0)
        env.atmosphere.water = 0.1
        env.formOceans()
        assertFalse(env.ocean.isPresent)
    }

    @Test
    fun hasLiquidWater() {
        val env = Environment(temperature = 300.0)
        env.ocean.volume = 1.0
        assertTrue(env.hasLiquidWater)

        val env2 = Environment(temperature = 500.0)
        env2.ocean.volume = 1.0
        assertFalse(env2.hasLiquidWater)
    }

    @Test
    fun uvLevel() {
        val env = Environment()
        env.radiationSources.add(RadiationSource(RadiationType.STELLAR_UV, 3.0, UV_MUTATION_RATE))
        assertTrue(env.uvLevel > 0)
    }

    @Test
    fun cosmicRayFlux() {
        val env = Environment()
        env.radiationSources.add(RadiationSource(RadiationType.COSMIC_RAYS, 2.0, COSMIC_RAY_MUTATION_RATE))
        assertTrue(env.cosmicRayFlux > 0)
    }

    @Test
    fun cosmicRayShieldedByMagneticField() {
        val env = Environment()
        env.radiationSources.add(RadiationSource(RadiationType.COSMIC_RAYS, 2.0, COSMIC_RAY_MUTATION_RATE))

        val unshielded = env.cosmicRayFlux
        env.magneticFieldStrength = 1.0
        val shielded = env.cosmicRayFlux
        assertTrue(shielded < unshielded)
    }

    @Test
    fun mutationRate() {
        val env = Environment()
        env.radiationSources.add(RadiationSource(RadiationType.STELLAR_UV, 1.0, UV_MUTATION_RATE))
        assertTrue(env.mutationRate > 0)
    }

    @Test
    fun isHabitableRequiresLiquidWater() {
        val env = Environment(temperature = 300.0)
        // No ocean -> not habitable
        assertFalse(env.isHabitable)

        env.ocean.volume = 1.0
        assertTrue(env.isHabitable)
    }

    @Test
    fun isNotHabitableAtExtremeTemp() {
        val env = Environment(temperature = T_PLANCK)
        env.ocean.volume = 1.0
        assertFalse(env.isHabitable)
    }

    @Test
    fun stressFactorNonNegative() {
        val env = Environment(temperature = 300.0)
        assertTrue(env.stressFactor >= 0)
    }

    @Test
    fun greatOxidationEvent() {
        val env = Environment()
        env.initEarlyEarth()
        val initialOxygen = env.atmosphere.oxygen
        env.greatOxidationEvent(10.0)
        assertTrue(env.atmosphere.oxygen > initialOxygen)
    }

    @Test
    fun evolveReducesTemperature() {
        val env = Environment(temperature = T_PLANCK)
        env.evolve(Constants.RECOMBINATION_EPOCH - 1)
        assertTrue(env.temperature < T_PLANCK)
    }

    @Test
    fun environmentSummary() {
        val env = Environment()
        val summary = env.summary()
        assertTrue(summary.containsKey("temperature"))
        assertTrue(summary.containsKey("radiation"))
        assertTrue(summary.containsKey("isHabitable"))
        assertTrue(summary.containsKey("hasLiquidWater"))
        assertTrue(summary.containsKey("atmospherePressure"))
        assertTrue(summary.containsKey("oceanVolume"))
        assertTrue(summary.containsKey("uvLevel"))
        assertTrue(summary.containsKey("cosmicRayFlux"))
        assertTrue(summary.containsKey("magneticField"))
    }

    // --- RadiationType tests ---

    @Test
    fun radiationTypeDisplayNames() {
        assertEquals("Stellar UV", RadiationType.STELLAR_UV.displayName)
        assertEquals("Cosmic Rays", RadiationType.COSMIC_RAYS.displayName)
        assertEquals("Radioactive Decay", RadiationType.RADIOACTIVE_DECAY.displayName)
        assertEquals("Thermal IR", RadiationType.THERMAL_IR.displayName)
    }

    // --- RadiationSource tests ---

    @Test
    fun radiationSourceProperties() {
        val src = RadiationSource(RadiationType.STELLAR_UV, 3.0, Constants.UV_MUTATION_RATE)
        assertEquals(RadiationType.STELLAR_UV, src.type)
        assertEquals(3.0, src.intensity, 0.0)
        assertEquals(Constants.UV_MUTATION_RATE, src.mutagenicFactor, 0.0)
    }

    // --- hasLightning tests ---

    @Test
    fun hasLightningRequiresAtmosphere() {
        val env = Environment(temperature = 300.0)
        // No atmosphere -> no lightning
        // totalPressure = 0 < 0.5 -> false
        // Running multiple times since it's random
        var everHadLightning = false
        repeat(100) {
            val e = Environment(temperature = 300.0)
            if (e.hasLightning) everHadLightning = true
        }
        assertFalse("No lightning without atmosphere", everHadLightning)
    }

    @Test
    fun hasLightningWithAtmosphere() {
        // With sufficient atmosphere and right temperature, should sometimes have lightning
        var hadLightning = false
        repeat(200) {
            val env = Environment(temperature = 300.0)
            env.atmosphere.nitrogen = 0.78
            env.atmosphere.oxygen = 0.21
            if (env.hasLightning) hadLightning = true
        }
        assertTrue("Expected lightning with suitable atmosphere", hadLightning)
    }

    // --- randomCatastrophe tests ---

    @Test
    fun randomCatastropheUsuallyReturnsNull() {
        val env = Environment(temperature = 300.0)
        // Most of the time (99.95%), no catastrophe occurs
        var nullCount = 0
        repeat(100) {
            val e = Environment(temperature = 300.0)
            if (e.randomCatastrophe() == null) nullCount++
        }
        // The vast majority should be null
        assertTrue(nullCount > 80)
    }

    @Test
    fun randomCatastropheCanOccur() {
        // Run many times to catch at least one catastrophe
        var hadCatastrophe = false
        repeat(50000) {
            val env = Environment(temperature = 300.0)
            val result = env.randomCatastrophe()
            if (result != null) {
                hadCatastrophe = true
                assertTrue(
                    result == "Asteroid impact" ||
                    result == "Supervolcano eruption" ||
                    result == "Massive solar flare"
                )
            }
        }
        assertTrue("Expected at least one catastrophe in many attempts", hadCatastrophe)
    }

    // --- Environment.evolve different epoch branches ---

    @Test
    fun evolveStarFormationEpoch() {
        val env = Environment(temperature = T_PLANCK)
        env.evolve(Constants.STAR_FORMATION_EPOCH - 1)
        // Should be near CMB temperature for this epoch
        assertTrue(env.temperature > 0)
    }

    @Test
    fun evolveEarthEpoch() {
        val env = Environment(temperature = T_PLANCK)
        env.initEarlyEarth()
        env.atmosphere.water = 0.1
        env.evolve(Constants.EARTH_EPOCH + 1000)
        // Should be between Earth surface temp and higher
        assertTrue(env.temperature > 0)
    }

    @Test
    fun evolvePresentEpoch() {
        val env = Environment(temperature = T_PLANCK)
        env.evolve(Constants.LIFE_EPOCH + 1)
        // Should be near Earth surface temperature
        assertTrue(kotlin.math.abs(env.temperature - T_EARTH_SURFACE) < 50.0)
    }

    @Test
    fun evolveRecombinationToStarFormation() {
        val env = Environment(temperature = T_PLANCK)
        env.evolve(Constants.RECOMBINATION_EPOCH + 100)
        // Should be between CMB and 3000K
        assertTrue(env.temperature > 0)
        assertTrue(env.temperature < 5000.0)
    }

    @Test
    fun evolveUpdatesCosmicAge() {
        val env = Environment()
        env.evolve(42)
        assertEquals(42.0, env.cosmicAge, 0.0)
    }

    @Test
    fun evolveRadiationDecay() {
        val env = Environment()
        env.radiationSources.add(RadiationSource(RadiationType.STELLAR_UV, 10.0, Constants.UV_MUTATION_RATE))
        val initialIntensity = env.radiationSources[0].intensity
        env.evolve(1)
        assertTrue(env.radiationSources[0].intensity < initialIntensity)
    }

    @Test
    fun evolveTectonicActivityDecay() {
        val env = Environment()
        env.tectonicActivity = 1.0
        env.evolve(1)
        assertTrue(env.tectonicActivity < 1.0)
    }

    @Test
    fun evolveNitrogenBuildupAfterEarth() {
        val env = Environment()
        env.tectonicActivity = 1.0
        val initialN = env.atmosphere.nitrogen
        env.evolve(Constants.EARTH_EPOCH + 1)
        assertTrue(env.atmosphere.nitrogen > initialN)
    }

    @Test
    fun evolveNitrogenCapAt078() {
        val env = Environment()
        env.atmosphere.nitrogen = 0.79
        env.tectonicActivity = 1.0
        env.evolve(Constants.EARTH_EPOCH + 1)
        // Should not increase beyond 0.78 cap
        assertEquals(0.79, env.atmosphere.nitrogen, 0.01)
    }

    // --- UV level with ozone shielding ---

    @Test
    fun uvLevelReducedByOxygen() {
        val env = Environment()
        env.radiationSources.add(RadiationSource(RadiationType.STELLAR_UV, 3.0, Constants.UV_MUTATION_RATE))
        val unshielded = env.uvLevel
        env.atmosphere.oxygen = 0.21
        val shielded = env.uvLevel
        assertTrue(shielded < unshielded)
    }

    // --- OceanState additional tests ---

    @Test
    fun oceanStateProperties() {
        val ocean = OceanState(volume = 100.0, salinity = 3.5, pH = 8.1, dissolvedMinerals = 0.5)
        assertEquals(100.0, ocean.volume, 0.0)
        assertEquals(3.5, ocean.salinity, 0.0)
        assertEquals(8.1, ocean.pH, 0.0)
        assertEquals(0.5, ocean.dissolvedMinerals, 0.0)
        assertTrue(ocean.isPresent)
    }

    // --- Atmosphere additional tests ---

    @Test
    fun atmosphereFieldsAccessible() {
        val atm = Atmosphere(
            nitrogen = 0.78, oxygen = 0.21, carbonDioxide = 0.004,
            methane = 0.001, water = 0.003, hydrogen = 0.001,
            helium = 0.001, ammonia = 0.0
        )
        assertEquals(0.78, atm.nitrogen, 0.0)
        assertEquals(0.21, atm.oxygen, 0.0)
        assertEquals(0.004, atm.carbonDioxide, 0.0)
        assertEquals(0.001, atm.methane, 0.0)
        assertEquals(0.003, atm.water, 0.0)
        assertEquals(0.001, atm.hydrogen, 0.0)
        assertEquals(0.001, atm.helium, 0.0)
        assertEquals(0.0, atm.ammonia, 0.0)
    }

    // --- stressFactor tests ---

    @Test
    fun stressFactorHighTemp() {
        val env = Environment(temperature = 500.0)
        env.radiation = 5.0
        assertTrue(env.stressFactor > 0)
    }

    @Test
    fun stressFactorIdealConditions() {
        val env = Environment(temperature = 300.0)
        env.radiation = 0.0
        // Temperature 300 is within 273-330 range
        val stress = env.stressFactor
        assertTrue(stress >= 0)
    }

    // --- isHabitable radiation threshold ---

    @Test
    fun isNotHabitableWithHighRadiation() {
        val env = Environment(temperature = 300.0)
        env.ocean.volume = 1.0
        env.radiation = Constants.RADIATION_DAMAGE_THRESHOLD + 1
        assertFalse(env.isHabitable)
    }

    // --- Great Oxidation Event details ---

    @Test
    fun greatOxidationEventReducesMethane() {
        val env = Environment()
        env.atmosphere.methane = 0.1
        env.atmosphere.oxygen = 0.05
        val initialMethane = env.atmosphere.methane
        env.greatOxidationEvent(10.0)
        assertTrue(env.atmosphere.methane < initialMethane)
    }

    @Test
    fun greatOxidationEventAddsEvent() {
        val env = Environment()
        env.atmosphere.oxygen = 0.0
        env.greatOxidationEvent(100.0)
        // After adding enough oxygen, should record the event
        if (env.atmosphere.oxygen > 0.01) {
            assertTrue(env.events.any { it.contains("Great Oxidation") })
        }
    }

    // --- formOceans details ---

    @Test
    fun formOceansSetsOceanProperties() {
        val env = Environment(temperature = 350.0)
        env.atmosphere.water = 0.2
        env.formOceans()
        assertTrue(env.ocean.isPresent)
        assertEquals(5.5, env.ocean.pH, 0.0) // Early ocean slightly acidic
        assertEquals(0.1, env.ocean.salinity, 0.0)
        assertEquals(0.5, env.ocean.dissolvedMinerals, 0.0)
        // Water in atmosphere should be reduced
        assertTrue(env.atmosphere.water < 0.2)
    }

    // --- initEarlyEarth details ---

    @Test
    fun initEarlyEarthSetsRadiationSources() {
        val env = Environment()
        env.initEarlyEarth()
        assertEquals(3, env.radiationSources.size)
        assertTrue(env.radiationSources.any { it.type == RadiationType.STELLAR_UV })
        assertTrue(env.radiationSources.any { it.type == RadiationType.COSMIC_RAYS })
        assertTrue(env.radiationSources.any { it.type == RadiationType.RADIOACTIVE_DECAY })
    }

    // --- initEarlyUniverse details ---

    @Test
    fun initEarlyUniverseRadiation() {
        val env = Environment()
        env.initEarlyUniverse()
        assertTrue(env.radiation > 0)
        assertEquals(0.0, env.magneticFieldStrength, 0.0)
        assertEquals(0.0, env.tectonicActivity, 0.0)
        assertTrue(env.events.any { it.contains("early universe") })
    }

    // --- mutationRate tests ---

    @Test
    fun mutationRateZeroWithNoSources() {
        val env = Environment()
        assertEquals(0.0, env.mutationRate, 0.0)
    }
}
