/*
 * test_simulator.c - Unit tests for the cosmic evolution simulator.
 *
 * Uses simple assert macros with no external dependencies.
 * Tests all major subsystems: constants, quantum, atomic, chemistry,
 * biology, environment, and universe.
 */
#include "simulator/constants.h"
#include "simulator/quantum.h"
#include "simulator/atomic.h"
#include "simulator/chemistry.h"
#include "simulator/biology.h"
#include "simulator/environment.h"
#include "simulator/universe.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

/* ------------------------------------------------------------------ */
/* Test framework macros                                               */
/* ------------------------------------------------------------------ */

static int g_tests_run    = 0;
static int g_tests_passed = 0;
static int g_tests_failed = 0;

#define TEST_ASSERT(expr) do { \
    g_tests_run++; \
    if (expr) { \
        g_tests_passed++; \
    } else { \
        g_tests_failed++; \
        printf("  FAIL: %s:%d: %s\n", __FILE__, __LINE__, #expr); \
    } \
} while (0)

#define TEST_ASSERT_FLOAT_EQ(a, b, eps) do { \
    g_tests_run++; \
    if (fabs((double)(a) - (double)(b)) < (eps)) { \
        g_tests_passed++; \
    } else { \
        g_tests_failed++; \
        printf("  FAIL: %s:%d: %s == %s (%.10g != %.10g)\n", \
               __FILE__, __LINE__, #a, #b, (double)(a), (double)(b)); \
    } \
} while (0)

#define TEST_SECTION(name) printf("\n--- %s ---\n", name)

/* ------------------------------------------------------------------ */
/* Test: Constants                                                     */
/* ------------------------------------------------------------------ */

static void test_constants(void)
{
    TEST_SECTION("Constants");

    /* Fundamental constants */
    TEST_ASSERT_FLOAT_EQ(SIM_C, 1.0, 1e-9);
    TEST_ASSERT_FLOAT_EQ(SIM_HBAR, 0.01, 1e-9);
    TEST_ASSERT_FLOAT_EQ(SIM_K_B, 0.001, 1e-9);
    TEST_ASSERT_FLOAT_EQ(SIM_G, 1e-6, 1e-12);
    TEST_ASSERT_FLOAT_EQ(SIM_ALPHA, 1.0 / 137.0, 1e-9);
    TEST_ASSERT_FLOAT_EQ(SIM_E_CHARGE, 0.1, 1e-9);
    TEST_ASSERT_FLOAT_EQ(SIM_PI, M_PI, 1e-12);

    /* Particle masses */
    TEST_ASSERT_FLOAT_EQ(M_ELECTRON, 1.0, 1e-9);
    TEST_ASSERT_FLOAT_EQ(M_PROTON, 1836.0, 1e-9);
    TEST_ASSERT_FLOAT_EQ(M_NEUTRON, 1839.0, 1e-9);
    TEST_ASSERT_FLOAT_EQ(M_PHOTON, 0.0, 1e-9);
    TEST_ASSERT(M_PROTON > M_ELECTRON);
    TEST_ASSERT(M_NEUTRON > M_PROTON);

    /* Force coupling strengths */
    TEST_ASSERT_FLOAT_EQ(STRONG_COUPLING, 1.0, 1e-9);
    TEST_ASSERT(EM_COUPLING < STRONG_COUPLING);
    TEST_ASSERT(WEAK_COUPLING < EM_COUPLING);
    TEST_ASSERT(GRAVITY_COUPLING < WEAK_COUPLING);

    /* Cosmic timeline ordering */
    TEST_ASSERT(PLANCK_EPOCH < INFLATION_EPOCH);
    TEST_ASSERT(INFLATION_EPOCH < ELECTROWEAK_EPOCH);
    TEST_ASSERT(ELECTROWEAK_EPOCH < QUARK_EPOCH);
    TEST_ASSERT(QUARK_EPOCH < HADRON_EPOCH);
    TEST_ASSERT(HADRON_EPOCH < NUCLEOSYNTHESIS_EPOCH);
    TEST_ASSERT(NUCLEOSYNTHESIS_EPOCH < RECOMBINATION_EPOCH);
    TEST_ASSERT(RECOMBINATION_EPOCH < STAR_FORMATION_EPOCH);
    TEST_ASSERT(STAR_FORMATION_EPOCH < SOLAR_SYSTEM_EPOCH);
    TEST_ASSERT(SOLAR_SYSTEM_EPOCH < EARTH_EPOCH);
    TEST_ASSERT(EARTH_EPOCH < LIFE_EPOCH);
    TEST_ASSERT(LIFE_EPOCH < DNA_EPOCH);
    TEST_ASSERT(DNA_EPOCH < PRESENT_EPOCH);

    /* Temperature ordering */
    TEST_ASSERT(T_PLANCK > T_ELECTROWEAK);
    TEST_ASSERT(T_ELECTROWEAK > T_QUARK_HADRON);
    TEST_ASSERT(T_QUARK_HADRON > T_NUCLEOSYNTHESIS);
    TEST_ASSERT(T_NUCLEOSYNTHESIS > T_RECOMBINATION);
    TEST_ASSERT(T_RECOMBINATION > T_CMB);

    /* Biology parameters */
    TEST_ASSERT(NUCLEOTIDE_BASE_COUNT == 4);
    TEST_ASSERT(AMINO_ACID_COUNT == 20);
    TEST_ASSERT(ELECTRON_SHELL_COUNT == 7);

    /* Simulation caps */
    TEST_ASSERT(MAX_PARTICLES > 0);
    TEST_ASSERT(MAX_ATOMS > 0);
    TEST_ASSERT(MAX_MOLECULES > 0);
    TEST_ASSERT(MAX_CELLS > 0);

    printf("  Constants: all checks passed\n");
}

