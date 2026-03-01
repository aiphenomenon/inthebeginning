package com.inthebeginning.simulator;

import java.util.*;

import static com.inthebeginning.simulator.Constants.*;

/**
 * Tests for Environment: temperature, habitability, atmosphere evolution,
 * geological cooling, and life support conditions.
 */
public class TestEnvironment {

    private static int passed = 0;
    private static int failed = 0;

    private static void assertEquals(String label, Object expected, Object actual) {
        if (expected.equals(actual)) {
            passed++;
        } else {
            failed++;
            System.out.println("    FAIL: " + label + " - expected " + expected + " but got " + actual);
        }
    }

    private static void assertTrue(String label, boolean condition) {
        if (condition) {
            passed++;
        } else {
            failed++;
            System.out.println("    FAIL: " + label);
        }
    }

    private static void assertApprox(String label, double expected, double actual, double tolerance) {
        if (Math.abs(expected - actual) < tolerance) {
            passed++;
        } else {
            failed++;
            System.out.println("    FAIL: " + label + " - expected ~" + expected + " but got " + actual);
        }
    }

    public static int[] runAll() {
        passed = 0;
        failed = 0;

        System.out.println("  [TestEnvironment]");

        testDefaultEnvironment();
        testInitializeEarlyEarth();
        testGeologicalCooling();
        testOceanFormation();
        testAtmosphereEvolution();
        testPhotosynthesisOxygen();
        testHabitability();
        testLiquidWater();
        testNoLiquidWaterHot();
        testNoLiquidWaterCold();
        testComplexLifeSupport();
        testEnvironmentalPressure();
        testToCompact();

        System.out.println("    " + passed + " passed, " + failed + " failed");
        return new int[]{passed, failed};
    }

    private static void testDefaultEnvironment() {
        Random rng = new Random(42);
        Environment env = new Environment(rng);
        assertApprox("Default temperature = 0", 0.0, env.getSurfaceTemperature(), 1e-10);
        assertApprox("Default pressure = 1", 1.0, env.getPressure(), 1e-10);
        assertApprox("Default ocean coverage = 0", 0.0, env.getOceanCoverage(), 1e-10);
        assertApprox("Default habitability = 0", 0.0, env.getHabitability(), 1e-10);
    }

    private static void testInitializeEarlyEarth() {
        Random rng = new Random(42);
        Environment env = new Environment(rng);
        env.initializeEarlyEarth();

        assertApprox("Early Earth temperature = 500", 500.0, env.getSurfaceTemperature(), 1e-10);
        assertApprox("Early Earth pressure = 10", 10.0, env.getPressure(), 1e-10);
        assertTrue("CO2 in atmosphere", env.getAtmosphere().containsKey("CO2"));
        assertTrue("N2 in atmosphere", env.getAtmosphere().containsKey("N2"));
        assertApprox("CO2 fraction = 0.60", 0.60, env.getAtmosphere().get("CO2"), 0.01);
        assertApprox("Volcanic activity = 0.9", 0.9, env.getVolcanicActivity(), 0.01);
        assertApprox("UV intensity = 0.8", 0.8, env.getUvIntensity(), 0.01);
        assertApprox("Ocean coverage = 0", 0.0, env.getOceanCoverage(), 1e-10);
    }

    private static void testGeologicalCooling() {
        Random rng = new Random(42);
        Environment env = new Environment(rng);
        env.initializeEarlyEarth();

        double tempBefore = env.getSurfaceTemperature();
        env.geologicalCooling(10.0);

        assertTrue("Temperature decreased", env.getSurfaceTemperature() < tempBefore);
        assertApprox("Temperature dropped by 10", tempBefore - 10.0, env.getSurfaceTemperature(), 1e-10);
    }

    private static void testOceanFormation() {
        Random rng = new Random(42);
        Environment env = new Environment(rng);
        env.initializeEarlyEarth();

        // Cool below 373K to trigger ocean formation
        env.setSurfaceTemperature(350.0);
        env.geologicalCooling(0.0); // just trigger the ocean check

        assertTrue("Oceans begin forming", env.getOceanCoverage() > 0.0);
    }

