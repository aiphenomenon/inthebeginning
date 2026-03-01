package com.inthebeginning.simulator

import com.inthebeginning.simulator.Constants.C
import com.inthebeginning.simulator.Constants.HBAR
import com.inthebeginning.simulator.Constants.M_DOWN_QUARK
import com.inthebeginning.simulator.Constants.M_ELECTRON
import com.inthebeginning.simulator.Constants.M_NEUTRINO
import com.inthebeginning.simulator.Constants.M_NEUTRON
import com.inthebeginning.simulator.Constants.M_PHOTON
import com.inthebeginning.simulator.Constants.M_PROTON
import com.inthebeginning.simulator.Constants.M_UP_QUARK
import com.inthebeginning.simulator.Constants.PI_VAL
import com.inthebeginning.simulator.Constants.T_PLANCK
import com.inthebeginning.simulator.Constants.T_QUARK_HADRON
import kotlin.math.cos
import kotlin.math.min
import kotlin.math.sqrt
import kotlin.random.Random

/**
 * Particle types in the simulation.
 */
enum class ParticleType(val displayName: String) {
    UP("up"),
    DOWN("down"),
    ELECTRON("electron"),
    POSITRON("positron"),
    NEUTRINO("neutrino"),
    PHOTON("photon"),
    GLUON("gluon"),
    W_BOSON("W"),
    Z_BOSON("Z"),
    PROTON("proton"),
    NEUTRON("neutron");
}

/**
 * Spin quantum number.
 */
enum class Spin(val value: Double) {
    UP(+0.5),
    DOWN(-0.5);
}

/**
 * Color charge for quarks.
 */
enum class ColorCharge(val code: String) {
    RED("r"),
    GREEN("g"),
    BLUE("b"),
    ANTI_RED("ar"),
    ANTI_GREEN("ag"),
    ANTI_BLUE("ab");
}

/** Mass lookup by particle type. */
val PARTICLE_MASSES: Map<ParticleType, Double> = mapOf(
    ParticleType.UP to M_UP_QUARK,
    ParticleType.DOWN to M_DOWN_QUARK,
    ParticleType.ELECTRON to M_ELECTRON,
    ParticleType.POSITRON to M_ELECTRON,
    ParticleType.NEUTRINO to M_NEUTRINO,
    ParticleType.PHOTON to M_PHOTON,
    ParticleType.GLUON to M_PHOTON,
    ParticleType.PROTON to M_PROTON,
    ParticleType.NEUTRON to M_NEUTRON,
)

/** Charge lookup by particle type. */
val PARTICLE_CHARGES: Map<ParticleType, Double> = mapOf(
    ParticleType.UP to 2.0 / 3.0,
    ParticleType.DOWN to -1.0 / 3.0,
    ParticleType.ELECTRON to -1.0,
    ParticleType.POSITRON to 1.0,
    ParticleType.NEUTRINO to 0.0,
    ParticleType.PHOTON to 0.0,
    ParticleType.GLUON to 0.0,
    ParticleType.PROTON to 1.0,
    ParticleType.NEUTRON to 0.0,
)

/**
 * Simplified quantum wave function with amplitude and phase.
 */
data class WaveFunction(
    var amplitude: Double = 1.0,
    var phase: Double = 0.0,
    var coherent: Boolean = true
) {
    /** Born rule: |psi|^2 */
    val probability: Double get() = amplitude * amplitude

    /** Time evolution: phase rotation by E*dt/hbar. */
    fun evolve(dt: Double, energy: Double) {
        if (coherent) {
            phase += energy * dt / HBAR
            phase %= (2.0 * PI_VAL)
        }
    }

    /** Measurement: collapse to eigenstate. Returns true if 'detected'. */
    fun collapse(): Boolean {
        val result = Random.nextDouble() < probability
        amplitude = if (result) 1.0 else 0.0
        coherent = false
        return result
    }

    /** Superposition of two states. */
    fun superpose(other: WaveFunction): WaveFunction {
        val phaseDiff = phase - other.phase
        val combinedAmp = sqrt(
            amplitude * amplitude + other.amplitude * other.amplitude
                    + 2.0 * amplitude * other.amplitude * cos(phaseDiff)
        )
        val combinedPhase = (phase + other.phase) / 2.0
        return WaveFunction(
            amplitude = min(combinedAmp, 1.0),
            phase = combinedPhase,
            coherent = true
        )
    }
}

/**
 * A quantum particle with position, momentum, and quantum numbers.
 */
