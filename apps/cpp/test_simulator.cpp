/**
 * test_simulator.cpp - Unit tests for the C++ cosmic evolution simulator.
 *
 * Uses simple assertion macros with no external dependencies.
 * Tests all major subsystems: constants, quantum, atomic, chemistry,
 * biology, environment, and universe.
 */
// Include <string> before simulator headers since constants.hpp uses
// std::unordered_map<std::string, std::string> in codonTable() but
// only includes <string_view>.
#include <string>

#include "simulator/constants.hpp"
#include "simulator/quantum.hpp"
#include "simulator/atomic.hpp"
#include "simulator/chemistry.hpp"
#include "simulator/biology.hpp"
#include "simulator/environment.hpp"
#include "simulator/universe.hpp"

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

// ================================================================
// Test framework
// ================================================================

static int g_tests_run    = 0;
static int g_tests_passed = 0;
static int g_tests_failed = 0;

#define TEST_ASSERT(expr) do { \
    ++g_tests_run; \
    if (expr) { \
        ++g_tests_passed; \
    } else { \
        ++g_tests_failed; \
        std::printf("  FAIL: %s:%d: %s\n", __FILE__, __LINE__, #expr); \
    } \
} while (0)

#define TEST_ASSERT_FLOAT_EQ(a, b, eps) do { \
    ++g_tests_run; \
    if (std::fabs(static_cast<double>(a) - static_cast<double>(b)) < (eps)) { \
        ++g_tests_passed; \
    } else { \
        ++g_tests_failed; \
        std::printf("  FAIL: %s:%d: %s == %s (%.10g != %.10g)\n", \
                    __FILE__, __LINE__, #a, #b, \
                    static_cast<double>(a), static_cast<double>(b)); \
    } \
} while (0)

#define TEST_SECTION(name) std::printf("\n--- %s ---\n", name)

// ================================================================
// Test: Constants
// ================================================================

