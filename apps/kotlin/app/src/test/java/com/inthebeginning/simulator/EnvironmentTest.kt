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
    }
}
