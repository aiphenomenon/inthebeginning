#include "universe.hpp"

#include <cmath>
#include <sstream>
#include <iomanip>
#include <memory>

namespace sim {

Universe::Universe()
    : quantumField(T_PLANCK),
      atomicSystem(T_RECOMBINATION),
      chemicalSystem(atomicSystem),
      environment(T_PLANCK) {}

EpochState Universe::snapshot(const std::string& name,
                              const std::string& details) const {
    EpochState state;
    state.epochName     = name;
    state.tick          = tick_;
    state.temperature   = environment.currentTemperature();
    state.totalEnergy   = quantumField.totalEnergy();
    state.particleCount = static_cast<int>(quantumField.particles.size());
    state.atomCount     = static_cast<int>(atomicSystem.atoms.size());
    state.moleculeCount = static_cast<int>(chemicalSystem.molecules.size());
    state.cellCount     = biosphere ? static_cast<int>(biosphere->cells.size()) : 0;
    state.scaleFactor   = environment.scaleFactor();
    state.details       = details;
    return state;
}

void Universe::simulate(std::function<void(const EpochState&)> onEpoch) {
    history_.clear();

    using EpochFn = EpochState (Universe::*)();
    EpochFn epochFns[] = {
        &Universe::simulatePlanck,
        &Universe::simulateInflation,
        &Universe::simulateElectroweak,
        &Universe::simulateQuark,
        &Universe::simulateHadron,
        &Universe::simulateNucleosynthesis,
        &Universe::simulateRecombination,
        &Universe::simulateStarFormation,
        &Universe::simulateSolarSystem,
        &Universe::simulateEarth,
        &Universe::simulateLife,
        &Universe::simulateDNA,
        &Universe::simulatePresent,
    };

    for (auto fn : epochFns) {
        auto state = (this->*fn)();
        history_.push_back(state);
        if (onEpoch) onEpoch(state);
    }
}

EpochState Universe::runEpoch(int epochIndex) {
    using EpochFn = EpochState (Universe::*)();
    EpochFn epochFns[] = {
        &Universe::simulatePlanck,
        &Universe::simulateInflation,
        &Universe::simulateElectroweak,
        &Universe::simulateQuark,
        &Universe::simulateHadron,
        &Universe::simulateNucleosynthesis,
        &Universe::simulateRecombination,
        &Universe::simulateStarFormation,
        &Universe::simulateSolarSystem,
        &Universe::simulateEarth,
        &Universe::simulateLife,
        &Universe::simulateDNA,
        &Universe::simulatePresent,
    };

    if (epochIndex < 0 || epochIndex >= 13) {
        return snapshot("Unknown", "Invalid epoch index");
    }

    return (this->*epochFns[epochIndex])();
}

// ============================================================
// Epoch implementations
// ============================================================

EpochState Universe::simulatePlanck() {
    tick_ = PLANCK_EPOCH;
    environment.update(tick_);
    quantumField.temperature = environment.currentTemperature();

    // At the Planck epoch, all forces are unified.
    // Vacuum fluctuations create the initial particle content.
    for (int i = 0; i < 20; ++i) {
        quantumField.vacuumFluctuation();
    }

    std::ostringstream details;
    details << "All four forces unified. "
            << "Vacuum fluctuations create " << quantumField.particles.size()
            << " virtual particles. "
            << "Vacuum energy = " << std::scientific << std::setprecision(2)
            << quantumField.vacuumEnergy;

    return snapshot("Planck", details.str());
}

EpochState Universe::simulateInflation() {
    tick_ = INFLATION_EPOCH;
    environment.update(tick_);
    quantumField.temperature = environment.currentTemperature();

    // Inflation: exponential expansion, quantum fluctuations seed structure.
    // Massive pair production from inflaton field decay.
    for (int i = 0; i < 50; ++i) {
        double energy = quantumField.temperature * K_B * 10.0;
        quantumField.pairProduction(energy);
        quantumField.vacuumFluctuation();
    }

    // Evolve the field
    quantumField.evolve(1.0);

    std::ostringstream details;
    details << "Exponential expansion by factor ~e^60. "
            << "Quantum fluctuations seed large-scale structure. "
            << quantumField.totalCreated << " particles created, "
            << quantumField.particles.size() << " surviving.";

    return snapshot("Inflation", details.str());
}

EpochState Universe::simulateElectroweak() {
    tick_ = ELECTROWEAK_EPOCH;
    environment.update(tick_);
    quantumField.temperature = environment.currentTemperature();

    // Electroweak symmetry breaking: W/Z bosons become massive
    // More pair production at high energy
    for (int i = 0; i < 30; ++i) {
        double energy = quantumField.temperature * K_B * 5.0;
        quantumField.pairProduction(energy);
    }

    // Some annihilation (matter-antimatter)
    int annihilations = 0;
    for (size_t i = 0; i + 1 < quantumField.particles.size() && annihilations < 10; ++i) {
        if (quantumField.particles[i].type == ParticleType::Electron) {
            for (size_t j = i + 1; j < quantumField.particles.size(); ++j) {
                if (quantumField.particles[j].type == ParticleType::Positron) {
                    quantumField.annihilate(i, j);
                    ++annihilations;
                    break;
                }
            }
        }
    }

    quantumField.evolve(1.0);

    std::ostringstream details;
    details << "Higgs field activates, W/Z bosons gain mass. "
            << "EM and weak forces separate. "
            << annihilations << " matter-antimatter annihilations. "
            << quantumField.particles.size() << " particles remain.";

    return snapshot("Electroweak", details.str());
}

EpochState Universe::simulateQuark() {
    tick_ = QUARK_EPOCH;
    environment.update(tick_);
    quantumField.temperature = environment.currentTemperature();

    // Quark-gluon plasma era
    // Generate quark pairs
    for (int i = 0; i < 40; ++i) {
        double energy = M_PROTON * C * C * 3.0;
        quantumField.pairProduction(energy);
    }

    quantumField.evolve(1.0);

    // Count quarks
    int ups = 0, downs = 0;
    for (auto& p : quantumField.particles) {
        if (p.type == ParticleType::Up) ++ups;
        if (p.type == ParticleType::Down) ++downs;
    }

    std::ostringstream details;
    details << "Quark-gluon plasma: free quarks and gluons. "
            << ups << " up quarks, " << downs << " down quarks, "
            << quantumField.particles.size() << " total particles.";

    return snapshot("Quark", details.str());
}

EpochState Universe::simulateHadron() {
    tick_ = HADRON_EPOCH;
    environment.update(tick_);
    quantumField.temperature = T_QUARK_HADRON * 0.5; // below QCD transition

    // Quark confinement: quarks bind into protons and neutrons
    auto hadrons = quantumField.quarkConfinement();

    quantumField.evolve(1.0);

    int protons = 0, neutrons = 0;
    for (auto& p : quantumField.particles) {
        if (p.type == ParticleType::Proton)  ++protons;
        if (p.type == ParticleType::Neutron) ++neutrons;
    }

    std::ostringstream details;
    details << "Quarks confined into hadrons. "
            << hadrons.size() << " new hadrons formed: "
            << protons << " protons, " << neutrons << " neutrons. "
            << quantumField.particles.size() << " total particles.";

    return snapshot("Hadron", details.str());
}

EpochState Universe::simulateNucleosynthesis() {
    tick_ = NUCLEOSYNTHESIS_EPOCH;
    environment.update(tick_);
    quantumField.temperature = T_NUCLEOSYNTHESIS;
    atomicSystem.temperature = T_NUCLEOSYNTHESIS;

    // Count protons and neutrons in the quantum field
    int protons = 0, neutrons = 0;
    for (auto& p : quantumField.particles) {
        if (p.type == ParticleType::Proton)  ++protons;
        if (p.type == ParticleType::Neutron) ++neutrons;
    }

    // Big Bang nucleosynthesis: form H and He
    auto nuclei = atomicSystem.nucleosynthesis(protons, neutrons);

    int hydrogen = 0, helium = 0;
    for (auto& a : atomicSystem.atoms) {
        if (a.atomicNumber == 1) ++hydrogen;
        if (a.atomicNumber == 2) ++helium;
    }

    std::ostringstream details;
    details << "Primordial nucleosynthesis: "
            << hydrogen << " hydrogen, " << helium << " helium nuclei. "
            << "~75% H, ~25% He by mass (cosmological ratio). "
            << nuclei.size() << " nuclei formed.";

    return snapshot("Nucleosynthesis", details.str());
}

EpochState Universe::simulateRecombination() {
    tick_ = RECOMBINATION_EPOCH;
    environment.update(tick_);
    quantumField.temperature = T_RECOMBINATION;
    atomicSystem.temperature = T_RECOMBINATION;

    // Add electrons to the quantum field for recombination
    int protonCount = 0;
    for (auto& p : quantumField.particles) {
        if (p.type == ParticleType::Proton) ++protonCount;
    }

    // Ensure we have electrons for recombination
    int electronCount = 0;
    for (auto& p : quantumField.particles) {
        if (p.type == ParticleType::Electron) ++electronCount;
    }

    // Add more electrons if needed
    while (electronCount < protonCount) {
        Particle electron;
        electron.type = ParticleType::Electron;
        electron.spin = Spin::Up;
        quantumField.particles.push_back(electron);
        ++electronCount;
    }

    // Electrons captured by nuclei -> neutral atoms
    auto newAtoms = atomicSystem.recombination(quantumField);

    std::ostringstream details;
    details << "Electrons captured by nuclei: universe becomes transparent. "
            << newAtoms.size() << " new neutral atoms formed. "
            << atomicSystem.atoms.size() << " total atoms. "
            << "Cosmic Microwave Background released (T=" << T_CMB << "K today).";

    return snapshot("Recombination", details.str());
}

EpochState Universe::simulateStarFormation() {
    tick_ = STAR_FORMATION_EPOCH;
    environment.update(tick_);

    // Stellar nucleosynthesis: forge heavier elements
    auto heavyElements = atomicSystem.stellarNucleosynthesis(T_STELLAR_CORE);

    // Count elements
    int carbon = 0, oxygen = 0, nitrogen = 0, iron = 0;
    for (auto& a : atomicSystem.atoms) {
        if (a.atomicNumber == 6) ++carbon;
        if (a.atomicNumber == 7) ++nitrogen;
        if (a.atomicNumber == 8) ++oxygen;
        if (a.atomicNumber == 26) ++iron;
    }

    std::ostringstream details;
    details << "First stars ignite from gravitational collapse. "
            << "Stellar fusion forges heavy elements: "
            << carbon << " C, " << nitrogen << " N, "
            << oxygen << " O atoms. "
            << heavyElements.size() << " new heavy elements created. "
            << "Supernovae distribute elements across space.";

    return snapshot("Star Formation", details.str());
}

EpochState Universe::simulateSolarSystem() {
    tick_ = SOLAR_SYSTEM_EPOCH;
    environment.update(tick_);

    // More stellar nucleosynthesis to produce enough elements for chemistry
    atomicSystem.stellarNucleosynthesis(T_STELLAR_CORE);
    atomicSystem.stellarNucleosynthesis(T_STELLAR_CORE);

    // Ensure we have enough hydrogen for later chemistry
    // (stellar debris has lots of H)
    int hCount = 0;
    for (auto& a : atomicSystem.atoms) {
        if (a.atomicNumber == 1) ++hCount;
    }
    // Add more hydrogen from the primordial reservoir
    for (int i = 0; i < 50 && hCount < 60; ++i) {
        Atom h;
        h.init(1, 1);
        atomicSystem.atoms.push_back(h);
        ++hCount;
    }

    std::ostringstream details;
    details << "Solar nebula coalesces from stellar debris. "
            << "Protoplanetary disk forms. "
            << atomicSystem.atoms.size() << " atoms in the system. "
            << "Elements available for rocky planet formation.";

    return snapshot("Solar System", details.str());
}

EpochState Universe::simulateEarth() {
    tick_ = EARTH_EPOCH;
    environment.update(tick_);

    // Form water and simple molecules
    auto waters = chemicalSystem.formWater();
    auto methanes = chemicalSystem.formMethane();
    auto ammonias = chemicalSystem.formAmmonia();

    std::ostringstream details;
    details << "Earth accretes and differentiates. "
            << "Oceans form: " << waters.size() << " water molecules. "
            << methanes.size() << " CH4, " << ammonias.size() << " NH3. "
            << "Total molecules: " << chemicalSystem.molecules.size() << ". "
            << environment.summary();

    return snapshot("Earth", details.str());
}

EpochState Universe::simulateLife() {
    tick_ = LIFE_EPOCH;
    environment.update(tick_);

    // Prebiotic chemistry: form amino acids and nucleotides
    int aaFormed = 0, nucFormed = 0;
    for (int i = 0; i < 20; ++i) {
        int formed = chemicalSystem.catalyzedReaction(
            environment.currentTemperature(), true);
        aaFormed += chemicalSystem.aminoAcidCount;
        nucFormed += chemicalSystem.nucleotideCount;
        if (formed > 0) break; // got some biomolecules
    }

    // First self-replicating molecules emerge
    biosphere = std::make_unique<Biosphere>(3, 60);

    std::ostringstream details;
    details << "First self-replicating molecules appear! "
            << "Amino acids: " << chemicalSystem.aminoAcidCount
            << ", Nucleotides: " << chemicalSystem.nucleotideCount << ". "
            << biosphere->cells.size() << " protocells formed. "
            << "Avg fitness: " << std::fixed << std::setprecision(3)
            << biosphere->averageFitness() << ". "
            << environment.summary();

    return snapshot("Life", details.str());
}

EpochState Universe::simulateDNA() {
    tick_ = DNA_EPOCH;
    environment.update(tick_);

    if (!biosphere) {
        biosphere = std::make_unique<Biosphere>(5, 90);
    }

    // Run several generations of biological evolution
    double uvShielding = environment.atmosphere.uvShielding();
    double uvIntensity = environment.radiation.uvIntensity * (1.0 - uvShielding);
    double cosmicFlux  = environment.radiation.cosmicRayFlux;
    double bioEnergy   = environment.biologicalEnergy();

    for (int gen = 0; gen < 10; ++gen) {
        biosphere->step(bioEnergy, uvIntensity, cosmicFlux,
                        environment.currentTemperature());
    }

    std::ostringstream details;
    details << "DNA-based life dominates. Epigenetics emerge. "
            << biosphere->cells.size() << " cells, "
            << biosphere->generation << " generations. "
            << "Avg fitness: " << std::fixed << std::setprecision(3)
            << biosphere->averageFitness()
            << ", GC content: " << std::setprecision(3)
            << biosphere->averageGcContent() << ". "
            << "Mutations: " << biosphere->totalMutations()
            << ", Born: " << biosphere->totalBorn
            << ", Died: " << biosphere->totalDied << ". "
            << environment.summary();

    return snapshot("DNA Era", details.str());
}

EpochState Universe::simulatePresent() {
    tick_ = PRESENT_EPOCH;
    environment.update(tick_);

    if (!biosphere) {
        biosphere = std::make_unique<Biosphere>(10, 120);
    }

    // Run more generations to evolve complexity
    double uvShielding = environment.atmosphere.uvShielding();
    double uvIntensity = environment.radiation.uvIntensity * (1.0 - uvShielding);
    double cosmicFlux  = environment.radiation.cosmicRayFlux;
    double bioEnergy   = environment.biologicalEnergy();

    for (int gen = 0; gen < 20; ++gen) {
        biosphere->step(bioEnergy, uvIntensity, cosmicFlux,
                        environment.currentTemperature());
    }

    // Final census
    int totalProteins = 0;
    int totalGenes = 0;
    for (auto& cell : biosphere->cells) {
        totalProteins += static_cast<int>(cell.proteins.size());
        totalGenes += static_cast<int>(cell.dna.genes.size());
    }

    std::ostringstream details;
    details << "Complex life, intelligence, and consciousness emerge. "
            << biosphere->cells.size() << " cells across "
            << biosphere->generation << " generations. "
            << "Avg fitness: " << std::fixed << std::setprecision(3)
            << biosphere->averageFitness() << ". "
            << totalProteins << " proteins, " << totalGenes << " genes active. "
            << "Total mutations: " << biosphere->totalMutations()
            << ", Born: " << biosphere->totalBorn
            << ", Died: " << biosphere->totalDied << ". "
            << environment.summary();

    return snapshot("Present", details.str());
}

} // namespace sim