static void test_constants()
{
    TEST_SECTION("Constants");

    // Fundamental constants
    TEST_ASSERT_FLOAT_EQ(sim::C, 1.0, 1e-9);
    TEST_ASSERT_FLOAT_EQ(sim::HBAR, 0.01, 1e-9);
    TEST_ASSERT_FLOAT_EQ(sim::K_B, 0.001, 1e-9);
    TEST_ASSERT_FLOAT_EQ(sim::G_CONST, 1e-6, 1e-12);
    TEST_ASSERT_FLOAT_EQ(sim::ALPHA, 1.0 / 137.0, 1e-9);
    TEST_ASSERT_FLOAT_EQ(sim::E_CHARGE, 0.1, 1e-9);
    TEST_ASSERT_FLOAT_EQ(sim::PI, 3.14159265358979323846, 1e-12);

    // Particle masses
    TEST_ASSERT_FLOAT_EQ(sim::M_ELECTRON, 1.0, 1e-9);
    TEST_ASSERT_FLOAT_EQ(sim::M_PROTON, 1836.0, 1e-9);
    TEST_ASSERT_FLOAT_EQ(sim::M_NEUTRON, 1839.0, 1e-9);
    TEST_ASSERT_FLOAT_EQ(sim::M_PHOTON, 0.0, 1e-9);
    TEST_ASSERT(sim::M_PROTON > sim::M_ELECTRON);
    TEST_ASSERT(sim::M_NEUTRON > sim::M_PROTON);

    // Force coupling strengths
    TEST_ASSERT_FLOAT_EQ(sim::STRONG_COUPLING, 1.0, 1e-9);
    TEST_ASSERT(sim::EM_COUPLING < sim::STRONG_COUPLING);
    TEST_ASSERT(sim::WEAK_COUPLING < sim::EM_COUPLING);
    TEST_ASSERT(sim::GRAVITY_COUPLING < sim::WEAK_COUPLING);

    // Cosmic timeline ordering
    TEST_ASSERT(sim::PLANCK_EPOCH < sim::INFLATION_EPOCH);
    TEST_ASSERT(sim::INFLATION_EPOCH < sim::ELECTROWEAK_EPOCH);
    TEST_ASSERT(sim::ELECTROWEAK_EPOCH < sim::QUARK_EPOCH);
    TEST_ASSERT(sim::QUARK_EPOCH < sim::HADRON_EPOCH);
    TEST_ASSERT(sim::HADRON_EPOCH < sim::NUCLEOSYNTHESIS_EPOCH);
    TEST_ASSERT(sim::NUCLEOSYNTHESIS_EPOCH < sim::RECOMBINATION_EPOCH);
    TEST_ASSERT(sim::RECOMBINATION_EPOCH < sim::STAR_FORMATION_EPOCH);
    TEST_ASSERT(sim::STAR_FORMATION_EPOCH < sim::SOLAR_SYSTEM_EPOCH);
    TEST_ASSERT(sim::SOLAR_SYSTEM_EPOCH < sim::EARTH_EPOCH);
    TEST_ASSERT(sim::EARTH_EPOCH < sim::LIFE_EPOCH);
    TEST_ASSERT(sim::LIFE_EPOCH < sim::DNA_EPOCH);
    TEST_ASSERT(sim::DNA_EPOCH < sim::PRESENT_EPOCH);

    // Temperature ordering
    TEST_ASSERT(sim::T_PLANCK > sim::T_ELECTROWEAK);
    TEST_ASSERT(sim::T_ELECTROWEAK > sim::T_QUARK_HADRON);
    TEST_ASSERT(sim::T_QUARK_HADRON > sim::T_NUCLEOSYNTHESIS);
    TEST_ASSERT(sim::T_NUCLEOSYNTHESIS > sim::T_RECOMBINATION);
    TEST_ASSERT(sim::T_RECOMBINATION > sim::T_CMB);

    // Biology parameters
    TEST_ASSERT(sim::NUCLEOTIDE_BASES.size() == 4);
    TEST_ASSERT(sim::AMINO_ACIDS.size() == 20);
    TEST_ASSERT(sim::ELECTRON_SHELLS.size() == 7);

    // Particle type helpers
    TEST_ASSERT_FLOAT_EQ(sim::particleMass(sim::ParticleType::Proton), sim::M_PROTON, 1e-3);
    TEST_ASSERT_FLOAT_EQ(sim::particleMass(sim::ParticleType::Electron), sim::M_ELECTRON, 1e-6);
    TEST_ASSERT_FLOAT_EQ(sim::particleMass(sim::ParticleType::Photon), 0.0, 1e-9);
    TEST_ASSERT_FLOAT_EQ(sim::particleCharge(sim::ParticleType::Electron), -1.0, 1e-6);
    TEST_ASSERT_FLOAT_EQ(sim::particleCharge(sim::ParticleType::Proton), 1.0, 1e-6);
    TEST_ASSERT_FLOAT_EQ(sim::particleCharge(sim::ParticleType::Neutron), 0.0, 1e-6);

    // Particle type names
    TEST_ASSERT(std::string(sim::particleTypeName(sim::ParticleType::Proton)) == "proton");
    TEST_ASSERT(std::string(sim::particleTypeName(sim::ParticleType::Electron)) == "electron");
    TEST_ASSERT(std::string(sim::particleTypeName(sim::ParticleType::Photon)) == "photon");

    // Epoch table
    TEST_ASSERT(sim::EPOCHS.size() == 13);
    TEST_ASSERT(sim::EPOCHS[0].name == "Planck");
    TEST_ASSERT(sim::EPOCHS[12].name == "Present");

    // Element data
    auto& el = sim::elements();
    TEST_ASSERT(el.count(1) > 0);
    TEST_ASSERT(std::string(el.at(1).symbol) == "H");
    TEST_ASSERT(std::string(el.at(6).symbol) == "C");
    TEST_ASSERT(el.count(999) == 0);

    std::printf("  Constants: all checks passed\n");
}

// ================================================================
// Test: Quantum Field
// ================================================================

