/**
 * Environmental effects simulation.
 *
 * Models random environmental perturbations that affect the evolution
 * of the universe from quantum to biological scales:
 * - Temperature gradients and thermal fluctuations
 * - Radiation (UV, cosmic rays, stellar winds)
 * - Geological events (volcanic, tectonic)
 * - Atmospheric composition changes
 * - Day/night cycles and seasonal variations
 */

import {
    T_PLANCK, T_CMB, T_EARTH_SURFACE, T_STELLAR_CORE,
    UV_MUTATION_RATE, COSMIC_RAY_MUTATION_RATE,
    RADIATION_DAMAGE_THRESHOLD, THERMAL_FLUCTUATION, K_B,
    PI,
} from './constants.js';


// === Helper: random gaussian ===

function gaussRandom(mean = 0, stddev = 1) {
    const u1 = Math.random();
    const u2 = Math.random();
    const z = Math.sqrt(-2.0 * Math.log(u1 || 1e-20)) * Math.cos(2.0 * PI * u2);
    return mean + stddev * z;
}

function expoVariate(lambda) {
    return -Math.log(Math.random() || 1e-20) / lambda;
}


// === EnvironmentalEvent ===

export class EnvironmentalEvent {
    /** A discrete environmental event. */
    constructor(eventType, intensity, duration, position = [0.0, 0.0, 0.0], tickOccurred = 0) {
        this.eventType = eventType;
        this.intensity = intensity;
        this.duration = duration;  // ticks
        this.position = [...position];
        this.tickOccurred = tickOccurred;
    }

    toCompact() {
        return `Ev:${this.eventType}(i=${this.intensity.toFixed(2)},d=${this.duration})`;
    }
}


// === Environment ===

export class Environment {
    /** The physical environment that affects all simulation levels. */
    constructor(initialTemperature = T_PLANCK) {
        this.temperature = initialTemperature;
        this.uvIntensity = 0.0;
        this.cosmicRayFlux = 0.0;
        this.stellarWind = 0.0;
        this.atmosphericDensity = 0.0;
        this.waterAvailability = 0.0;
        this.dayNightCycle = 0.0;  // 0-1, 0=midnight, 0.5=noon
        this.season = 0.0;  // 0-1, 0=winter, 0.5=summer
        this.events = [];
        this.eventHistory = [];
        this.tick = 0;
    }

    /** Update environment based on cosmic epoch. */
    update(epoch) {
        this.tick++;

        // Temperature evolution (logarithmic cooling)
        if (epoch < 1000) {
            // Early universe: rapid cooling
            this.temperature = T_PLANCK * Math.exp(-epoch / 200);
        } else if (epoch < 50000) {
            // Pre-recombination
            this.temperature = Math.max(
                T_CMB, T_PLANCK * Math.exp(-epoch / 200)
            );
        } else if (epoch < 200000) {
            // Post-recombination to star formation
            this.temperature = T_CMB + gaussRandom(0, 0.5);
        } else {
            // Planet era
            this.temperature = T_EARTH_SURFACE + gaussRandom(0, 5);
            // Day/night
            this.dayNightCycle = (this.tick % 100) / 100.0;
            const tempMod = 10 * Math.sin(this.dayNightCycle * 2 * PI);
            this.temperature += tempMod;
            // Seasons
            this.season = (this.tick % 1000) / 1000.0;
            const seasonMod = 15 * Math.sin(this.season * 2 * PI);
            this.temperature += seasonMod;
        }

        // UV intensity (appears with stars)
        if (epoch > 100000) {
            const baseUv = 1.0;
            if (this.dayNightCycle > 0.25 && this.dayNightCycle < 0.75) {
                this.uvIntensity = baseUv * Math.sin(
                    (this.dayNightCycle - 0.25) * 2 * PI
                );
            } else {
                this.uvIntensity = 0.0;
            }
        } else {
            this.uvIntensity = 0.0;
        }

        // Cosmic ray flux
        if (epoch > 10000) {
            this.cosmicRayFlux = 0.1 + expoVariate(10.0);
        } else {
            this.cosmicRayFlux = 1.0;  // High in early universe
        }

        // Atmospheric density (grows with planet formation)
        if (epoch > 210000) {
            this.atmosphericDensity = Math.min(1.0, (epoch - 210000) / 50000);
            // Atmosphere shields from UV
            this.uvIntensity *= (1 - this.atmosphericDensity * 0.7);
            this.cosmicRayFlux *= (1 - this.atmosphericDensity * 0.5);
        }

        // Water availability
        if (epoch > 220000) {
            this.waterAvailability = Math.min(1.0, (epoch - 220000) / 30000);
        }

        // Random events
        this._generateEvents(epoch);

        // Process active events
        this._processEvents();
    }