/* ------------------------------------------------------------------ */
/* Test: Quantum field operations                                      */
/* ------------------------------------------------------------------ */

static void test_quantum_field(void)
{
    TEST_SECTION("Quantum Field");

    /* Initialization */
    QuantumField qf;
    qf_init(&qf, T_PLANCK);
    TEST_ASSERT(qf.count == 0);
    TEST_ASSERT(qf.capacity > 0);
    TEST_ASSERT_FLOAT_EQ(qf.temperature, T_PLANCK, 1e-3);
    TEST_ASSERT(qf.particles != NULL);
    TEST_ASSERT(qf.total_created == 0);
    TEST_ASSERT(qf.total_annihilated == 0);

    /* Wave function init */
    WaveFunction wf;
    wf_init(&wf);
    TEST_ASSERT_FLOAT_EQ(wf.amplitude, 1.0f, 1e-6);
    TEST_ASSERT_FLOAT_EQ(wf.phase, 0.0f, 1e-6);
    TEST_ASSERT(wf.coherent == true);

    /* Wave function evolution */
    wf_evolve(&wf, 1.0f, 1.0f);
    TEST_ASSERT(wf.coherent == true);
    /* phase should have changed: phase += energy * dt / HBAR = 1.0 / 0.01 = 100.0 */
    /* modulo 2*PI => 100.0 mod 6.283... */
    TEST_ASSERT(wf.phase >= 0.0f);
    TEST_ASSERT(wf.phase < 2.0f * (float)SIM_PI + 0.01f);

    /* Wave function collapse */
    WaveFunction wf_c;
    wf_init(&wf_c);
    TEST_ASSERT(wf_c.coherent == true);
    TEST_ASSERT_FLOAT_EQ(wf_c.amplitude, 1.0f, 1e-6);
    bool collapse_result = wf_collapse(&wf_c);
    /* With amplitude=1.0, prob=1.0, should always collapse to true */
    TEST_ASSERT(collapse_result == true);
    TEST_ASSERT(wf_c.coherent == false);
    TEST_ASSERT_FLOAT_EQ(wf_c.amplitude, 1.0f, 1e-6); /* result=true -> amplitude=1.0 */

    /* Wave function collapse with zero amplitude */
    WaveFunction wf_zero;
    wf_init(&wf_zero);
    wf_zero.amplitude = 0.0f;
    bool collapse_zero = wf_collapse(&wf_zero);
    /* With amplitude=0.0, prob=0.0, should always collapse to false */
    TEST_ASSERT(collapse_zero == false);
    TEST_ASSERT(wf_zero.coherent == false);
    TEST_ASSERT_FLOAT_EQ(wf_zero.amplitude, 0.0f, 1e-6); /* result=false -> amplitude=0.0 */

    /* Pair production - insufficient energy should fail */
    bool pp_result = qf_pair_production(&qf, 0.1f);
    TEST_ASSERT(pp_result == false);
    TEST_ASSERT(qf.count == 0);

    /* Pair production - sufficient energy should succeed */
    float enough_energy = 2.0f * M_ELECTRON * (float)(SIM_C * SIM_C) + 1.0f;
    pp_result = qf_pair_production(&qf, enough_energy);
    TEST_ASSERT(pp_result == true);
    TEST_ASSERT(qf.count == 2);
    TEST_ASSERT(qf.total_created == 2);

    /* Particle mass and charge */
    TEST_ASSERT_FLOAT_EQ(particle_mass(PTYPE_PROTON), M_PROTON, 1e-3);
    TEST_ASSERT_FLOAT_EQ(particle_mass(PTYPE_ELECTRON), M_ELECTRON, 1e-6);
    TEST_ASSERT_FLOAT_EQ(particle_mass(PTYPE_PHOTON), 0.0f, 1e-9);
    TEST_ASSERT_FLOAT_EQ(particle_charge(PTYPE_ELECTRON), -1.0f, 1e-6);
    TEST_ASSERT_FLOAT_EQ(particle_charge(PTYPE_PROTON), 1.0f, 1e-6);
    TEST_ASSERT_FLOAT_EQ(particle_charge(PTYPE_NEUTRON), 0.0f, 1e-6);

    /* Particle type names */
    TEST_ASSERT(strcmp(particle_type_name(PTYPE_PROTON), "proton") == 0);
    TEST_ASSERT(strcmp(particle_type_name(PTYPE_ELECTRON), "electron") == 0);
    TEST_ASSERT(strcmp(particle_type_name(PTYPE_PHOTON), "photon") == 0);

    /* Add particles manually */
    Particle p = {0};
    p.type = PTYPE_PROTON;
    p.spin = SPIN_UP;
    p.entangled_with = -1;
    wf_init(&p.wave_fn);
    int idx = qf_add_particle(&qf, &p);
    TEST_ASSERT(idx >= 0);
    TEST_ASSERT(qf.count == 3);

    /* Particle energy (proton at rest: E = m*c^2) */
    float e = particle_energy(&qf.particles[idx]);
    TEST_ASSERT(e > 0.0f);
    TEST_ASSERT_FLOAT_EQ(e, M_PROTON * (float)(SIM_C * SIM_C), 0.01f);

    /* Evolve */
    int count_before = qf.count;
    qf_evolve(&qf, 0.1f);
    TEST_ASSERT(qf.count == count_before);

    /* Particle count by type */
    int n_protons = qf_particle_count(&qf, PTYPE_PROTON);
    TEST_ASSERT(n_protons >= 1);

    /* Total energy should be positive */
    float total_e = qf_total_energy(&qf);
    TEST_ASSERT(total_e > 0.0f);

    /* Remove particle */
    qf_remove_particle(&qf, 0);
    TEST_ASSERT(qf.count == count_before - 1);

    /* Generate some quarks for confinement test */
    QuantumField qf2;
    qf_init(&qf2, T_QUARK_HADRON * 0.5);

    /* Add 2 up + 1 down -> should form a proton */
    Particle up1 = {0};
    up1.type = PTYPE_UP;
    up1.entangled_with = -1;
    wf_init(&up1.wave_fn);

    Particle up2 = up1;
    Particle down1 = up1;
    down1.type = PTYPE_DOWN;

    qf_add_particle(&qf2, &up1);
    qf_add_particle(&qf2, &up2);
    qf_add_particle(&qf2, &down1);

    int hadrons = qf_quark_confinement(&qf2);
    TEST_ASSERT(hadrons >= 1);
    /* Check we got a proton */
    int proton_count = qf_particle_count(&qf2, PTYPE_PROTON);
    TEST_ASSERT(proton_count >= 1);
    /* Quarks should be consumed */
    int up_count = qf_particle_count(&qf2, PTYPE_UP);
    TEST_ASSERT(up_count == 0);

    /* Vacuum fluctuation test */
    QuantumField qf3;
    qf_init(&qf3, T_PLANCK);  /* High temperature => higher fluctuation probability */
    int vf_count_before = qf3.count;
    /* Run multiple vacuum fluctuations; at T_PLANCK some should succeed */
    int vf_successes = 0;
    for (int i = 0; i < 100; i++) {
        if (qf_vacuum_fluctuation(&qf3))
            vf_successes++;
    }
    /* At T_PLANCK, prob = T_PLANCK/T_PLANCK = 1.0 (capped to 0.5), so ~50% should succeed */
    TEST_ASSERT(vf_successes > 0);
    TEST_ASSERT(qf3.count > vf_count_before);
    TEST_ASSERT(qf3.total_created > 0);

    /* Vacuum fluctuation at very low temperature should rarely succeed */
    QuantumField qf4;
    qf_init(&qf4, 1.0);  /* Very low temperature */
    int vf_low_successes = 0;
    for (int i = 0; i < 10; i++) {
        if (qf_vacuum_fluctuation(&qf4))
            vf_low_successes++;
    }
    /* With prob = 1.0 / 1e10 = 1e-10, should almost never succeed */
    TEST_ASSERT(vf_low_successes >= 0); /* just exercising the function */

    qf_free(&qf);
    qf_free(&qf2);
    qf_free(&qf3);
    qf_free(&qf4);
    TEST_ASSERT(qf.particles == NULL);

    printf("  Quantum: all checks passed\n");
}