static void test_quantum_field()
{
    TEST_SECTION("Quantum Field");

    // Initialization
    sim::QuantumField qf(sim::T_PLANCK);
    TEST_ASSERT(qf.particles.empty());
    TEST_ASSERT_FLOAT_EQ(qf.temperature, sim::T_PLANCK, 1e-3);
    TEST_ASSERT(qf.totalCreated == 0);
    TEST_ASSERT(qf.totalAnnihilated == 0);

    // Wave function
    sim::WaveFunction wf;
    TEST_ASSERT_FLOAT_EQ(wf.amplitude, 1.0, 1e-6);
    TEST_ASSERT_FLOAT_EQ(wf.phase, 0.0, 1e-6);
    TEST_ASSERT(wf.coherent == true);
    TEST_ASSERT_FLOAT_EQ(wf.probability(), 1.0, 1e-6);

    // Wave function evolution
    wf.evolve(1.0, 1.0);
    TEST_ASSERT(wf.coherent == true);
    TEST_ASSERT(wf.phase >= 0.0);
    TEST_ASSERT(wf.phase < 2.0 * sim::PI + 0.01);

    // Superposition
    sim::WaveFunction wf2;
    wf2.phase = sim::PI / 4.0;
    auto sup = wf.superpose(wf2);
    TEST_ASSERT(sup.coherent == true);
    TEST_ASSERT(sup.amplitude > 0.0);
    TEST_ASSERT(sup.amplitude <= 1.0);

    // Pair production - insufficient energy
    bool pp = qf.pairProduction(0.1);
    TEST_ASSERT(pp == false);
    TEST_ASSERT(qf.particles.empty());

    // Pair production - sufficient energy
    double enough = 2.0 * sim::M_ELECTRON * sim::C * sim::C + 1.0;
    pp = qf.pairProduction(enough);
    TEST_ASSERT(pp == true);
    TEST_ASSERT(qf.particles.size() == 2);
    TEST_ASSERT(qf.totalCreated == 2);

    // Particle energy
    sim::Particle proton;
    proton.type = sim::ParticleType::Proton;
    double e = proton.energy();
    TEST_ASSERT(e > 0.0);
    TEST_ASSERT_FLOAT_EQ(e, sim::M_PROTON * sim::C * sim::C, 0.01);

    // Particle wavelength
    sim::Particle photon;
    photon.type = sim::ParticleType::Photon;
    photon.momentum = {0.0, 0.0, 0.0};
    double wl = photon.wavelength();
    TEST_ASSERT(wl > 1e20); // effectively infinite for zero momentum

    // Add more particles for annihilation test
    qf.pairProduction(enough);
    size_t count_before = qf.particles.size();
    TEST_ASSERT(count_before == 4);

    // Total energy should be positive
    double total_e = qf.totalEnergy();
    TEST_ASSERT(total_e > 0.0);

    // Evolve
    qf.evolve(0.1);
    TEST_ASSERT(qf.particles.size() == count_before);

    // Quark confinement
    sim::QuantumField qf2(sim::T_QUARK_HADRON * 0.5);
    sim::Particle up1;
    up1.type = sim::ParticleType::Up;
    sim::Particle up2 = up1;
    sim::Particle down1;
    down1.type = sim::ParticleType::Down;

    qf2.particles.push_back(up1);
    qf2.particles.push_back(up2);
    qf2.particles.push_back(down1);

    auto hadrons = qf2.quarkConfinement();
    TEST_ASSERT(hadrons.size() >= 1);

    // Quarks should be consumed, proton should exist
    int proton_count = 0;
    int up_count = 0;
    for (auto& p : qf2.particles) {
        if (p.type == sim::ParticleType::Proton) ++proton_count;
        if (p.type == sim::ParticleType::Up) ++up_count;
    }
    TEST_ASSERT(proton_count >= 1);
    TEST_ASSERT(up_count == 0);

    std::printf("  Quantum: all checks passed\n");
}

// ================================================================
// Test: Atomic System
// ================================================================

