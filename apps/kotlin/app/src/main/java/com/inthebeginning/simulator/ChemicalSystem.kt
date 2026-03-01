package com.inthebeginning.simulator

import com.inthebeginning.simulator.Constants.BOND_ENERGY_COVALENT
import com.inthebeginning.simulator.Constants.BOND_ENERGY_HYDROGEN
import com.inthebeginning.simulator.Constants.BOND_ENERGY_VAN_DER_WAALS
import com.inthebeginning.simulator.Constants.K_B
import kotlin.math.exp
import kotlin.random.Random

/**
 * Type of chemical bond between atoms.
 */
enum class BondType(val displayName: String, val energy: Double) {
    COVALENT("covalent", BOND_ENERGY_COVALENT),
    IONIC("ionic", Constants.BOND_ENERGY_IONIC),
    HYDROGEN("hydrogen", BOND_ENERGY_HYDROGEN),
    VAN_DER_WAALS("van der Waals", BOND_ENERGY_VAN_DER_WAALS);
}

/**
 * A chemical bond between two atoms.
 */
data class Bond(
    val atom1Id: Int,
    val atom2Id: Int,
    val type: BondType,
    val strength: Double = type.energy
)

/**
 * A molecule composed of multiple bonded atoms.
 */
data class Molecule(
    val name: String,
    val formula: String,
    val atoms: List<Atom>,
    val bonds: List<Bond>,
    val moleculeId: Int = nextId()
) {
    companion object {
        private var idCounter = 0
        fun nextId(): Int = ++idCounter
        fun resetIds() { idCounter = 0 }
    }

    /** Total molecular mass. */
    val mass: Double get() = atoms.sumOf { it.massNumber.toDouble() }

    /** Number of atoms in the molecule. */
    val size: Int get() = atoms.size

    /** Total bond energy of the molecule. */
    val totalBondEnergy: Double get() = bonds.sumOf { it.strength }

    /** Check if this molecule contains a specific element. */
    fun containsElement(atomicNumber: Int): Boolean =
        atoms.any { it.atomicNumber == atomicNumber }

    /** Count occurrences of a specific element. */
    fun elementCount(atomicNumber: Int): Int =
        atoms.count { it.atomicNumber == atomicNumber }
}

/**
 * Predefined molecular templates for common molecules.
 */
sealed class MoleculeTemplate(val name: String, val formula: String) {
    /** Required atomic numbers and counts. */
    abstract val composition: Map<Int, Int>

    data object Water : MoleculeTemplate("Water", "H2O") {
        override val composition = mapOf(1 to 2, 8 to 1)
    }

    data object CarbonDioxide : MoleculeTemplate("Carbon Dioxide", "CO2") {
        override val composition = mapOf(6 to 1, 8 to 2)
    }

    data object Methane : MoleculeTemplate("Methane", "CH4") {
        override val composition = mapOf(6 to 1, 1 to 4)
    }

    data object Ammonia : MoleculeTemplate("Ammonia", "NH3") {
        override val composition = mapOf(7 to 1, 1 to 3)
    }

    data object HydrogenCyanide : MoleculeTemplate("Hydrogen Cyanide", "HCN") {
        override val composition = mapOf(1 to 1, 6 to 1, 7 to 1)
    }

    data object Formaldehyde : MoleculeTemplate("Formaldehyde", "CH2O") {
        override val composition = mapOf(6 to 1, 1 to 2, 8 to 1)
    }

    data object PhosphoricAcid : MoleculeTemplate("Phosphoric Acid", "H3PO4") {
        override val composition = mapOf(1 to 3, 15 to 1, 8 to 4)
    }

    data object Glycine : MoleculeTemplate("Glycine", "C2H5NO2") {
        override val composition = mapOf(6 to 2, 1 to 5, 7 to 1, 8 to 2)
    }

    data object Adenine : MoleculeTemplate("Adenine", "C5H5N5") {
        override val composition = mapOf(6 to 5, 1 to 5, 7 to 5)
    }

    data object Ribose : MoleculeTemplate("Ribose", "C5H10O5") {
        override val composition = mapOf(6 to 5, 1 to 10, 8 to 5)
    }
}

/**
 * Represents the type of an amino acid within the simulation.
 */
data class AminoAcidInfo(
    val code: String,
    val hydrophobic: Boolean,
    val charge: Int
)