class Particle(
    val particleType: ParticleType,
    val position: DoubleArray = doubleArrayOf(0.0, 0.0, 0.0),
    val momentum: DoubleArray = doubleArrayOf(0.0, 0.0, 0.0),
    var spin: Spin = Spin.UP,
    var color: ColorCharge? = null,
    val waveFn: WaveFunction = WaveFunction(),
    var entangledWith: Int? = null,
    val particleId: Int = nextId()
) {
    companion object {
        private var idCounter = 0
        fun nextId(): Int = ++idCounter
        fun resetIds() { idCounter = 0 }
    }

    val mass: Double get() = PARTICLE_MASSES[particleType] ?: 0.0
    val charge: Double get() = PARTICLE_CHARGES[particleType] ?: 0.0

    /** E = sqrt(p^2 * c^2 + m^2 * c^4) */
    val energy: Double
        get() {
            val p2 = momentum[0] * momentum[0] + momentum[1] * momentum[1] + momentum[2] * momentum[2]
            return sqrt(p2 * C * C + (mass * C * C) * (mass * C * C))
        }

    /** de Broglie wavelength: lambda = h / p */
    val wavelength: Double
        get() {
            val p = sqrt(momentum[0] * momentum[0] + momentum[1] * momentum[1] + momentum[2] * momentum[2])
            return if (p < 1e-20) Double.MAX_VALUE else 2.0 * PI_VAL * HBAR / p
        }
}

/**
 * An entangled pair of particles (EPR pair).
 */
data class EntangledPair(
    val particleA: Particle,
    val particleB: Particle,
    val bellState: String = "phi+"
) {
    /** Measure particle A, instantly determining B. */
    fun measureA(): Spin {
        if (Random.nextDouble() < 0.5) {
            particleA.spin = Spin.UP
            particleB.spin = Spin.DOWN
        } else {
            particleA.spin = Spin.DOWN
            particleB.spin = Spin.UP
        }
        particleA.waveFn.coherent = false
        particleB.waveFn.coherent = false
        return particleA.spin
    }
}

/**
 * Represents a quantum field that can create and annihilate particles.
 */