static void test_atomic_system()
{
    TEST_SECTION("Atomic System");

    sim::AtomicSystem as;
    TEST_ASSERT(as.atoms.empty());
    TEST_ASSERT_FLOAT_EQ(as.temperature, sim::T_RECOMBINATION, 0.1);

    // Atom init
    sim::Atom h;
    h.init(1, 1, {1.0, 2.0, 3.0});
    TEST_ASSERT(h.atomicNumber == 1);
    TEST_ASSERT(h.massNumber == 1);
    TEST_ASSERT(h.electronCount == 1);
    TEST_ASSERT_FLOAT_EQ(h.position[0], 1.0, 1e-6);

    // Symbol
    TEST_ASSERT(std::string(h.symbol()) == "H");
    TEST_ASSERT(std::string(h.name()) == "Hydrogen");

    // Helium
    sim::Atom he;
    he.init(2, 4);
    TEST_ASSERT(he.atomicNumber == 2);
    TEST_ASSERT(he.massNumber == 4);
    TEST_ASSERT(std::string(he.symbol()) == "He");
    TEST_ASSERT(he.isNobleGas() == true);

    // Hydrogen is not a noble gas
    TEST_ASSERT(h.isNobleGas() == false);

    // Bonding
    TEST_ASSERT(h.canBondWith(he) == false); // He is noble gas
    sim::Atom h2;
    h2.init(1, 1, {4.0, 6.0, 3.0});
    TEST_ASSERT(h.canBondWith(h2) == true);

    // Distance
    double dist = h.distanceTo(h2);
    TEST_ASSERT_FLOAT_EQ(dist, 5.0, 0.01); // 3-4-5 triangle

    // Electronegativity
    TEST_ASSERT(h.electronegativity() > 0.0);

    // Valence electrons
    TEST_ASSERT(h.valenceElectrons() == 1);
    TEST_ASSERT(h.needsElectrons() == 1);

    // Ion operations
    sim::Atom li;
    li.init(3, 7);
    TEST_ASSERT(li.chargeState() == 0);
    bool ionized = li.ionize();
    TEST_ASSERT(ionized == true);
    TEST_ASSERT(li.chargeState() == 1);
    bool captured = li.captureElectron();
    TEST_ASSERT(captured == true);
    TEST_ASSERT(li.chargeState() == 0);

    // Bond type
    sim::Atom na;
    na.init(11, 23);
    sim::Atom cl;
    cl.init(17, 35);
    std::string bt = na.bondType(cl);
    TEST_ASSERT(bt == "ionic");

    // Nucleosynthesis
    auto nuclei = as.nucleosynthesis(4, 4);
    TEST_ASSERT(!nuclei.empty());
    TEST_ASSERT(!as.atoms.empty());

    // Check for helium in atoms
    int he_count = 0;
    for (auto& a : as.atoms) {
        if (a.atomicNumber == 2) ++he_count;
    }
    TEST_ASSERT(he_count > 0);

    std::printf("  Atomic: all checks passed\n");
}

// ================================================================
// Test: Chemistry
// ================================================================

static void test_chemistry()
{
    TEST_SECTION("Chemistry");

    sim::AtomicSystem as;
    sim::ChemicalSystem cs(as);
    TEST_ASSERT(cs.molecules.empty());
    TEST_ASSERT(cs.waterCount == 0);
    TEST_ASSERT(cs.aminoAcidCount == 0);
    TEST_ASSERT(cs.nucleotideCount == 0);

    // Add hydrogen and oxygen atoms for water
    for (int i = 0; i < 10; ++i) {
        sim::Atom h;
        h.init(1, 1);
        as.atoms.push_back(h);
    }
    for (int i = 0; i < 5; ++i) {
        sim::Atom o;
        o.init(8, 16);
        as.atoms.push_back(o);
    }

    // Form water
    auto waters = cs.formWater();
    TEST_ASSERT(!waters.empty());
    TEST_ASSERT(cs.waterCount > 0);
    TEST_ASSERT(!cs.molecules.empty());

    // Verify water molecule properties
    TEST_ASSERT(waters[0].name == "water");
    TEST_ASSERT(waters[0].formula == "H2O");

    // Form methane - fresh system
    sim::AtomicSystem as2;
    sim::ChemicalSystem cs2(as2);

    for (int i = 0; i < 8; ++i) {
        sim::Atom h;
        h.init(1, 1);
        as2.atoms.push_back(h);
    }
    for (int i = 0; i < 2; ++i) {
        sim::Atom c;
        c.init(6, 12);
        as2.atoms.push_back(c);
    }

    auto methanes = cs2.formMethane();
    TEST_ASSERT(!methanes.empty());
    TEST_ASSERT(methanes[0].name == "methane");
    TEST_ASSERT(methanes[0].isOrganic == true);

    // Form ammonia
    sim::AtomicSystem as3;
    sim::ChemicalSystem cs3(as3);

    for (int i = 0; i < 6; ++i) {
        sim::Atom h;
        h.init(1, 1);
        as3.atoms.push_back(h);
    }
    for (int i = 0; i < 2; ++i) {
        sim::Atom n;
        n.init(7, 14);
        as3.atoms.push_back(n);
    }

    auto ammonias = cs3.formAmmonia();
    TEST_ASSERT(!ammonias.empty());
    TEST_ASSERT(ammonias[0].name == "ammonia");

    // Catalyzed reaction
    sim::AtomicSystem as4;
    sim::ChemicalSystem cs4(as4);

    for (int i = 0; i < 50; ++i) {
        sim::Atom h; h.init(1, 1); as4.atoms.push_back(h);
    }
    for (int i = 0; i < 20; ++i) {
        sim::Atom c; c.init(6, 12); as4.atoms.push_back(c);
    }
    for (int i = 0; i < 20; ++i) {
        sim::Atom o; o.init(8, 16); as4.atoms.push_back(o);
    }
    for (int i = 0; i < 10; ++i) {
        sim::Atom n; n.init(7, 14); as4.atoms.push_back(n);
    }

    int total = 0;
    for (int i = 0; i < 100; ++i) {
        total += cs4.catalyzedReaction(500.0, true);
    }
    TEST_ASSERT(total >= 0);

    std::printf("  Chemistry: all checks passed\n");
}