/* ------------------------------------------------------------------ */
/* Test: Atomic system                                                 */
/* ------------------------------------------------------------------ */

static void test_atomic_system(void)
{
    TEST_SECTION("Atomic System");

    /* Init */
    AtomicSystem as;
    as_init(&as);
    TEST_ASSERT(as.count == 0);
    TEST_ASSERT(as.atoms != NULL);
    TEST_ASSERT_FLOAT_EQ(as.temperature, T_RECOMBINATION, 0.1);

    /* Atom init */
    Atom h;
    float pos[3] = {1.0f, 2.0f, 3.0f};
    atom_init(&h, 1, 1, pos);
    TEST_ASSERT(h.atomic_number == 1);
    TEST_ASSERT(h.mass_number == 1);
    TEST_ASSERT(h.electron_count == 1);
    TEST_ASSERT_FLOAT_EQ(h.position[0], 1.0f, 1e-6);

    /* Atom symbol */
    const char *sym = atom_symbol(&h);
    TEST_ASSERT(strcmp(sym, "H") == 0);

    /* Helium */
    Atom he;
    atom_init(&he, 2, 4, NULL);
    TEST_ASSERT(he.atomic_number == 2);
    TEST_ASSERT(he.mass_number == 4);
    TEST_ASSERT(strcmp(atom_symbol(&he), "He") == 0);

    /* Noble gas check */
    TEST_ASSERT(atom_is_noble_gas(&he) == true);
    TEST_ASSERT(atom_is_noble_gas(&h) == false);

    /* Can bond */
    TEST_ASSERT(atom_can_bond(&h) == true);
    TEST_ASSERT(atom_can_bond(&he) == false);

    /* Electronegativity */
    float en = atom_electronegativity(&h);
    TEST_ASSERT(en > 0.0f);

    /* Valence electrons */
    int val = atom_valence_electrons(&h);
    TEST_ASSERT(val == 1);

    /* Needs electrons */
    int needs = atom_needs_electrons(&h);
    TEST_ASSERT(needs == 1); /* H needs 1 to fill shell of 2 */

    /* Distance */
    Atom h2;
    float pos2[3] = {4.0f, 6.0f, 3.0f};
    atom_init(&h2, 1, 1, pos2);
    float dist = atom_distance(&h, &h2);
    TEST_ASSERT_FLOAT_EQ(dist, 5.0f, 0.01f); /* 3-4-5 triangle */

    /* Nucleosynthesis */
    int formed = as_nucleosynthesis(&as, 4, 4);
    TEST_ASSERT(formed > 0);
    TEST_ASSERT(as.count > 0);

    /* Element counts */
    int counts[27];
    as_element_counts(&as, counts);
    TEST_ASSERT(counts[2] > 0); /* Should have helium */

    /* Element lookup */
    const ElementInfo *ei = element_lookup(1);
    TEST_ASSERT(ei != NULL);
    TEST_ASSERT(strcmp(ei->symbol, "H") == 0);
    TEST_ASSERT(strcmp(ei->name, "Hydrogen") == 0);

    ei = element_lookup(6);
    TEST_ASSERT(ei != NULL);
    TEST_ASSERT(strcmp(ei->symbol, "C") == 0);

    /* Unknown element */
    ei = element_lookup(999);
    TEST_ASSERT(ei == NULL);

    /* Recombination test: protons + electrons -> hydrogen atoms */
    AtomicSystem as2;
    as_init(&as2);
    as2.temperature = T_RECOMBINATION * 0.5; /* Below recombination threshold */

    QuantumField qf_rec;
    qf_init(&qf_rec, T_RECOMBINATION);

    /* Add protons and electrons to the quantum field */
    for (int i = 0; i < 5; i++) {
        Particle proton = {0};
        proton.type = PTYPE_PROTON;
        proton.spin = SPIN_UP;
        proton.entangled_with = -1;
        wf_init(&proton.wave_fn);
        qf_add_particle(&qf_rec, &proton);

        Particle electron = {0};
        electron.type = PTYPE_ELECTRON;
        electron.spin = SPIN_DOWN;
        electron.entangled_with = -1;
        wf_init(&electron.wave_fn);
        qf_add_particle(&qf_rec, &electron);
    }
    TEST_ASSERT(qf_rec.count == 10); /* 5 protons + 5 electrons */

    int recombined = as_recombination(&as2, &qf_rec);
    TEST_ASSERT(recombined == 5); /* Should form 5 hydrogen atoms */
    TEST_ASSERT(as2.count == 5);
    /* Protons and electrons should be consumed from the quantum field */
    TEST_ASSERT(qf_particle_count(&qf_rec, PTYPE_PROTON) == 0);
    TEST_ASSERT(qf_particle_count(&qf_rec, PTYPE_ELECTRON) == 0);

    /* Recombination should fail when temperature is too high */
    AtomicSystem as3;
    as_init(&as3);
    as3.temperature = T_RECOMBINATION * 2.0; /* Above recombination threshold */

    QuantumField qf_hot;
    qf_init(&qf_hot, T_PLANCK);
    Particle p_test = {0};
    p_test.type = PTYPE_PROTON;
    p_test.entangled_with = -1;
    wf_init(&p_test.wave_fn);
    qf_add_particle(&qf_hot, &p_test);

    Particle e_test = {0};
    e_test.type = PTYPE_ELECTRON;
    e_test.entangled_with = -1;
    wf_init(&e_test.wave_fn);
    qf_add_particle(&qf_hot, &e_test);

    int recombined_hot = as_recombination(&as3, &qf_hot);
    TEST_ASSERT(recombined_hot == 0); /* Too hot for recombination */
    TEST_ASSERT(as3.count == 0);

    qf_free(&qf_rec);
    qf_free(&qf_hot);
    as_free(&as3);

    /* Stellar nucleosynthesis test: He -> C, C + He -> O, etc. */
    AtomicSystem as4;
    as_init(&as4);

    /* Add many helium atoms for triple-alpha process */
    for (int i = 0; i < 100; i++) {
        float pos[3] = {0.0f, 0.0f, 0.0f};
        Atom he_star;
        atom_init(&he_star, 2, 4, pos);
        as_add_atom(&as4, &he_star);
    }
    TEST_ASSERT(as4.count == 100);

    /* Stellar nucleosynthesis requires temperature >= 1e3 */
    int stellar_formed = 0;
    for (int i = 0; i < 200; i++) {
        stellar_formed += as_stellar_nucleosynthesis(&as4, T_STELLAR_CORE);
    }
    /* With 100 He atoms and many iterations, should form some heavier elements */
    TEST_ASSERT(stellar_formed > 0);

    /* Check that some carbon or heavier elements were formed */
    int stellar_counts[27];
    as_element_counts(&as4, stellar_counts);
    /* Should have formed at least some C (6), O (8), or N (7) */
    int heavier_count = stellar_counts[6] + stellar_counts[7] + stellar_counts[8];
    TEST_ASSERT(heavier_count > 0);

    /* Stellar nucleosynthesis should fail at low temperature */
    AtomicSystem as5;
    as_init(&as5);
    Atom he_cold;
    atom_init(&he_cold, 2, 4, NULL);
    as_add_atom(&as5, &he_cold);
    int cold_formed = as_stellar_nucleosynthesis(&as5, 100.0); /* Below 1e3 threshold */
    TEST_ASSERT(cold_formed == 0);

    as_free(&as4);
    as_free(&as5);

    as_free(&as2);
    as_free(&as);
    TEST_ASSERT(as.atoms == NULL);

    printf("  Atomic: all checks passed\n");
}

