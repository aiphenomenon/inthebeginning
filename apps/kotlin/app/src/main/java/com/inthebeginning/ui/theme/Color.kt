package com.inthebeginning.ui.theme

import androidx.compose.ui.graphics.Color

/**
 * Epoch-specific color palette for the cosmic simulation.
 * Each epoch has a characteristic color that represents the dominant
 * physics/chemistry of that era.
 */
object EpochColors {
    val Planck = Color(0xFFFFFFFF)          // Pure white - unified force
    val Inflation = Color(0xFFE0F7FA)       // Pale cyan - rapid expansion
    val Electroweak = Color(0xFFCE93D8)     // Light purple - symmetry breaking
    val Quark = Color(0xFFFF6B9D)           // Plasma pink - quark-gluon plasma
    val Hadron = Color(0xFFEF5350)          // Red - hot hadron soup
    val Nucleosynthesis = Color(0xFFFFAB40) // Amber - nuclear forge
    val Recombination = Color(0xFFFFD54F)   // Gold - first light (CMB)
    val StarFormation = Color(0xFF4FC3F7)   // Neutron blue - stellar ignition
    val SolarSystem = Color(0xFFFFB74D)     // Orange - protoplanetary disk
    val Earth = Color(0xFF42A5F5)           // Blue - water world
    val Life = Color(0xFF66BB6A)            // Life green - first cells
    val DNAEra = Color(0xFF26A69A)          // Teal - DNA complexity
    val Present = Color(0xFF00E5FF)         // Nova cyan - intelligence

    /** Get color for epoch by index (0..12). */
    fun forEpoch(index: Int): Color = when (index) {
        0 -> Planck
        1 -> Inflation
        2 -> Electroweak
        3 -> Quark
        4 -> Hadron
        5 -> Nucleosynthesis
        6 -> Recombination
        7 -> StarFormation
        8 -> SolarSystem
        9 -> Earth
        10 -> Life
        11 -> DNAEra
        12 -> Present
        else -> Present
    }

    /** All epoch colors in order. */
    val all = listOf(
        Planck, Inflation, Electroweak, Quark, Hadron,
        Nucleosynthesis, Recombination, StarFormation, SolarSystem,
        Earth, Life, DNAEra, Present
    )
}

/**
 * Particle-type colors for rendering.
 */
object ParticleColors {
    val Photon = Color(0xFFFFEB3B)          // Yellow
    val Electron = Color(0xFF2196F3)        // Blue
    val Positron = Color(0xFFFF5252)        // Red
    val Proton = Color(0xFFFF9800)          // Orange
    val Neutron = Color(0xFF9E9E9E)         // Gray
    val Quark = Color(0xFFE040FB)           // Magenta
    val Neutrino = Color(0x80FFFFFF)        // Translucent white
    val Gluon = Color(0xFF00E676)           // Green
    val WBoson = Color(0xFFAA00FF)          // Purple
    val ZBoson = Color(0xFF6200EA)          // Deep purple

    fun forType(type: String): Color = when (type) {
        "photon" -> Photon
        "electron" -> Electron
        "positron" -> Positron
        "proton" -> Proton
        "neutron" -> Neutron
        "up", "down" -> Quark
        "neutrino" -> Neutrino
        "gluon" -> Gluon
        "W" -> WBoson
        "Z" -> ZBoson
        else -> Color.White
    }
}

/**
 * Element colors for atom rendering.
 */
object ElementColors {
    val Hydrogen = Color(0xFFE0E0E0)
    val Helium = Color(0xFFFFF9C4)
    val Carbon = Color(0xFF424242)
    val Nitrogen = Color(0xFF42A5F5)
    val Oxygen = Color(0xFFEF5350)
    val Iron = Color(0xFFBF360C)

    fun forSymbol(symbol: String): Color = when (symbol) {
        "H" -> Hydrogen
        "He" -> Helium
        "C" -> Carbon
        "N" -> Nitrogen
        "O" -> Oxygen
        "Fe" -> Iron
        else -> Color(0xFF78909C)
    }
}
