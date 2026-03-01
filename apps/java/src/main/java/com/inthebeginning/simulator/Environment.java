package com.inthebeginning.simulator;

import java.util.*;

import static com.inthebeginning.simulator.Constants.*;

/**
 * Environmental system modeling planetary conditions.
 * Tracks temperature, atmosphere composition, radiation levels,
 * ocean chemistry, and geological activity that influence chemical
 * and biological evolution.
 */
public class Environment {

    /** Atmospheric composition as gas name -> fraction. */
    private final Map<String, Double> atmosphere = new LinkedHashMap<>();

    /** Ocean properties. */
    private double oceanCoverage = 0.0;   // fraction 0-1
    private double oceanPH = 7.0;
    private double oceanTemperature = 0.0;

    /** Surface conditions. */
    private double surfaceTemperature;
    private double pressure = 1.0;         // atmospheres
    private double uvIntensity = 0.0;
    private double cosmicRayFlux = 0.0;
    private double volcanicActivity = 0.0;
    private double magneticFieldStrength = 0.0;

    /** Energy sources. */
    private double solarLuminosity = 0.0;
    private double geothermalEnergy = 0.0;
    private double lightningFrequency = 0.0;

    /** Habitability score 0-1. */
    private double habitability = 0.0;

    private final Random rng;

    public Environment(Random rng) {
        this.surfaceTemperature = 0.0;
        this.rng = rng;
    }

    // --- Accessors ---

    public Map<String, Double> getAtmosphere()     { return atmosphere; }
    public double getOceanCoverage()               { return oceanCoverage; }
    public double getOceanPH()                     { return oceanPH; }
    public double getOceanTemperature()            { return oceanTemperature; }
    public double getSurfaceTemperature()          { return surfaceTemperature; }
    public double getPressure()                    { return pressure; }
    public double getUvIntensity()                 { return uvIntensity; }
    public double getCosmicRayFlux()               { return cosmicRayFlux; }
    public double getVolcanicActivity()            { return volcanicActivity; }
    public double getMagneticFieldStrength()        { return magneticFieldStrength; }
    public double getSolarLuminosity()             { return solarLuminosity; }
    public double getGeothermalEnergy()            { return geothermalEnergy; }
    public double getLightningFrequency()          { return lightningFrequency; }
    public double getHabitability()                { return habitability; }

    public void setSurfaceTemperature(double t)    { this.surfaceTemperature = t; }
    public void setPressure(double p)              { this.pressure = p; }

    // --- Planetary formation ---

    /**
     * Initialize early Earth conditions:
     * reducing atmosphere, high volcanic activity, no oceans yet.
     */
    public void initializeEarlyEarth() {
        surfaceTemperature = 500.0; // hot early Earth
        pressure = 10.0;           // thick early atmosphere

        atmosphere.clear();
        atmosphere.put("CO2", 0.60);
        atmosphere.put("N2", 0.20);
        atmosphere.put("H2O", 0.10);
        atmosphere.put("CH4", 0.05);
        atmosphere.put("NH3", 0.03);
        atmosphere.put("H2", 0.02);

        volcanicActivity = 0.9;
        geothermalEnergy = 100.0;
        magneticFieldStrength = 0.5;
        uvIntensity = 0.8;        // no ozone layer yet
        cosmicRayFlux = 0.3;
        solarLuminosity = 0.7;    // young sun was dimmer
        lightningFrequency = 0.8;

        oceanCoverage = 0.0;
        habitability = 0.0;
    }

    /**
     * Cool the planet and form oceans.
     * Called over multiple ticks to simulate geological cooling.
     */
    public void geologicalCooling(double coolingRate) {
        if (surfaceTemperature > T_EARTH_SURFACE) {
            surfaceTemperature -= coolingRate;
            if (surfaceTemperature < T_EARTH_SURFACE) {
                surfaceTemperature = T_EARTH_SURFACE;
            }
        }

        // Oceans form when temperature drops below 373K (boiling point)
        if (surfaceTemperature < 373.0 && oceanCoverage < 0.71) {
            oceanCoverage += 0.01;
            if (oceanCoverage > 0.71) oceanCoverage = 0.71;
            oceanTemperature = surfaceTemperature - 10;
            oceanPH = 5.5 + rng.nextGaussian() * 0.2; // early oceans were acidic
        }

        // Volcanic activity decreases over time
        if (volcanicActivity > 0.1) {
            volcanicActivity *= 0.999;
        }

        // Pressure normalizes
        if (pressure > 1.0) {
            pressure *= 0.999;
            if (pressure < 1.0) pressure = 1.0;
        }

        updateHabitability();
    }