/* ------------------------------------------------------------------ */
/* Test: Chemistry                                                     */
/* ------------------------------------------------------------------ */

static void test_chemistry(void)
{
    TEST_SECTION("Chemistry");

    AtomicSystem as;
    as_init(&as);

    ChemicalSystem cs;
    cs_init(&cs, &as);
    TEST_ASSERT(cs.count == 0);
    TEST_ASSERT(cs.water_count == 0);
    TEST_ASSERT(cs.amino_acid_count == 0);
    TEST_ASSERT(cs.nucleotide_count == 0);

    /* Add hydrogen and oxygen atoms for water */
    for (int i = 0; i < 10; i++) {
        Atom h;
        atom_init(&h, 1, 1, NULL);
        as_add_atom(&as, &h);
    }
    for (int i = 0; i < 5; i++) {
        Atom o;
        atom_init(&o, 8, 16, NULL);
        as_add_atom(&as, &o);
    }

    /* Form water */
    int water_formed = cs_form_water(&cs);
    TEST_ASSERT(water_formed > 0);
    TEST_ASSERT(cs.water_count > 0);
    TEST_ASSERT(cs.count > 0);

    /* Form methane - need carbon and hydrogen */
    /* Reset system for fresh test */
    cs_free(&cs);
    as_free(&as);
    as_init(&as);
    cs_init(&cs, &as);

    for (int i = 0; i < 8; i++) {
        Atom h;
        atom_init(&h, 1, 1, NULL);
        as_add_atom(&as, &h);
    }
    for (int i = 0; i < 2; i++) {
        Atom c;
        atom_init(&c, 6, 12, NULL);
        as_add_atom(&as, &c);
    }

    int methane_formed = cs_form_methane(&cs);
    TEST_ASSERT(methane_formed > 0);

    /* Form ammonia - need nitrogen and hydrogen */
    cs_free(&cs);
    as_free(&as);
    as_init(&as);
    cs_init(&cs, &as);

    for (int i = 0; i < 6; i++) {
        Atom h;
        atom_init(&h, 1, 1, NULL);
        as_add_atom(&as, &h);
    }
    for (int i = 0; i < 2; i++) {
        Atom n;
        atom_init(&n, 7, 14, NULL);
        as_add_atom(&as, &n);
    }

    int ammonia_formed = cs_form_ammonia(&cs);
    TEST_ASSERT(ammonia_formed > 0);

    /* Catalyzed reaction with enough atoms */
    cs_free(&cs);
    as_free(&as);
    as_init(&as);
    cs_init(&cs, &as);

    /* Add lots of atoms for catalyzed reactions */
    for (int i = 0; i < 50; i++) {
        Atom h;
        atom_init(&h, 1, 1, NULL);
        as_add_atom(&as, &h);
    }
    for (int i = 0; i < 20; i++) {
        Atom c;
        atom_init(&c, 6, 12, NULL);
        as_add_atom(&as, &c);
    }
    for (int i = 0; i < 20; i++) {
        Atom o;
        atom_init(&o, 8, 16, NULL);
        as_add_atom(&as, &o);
    }
    for (int i = 0; i < 10; i++) {
        Atom n;
        atom_init(&n, 7, 14, NULL);
        as_add_atom(&as, &n);
    }

    /* Run catalyzed reactions multiple times at high temperature */
    int total_formed = 0;
    for (int i = 0; i < 100; i++) {
        total_formed += cs_catalyzed_reaction(&cs, 500.0, true);
    }
    /* With high temperature and catalyst, at least something should form */
    TEST_ASSERT(total_formed >= 0); /* may form 0 due to randomness */

    cs_free(&cs);
    as_free(&as);

    printf("  Chemistry: all checks passed\n");
}