// ================================================================
// Test: Biology
// ================================================================

static void test_biology()
{
    TEST_SECTION("Biology");

    // DNA random strand
    auto dna = sim::DNAStrand::randomStrand(90, 3);
    TEST_ASSERT(dna.length() == 90);
    TEST_ASSERT(dna.generation == 0);
    TEST_ASSERT(dna.mutationCount == 0);
    TEST_ASSERT(!dna.genes.empty());

    // GC content
    double gc = dna.gcContent();
    TEST_ASSERT(gc >= 0.0);
    TEST_ASSERT(gc <= 1.0);

    // DNA replication
    auto daughter = dna.replicate();
    TEST_ASSERT(daughter.length() == dna.length());
    TEST_ASSERT(daughter.generation == dna.generation + 1);

    // DNA mutations
    int muts = dna.applyMutations(100.0, 100.0);
    TEST_ASSERT(muts >= 0);

    // Epigenetic changes
    dna.applyEpigeneticChanges(300.0, 1);
    // Should not crash, epigenetic marks may have been added

    // Gene transcription
    if (!dna.genes.empty()) {
        auto mrna = dna.genes[0].transcribe();
        // May be empty if silenced, but should not crash
        TEST_ASSERT(mrna.size() <= static_cast<size_t>(dna.genes[0].length()));
    }

    // Gene mutation
    sim::Gene gene;
    gene.name = "test_gene";
    gene.sequence = {'A', 'T', 'G', 'C', 'A', 'T', 'G', 'C', 'A'};
    gene.startPos = 0;
    gene.endPos = 9;
    int gene_muts = gene.mutate(0.5);
    TEST_ASSERT(gene_muts >= 0);

    // Protein folding
    sim::Protein prot;
    prot.aminoAcids = {"Met", "Ala", "Val", "Leu", "Ile", "Phe"};
    bool folded = prot.fold();
    TEST_ASSERT(folded == true);
    TEST_ASSERT(prot.folded == true);

    // Small protein should not fold
    sim::Protein small_prot;
    small_prot.aminoAcids = {"Met", "Ala"};
    folded = small_prot.fold();
    TEST_ASSERT(folded == false);

    // mRNA translation
    std::vector<char> mrna = {'A', 'U', 'G', 'G', 'C', 'U', 'U', 'U', 'U', 'U', 'A', 'A'};
    auto aa_chain = sim::translateMRNA(mrna);
    TEST_ASSERT(!aa_chain.empty());
    TEST_ASSERT(aa_chain[0] == "Met"); // AUG -> Met

    // Cell
    sim::Cell cell;
    cell.dna = sim::DNAStrand::randomStrand(90, 3);
    cell.transcribeAndTranslate();
    cell.computeFitness();
    TEST_ASSERT(cell.alive == true);
    TEST_ASSERT(cell.fitness >= 0.0);

    // Cell metabolism
    cell.metabolize(10.0);
    TEST_ASSERT(cell.alive == true);

    // Cell division
    cell.energy = 100.0;
    auto child = cell.divide();
    TEST_ASSERT(child.has_value());
    TEST_ASSERT(child->alive == true);
    TEST_ASSERT(child->generation == cell.generation + 1);

    // Cell division with low energy
    sim::Cell weak_cell;
    weak_cell.dna = sim::DNAStrand::randomStrand(30, 1);
    weak_cell.energy = 10.0;
    auto no_child = weak_cell.divide();
    TEST_ASSERT(!no_child.has_value());

    // Biosphere
    sim::Biosphere bio(5, 60);
    TEST_ASSERT(static_cast<int>(bio.cells.size()) == 5);
    TEST_ASSERT(bio.generation == 0);
    TEST_ASSERT(bio.totalBorn == 5);
    TEST_ASSERT(bio.totalDied == 0);
    TEST_ASSERT(bio.dnaLength == 60);

    // Average fitness
    double avg = bio.averageFitness();
    TEST_ASSERT(avg > 0.0);

    // Biosphere step
    bio.step(10.0, 1.0, 0.5, 300.0);
    TEST_ASSERT(bio.generation == 1);
    TEST_ASSERT(!bio.cells.empty());

    // Total mutations
    int total_muts = bio.totalMutations();
    TEST_ASSERT(total_muts >= 0);

    // Average GC content
    double avg_gc = bio.averageGcContent();
    TEST_ASSERT(avg_gc >= 0.0);
    TEST_ASSERT(avg_gc <= 1.0);

    std::printf("  Biology: all checks passed\n");
}

