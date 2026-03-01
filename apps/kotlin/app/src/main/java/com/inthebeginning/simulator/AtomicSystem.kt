package com.inthebeginning.simulator

import com.inthebeginning.simulator.Constants.BOND_ENERGY_COVALENT
import com.inthebeginning.simulator.Constants.BOND_ENERGY_IONIC
import com.inthebeginning.simulator.Constants.ELECTRON_SHELLS
import com.inthebeginning.simulator.Constants.K_B
import com.inthebeginning.simulator.Constants.T_RECOMBINATION
import kotlin.math.abs
import kotlin.math.exp
import kotlin.math.sqrt
import kotlin.random.Random

/**
 * Periodic table data: (symbol, name, group, period, electronegativity)
 */
data class ElementData(
    val symbol: String,
    val name: String,
    val group: Int,
    val period: Int,
    val electronegativity: Double
)

val ELEMENTS: Map<Int, ElementData> = mapOf(
    1 to ElementData("H", "Hydrogen", 1, 1, 2.20),
    2 to ElementData("He", "Helium", 18, 1, 0.0),
    3 to ElementData("Li", "Lithium", 1, 2, 0.98),
    4 to ElementData("Be", "Beryllium", 2, 2, 1.57),
    5 to ElementData("B", "Boron", 13, 2, 2.04),
    6 to ElementData("C", "Carbon", 14, 2, 2.55),
    7 to ElementData("N", "Nitrogen", 15, 2, 3.04),
    8 to ElementData("O", "Oxygen", 16, 2, 3.44),
    9 to ElementData("F", "Fluorine", 17, 2, 3.98),
    10 to ElementData("Ne", "Neon", 18, 2, 0.0),
    11 to ElementData("Na", "Sodium", 1, 3, 0.93),
    12 to ElementData("Mg", "Magnesium", 2, 3, 1.31),
    13 to ElementData("Al", "Aluminum", 13, 3, 1.61),
    14 to ElementData("Si", "Silicon", 14, 3, 1.90),
    15 to ElementData("P", "Phosphorus", 15, 3, 2.19),
    16 to ElementData("S", "Sulfur", 16, 3, 2.58),
    17 to ElementData("Cl", "Chlorine", 17, 3, 3.16),
    18 to ElementData("Ar", "Argon", 18, 3, 0.0),
    19 to ElementData("K", "Potassium", 1, 4, 0.82),
    20 to ElementData("Ca", "Calcium", 2, 4, 1.00),
    26 to ElementData("Fe", "Iron", 8, 4, 1.83),
)

/**
 * An electron shell with quantum numbers.
 */
data class ElectronShell(
    val n: Int,
    val maxElectrons: Int,
    var electrons: Int = 0
) {
    val isFull: Boolean get() = electrons >= maxElectrons
    val isEmpty: Boolean get() = electrons == 0

    fun addElectron(): Boolean {
        if (!isFull) { electrons++; return true }
        return false
    }

    fun removeElectron(): Boolean {
        if (!isEmpty) { electrons--; return true }
        return false
    }
}

/**
 * An atom with protons, neutrons, and electron shells.
 */