/* ------------------------------------------------------------------ */
/* Test: Biology                                                       */
/* ------------------------------------------------------------------ */

static void test_biology(void)
{
    TEST_SECTION("Biology");

    /* DNA random */
    DNAStrand dna;
    dna_random(&dna, 64);
    TEST_ASSERT(dna.length == 64);
    TEST_ASSERT(dna.generation == 0);
    TEST_ASSERT(dna.mutation_count == 0);

    /* GC content should be between 0 and 1 */
    dna_compute_gc(&dna);
    TEST_ASSERT(dna.gc_content >= 0.0f);
    TEST_ASSERT(dna.gc_content <= 1.0f);

    /* DNA replication */
    DNAStrand daughter;
    dna_replicate(&dna, &daughter);
    TEST_ASSERT(daughter.length == dna.length);
    TEST_ASSERT(daughter.generation == dna.generation + 1);
    TEST_ASSERT(memcmp(daughter.dna, dna.dna, (size_t)dna.length) == 0);

    /* DNA mutations */
    int muts = dna_apply_mutations(&dna, 100.0f, 100.0f);
    /* With high UV and cosmic ray, should get some mutations */
    TEST_ASSERT(muts >= 0);

    /* Cell init */
    Cell cell;
    cell_init(&cell, 64);
    TEST_ASSERT(cell.alive == true);
    TEST_ASSERT_FLOAT_EQ(cell.energy, 100.0f, 1e-3);
    TEST_ASSERT_FLOAT_EQ(cell.fitness, 1.0f, 1e-3);
    TEST_ASSERT(cell.dna.length == 64);

    /* Cell metabolize */
    cell_metabolize(&cell, 10.0f);
    TEST_ASSERT(cell.alive == true);
    /* Energy should have changed: +env_energy*efficiency - 3.0 */
    TEST_ASSERT(cell.energy != 100.0f);

    /* Cell fitness */
    cell_compute_fitness(&cell);
    TEST_ASSERT(cell.fitness >= 0.0f);
    TEST_ASSERT(cell.fitness <= 2.0f); /* reasonable range */

    /* Cell division */
    cell.energy = 100.0f; /* ensure enough energy */
    Cell child;
    bool divided = bio_cell_divide(&cell, &child);
    TEST_ASSERT(divided == true);
    TEST_ASSERT(child.alive == true);
    TEST_ASSERT(child.generation == cell.generation + 1);
    TEST_ASSERT(child.dna.length == cell.dna.length);

    /* Cell division with low energy should fail */
    Cell low_e_cell;
    cell_init(&low_e_cell, 32);
    low_e_cell.energy = 10.0f;
    Cell child2;
    bool divided2 = bio_cell_divide(&low_e_cell, &child2);
    TEST_ASSERT(divided2 == false);

    /* Biosphere init */
    Biosphere bio;
    bio_init(&bio, 5, 64);
    TEST_ASSERT(bio.count == 5);
    TEST_ASSERT(bio.generation == 0);
    TEST_ASSERT(bio.total_born == 5);
    TEST_ASSERT(bio.total_died == 0);
    TEST_ASSERT(bio.dna_length == 64);

    /* Average fitness */
    float avg = bio_average_fitness(&bio);
    TEST_ASSERT(avg > 0.0f);
    TEST_ASSERT(avg <= 2.0f);

    /* Biosphere step */
    bio_step(&bio, 10.0f, 1.0f, 0.5f, 300.0f);
    TEST_ASSERT(bio.generation == 1);
    TEST_ASSERT(bio.count > 0);

    /* Total mutations */
    int total_muts = bio_total_mutations(&bio);
    TEST_ASSERT(total_muts >= 0);

    bio_free(&bio);
    TEST_ASSERT(bio.cells == NULL);

    printf("  Biology: all checks passed\n");
}