    _generateEvents(epoch) {
        // Volcanic activity
        if (epoch > 210000 && Math.random() < 0.005) {
            this.events.push(new EnvironmentalEvent(
                "volcanic",
                Math.random() * 2.5 + 0.5,  // uniform(0.5, 3.0)
                Math.floor(Math.random() * 91) + 10,  // randint(10, 100)
                [0.0, 0.0, 0.0],
                this.tick,
            ));
        }

        // Asteroid impact
        if (Math.random() < 0.0001) {
            this.events.push(new EnvironmentalEvent(
                "asteroid",
                Math.random() * 9.0 + 1.0,  // uniform(1.0, 10.0)
                Math.floor(Math.random() * 451) + 50,  // randint(50, 500)
                [0.0, 0.0, 0.0],
                this.tick,
            ));
        }

        // Solar flare
        if (epoch > 100000 && Math.random() < 0.01) {
            this.events.push(new EnvironmentalEvent(
                "solar_flare",
                Math.random() * 1.9 + 0.1,  // uniform(0.1, 2.0)
                Math.floor(Math.random() * 16) + 5,  // randint(5, 20)
                [0.0, 0.0, 0.0],
                this.tick,
            ));
        }

        // Ice age
        if (epoch > 250000 && Math.random() < 0.001) {
            this.events.push(new EnvironmentalEvent(
                "ice_age",
                Math.random() * 1.0 + 0.5,  // uniform(0.5, 1.5)
                Math.floor(Math.random() * 1501) + 500,  // randint(500, 2000)
                [0.0, 0.0, 0.0],
                this.tick,
            ));
        }
    }

    _processEvents() {
        const active = [];
        for (const event of this.events) {
            const elapsed = this.tick - event.tickOccurred;
            if (elapsed < event.duration) {
                active.push(event);
                this._applyEvent(event);
            } else {
                this.eventHistory.push(event);
            }
        }
        this.events = active;
    }

    _applyEvent(event) {
        if (event.eventType === "volcanic") {
            this.temperature += event.intensity * 2;
            this.atmosphericDensity = Math.min(
                1.0, this.atmosphericDensity + 0.01
            );
            this.uvIntensity *= 0.9;  // Ash blocks UV

        } else if (event.eventType === "asteroid") {
            this.temperature -= event.intensity * 5;  // Nuclear winter
            this.cosmicRayFlux += event.intensity;
            this.uvIntensity *= 0.5;

        } else if (event.eventType === "solar_flare") {
            this.uvIntensity += event.intensity;
            this.cosmicRayFlux += event.intensity * 0.5;

        } else if (event.eventType === "ice_age") {
            this.temperature -= event.intensity * 20;
            this.waterAvailability *= 0.8;
        }
    }

    /** Total radiation dose from all sources. */
    getRadiationDose() {
        return this.uvIntensity + this.cosmicRayFlux + this.stellarWind;
    }

    /** Check if conditions support life. */
    isHabitable() {
        return (
            this.temperature > 200
            && this.temperature < 400
            && this.waterAvailability > 0.1
            && this.getRadiationDose() < RADIATION_DAMAGE_THRESHOLD
        );
    }

    /**
     * Available thermal energy for biological processes.
     * Scaled to provide meaningful energy in habitable range.
     * At ~300K, returns ~30 units (enough to sustain cell metabolism).
     */
    thermalEnergy() {
        if (this.temperature < 100 || this.temperature > 500) {
            return 0.1;
        }
        return Math.max(0.1, this.temperature * 0.1);
    }

    toCompact() {
        return (
            `Env[T=${this.temperature.toFixed(1)} `
            + `UV=${this.uvIntensity.toFixed(3)} `
            + `CR=${this.cosmicRayFlux.toFixed(3)} `
            + `atm=${this.atmosphericDensity.toFixed(2)} `
            + `H2O=${this.waterAvailability.toFixed(2)} `
            + `hab=${this.isHabitable() ? "Y" : "N"} `
            + `ev=${this.events.length}]`
        );
    }
}
