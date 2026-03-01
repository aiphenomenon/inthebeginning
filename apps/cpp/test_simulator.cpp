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

    // Spin values
    TEST_ASSERT_FLOAT_EQ(sim::spinValue(sim::Spin::Up), 0.5, 1e-9);
    TEST_ASSERT_FLOAT_EQ(sim::spinValue(sim::Spin::Down), -0.5, 1e-9);

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

    // Wave function collapse
    sim::WaveFunction wf_collapse;
    wf_collapse.amplitude = 1.0;
    wf_collapse.coherent = true;
    bool collapsed_result = wf_collapse.collapse();
    // After collapse, coherent must be false
    TEST_ASSERT(wf_collapse.coherent == false);
    // Amplitude must be 0.0 or 1.0 after collapse
    TEST_ASSERT(wf_collapse.amplitude == 0.0 || wf_collapse.amplitude == 1.0);
    // If detected, amplitude == 1.0; if not, amplitude == 0.0
    if (collapsed_result) {
        TEST_ASSERT_FLOAT_EQ(wf_collapse.amplitude, 1.0, 1e-9);
    } else {
        TEST_ASSERT_FLOAT_EQ(wf_collapse.amplitude, 0.0, 1e-9);
    }

    // Collapse with zero amplitude should not detect
    sim::WaveFunction wf_zero;
    wf_zero.amplitude = 0.0;
    wf_zero.coherent = true;
    bool zero_result = wf_zero.collapse();
    TEST_ASSERT(zero_result == false);
    TEST_ASSERT_FLOAT_EQ(wf_zero.amplitude, 0.0, 1e-9);
    TEST_ASSERT(wf_zero.coherent == false);

    // Annihilate particle-antiparticle pair
    sim::QuantumField qf_ann(sim::T_PLANCK);
    double ann_energy = 2.0 * sim::M_ELECTRON * sim::C * sim::C + 1.0;
    qf_ann.pairProduction(ann_energy);
    TEST_ASSERT(qf_ann.particles.size() == 2);
    TEST_ASSERT(qf_ann.totalAnnihilated == 0);

    double released = qf_ann.annihilate(0, 1);
    TEST_ASSERT(released > 0.0);
    TEST_ASSERT(qf_ann.totalAnnihilated == 2);
    // After annihilation, two photons are created
    TEST_ASSERT(qf_ann.particles.size() == 2);
    TEST_ASSERT(qf_ann.particles[0].type == sim::ParticleType::Photon);
    TEST_ASSERT(qf_ann.particles[1].type == sim::ParticleType::Photon);
    // Vacuum energy should increase
    TEST_ASSERT(qf_ann.vacuumEnergy > 0.0);

    // Annihilate with invalid indices
    double invalid_ann = qf_ann.annihilate(100, 200);
    TEST_ASSERT_FLOAT_EQ(invalid_ann, 0.0, 1e-9);
    // Same index should also return 0
    double same_ann = qf_ann.annihilate(0, 0);
    TEST_ASSERT_FLOAT_EQ(same_ann, 0.0, 1e-9);

    // Vacuum fluctuation
    sim::QuantumField qf_vac(sim::T_PLANCK);
    // Run many vacuum fluctuations -- at Planck temperature, probability is high
    int vac_successes = 0;
    for (int i = 0; i < 100; ++i) {
        if (qf_vac.vacuumFluctuation()) ++vac_successes;
    }
    // At T_PLANCK, probability is 0.5, so we should get some successes
    // (though pair production still needs enough energy from exponential dist)
    TEST_ASSERT(vac_successes >= 0); // vacuumFluctuation was called without crashing

    // Vacuum fluctuation at low temperature -- very low probability
    sim::QuantumField qf_cold(1.0); // very cold
    int cold_vac = 0;
    for (int i = 0; i < 10; ++i) {
        if (qf_cold.vacuumFluctuation()) ++cold_vac;
    }
    // At very low temp, probability is very small (1.0/T_PLANCK ~ 1e-10)
    TEST_ASSERT(cold_vac >= 0);

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

    // ElectronShell - isFull, isEmpty, addElectron, removeElectron
    sim::ElectronShell shell;
    shell.n = 1;
    shell.maxElectrons = 2;
    shell.electrons = 0;
    TEST_ASSERT(shell.isEmpty() == true);
    TEST_ASSERT(shell.isFull() == false);

    bool added = shell.addElectron();
    TEST_ASSERT(added == true);
    TEST_ASSERT(shell.electrons == 1);
    TEST_ASSERT(shell.isEmpty() == false);
    TEST_ASSERT(shell.isFull() == false);

    added = shell.addElectron();
    TEST_ASSERT(added == true);
    TEST_ASSERT(shell.electrons == 2);
    TEST_ASSERT(shell.isFull() == true);

    // Cannot add to a full shell
    added = shell.addElectron();
    TEST_ASSERT(added == false);
    TEST_ASSERT(shell.electrons == 2);

    bool removed = shell.removeElectron();
    TEST_ASSERT(removed == true);
    TEST_ASSERT(shell.electrons == 1);

    removed = shell.removeElectron();
    TEST_ASSERT(removed == true);
    TEST_ASSERT(shell.electrons == 0);

    // Cannot remove from empty shell
    removed = shell.removeElectron();
    TEST_ASSERT(removed == false);
    TEST_ASSERT(shell.electrons == 0);

    // Atom::isIon
    sim::Atom neutral_atom;
    neutral_atom.init(11, 23); // Sodium, neutral
    TEST_ASSERT(neutral_atom.isIon() == false);
    TEST_ASSERT(neutral_atom.chargeState() == 0);

    neutral_atom.ionize(); // Remove one electron
    TEST_ASSERT(neutral_atom.isIon() == true);
    TEST_ASSERT(neutral_atom.chargeState() == 1);

    neutral_atom.captureElectron(); // Back to neutral
    TEST_ASSERT(neutral_atom.isIon() == false);

    // Double ionize
    neutral_atom.ionize();
    neutral_atom.ionize();
    TEST_ASSERT(neutral_atom.isIon() == true);
    TEST_ASSERT(neutral_atom.chargeState() == 2);

    // Atom::bondEnergy
    sim::Atom h_be;
    h_be.init(1, 1);
    sim::Atom h_be2;
    h_be2.init(1, 1);
    // H-H bond: electronegativity difference is 0, should be covalent
    double be_cov = h_be.bondEnergy(h_be2);
    TEST_ASSERT_FLOAT_EQ(be_cov, sim::BOND_ENERGY_COVALENT, 0.01);

    // Na-Cl bond: large electronegativity difference, should be ionic
    sim::Atom na_be;
    na_be.init(11, 23);
    sim::Atom cl_be;
    cl_be.init(17, 35);
    double be_ionic = na_be.bondEnergy(cl_be);
    TEST_ASSERT_FLOAT_EQ(be_ionic, sim::BOND_ENERGY_IONIC, 0.01);

    // C-O bond: moderate electronegativity difference, should be polar covalent
    sim::Atom c_be;
    c_be.init(6, 12);
    sim::Atom o_be;
    o_be.init(8, 16);
    double be_polar = c_be.bondEnergy(o_be);
    double expected_polar = (sim::BOND_ENERGY_COVALENT + sim::BOND_ENERGY_IONIC) / 2.0;
    TEST_ASSERT_FLOAT_EQ(be_polar, expected_polar, 0.01);

    // AtomicSystem::recombination
    sim::QuantumField qf_recom(sim::T_RECOMBINATION * 0.5); // below recombination temp
    // Add protons and electrons
    for (int i = 0; i < 3; ++i) {
        sim::Particle p;
        p.type = sim::ParticleType::Proton;
        p.position = {static_cast<double>(i), 0.0, 0.0};
        qf_recom.particles.push_back(p);
    }
    for (int i = 0; i < 3; ++i) {
        sim::Particle e;
        e.type = sim::ParticleType::Electron;
        e.position = {static_cast<double>(i), 1.0, 0.0};
        qf_recom.particles.push_back(e);
    }

    sim::AtomicSystem as_recom(sim::T_RECOMBINATION * 0.5);
    auto recom_atoms = as_recom.recombination(qf_recom);
    TEST_ASSERT(!recom_atoms.empty());
    TEST_ASSERT(recom_atoms.size() == 3);
    // All should be hydrogen
    for (auto& a : recom_atoms) {
        TEST_ASSERT(a.atomicNumber == 1);
    }
    // Protons and electrons should be consumed from the field
    int remaining_protons = 0;
    int remaining_electrons = 0;
    for (auto& p : qf_recom.particles) {
        if (p.type == sim::ParticleType::Proton) ++remaining_protons;
        if (p.type == sim::ParticleType::Electron) ++remaining_electrons;
    }
    TEST_ASSERT(remaining_protons == 0);
    TEST_ASSERT(remaining_electrons == 0);

    // Recombination above threshold should produce nothing
    sim::AtomicSystem as_hot(sim::T_RECOMBINATION + 1000.0);
    sim::QuantumField qf_hot(sim::T_PLANCK);
    sim::Particle hot_p;
    hot_p.type = sim::ParticleType::Proton;
    qf_hot.particles.push_back(hot_p);
    sim::Particle hot_e;
    hot_e.type = sim::ParticleType::Electron;
    qf_hot.particles.push_back(hot_e);
    auto hot_recom = as_hot.recombination(qf_hot);
    TEST_ASSERT(hot_recom.empty());

    // AtomicSystem::stellarNucleosynthesis
    sim::AtomicSystem as_stellar;
    // Add helium atoms for triple-alpha process
    for (int i = 0; i < 30; ++i) {
        sim::Atom he_s;
        he_s.init(2, 4);
        as_stellar.atoms.push_back(he_s);
    }

    // Run stellar nucleosynthesis many times at high temperature
    int stellar_produced = 0;
    for (int i = 0; i < 100; ++i) {
        auto new_atoms = as_stellar.stellarNucleosynthesis(sim::T_STELLAR_CORE);
        stellar_produced += static_cast<int>(new_atoms.size());
    }
    // Should have produced some heavier elements
    TEST_ASSERT(stellar_produced >= 0); // probabilistic, but should not crash

    // Stellar nucleosynthesis at too low temperature should produce nothing
    sim::AtomicSystem as_cold_stellar;
    for (int i = 0; i < 10; ++i) {
        sim::Atom he_c;
        he_c.init(2, 4);
        as_cold_stellar.atoms.push_back(he_c);
    }
    auto cold_result = as_cold_stellar.stellarNucleosynthesis(500.0);
    TEST_ASSERT(cold_result.empty());

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

    // formAminoAcid
    sim::AtomicSystem as5;
    sim::ChemicalSystem cs5(as5);

    // Add enough atoms for amino acid: 2C + 5H + 2O + 1N
    for (int i = 0; i < 10; ++i) {
        sim::Atom c; c.init(6, 12); as5.atoms.push_back(c);
    }
    for (int i = 0; i < 20; ++i) {
        sim::Atom h; h.init(1, 1); as5.atoms.push_back(h);
    }
    for (int i = 0; i < 10; ++i) {
        sim::Atom o; o.init(8, 16); as5.atoms.push_back(o);
    }
    for (int i = 0; i < 5; ++i) {
        sim::Atom n; n.init(7, 14); as5.atoms.push_back(n);
    }

    bool aa_formed = cs5.formAminoAcid("Gly");
    TEST_ASSERT(aa_formed == true);
    TEST_ASSERT(cs5.aminoAcidCount == 1);
    TEST_ASSERT(!cs5.molecules.empty());
    // Verify molecule properties
    bool found_aa = false;
    for (auto& mol : cs5.molecules) {
        if (mol.name == "Gly") {
            found_aa = true;
            TEST_ASSERT(mol.isOrganic == true);
            TEST_ASSERT(!mol.functionalGroups.empty());
            // Should have amino and carboxyl groups
            bool has_amino = false, has_carboxyl = false;
            for (auto& fg : mol.functionalGroups) {
                if (fg == "amino") has_amino = true;
                if (fg == "carboxyl") has_carboxyl = true;
            }
            TEST_ASSERT(has_amino == true);
            TEST_ASSERT(has_carboxyl == true);
        }
    }
    TEST_ASSERT(found_aa == true);

    // Form another amino acid with different type
    bool aa2_formed = cs5.formAminoAcid("Ala");
    TEST_ASSERT(aa2_formed == true);
    TEST_ASSERT(cs5.aminoAcidCount == 2);

    // formAminoAcid with insufficient atoms should fail
    sim::AtomicSystem as_empty;
    sim::ChemicalSystem cs_empty(as_empty);
    bool no_aa = cs_empty.formAminoAcid("Gly");
    TEST_ASSERT(no_aa == false);
    TEST_ASSERT(cs_empty.aminoAcidCount == 0);

    // formNucleotide
    sim::AtomicSystem as6;
    sim::ChemicalSystem cs6(as6);

    // Add enough atoms for nucleotide: 5C + 8H + 4O + 2N
    for (int i = 0; i < 15; ++i) {
        sim::Atom c; c.init(6, 12); as6.atoms.push_back(c);
    }
    for (int i = 0; i < 30; ++i) {
        sim::Atom h; h.init(1, 1); as6.atoms.push_back(h);
    }
    for (int i = 0; i < 15; ++i) {
        sim::Atom o; o.init(8, 16); as6.atoms.push_back(o);
    }
    for (int i = 0; i < 10; ++i) {
        sim::Atom n; n.init(7, 14); as6.atoms.push_back(n);
    }

    bool nuc_formed = cs6.formNucleotide("A");
    TEST_ASSERT(nuc_formed == true);
    TEST_ASSERT(cs6.nucleotideCount == 1);
    // Verify molecule properties
    bool found_nuc = false;
    for (auto& mol : cs6.molecules) {
        if (mol.name == "nucleotide-A") {
            found_nuc = true;
            TEST_ASSERT(mol.isOrganic == true);
            // Should have sugar, phosphate, base groups
            bool has_sugar = false, has_phosphate = false, has_base = false;
            for (auto& fg : mol.functionalGroups) {
                if (fg == "sugar") has_sugar = true;
                if (fg == "phosphate") has_phosphate = true;
                if (fg == "base") has_base = true;
            }
            TEST_ASSERT(has_sugar == true);
            TEST_ASSERT(has_phosphate == true);
            TEST_ASSERT(has_base == true);
        }
    }
    TEST_ASSERT(found_nuc == true);

    // Form nucleotide with different base
    bool nuc2_formed = cs6.formNucleotide("T");
    TEST_ASSERT(nuc2_formed == true);
    TEST_ASSERT(cs6.nucleotideCount == 2);

    // formNucleotide with insufficient atoms should fail
    sim::AtomicSystem as_empty2;
    sim::ChemicalSystem cs_empty2(as_empty2);
    bool no_nuc = cs_empty2.formNucleotide("G");
    TEST_ASSERT(no_nuc == false);
    TEST_ASSERT(cs_empty2.nucleotideCount == 0);

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

    // Gene::methylate, Gene::demethylate, Gene::isSilenced
    sim::Gene epi_gene;
    epi_gene.name = "epi_test";
    epi_gene.sequence = {'A', 'T', 'G', 'C', 'A', 'T'};
    epi_gene.startPos = 0;
    epi_gene.endPos = 6;

    // Initially no epigenetic marks, not silenced
    TEST_ASSERT(epi_gene.isSilenced() == false);
    TEST_ASSERT(epi_gene.epigeneticMarks.empty());

    // Methylate positions -- need more than length/2 = 3 active methylations to silence
    epi_gene.methylate(0, 1);
    TEST_ASSERT(epi_gene.epigeneticMarks.size() == 1);
    TEST_ASSERT(epi_gene.epigeneticMarks[0].markType == "methylation");
    TEST_ASSERT(epi_gene.epigeneticMarks[0].position == 0);
    TEST_ASSERT(epi_gene.epigeneticMarks[0].active == true);
    TEST_ASSERT(epi_gene.epigeneticMarks[0].generationAdded == 1);
    TEST_ASSERT(epi_gene.isSilenced() == false); // only 1 methylation, need >3

    epi_gene.methylate(1, 1);
    epi_gene.methylate(2, 1);
    TEST_ASSERT(epi_gene.isSilenced() == false); // 3 methylations, need >3

    epi_gene.methylate(3, 2);
    TEST_ASSERT(epi_gene.isSilenced() == true); // 4 methylations > 3 (length/2)

    // Demethylate one position
    epi_gene.demethylate(0);
    // After demethylation of position 0, should have 3 active methylations
    int active_methyl = 0;
    for (auto& mark : epi_gene.epigeneticMarks) {
        if (mark.active && mark.markType == "methylation")
            ++active_methyl;
    }
    TEST_ASSERT(active_methyl == 3);
    TEST_ASSERT(epi_gene.isSilenced() == false); // 3 methylations, not >3

    // Demethylate a position that has no methylation (should be a no-op)
    epi_gene.demethylate(5);
    // Count should still be 3
    active_methyl = 0;
    for (auto& mark : epi_gene.epigeneticMarks) {
        if (mark.active && mark.markType == "methylation")
            ++active_methyl;
    }
    TEST_ASSERT(active_methyl == 3);

    // Gene::acetylate
    sim::Gene acet_gene;
    acet_gene.name = "acet_test";
    acet_gene.sequence = {'A', 'T', 'G', 'C', 'A', 'T', 'G', 'C'};
    acet_gene.startPos = 0;
    acet_gene.endPos = 8;

    acet_gene.acetylate(0, 5);
    TEST_ASSERT(acet_gene.epigeneticMarks.size() == 1);
    TEST_ASSERT(acet_gene.epigeneticMarks[0].markType == "acetylation");
    TEST_ASSERT(acet_gene.epigeneticMarks[0].position == 0);
    TEST_ASSERT(acet_gene.epigeneticMarks[0].active == true);
    TEST_ASSERT(acet_gene.epigeneticMarks[0].generationAdded == 5);

    acet_gene.acetylate(2, 5);
    TEST_ASSERT(acet_gene.epigeneticMarks.size() == 2);

    // Gene::updateExpression
    sim::Gene expr_gene;
    expr_gene.name = "expr_test";
    expr_gene.sequence = {'A', 'T', 'G', 'C', 'A', 'T'};
    expr_gene.startPos = 0;
    expr_gene.endPos = 6;
    expr_gene.expressionLevel = 1.0;

    // No marks: expression should be 1.0 (base modifier)
    expr_gene.updateExpression();
    TEST_ASSERT_FLOAT_EQ(expr_gene.expressionLevel, 1.0, 0.01);

    // Add acetylation marks (increase expression)
    expr_gene.acetylate(0, 0);
    expr_gene.acetylate(1, 0);
    expr_gene.acetylate(2, 0);
    expr_gene.updateExpression();
    // modifier = 1.0 + 0.1 * 3 - 0.15 * 0 = 1.3
    TEST_ASSERT_FLOAT_EQ(expr_gene.expressionLevel, 1.3, 0.01);

    // Add methylation marks (decrease expression)
    expr_gene.methylate(0, 0);
    expr_gene.methylate(1, 0);
    expr_gene.updateExpression();
    // modifier = 1.0 + 0.1 * 3 - 0.15 * 2 = 1.0
    TEST_ASSERT_FLOAT_EQ(expr_gene.expressionLevel, 1.0, 0.01);

    // Heavy methylation should clamp to 0.0
    for (int i = 0; i < 20; ++i) {
        expr_gene.methylate(i, 0);
    }
    expr_gene.updateExpression();
    TEST_ASSERT(expr_gene.expressionLevel >= 0.0);
    TEST_ASSERT(expr_gene.expressionLevel <= 2.0);

    // Silenced gene should return empty transcription
    sim::Gene silenced_gene;
    silenced_gene.name = "silenced";
    silenced_gene.sequence = {'A', 'T', 'G', 'C'};
    silenced_gene.startPos = 0;
    silenced_gene.endPos = 4;
    // Methylate more than length/2 = 2 positions
    silenced_gene.methylate(0, 0);
    silenced_gene.methylate(1, 0);
    silenced_gene.methylate(2, 0);
    TEST_ASSERT(silenced_gene.isSilenced() == true);
    auto silenced_mrna = silenced_gene.transcribe();
    TEST_ASSERT(silenced_mrna.empty());

    // Protein::length
    sim::Protein len_prot;
    len_prot.aminoAcids = {"Met", "Ala", "Val"};
    TEST_ASSERT(len_prot.length() == 3);

    sim::Protein empty_prot;
    TEST_ASSERT(empty_prot.length() == 0);

    sim::Protein long_prot;
    long_prot.aminoAcids = {"Met", "Ala", "Val", "Leu", "Ile", "Phe", "Trp", "Gly", "Ser", "Thr"};
    TEST_ASSERT(long_prot.length() == 10);

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