class Atom(
    val atomicNumber: Int,
    var massNumber: Int = 0,
    var electronCount: Int = 0,
    val position: DoubleArray = doubleArrayOf(0.0, 0.0, 0.0),
    val velocity: DoubleArray = doubleArrayOf(0.0, 0.0, 0.0),
    val bonds: MutableList<Int> = mutableListOf(),
    val atomId: Int = nextId()
) {
    companion object {
        private var idCounter = 0
        fun nextId(): Int = ++idCounter
        fun resetIds() { idCounter = 0 }
    }

    var shells: MutableList<ElectronShell> = mutableListOf()
    var ionizationEnergy: Double = 0.0

    init {
        if (massNumber == 0) {
            massNumber = if (atomicNumber == 1) 1 else atomicNumber * 2
        }
        if (electronCount == 0) {
            electronCount = atomicNumber
        }
        buildShells()
        computeIonizationEnergy()
    }

    private fun buildShells() {
        shells.clear()
        var remaining = electronCount
        for (i in ELECTRON_SHELLS.indices) {
            if (remaining <= 0) break
            val maxE = ELECTRON_SHELLS[i]
            val shell = ElectronShell(
                n = i + 1,
                maxElectrons = maxE,
                electrons = minOf(remaining, maxE)
            )
            shells.add(shell)
            remaining -= shell.electrons
        }
    }

    private fun computeIonizationEnergy() {
        if (shells.isEmpty() || shells.last().isEmpty) {
            ionizationEnergy = 0.0
            return
        }
        val n = shells.last().n
        val zEff = atomicNumber - shells.dropLast(1).sumOf { it.electrons }
        ionizationEnergy = 13.6 * zEff * zEff / (n * n).toDouble()
    }

    val symbol: String get() = ELEMENTS[atomicNumber]?.symbol ?: "E$atomicNumber"
    val name: String get() = ELEMENTS[atomicNumber]?.name ?: "Element-$atomicNumber"
    val electronegativity: Double get() = ELEMENTS[atomicNumber]?.electronegativity ?: 1.0
    val charge: Int get() = atomicNumber - electronCount
    val valenceElectrons: Int get() = if (shells.isEmpty()) 0 else shells.last().electrons
    val needsElectrons: Int
        get() = if (shells.isEmpty()) 0 else shells.last().maxElectrons - shells.last().electrons
    val isNobleGas: Boolean get() = shells.isNotEmpty() && shells.last().isFull
    val isIon: Boolean get() = charge != 0

    fun ionize(): Boolean {
        if (electronCount > 0) {
            electronCount--
            buildShells()
            computeIonizationEnergy()
            return true
        }
        return false
    }

    fun captureElectron(): Boolean {
        electronCount++
        buildShells()
        computeIonizationEnergy()
        return true
    }

    fun canBondWith(other: Atom): Boolean {
        if (isNobleGas || other.isNobleGas) return false
        if (bonds.size >= 4 || other.bonds.size >= 4) return false
        return true
    }

    fun bondType(other: Atom): String {
        val diff = abs(electronegativity - other.electronegativity)
        return when {
            diff > 1.7 -> "ionic"
            diff > 0.4 -> "polar_covalent"
            else -> "covalent"
        }
    }

    fun bondEnergy(other: Atom): Double {
        return when (bondType(other)) {
            "ionic" -> BOND_ENERGY_IONIC
            "polar_covalent" -> (BOND_ENERGY_COVALENT + BOND_ENERGY_IONIC) / 2.0
            else -> BOND_ENERGY_COVALENT
        }
    }

    fun distanceTo(other: Atom): Double {
        val dx = position[0] - other.position[0]
        val dy = position[1] - other.position[1]
        val dz = position[2] - other.position[2]
        return sqrt(dx * dx + dy * dy + dz * dz)
    }
}

/**
 * Collection of atoms with interactions.
 */