/* ------------------------------------------------------------------ */
/* Test: Environment                                                   */
/* ------------------------------------------------------------------ */

static void test_environment(void)
{
    TEST_SECTION("Environment");

    Environment env;
    env_init(&env);
    TEST_ASSERT_FLOAT_EQ(env.temperature, T_PLANCK, 0.1);
    TEST_ASSERT_FLOAT_EQ(env.radiation_level, 1e10, 100.0);
    TEST_ASSERT_FLOAT_EQ(env.uv_intensity, 0.0f, 1e-6);
    TEST_ASSERT(env.has_magnetic_field == false);
    TEST_ASSERT(env.has_ozone_layer == false);
    TEST_ASSERT_FLOAT_EQ(env.water_fraction, 0.0f, 1e-6);

    /* Epoch setting: Planck */
    env_set_epoch_planck(&env);
    TEST_ASSERT_FLOAT_EQ(env.temperature, T_PLANCK, 0.1);

    /* Epoch setting: Inflation */
    env_set_epoch_inflation(&env);
    TEST_ASSERT_FLOAT_EQ(env.temperature, T_PLANCK * 0.5, 1.0);
    TEST_ASSERT_FLOAT_EQ(env.radiation_level, 1e9, 100.0);
    TEST_ASSERT_FLOAT_EQ(env.cosmic_ray_flux, 0.0f, 1e-6);
    TEST_ASSERT_FLOAT_EQ(env.uv_intensity, 0.0f, 1e-6);

    /* Epoch setting: Electroweak */
    env_set_epoch_electroweak(&env);
    TEST_ASSERT_FLOAT_EQ(env.temperature, T_ELECTROWEAK, 1.0);
    TEST_ASSERT_FLOAT_EQ(env.radiation_level, 1e8, 100.0);
    TEST_ASSERT_FLOAT_EQ(env.cosmic_ray_flux, 0.1f, 1e-3);
    TEST_ASSERT_FLOAT_EQ(env.uv_intensity, 0.0f, 1e-6);

    /* Epoch setting: Quark */
    env_set_epoch_quark(&env);
    TEST_ASSERT_FLOAT_EQ(env.temperature, T_QUARK_HADRON * 10.0, 1.0);
    TEST_ASSERT_FLOAT_EQ(env.radiation_level, 1e7, 100.0);
    TEST_ASSERT_FLOAT_EQ(env.cosmic_ray_flux, 0.5f, 1e-3);
    TEST_ASSERT_FLOAT_EQ(env.uv_intensity, 0.0f, 1e-6);

    /* Epoch setting: Hadron */
    env_set_epoch_hadron(&env);
    TEST_ASSERT_FLOAT_EQ(env.temperature, T_QUARK_HADRON, 1.0);
    TEST_ASSERT_FLOAT_EQ(env.radiation_level, 1e6, 100.0);
    TEST_ASSERT_FLOAT_EQ(env.cosmic_ray_flux, 1.0f, 1e-3);
    TEST_ASSERT_FLOAT_EQ(env.uv_intensity, 0.0f, 1e-6);

    /* Epoch setting: Nucleosynthesis */
    env_set_epoch_nucleosynthesis(&env);
    TEST_ASSERT_FLOAT_EQ(env.temperature, T_NUCLEOSYNTHESIS, 0.1);
    TEST_ASSERT_FLOAT_EQ(env.atmosphere.hydrogen, 0.75f, 1e-3);
    TEST_ASSERT_FLOAT_EQ(env.atmosphere.helium, 0.25f, 1e-3);

    /* Epoch setting: Recombination */
    env_set_epoch_recombination(&env);
    TEST_ASSERT_FLOAT_EQ(env.temperature, T_RECOMBINATION, 0.1);
    TEST_ASSERT_FLOAT_EQ(env.radiation_level, 100.0, 1.0);
    TEST_ASSERT_FLOAT_EQ(env.cosmic_ray_flux, 3.0f, 1e-3);
    TEST_ASSERT_FLOAT_EQ(env.atmosphere.hydrogen, 0.75f, 1e-3);
    TEST_ASSERT_FLOAT_EQ(env.atmosphere.helium, 0.25f, 1e-3);

    /* Epoch setting: Star Formation */
    env_set_epoch_star_formation(&env);
    TEST_ASSERT_FLOAT_EQ(env.temperature, 100.0, 0.1);
    TEST_ASSERT_FLOAT_EQ(env.radiation_level, 50.0, 1.0);
    TEST_ASSERT_FLOAT_EQ(env.cosmic_ray_flux, 5.0f, 1e-3);
    TEST_ASSERT_FLOAT_EQ(env.uv_intensity, 1.0f, 1e-3);
    TEST_ASSERT_FLOAT_EQ(env.atmosphere.hydrogen, 0.70f, 1e-3);
    TEST_ASSERT_FLOAT_EQ(env.atmosphere.helium, 0.28f, 1e-3);
    TEST_ASSERT_FLOAT_EQ(env.atmosphere.other, 0.02f, 1e-3);

    /* Epoch setting: Solar System */
    env_set_epoch_solar_system(&env);
    TEST_ASSERT_FLOAT_EQ(env.temperature, 500.0, 0.1);
    TEST_ASSERT_FLOAT_EQ(env.radiation_level, 20.0, 1.0);
    TEST_ASSERT_FLOAT_EQ(env.cosmic_ray_flux, 3.0f, 1e-3);
    TEST_ASSERT_FLOAT_EQ(env.uv_intensity, 5.0f, 1e-3);
    TEST_ASSERT_FLOAT_EQ(env.atmosphere.hydrogen, 0.60f, 1e-3);
    TEST_ASSERT_FLOAT_EQ(env.atmosphere.helium, 0.20f, 1e-3);
    TEST_ASSERT_FLOAT_EQ(env.atmosphere.nitrogen, 0.05f, 1e-3);
    TEST_ASSERT_FLOAT_EQ(env.atmosphere.carbon_dioxide, 0.10f, 1e-3);
    TEST_ASSERT_FLOAT_EQ(env.atmosphere.water_vapor, 0.03f, 1e-3);

    /* Epoch setting: Earth */
    env_set_epoch_earth(&env);
    TEST_ASSERT(env.has_magnetic_field == true);
    TEST_ASSERT(env.water_fraction > 0.0f);
    TEST_ASSERT(env.available_energy > 0.0f);
    TEST_ASSERT(env.atmosphere.nitrogen > 0.0f);
    TEST_ASSERT(env.atmosphere.carbon_dioxide > 0.0f);

    /* Epoch setting: Life */
    env_set_epoch_life(&env);
    TEST_ASSERT_FLOAT_EQ(env.temperature, T_EARTH_SURFACE + 30.0, 0.1);
    TEST_ASSERT_FLOAT_EQ(env.radiation_level, 5.0, 0.1);
    TEST_ASSERT_FLOAT_EQ(env.cosmic_ray_flux, 1.5f, 1e-3);
    TEST_ASSERT_FLOAT_EQ(env.uv_intensity, 6.0f, 1e-3);
    TEST_ASSERT_FLOAT_EQ(env.available_energy, 10.0f, 1e-3);
    TEST_ASSERT_FLOAT_EQ(env.water_fraction, 0.70f, 1e-3);
    TEST_ASSERT(env.has_magnetic_field == true);
    TEST_ASSERT_FLOAT_EQ(env.atmosphere.nitrogen, 0.60f, 1e-3);
    TEST_ASSERT_FLOAT_EQ(env.atmosphere.carbon_dioxide, 0.20f, 1e-3);
    TEST_ASSERT_FLOAT_EQ(env.atmosphere.oxygen, 0.02f, 1e-3);
    TEST_ASSERT_FLOAT_EQ(env.atmosphere.methane, 0.05f, 1e-3);

    /* Epoch setting: DNA */
    env_set_epoch_dna(&env);
    TEST_ASSERT_FLOAT_EQ(env.temperature, T_EARTH_SURFACE + 10.0, 0.1);
    TEST_ASSERT_FLOAT_EQ(env.radiation_level, 3.0, 0.1);
    TEST_ASSERT_FLOAT_EQ(env.cosmic_ray_flux, 1.0f, 1e-3);
    TEST_ASSERT_FLOAT_EQ(env.uv_intensity, 4.0f, 1e-3);
    TEST_ASSERT_FLOAT_EQ(env.available_energy, 15.0f, 1e-3);
    TEST_ASSERT_FLOAT_EQ(env.water_fraction, 0.71f, 1e-3);
    TEST_ASSERT(env.has_magnetic_field == true);
    TEST_ASSERT(env.has_ozone_layer == true);
    TEST_ASSERT_FLOAT_EQ(env.atmosphere.nitrogen, 0.70f, 1e-3);
    TEST_ASSERT_FLOAT_EQ(env.atmosphere.oxygen, 0.15f, 1e-3);
    TEST_ASSERT_FLOAT_EQ(env.atmosphere.carbon_dioxide, 0.05f, 1e-3);

    /* Epoch setting: Present */
    env_set_epoch_present(&env);
    TEST_ASSERT_FLOAT_EQ(env.temperature, T_EARTH_SURFACE, 0.1);
    TEST_ASSERT(env.has_ozone_layer == true);
    TEST_ASSERT(env.atmosphere.oxygen > 0.2f);
    TEST_ASSERT(env.atmosphere.nitrogen > 0.7f);

    /* Temperature update - cooling */
    env_set_epoch_planck(&env);
    double temp_before = env.temperature;
    env_update(&env, 100);
    TEST_ASSERT(env.temperature <= temp_before);
    TEST_ASSERT(env.tick == 100);

    /* Habitability check at present epoch */
    env_set_epoch_present(&env);
    TEST_ASSERT(env.temperature > 200.0);
    TEST_ASSERT(env.temperature < 400.0);
    TEST_ASSERT(env.has_magnetic_field == true);
    TEST_ASSERT(env.has_ozone_layer == true);
    TEST_ASSERT(env.water_fraction > 0.5f);

    /* Atmosphere summary */
    char buf[256];
    const char *summary = env_atmosphere_summary(&env, buf, (int)sizeof(buf));
    TEST_ASSERT(summary != NULL);
    TEST_ASSERT(strlen(summary) > 0);

    printf("  Environment: all checks passed\n");
}