/** Simplified amino acid properties. */
val AMINO_ACID_PROPERTIES: Map<String, AminoAcidInfo> = mapOf(
    "Ala" to AminoAcidInfo("A", hydrophobic = true, charge = 0),
    "Arg" to AminoAcidInfo("R", hydrophobic = false, charge = 1),
    "Asn" to AminoAcidInfo("N", hydrophobic = false, charge = 0),
    "Asp" to AminoAcidInfo("D", hydrophobic = false, charge = -1),
    "Cys" to AminoAcidInfo("C", hydrophobic = true, charge = 0),
    "Gln" to AminoAcidInfo("Q", hydrophobic = false, charge = 0),
    "Glu" to AminoAcidInfo("E", hydrophobic = false, charge = -1),
    "Gly" to AminoAcidInfo("G", hydrophobic = true, charge = 0),
    "His" to AminoAcidInfo("H", hydrophobic = false, charge = 1),
    "Ile" to AminoAcidInfo("I", hydrophobic = true, charge = 0),
    "Leu" to AminoAcidInfo("L", hydrophobic = true, charge = 0),
    "Lys" to AminoAcidInfo("K", hydrophobic = false, charge = 1),
    "Met" to AminoAcidInfo("M", hydrophobic = true, charge = 0),
    "Phe" to AminoAcidInfo("F", hydrophobic = true, charge = 0),
    "Pro" to AminoAcidInfo("P", hydrophobic = true, charge = 0),
    "Ser" to AminoAcidInfo("S", hydrophobic = false, charge = 0),
    "Thr" to AminoAcidInfo("T", hydrophobic = false, charge = 0),
    "Trp" to AminoAcidInfo("W", hydrophobic = true, charge = 0),
    "Tyr" to AminoAcidInfo("Y", hydrophobic = false, charge = 0),
    "Val" to AminoAcidInfo("V", hydrophobic = true, charge = 0),
)

/**
 * Represents a nucleotide (base + sugar + phosphate).
 */
data class Nucleotide(
    val base: String,
    val isRNA: Boolean = false
) {
    /** Watson-Crick complement. */
    val complement: String
        get() = when (base) {
            "A" -> if (isRNA) "U" else "T"
            "T" -> "A"
            "U" -> "A"
            "G" -> "C"
            "C" -> "G"
            else -> "?"
        }
}

/**
 * The chemical system manages molecular synthesis, reactions,
 * and the emergence of prebiotic chemistry.
 */