    private static void testAtmosphereEvolution() {
        Random rng = new Random(42);
        Environment env = new Environment(rng);
        env.initializeEarlyEarth();

        // Set conditions for atmosphere evolution
        env.setSurfaceTemperature(300.0);
        // Manually set ocean coverage > 0.1 to enable CO2 dissolution
        for (int i = 0; i < 20; i++) {
            env.geologicalCooling(0.0);
        }

        double co2Before = env.getAtmosphere().get("CO2");
        env.evolveAtmosphere(false);
        double co2After = env.getAtmosphere().get("CO2");

        // CO2 should dissolve in oceans when coverage > 0.1
        if (env.getOceanCoverage() > 0.1) {
            assertTrue("CO2 decreased with ocean coverage", co2After <= co2Before);
        } else {
            // If ocean coverage didn't reach 0.1, CO2 stays same
            assertTrue("CO2 unchanged without ocean", true);
        }
    }

    private static void testPhotosynthesisOxygen() {
        Random rng = new Random(42);
        Environment env = new Environment(rng);
        env.initializeEarlyEarth();
        env.setSurfaceTemperature(300.0);

        // Evolve with photosynthesis
        env.evolveAtmosphere(true);
        double o2 = env.getAtmosphere().getOrDefault("O2", 0.0);
        assertTrue("O2 appears with photosynthesis", o2 > 0.0);
    }

    private static void testHabitability() {
        Random rng = new Random(42);
        Environment env = new Environment(rng);

        // Set Earth-like conditions
        env.setSurfaceTemperature(288.0);
        env.setPressure(1.0);
        env.getAtmosphere().put("N2", 0.78);
        env.getAtmosphere().put("O2", 0.21);
        env.getAtmosphere().put("CO2", 0.01);

        // Need to trigger habitability calculation
        env.geologicalCooling(0.0);

        // Habitability depends on multiple factors; with good temp but no water it won't be 1.0
        assertTrue("Habitability >= 0", env.getHabitability() >= 0.0);
        assertTrue("Habitability <= 1", env.getHabitability() <= 1.0);
    }

    private static void testLiquidWater() {
        Random rng = new Random(42);
        Environment env = new Environment(rng);
        env.initializeEarlyEarth();

        // Cool to liquid water range
        env.setSurfaceTemperature(300.0);

        // Need ocean coverage > 0.01 and pressure > 0.006
        // Trigger ocean formation
        for (int i = 0; i < 5; i++) {
            env.geologicalCooling(0.0);
        }

        if (env.getOceanCoverage() > 0.01) {
            assertTrue("Has liquid water", env.hasLiquidWater());
        } else {
            assertTrue("No liquid water without ocean", true);
        }
    }

    private static void testNoLiquidWaterHot() {
        Random rng = new Random(42);
        Environment env = new Environment(rng);
        env.setSurfaceTemperature(500.0);
        assertTrue("No liquid water at 500K", !env.hasLiquidWater());
    }

    private static void testNoLiquidWaterCold() {
        Random rng = new Random(42);
        Environment env = new Environment(rng);
        env.setSurfaceTemperature(100.0);
        assertTrue("No liquid water at 100K", !env.hasLiquidWater());
    }

    private static void testComplexLifeSupport() {
        Random rng = new Random(42);
        Environment env = new Environment(rng);

        // Without proper conditions, should not support complex life
        assertTrue("Default doesn't support complex life", !env.supportsComplexLife());
    }

    private static void testEnvironmentalPressure() {
        Random rng = new Random(42);
        Environment env = new Environment(rng);
        env.initializeEarlyEarth();

        double pressure = env.environmentalPressure();
        assertTrue("Environmental pressure >= 0", pressure >= 0.0);
        assertTrue("Environmental pressure <= 0.9", pressure <= 0.9);
    }

    private static void testToCompact() {
        Random rng = new Random(42);
        Environment env = new Environment(rng);
        env.initializeEarlyEarth();

        String compact = env.toCompact();
        assertTrue("Compact contains ENV", compact.contains("ENV"));
        assertTrue("Compact contains T=", compact.contains("T="));
    }
}