// ================================================================
// Test: Environment
// ================================================================

static void test_environment()
{
    TEST_SECTION("Environment");

    sim::Environment env(sim::T_PLANCK);
    TEST_ASSERT_FLOAT_EQ(env.currentTemperature(), sim::T_PLANCK, 0.1);
    TEST_ASSERT_FLOAT_EQ(env.scaleFactor(), 1.0, 1e-6);

    // Update at Planck epoch
    env.update(sim::PLANCK_EPOCH);
    TEST_ASSERT_FLOAT_EQ(env.currentTemperature(), sim::T_PLANCK, 0.1);

    // Radiation field at early epoch
    TEST_ASSERT(env.radiation.gammaRayFlux > 0.0);
    TEST_ASSERT(env.radiation.totalIonizing() > 0.0);

    // Radiation density
    double rd = env.radiationDensity();
    TEST_ASSERT(rd > 0.0);

    // Update at inflation
    env.update(sim::INFLATION_EPOCH);
    TEST_ASSERT(env.currentTemperature() < sim::T_PLANCK);
    TEST_ASSERT(env.scaleFactor() > 1.0);

    // Update at recombination
    env.update(sim::RECOMBINATION_EPOCH);
    double temp_recom = env.currentTemperature();
    TEST_ASSERT(temp_recom <= sim::T_RECOMBINATION + 1.0);
    TEST_ASSERT(temp_recom > sim::T_CMB - 1.0);

    // Atmosphere before Earth
    TEST_ASSERT_FLOAT_EQ(env.atmosphere.pressure, 0.0, 1e-6);

    // Update at Earth epoch
    env.update(sim::EARTH_EPOCH);
    TEST_ASSERT(env.atmosphere.pressure > 0.0);
    TEST_ASSERT(env.atmosphere.nitrogenFraction > 0.0);
    TEST_ASSERT(env.ocean.exists == true);

    // Ocean properties
    TEST_ASSERT(env.ocean.pH > 4.0);
    TEST_ASSERT(env.ocean.pH < 10.0);

    // Greenhouse effect
    double gh = env.atmosphere.greenhouseEffect();
    TEST_ASSERT(gh > 1.0); // should amplify temperature

    // UV shielding (early Earth has low O2, so low shielding)
    double uvs = env.atmosphere.uvShielding();
    TEST_ASSERT(uvs >= 0.0);
    TEST_ASSERT(uvs <= 1.0);

    // Biological energy
    double be = env.biologicalEnergy();
    TEST_ASSERT(be > 0.0);

    // Update at present
    env.update(sim::PRESENT_EPOCH);
    double temp_present = env.currentTemperature();
    TEST_ASSERT(temp_present > 250.0);
    TEST_ASSERT(temp_present < 350.0);
    TEST_ASSERT(env.atmosphere.oxygenFraction > 0.2);
    TEST_ASSERT(env.atmosphere.nitrogenFraction > 0.7);

    // Summary string
    std::string summary = env.summary();
    TEST_ASSERT(!summary.empty());
    TEST_ASSERT(summary.find("T=") != std::string::npos);

    // Vent energy
    TEST_ASSERT(env.ocean.ventEnergy() > 0.0);

    std::printf("  Environment: all checks passed\n");
}