class ChemicalSystem(
    var temperature: Double = Constants.T_EARTH_SURFACE
) {
    val molecules: MutableList<Molecule> = mutableListOf()
    val aminoAcids: MutableList<String> = mutableListOf()
    val nucleotides: MutableList<Nucleotide> = mutableListOf()
    var reactionsPerformed: Int = 0

    private val rng = Random

    /**
     * Attempt to synthesize a molecule from available atoms in the atomic system.
     * Returns the molecule if successful, null otherwise.
     */
    fun synthesize(template: MoleculeTemplate, atomicSystem: AtomicSystem): Molecule? {
        val available = atomicSystem.atoms.groupBy { it.atomicNumber }
            .mapValues { it.value.toMutableList() }

        // Check if we have enough atoms
        for ((atomicNum, count) in template.composition) {
            val have = available[atomicNum]?.size ?: 0
            if (have < count) return null
        }

        // Check thermal feasibility
        val thermalEnergy = K_B * temperature
        val activationEnergy = BOND_ENERGY_COVALENT * 0.5
        val reactionProb = exp(-activationEnergy / thermalEnergy.coerceAtLeast(1e-10))
        if (rng.nextDouble() > reactionProb) return null

        // Consume atoms from the atomic system
        val usedAtoms = mutableListOf<Atom>()
        val bonds = mutableListOf<Bond>()
        for ((atomicNum, count) in template.composition) {
            val pool = available[atomicNum]!!
            repeat(count) {
                val atom = pool.removeAt(pool.lastIndex)
                atomicSystem.atoms.remove(atom)
                usedAtoms.add(atom)
            }
        }

        // Create bonds between consecutive atoms (simplified linear bonding)
        for (i in 0 until usedAtoms.size - 1) {
            val a1 = usedAtoms[i]
            val a2 = usedAtoms[i + 1]
            val bondType = when {
                kotlin.math.abs(a1.electronegativity - a2.electronegativity) > 1.7 -> BondType.IONIC
                else -> BondType.COVALENT
            }
            bonds.add(Bond(a1.atomId, a2.atomId, bondType))
        }

        val molecule = Molecule(
            name = template.name,
            formula = template.formula,
            atoms = usedAtoms,
            bonds = bonds
        )
        molecules.add(molecule)
        reactionsPerformed++
        return molecule
    }

    /**
     * Form water molecules from available H and O atoms.
     */
    fun formWater(atomicSystem: AtomicSystem): List<Molecule> {
        val formed = mutableListOf<Molecule>()
        var attempts = 0
        val maxAttempts = atomicSystem.atoms.size / 3 + 1
        while (attempts < maxAttempts) {
            val mol = synthesize(MoleculeTemplate.Water, atomicSystem) ?: break
            formed.add(mol)
            attempts++
        }
        return formed
    }

    /**
     * Attempt to form simple organic molecules (prebiotic chemistry).
     * Requires carbon, hydrogen, nitrogen, oxygen atoms in the atomic system.
     */
    fun prebioticSynthesis(atomicSystem: AtomicSystem): List<Molecule> {
        val formed = mutableListOf<Molecule>()

        // Try forming each type of prebiotic molecule
        val templates = listOf(
            MoleculeTemplate.Methane,
            MoleculeTemplate.Ammonia,
            MoleculeTemplate.HydrogenCyanide,
            MoleculeTemplate.Formaldehyde,
        )

        for (template in templates) {
            val mol = synthesize(template, atomicSystem)
            if (mol != null) formed.add(mol)
        }

        return formed
    }

    /**
     * Attempt amino acid synthesis from simpler molecules.
     * In reality this requires specific conditions (Miller-Urey experiment).
     */
    fun aminoAcidSynthesis(environment: Environment): List<String> {
        val formed = mutableListOf<String>()

        // Requires liquid water and energy source
        if (!environment.hasLiquidWater) return formed
        if (environment.radiation < 1.0 && !environment.hasLightning) return formed

        // UV radiation or lightning provides energy for synthesis
        val energyFactor = if (environment.hasLightning) 2.0 else 1.0
        val prob = 0.001 * energyFactor

        for (aminoAcid in Constants.AMINO_ACIDS) {
            if (rng.nextDouble() < prob) {
                aminoAcids.add(aminoAcid)
                formed.add(aminoAcid)
            }
        }

        return formed
    }

    /**
     * Attempt nucleotide synthesis from available molecules.
     * Requires phosphoric acid, ribose, and nucleobases.
     */
    fun nucleotideSynthesis(environment: Environment): List<Nucleotide> {
        val formed = mutableListOf<Nucleotide>()

        if (!environment.hasLiquidWater) return formed

        // Probability depends on temperature (warm ponds hypothesis)
        val tempFactor = if (temperature in 300.0..380.0) 2.0 else 0.5
        val prob = 0.0005 * tempFactor

        val bases = if (rng.nextDouble() < 0.5) {
            Constants.NUCLEOTIDE_BASES
        } else {
            Constants.RNA_BASES
        }

        for (base in bases) {
            if (rng.nextDouble() < prob) {
                val isRNA = base == "U" || (base != "T" && rng.nextDouble() < 0.7)
                val nucleotide = Nucleotide(base, isRNA)
                nucleotides.add(nucleotide)
                formed.add(nucleotide)
            }
        }

        return formed
    }

    /**
     * Polymerize nucleotides into short RNA chains (RNA World hypothesis).
     * Returns the length of the chain formed, or 0 if none.
     */
    fun polymerizeRNA(): Int {
        val rnaNucleotides = nucleotides.filter { it.isRNA }
        if (rnaNucleotides.size < 3) return 0

        // Probability of successful polymerization decreases with chain length
        val maxLen = rnaNucleotides.size.coerceAtMost(50)
        var chainLen = 0
        for (i in 0 until maxLen) {
            if (rng.nextDouble() < 0.3) {
                chainLen++
            } else {
                break
            }
        }

        // Remove used nucleotides
        repeat(chainLen.coerceAtMost(nucleotides.size)) {
            val idx = nucleotides.indexOfFirst { it.isRNA }
            if (idx >= 0) nucleotides.removeAt(idx)
        }

        return chainLen
    }

    /** Count molecules by name. */
    fun moleculeCounts(): Map<String, Int> {
        val counts = mutableMapOf<String, Int>()
        for (m in molecules) {
            counts[m.name] = (counts[m.name] ?: 0) + 1
        }
        return counts
    }

    /** Total number of distinct molecule types. */
    val moleculeDiversity: Int get() = molecules.map { it.name }.distinct().size
}