class AtomicSystem(
    var temperature: Double = T_RECOMBINATION
) {
    val atoms: MutableList<Atom> = mutableListOf()
    val freeElectrons: MutableList<Particle> = mutableListOf()
    var bondsFormed: Int = 0
    var bondsBroken: Int = 0

    private val rng = Random

    /**
     * Capture free electrons into ions when T < T_recombination.
     */
    fun recombination(field: QuantumField): List<Atom> {
        if (temperature > T_RECOMBINATION) return emptyList()

        val newAtoms = mutableListOf<Atom>()
        val protons = field.particles.filter { it.particleType == ParticleType.PROTON }.toMutableList()
        val electrons = field.particles.filter { it.particleType == ParticleType.ELECTRON }.toMutableList()

        for (proton in protons) {
            if (electrons.isEmpty()) break
            val electron = electrons.removeAt(electrons.lastIndex)
            val atom = Atom(
                atomicNumber = 1,
                massNumber = 1,
                position = proton.position.copyOf(),
                velocity = proton.momentum.copyOf()
            )
            newAtoms.add(atom)
            atoms.add(atom)
            field.particles.remove(proton)
            field.particles.remove(electron)
        }

        return newAtoms
    }

    /**
     * Form heavier elements through nuclear fusion.
     */
    fun nucleosynthesis(protons: Int, neutrons: Int): List<Atom> {
        var p = protons
        var n = neutrons
        val newAtoms = mutableListOf<Atom>()

        // Helium-4: 2 protons + 2 neutrons
        while (p >= 2 && n >= 2) {
            val he = Atom(
                atomicNumber = 2,
                massNumber = 4,
                position = doubleArrayOf(
                    rng.nextGaussian() * 10.0,
                    rng.nextGaussian() * 10.0,
                    rng.nextGaussian() * 10.0
                )
            )
            newAtoms.add(he)
            atoms.add(he)
            p -= 2
            n -= 2
        }

        // Remaining protons become hydrogen
        repeat(p) {
            val h = Atom(
                atomicNumber = 1,
                massNumber = 1,
                position = doubleArrayOf(
                    rng.nextGaussian() * 10.0,
                    rng.nextGaussian() * 10.0,
                    rng.nextGaussian() * 10.0
                )
            )
            newAtoms.add(h)
            atoms.add(h)
        }

        return newAtoms
    }

    /**
     * Form heavier elements in stellar cores.
     * Carbon (6), Nitrogen (7), Oxygen (8), up to Iron (26).
     */
    fun stellarNucleosynthesis(temperature: Double): List<Atom> {
        val newAtoms = mutableListOf<Atom>()
        if (temperature < 1e3) return newAtoms

        val heliums = atoms.filter { it.atomicNumber == 2 }.toMutableList()

        // Triple-alpha process: 3 He -> C
        while (heliums.size >= 3 && rng.nextDouble() < 0.01) {
            repeat(3) {
                val he = heliums.removeAt(heliums.lastIndex)
                atoms.remove(he)
            }
            val carbon = Atom(
                atomicNumber = 6,
                massNumber = 12,
                position = doubleArrayOf(
                    rng.nextGaussian() * 5.0,
                    rng.nextGaussian() * 5.0,
                    rng.nextGaussian() * 5.0
                )
            )
            newAtoms.add(carbon)
            atoms.add(carbon)
        }

        // C + He -> O
        val carbons = atoms.filter { it.atomicNumber == 6 }.toMutableList()
        val heliums2 = atoms.filter { it.atomicNumber == 2 }.toMutableList()
        while (carbons.isNotEmpty() && heliums2.isNotEmpty() && rng.nextDouble() < 0.02) {
            val c = carbons.removeAt(carbons.lastIndex)
            val he = heliums2.removeAt(heliums2.lastIndex)
            atoms.remove(c)
            atoms.remove(he)

            val oxygen = Atom(
                atomicNumber = 8,
                massNumber = 16,
                position = c.position.copyOf()
            )
            newAtoms.add(oxygen)
            atoms.add(oxygen)
        }

        // O + He -> N (simplified chain)
        val oxygens = atoms.filter { it.atomicNumber == 8 }.toMutableList()
        val heliums3 = atoms.filter { it.atomicNumber == 2 }.toMutableList()
        if (oxygens.isNotEmpty() && heliums3.isNotEmpty() && rng.nextDouble() < 0.005) {
            val o = oxygens[0]
            val he = heliums3[0]
            atoms.remove(o)
            atoms.remove(he)
            val nitrogen = Atom(
                atomicNumber = 7,
                massNumber = 14,
                position = o.position.copyOf()
            )
            newAtoms.add(nitrogen)
            atoms.add(nitrogen)
        }

        return newAtoms
    }

    /**
     * Try to form a chemical bond between two atoms.
     */
    fun attemptBond(a1: Atom, a2: Atom): Boolean {
        if (!a1.canBondWith(a2)) return false
        val dist = a1.distanceTo(a2)
        val bondDist = 2.0
        if (dist > bondDist * 3) return false

        val energyBarrier = a1.bondEnergy(a2)
        val thermalEnergy = K_B * temperature
        val prob = if (thermalEnergy > 0) {
            exp(-energyBarrier / thermalEnergy)
        } else {
            if (dist < bondDist) 1.0 else 0.0
        }

        if (rng.nextDouble() < prob) {
            a1.bonds.add(a2.atomId)
            a2.bonds.add(a1.atomId)
            bondsFormed++
            return true
        }
        return false
    }

    /** Count atoms by element symbol. */
    fun elementCounts(): Map<String, Int> {
        val counts = mutableMapOf<String, Int>()
        for (a in atoms) {
            counts[a.symbol] = (counts[a.symbol] ?: 0) + 1
        }
        return counts
    }
}