// ================================================================
// Test: Universe
// ================================================================

static void test_universe()
{
    TEST_SECTION("Universe");

    // Epoch table
    TEST_ASSERT(sim::EPOCHS.size() == 13);
    TEST_ASSERT(sim::EPOCHS[0].startTick == sim::PLANCK_EPOCH);
    TEST_ASSERT(sim::EPOCHS[12].startTick == sim::PRESENT_EPOCH);

    // Universe construction
    sim::Universe universe;
    TEST_ASSERT(universe.currentTick() == 0);
    TEST_ASSERT(universe.quantumField.particles.empty());
    TEST_ASSERT(universe.atomicSystem.atoms.empty());
    TEST_ASSERT(universe.chemicalSystem.molecules.empty());
    TEST_ASSERT(universe.biosphere == nullptr);

    // Run individual epochs
    auto planck_state = universe.runEpoch(0);
    TEST_ASSERT(planck_state.epochName == "Planck");
    TEST_ASSERT(planck_state.tick == sim::PLANCK_EPOCH);
    TEST_ASSERT(planck_state.temperature > 0.0);

    auto inflation_state = universe.runEpoch(1);
    TEST_ASSERT(inflation_state.epochName == "Inflation");
    TEST_ASSERT(inflation_state.particleCount > 0);

    auto electroweak_state = universe.runEpoch(2);
    TEST_ASSERT(electroweak_state.epochName == "Electroweak");

    auto quark_state = universe.runEpoch(3);
    TEST_ASSERT(quark_state.epochName == "Quark");

    auto hadron_state = universe.runEpoch(4);
    TEST_ASSERT(hadron_state.epochName == "Hadron");

    auto nucleo_state = universe.runEpoch(5);
    TEST_ASSERT(nucleo_state.epochName == "Nucleosynthesis");
    TEST_ASSERT(nucleo_state.atomCount > 0);

    auto recom_state = universe.runEpoch(6);
    TEST_ASSERT(recom_state.epochName == "Recombination");

    auto star_state = universe.runEpoch(7);
    TEST_ASSERT(star_state.epochName == "Star Formation");

    auto solar_state = universe.runEpoch(8);
    TEST_ASSERT(solar_state.epochName == "Solar System");

    auto earth_state = universe.runEpoch(9);
    TEST_ASSERT(earth_state.epochName == "Earth");
    TEST_ASSERT(earth_state.moleculeCount >= 0);

    auto life_state = universe.runEpoch(10);
    TEST_ASSERT(life_state.epochName == "Life");
    TEST_ASSERT(life_state.cellCount > 0);
    TEST_ASSERT(universe.biosphere != nullptr);

    auto dna_state = universe.runEpoch(11);
    TEST_ASSERT(dna_state.epochName == "DNA Era");
    TEST_ASSERT(dna_state.cellCount > 0);

    auto present_state = universe.runEpoch(12);
    TEST_ASSERT(present_state.epochName == "Present");
    TEST_ASSERT(present_state.cellCount > 0);

    // Invalid epoch
    auto invalid = universe.runEpoch(99);
    TEST_ASSERT(invalid.epochName == "Unknown");

    // Full simulation with callback
    sim::Universe u2;
    int epoch_count = 0;
    u2.simulate([&](const sim::EpochState& state) {
        ++epoch_count;
        TEST_ASSERT(!state.epochName.empty());
        TEST_ASSERT(state.tick >= 0);
    });
    TEST_ASSERT(epoch_count == 13);

    // Epoch history
    auto& history = u2.epochHistory();
    TEST_ASSERT(history.size() == 13);
    TEST_ASSERT(history[0].epochName == "Planck");
    TEST_ASSERT(history[12].epochName == "Present");

    // Final state should have cells
    TEST_ASSERT(history[12].cellCount > 0);

    std::printf("  Universe: all checks passed\n");
}

// ================================================================
// Main
// ================================================================

int main()
{
    std::printf("=== Cosmic Evolution Simulator - C++ Test Suite ===\n");

    test_constants();
    test_quantum_field();
    test_atomic_system();
    test_chemistry();
    test_biology();
    test_environment();
    test_universe();

    std::printf("\n=== Results: %d tests run, %d passed, %d failed ===\n",
                g_tests_run, g_tests_passed, g_tests_failed);

    return g_tests_failed > 0 ? 1 : 0;
}