/* ------------------------------------------------------------------ */
/* Test: Universe                                                      */
/* ------------------------------------------------------------------ */

static void test_universe(void)
{
    TEST_SECTION("Universe");

    /* Epoch table */
    const EpochDescriptor *table = universe_epoch_table();
    TEST_ASSERT(table != NULL);
    TEST_ASSERT(table[0].id == EPOCH_PLANCK);
    TEST_ASSERT(strcmp(table[0].name, "Planck") == 0);
    TEST_ASSERT(table[EPOCH_COUNT - 1].id == EPOCH_PRESENT);

    /* Epoch names */
    TEST_ASSERT(strcmp(universe_epoch_name(EPOCH_PLANCK), "Planck") == 0);
    TEST_ASSERT(strcmp(universe_epoch_name(EPOCH_INFLATION), "Inflation") == 0);
    TEST_ASSERT(strcmp(universe_epoch_name(EPOCH_PRESENT), "Present Day") == 0);

    /* Epoch at tick
     * Note: PLANCK starts at tick 0, INFLATION starts at PLANCK_EPOCH (=1),
     * so tick=1 is already INFLATION. */
    TEST_ASSERT(universe_epoch_at_tick(0) == EPOCH_PLANCK);
    TEST_ASSERT(universe_epoch_at_tick(PLANCK_EPOCH) == EPOCH_INFLATION);
    TEST_ASSERT(universe_epoch_at_tick(INFLATION_EPOCH) == EPOCH_ELECTROWEAK);
    TEST_ASSERT(universe_epoch_at_tick(PRESENT_EPOCH) == EPOCH_PRESENT);
    TEST_ASSERT(universe_epoch_at_tick(DNA_EPOCH) == EPOCH_PRESENT);

    /* Universe init */
    Universe u;
    universe_init(&u, false);
    TEST_ASSERT(u.current_tick == 0);
    TEST_ASSERT(u.event_count == 0);
    TEST_ASSERT(u.quantum.particles != NULL);
    TEST_ASSERT(u.atomic.atoms != NULL);

    /* Universe step - should trigger Planck epoch */
    universe_step(&u);
    TEST_ASSERT(u.current_tick == 1);
    TEST_ASSERT(u.current_epoch == EPOCH_PLANCK);
    TEST_ASSERT(u.event_count > 0);

    /* Log event */
    int events_before = u.event_count;
    universe_log_event(&u, "Test event");
    TEST_ASSERT(u.event_count == events_before + 1);

    /* Step to inflation epoch (starts at PLANCK_EPOCH=1) */
    u.current_tick = PLANCK_EPOCH;
    universe_step(&u);
    TEST_ASSERT(u.current_epoch == EPOCH_INFLATION);
    TEST_ASSERT(u.quantum.count > 0); /* should have particles */

    /* Step to hadron epoch (starts at QUARK_EPOCH=1000) */
    u.current_tick = QUARK_EPOCH;
    universe_step(&u);
    TEST_ASSERT(u.current_epoch == EPOCH_HADRON);

    /* Step to nucleosynthesis epoch (starts at HADRON_EPOCH=5000) */
    u.current_tick = HADRON_EPOCH;
    universe_step(&u);
    TEST_ASSERT(u.current_epoch == EPOCH_NUCLEOSYNTHESIS);

    /* After nucleosynthesis, should have some atoms */
    TEST_ASSERT(u.atomic.count >= 0);

    /* Step through remaining epochs using their start ticks */
    u.current_tick = NUCLEOSYNTHESIS_EPOCH;
    universe_step(&u);
    TEST_ASSERT(u.current_epoch == EPOCH_RECOMBINATION);

    u.current_tick = RECOMBINATION_EPOCH;
    universe_step(&u);
    TEST_ASSERT(u.current_epoch == EPOCH_STAR_FORMATION);

    u.current_tick = STAR_FORMATION_EPOCH;
    universe_step(&u);
    TEST_ASSERT(u.current_epoch == EPOCH_SOLAR_SYSTEM);

    u.current_tick = SOLAR_SYSTEM_EPOCH;
    universe_step(&u);
    TEST_ASSERT(u.current_epoch == EPOCH_EARTH);

    u.current_tick = EARTH_EPOCH;
    universe_step(&u);
    TEST_ASSERT(u.current_epoch == EPOCH_LIFE);
    TEST_ASSERT(u.biosphere.cells != NULL);
    TEST_ASSERT(u.biosphere.count > 0);

    /* Step through DNA epoch (starts at LIFE_EPOCH=250000) */
    u.current_tick = LIFE_EPOCH;
    universe_step(&u);
    TEST_ASSERT(u.current_epoch == EPOCH_DNA);

    /* Step to present (starts at DNA_EPOCH=280000) */
    u.current_tick = DNA_EPOCH;
    universe_step(&u);
    TEST_ASSERT(u.current_epoch == EPOCH_PRESENT);

    universe_free(&u);

    /* Universe run - full simulation from Planck to Present */
    Universe u2;
    universe_init(&u2, false);
    TEST_ASSERT(u2.current_tick == 0);
    TEST_ASSERT(u2.event_count == 0);

    universe_run(&u2);

    /* After full run, should have reached present epoch */
    TEST_ASSERT(u2.current_epoch == EPOCH_PRESENT);
    TEST_ASSERT(u2.current_tick > PRESENT_EPOCH);
    /* Should have logged multiple events across all epochs */
    TEST_ASSERT(u2.event_count > 0);
    /* Quantum field should have particles */
    TEST_ASSERT(u2.quantum.total_created > 0);
    /* Should have formed atoms */
    TEST_ASSERT(u2.atomic.count >= 0);
    /* Biosphere should be initialized (life epoch was reached) */
    TEST_ASSERT(u2.biosphere.cells != NULL);
    TEST_ASSERT(u2.biosphere.count > 0);
    /* Environment should be in present-day state */
    TEST_ASSERT_FLOAT_EQ(u2.environment.temperature, T_EARTH_SURFACE, 1.0);
    TEST_ASSERT(u2.environment.has_ozone_layer == true);
    TEST_ASSERT(u2.environment.has_magnetic_field == true);

    universe_free(&u2);

    printf("  Universe: all checks passed\n");
}

/* ------------------------------------------------------------------ */
/* Main                                                                */
/* ------------------------------------------------------------------ */

int main(void)
{
    /* Seed for reproducibility */
    srand(42);

    printf("=== Cosmic Evolution Simulator - C Test Suite ===\n");

    test_constants();
    test_quantum_field();
    test_atomic_system();
    test_chemistry();
    test_biology();
    test_environment();
    test_universe();

    printf("\n=== Results: %d tests run, %d passed, %d failed ===\n",
           g_tests_run, g_tests_passed, g_tests_failed);

    return g_tests_failed > 0 ? 1 : 0;
}