class QuantumField(
    var temperature: Double = T_PLANCK
) {
    val particles: MutableList<Particle> = mutableListOf()
    val entangledPairs: MutableList<EntangledPair> = mutableListOf()
    var vacuumEnergy: Double = 0.0
    var totalCreated: Int = 0
    var totalAnnihilated: Int = 0

    private val rng = Random

    /**
     * Create particle-antiparticle pair from vacuum energy.
     * Requires E >= 2mc^2 for the lightest possible pair.
     */
    fun pairProduction(energy: Double): Pair<Particle, Particle>? {
        if (energy < 2.0 * M_ELECTRON * C * C) return null

        val pType: ParticleType
        val apType: ParticleType
        if (energy >= 2.0 * M_PROTON * C * C && rng.nextDouble() < 0.1) {
            pType = ParticleType.UP
            apType = ParticleType.DOWN
        } else {
            pType = ParticleType.ELECTRON
            apType = ParticleType.POSITRON
        }

        val direction = doubleArrayOf(
            rng.nextGaussian(), rng.nextGaussian(), rng.nextGaussian()
        )
        val norm = sqrt(direction[0] * direction[0] + direction[1] * direction[1] + direction[2] * direction[2]).coerceAtLeast(1.0)
        val pMomentum = energy / (2.0 * C)

        val particle = Particle(
            particleType = pType,
            momentum = doubleArrayOf(
                direction[0] / norm * pMomentum,
                direction[1] / norm * pMomentum,
                direction[2] / norm * pMomentum
            ),
            spin = Spin.UP
        )
        val antiparticle = Particle(
            particleType = apType,
            momentum = doubleArrayOf(
                -direction[0] / norm * pMomentum,
                -direction[1] / norm * pMomentum,
                -direction[2] / norm * pMomentum
            ),
            spin = Spin.DOWN
        )

        particle.entangledWith = antiparticle.particleId
        antiparticle.entangledWith = particle.particleId

        particles.add(particle)
        particles.add(antiparticle)
        entangledPairs.add(EntangledPair(particle, antiparticle))
        totalCreated += 2

        return Pair(particle, antiparticle)
    }

    /**
     * Annihilate particle-antiparticle pair, returning released energy.
     */
    fun annihilate(p1: Particle, p2: Particle): Double {
        val energy = p1.energy + p2.energy
        particles.remove(p1)
        particles.remove(p2)
        totalAnnihilated += 2
        vacuumEnergy += energy * 0.01

        val photon1 = Particle(
            particleType = ParticleType.PHOTON,
            momentum = doubleArrayOf(energy / (2.0 * C), 0.0, 0.0)
        )
        val photon2 = Particle(
            particleType = ParticleType.PHOTON,
            momentum = doubleArrayOf(-energy / (2.0 * C), 0.0, 0.0)
        )
        particles.add(photon1)
        particles.add(photon2)
        return energy
    }

    /**
     * Combine quarks into hadrons when temperature drops below quark-hadron transition.
     */
    fun quarkConfinement(): List<Particle> {
        if (temperature > T_QUARK_HADRON) return emptyList()

        val hadrons = mutableListOf<Particle>()
        val ups = particles.filter { it.particleType == ParticleType.UP }.toMutableList()
        val downs = particles.filter { it.particleType == ParticleType.DOWN }.toMutableList()

        // Form protons (uud)
        while (ups.size >= 2 && downs.isNotEmpty()) {
            val u1 = ups.removeAt(ups.lastIndex)
            val u2 = ups.removeAt(ups.lastIndex)
            val d1 = downs.removeAt(downs.lastIndex)

            u1.color = ColorCharge.RED
            u2.color = ColorCharge.GREEN
            d1.color = ColorCharge.BLUE

            val proton = Particle(
                particleType = ParticleType.PROTON,
                position = u1.position.copyOf(),
                momentum = doubleArrayOf(
                    u1.momentum[0] + u2.momentum[0] + d1.momentum[0],
                    u1.momentum[1] + u2.momentum[1] + d1.momentum[1],
                    u1.momentum[2] + u2.momentum[2] + d1.momentum[2]
                )
            )

            particles.remove(u1)
            particles.remove(u2)
            particles.remove(d1)
            particles.add(proton)
            hadrons.add(proton)
        }

        // Form neutrons (udd)
        while (ups.isNotEmpty() && downs.size >= 2) {
            val u1 = ups.removeAt(ups.lastIndex)
            val d1 = downs.removeAt(downs.lastIndex)
            val d2 = downs.removeAt(downs.lastIndex)

            u1.color = ColorCharge.RED
            d1.color = ColorCharge.GREEN
            d2.color = ColorCharge.BLUE

            val neutron = Particle(
                particleType = ParticleType.NEUTRON,
                position = u1.position.copyOf(),
                momentum = doubleArrayOf(
                    u1.momentum[0] + d1.momentum[0] + d2.momentum[0],
                    u1.momentum[1] + d1.momentum[1] + d2.momentum[1],
                    u1.momentum[2] + d1.momentum[2] + d2.momentum[2]
                )
            )

            particles.remove(u1)
            particles.remove(d1)
            particles.remove(d2)
            particles.add(neutron)
            hadrons.add(neutron)
        }

        return hadrons
    }

    /**
     * Spontaneous virtual particle pair from vacuum energy.
     */
    fun vacuumFluctuation(): Pair<Particle, Particle>? {
        val prob = min(0.5, temperature / T_PLANCK)
        if (rng.nextDouble() < prob) {
            val energy = -kotlin.math.ln(rng.nextDouble()) * (temperature * 0.001)
            return pairProduction(energy)
        }
        return null
    }

    /**
     * Environmental decoherence of a particle's wave function.
     */
    fun decohere(particle: Particle, environmentCoupling: Double = 0.1) {
        if (particle.waveFn.coherent) {
            val decoherenceRate = environmentCoupling * temperature
            if (rng.nextDouble() < decoherenceRate) {
                particle.waveFn.collapse()
            }
        }
    }

    /** Cool the field (universe expansion). */
    fun cool(factor: Double = 0.999) {
        temperature *= factor
    }

    /** Evolve all particles by one time step. */
    fun evolve(dt: Double = 1.0) {
        for (p in particles) {
            if (p.mass > 0) {
                for (i in 0..2) {
                    p.position[i] += p.momentum[i] / p.mass * dt
                }
            } else {
                val pMag = sqrt(
                    p.momentum[0] * p.momentum[0] +
                            p.momentum[1] * p.momentum[1] +
                            p.momentum[2] * p.momentum[2]
                ).coerceAtLeast(1.0)
                for (i in 0..2) {
                    p.position[i] += p.momentum[i] / pMag * C * dt
                }
            }
            p.waveFn.evolve(dt, p.energy)
        }
    }

    /** Count particles by type. */
    fun particleCount(): Map<String, Int> {
        val counts = mutableMapOf<String, Int>()
        for (p in particles) {
            val key = p.particleType.displayName
            counts[key] = (counts[key] ?: 0) + 1
        }
        return counts
    }

    /** Total energy in the field. */
    fun totalEnergy(): Double {
        return particles.sumOf { it.energy } + vacuumEnergy
    }
}

/**
 * Extension to generate Gaussian random doubles from kotlin.random.Random.
 */
fun Random.nextGaussian(): Double {
    // Box-Muller transform
    val u1 = nextDouble()
    val u2 = nextDouble()
    return sqrt(-2.0 * kotlin.math.ln(u1.coerceAtLeast(1e-20))) * cos(2.0 * PI_VAL * u2)
}