    /**
     * Atmosphere evolves: CO2 dissolves in oceans, O2 builds up from photosynthesis.
     */
    public void evolveAtmosphere(boolean photosynthesisActive) {
        // CO2 dissolves in oceans
        if (oceanCoverage > 0.1) {
            double co2 = atmosphere.getOrDefault("CO2", 0.0);
            if (co2 > 0.001) {
                atmosphere.put("CO2", co2 * 0.999);
            }
        }

        // Photosynthesis produces O2
        if (photosynthesisActive) {
            double o2 = atmosphere.getOrDefault("O2", 0.0);
            atmosphere.put("O2", Math.min(0.21, o2 + 0.0001));

            // O2 -> ozone reduces UV
            if (o2 > 0.01) {
                uvIntensity = Math.max(0.05, uvIntensity * 0.999);
            }
        }

        // Normalize atmosphere fractions
        double total = atmosphere.values().stream().mapToDouble(Double::doubleValue).sum();
        if (total > 0) {
            for (Map.Entry<String, Double> entry : atmosphere.entrySet()) {
                entry.setValue(entry.getValue() / total);
            }
        }

        updateHabitability();
    }

    /**
     * Compute a composite habitability score.
     * Considers temperature, water, atmosphere, and radiation.
     */
    private void updateHabitability() {
        double tempScore = 0.0;
        if (surfaceTemperature > 273 && surfaceTemperature < 373) {
            // Optimal around 288K
            tempScore = 1.0 - Math.abs(surfaceTemperature - 288.0) / 85.0;
            tempScore = Math.max(0, Math.min(1, tempScore));
        }

        double waterScore = Math.min(1.0, oceanCoverage / 0.5);

        double atmosphereScore = 0.0;
        double n2 = atmosphere.getOrDefault("N2", 0.0);
        double o2 = atmosphere.getOrDefault("O2", 0.0);
        double co2 = atmosphere.getOrDefault("CO2", 0.0);
        atmosphereScore = Math.min(1.0, n2 + o2 * 2.0);
        if (co2 > 0.5) atmosphereScore *= 0.5; // too much CO2 is bad

        double radiationScore = 1.0 - Math.min(1.0, uvIntensity);

        habitability = (tempScore * 0.3 + waterScore * 0.3 +
                        atmosphereScore * 0.2 + radiationScore * 0.2);
    }

    /**
     * Determine environmental pressure on organisms.
     * Higher = harder to survive.
     */
    public double environmentalPressure() {
        double pressure = 0.0;
        pressure += uvIntensity * UV_MUTATION_RATE * 1000;
        pressure += cosmicRayFlux * COSMIC_RAY_MUTATION_RATE * 1000;
        pressure += Math.max(0, (surfaceTemperature - 373) / 100.0);
        pressure += Math.max(0, (273 - surfaceTemperature) / 100.0);
        pressure += volcanicActivity * 0.1;
        return Math.min(0.9, pressure);
    }

    /**
     * Check whether conditions support liquid water.
     */
    public boolean hasLiquidWater() {
        return surfaceTemperature > 273 && surfaceTemperature < 373
                && oceanCoverage > 0.01 && pressure > 0.006;
    }

    /**
     * Check whether conditions can support complex life.
     */
    public boolean supportsComplexLife() {
        return habitability > 0.5
                && hasLiquidWater()
                && atmosphere.getOrDefault("O2", 0.0) > 0.05
                && uvIntensity < 0.3;
    }

    public String toCompact() {
        StringBuilder atmo = new StringBuilder();
        atmosphere.entrySet().stream()
                .sorted((a, b) -> Double.compare(b.getValue(), a.getValue()))
                .limit(4)
                .forEach(e -> {
                    if (atmo.length() > 0) atmo.append(",");
                    atmo.append(String.format("%s:%.1f%%", e.getKey(), e.getValue() * 100));
                });

        return String.format(
                "ENV[T=%.0fK P=%.1fatm ocean=%.0f%% UV=%.2f hab=%.2f atmo={%s}]",
                surfaceTemperature, pressure, oceanCoverage * 100,
                uvIntensity, habitability, atmo);
    }
}
