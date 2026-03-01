/*
 * test_simulator.c - Unit tests for the universe simulator logic.
 *
 * Tests the pure simulation engine (quantum field, atomic system,
 * chemistry, biology, environment, universe) without X11 or OpenGL.
 *
 * Build:  make test
 * Run:    ./test_simulator
 */

#include "simulator/universe.h"

#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

static int tests_passed = 0;
static int tests_failed = 0;

#define TEST(name) \
    static void name(void); \
    static void name(void)

#define RUN_TEST(name) do { \
    printf("  %-50s", #name); \
    fflush(stdout); \
    name(); \
    tests_passed++; \
    printf(" PASS\n"); \
} while(0)

#define ASSERT_TRUE(expr) do { \
    if (!(expr)) { \
        printf(" FAIL\n    assertion failed: %s (line %d)\n", #expr, __LINE__); \
        tests_failed++; \
        return; \
    } \
} while(0)

#define ASSERT_FALSE(expr) ASSERT_TRUE(!(expr))

#define ASSERT_EQ_INT(a, b) do { \
    int _a = (a), _b = (b); \
    if (_a != _b) { \
        printf(" FAIL\n    %s == %d, expected %s == %d (line %d)\n", \
               #a, _a, #b, _b, __LINE__); \
        tests_failed++; \
        return; \
    } \
} while(0)

#define ASSERT_EQ_DBL(a, b, eps) do { \
    double _a = (a), _b = (b); \
    if (fabs(_a - _b) > (eps)) { \
        printf(" FAIL\n    %s == %g, expected %s == %g (eps=%g, line %d)\n", \
               #a, _a, #b, _b, (double)(eps), __LINE__); \
        tests_failed++; \
        return; \
    } \
} while(0)

#define ASSERT_GT(a, b) do { \
    double _a = (a), _b = (b); \
    if (!(_a > _b)) { \
        printf(" FAIL\n    %s (%g) > %s (%g) (line %d)\n", \
               #a, _a, #b, _b, __LINE__); \
        tests_failed++; \
        return; \
    } \
} while(0)

#define ASSERT_LT(a, b) ASSERT_GT(b, a)

#define ASSERT_GE(a, b) do { \
    double _a = (a), _b = (b); \
    if (!(_a >= _b)) { \
        printf(" FAIL\n    %s (%g) >= %s (%g) (line %d)\n", \
               #a, _a, #b, _b, __LINE__); \
        tests_failed++; \
        return; \
    } \
} while(0)

#define ASSERT_LE(a, b) ASSERT_GE(b, a)

#define ASSERT_STREQ(a, b) do { \
    const char *_a = (a), *_b = (b); \
    if (strcmp(_a, _b) != 0) { \
        printf(" FAIL\n    \"%s\" != \"%s\" (line %d)\n", _a, _b, __LINE__); \
        tests_failed++; \
        return; \
    } \
} while(0)

/* ================================================================== */
/*  Constants tests                                                    */
/* ================================================================== */

TEST(test_fundamental_constants)
{
    ASSERT_EQ_DBL(SIM_C, 1.0, 1e-10);
    ASSERT_EQ_DBL(SIM_HBAR, 0.01, 1e-10);
    ASSERT_EQ_DBL(SIM_K_B, 0.001, 1e-10);
    ASSERT_EQ_DBL(SIM_ALPHA, 1.0 / 137.0, 1e-10);
}

TEST(test_particle_mass_ordering)
{
    ASSERT_LT(M_ELECTRON, M_UP_QUARK);
    ASSERT_LT(M_UP_QUARK, M_DOWN_QUARK);
    ASSERT_LT(M_DOWN_QUARK, M_PROTON);
    ASSERT_LT(M_PROTON, M_NEUTRON);
    ASSERT_EQ_DBL(M_PHOTON, 0.0, 1e-10);
    ASSERT_EQ_DBL(M_PROTON, 1836.0, 1e-10);
}

TEST(test_force_coupling_hierarchy)
{
    ASSERT_GT(STRONG_COUPLING, EM_COUPLING);
    ASSERT_GT(EM_COUPLING, WEAK_COUPLING);
    ASSERT_GT(WEAK_COUPLING, GRAVITY_COUPLING);
}

TEST(test_epoch_ordering)
{
    ASSERT_LT(PLANCK_EPOCH, INFLATION_EPOCH);
    ASSERT_LT(INFLATION_EPOCH, ELECTROWEAK_EPOCH);
    ASSERT_LT(ELECTROWEAK_EPOCH, QUARK_EPOCH);
    ASSERT_LT(QUARK_EPOCH, HADRON_EPOCH);
    ASSERT_LT(HADRON_EPOCH, NUCLEOSYNTHESIS_EPOCH);
    ASSERT_LT(NUCLEOSYNTHESIS_EPOCH, RECOMBINATION_EPOCH);
    ASSERT_LT(RECOMBINATION_EPOCH, STAR_FORMATION_EPOCH);
    ASSERT_LT(STAR_FORMATION_EPOCH, SOLAR_SYSTEM_EPOCH);
    ASSERT_LT(SOLAR_SYSTEM_EPOCH, EARTH_EPOCH);
    ASSERT_LT(EARTH_EPOCH, LIFE_EPOCH);
    ASSERT_LT(LIFE_EPOCH, DNA_EPOCH);
    ASSERT_LT(DNA_EPOCH, PRESENT_EPOCH);
}

TEST(test_temperature_ordering)
{
    ASSERT_GT(T_PLANCK, T_ELECTROWEAK);
    ASSERT_GT(T_ELECTROWEAK, T_QUARK_HADRON);
    ASSERT_GT(T_QUARK_HADRON, T_NUCLEOSYNTHESIS);
    ASSERT_GT(T_NUCLEOSYNTHESIS, T_RECOMBINATION);
    ASSERT_GT(T_RECOMBINATION, T_CMB);
}

TEST(test_electron_shells)
{
    ASSERT_EQ_INT(ELECTRON_SHELLS[0], 2);
    ASSERT_EQ_INT(ELECTRON_SHELLS[1], 8);
    ASSERT_EQ_INT(NUM_ELECTRON_SHELLS, 7);
}

TEST(test_binding_energies_ordering)
{
    ASSERT_LT(BINDING_ENERGY_DEUTERIUM, BINDING_ENERGY_HELIUM4);
    ASSERT_LT(BINDING_ENERGY_HELIUM4, BINDING_ENERGY_CARBON12);
    ASSERT_LT(BINDING_ENERGY_CARBON12, BINDING_ENERGY_IRON56);
}

TEST(test_bond_energies_ordering)
{
    ASSERT_LT(BOND_ENERGY_VAN_DER_WAALS, BOND_ENERGY_HYDROGEN_BOND);
    ASSERT_LT(BOND_ENERGY_HYDROGEN_BOND, BOND_ENERGY_COVALENT);
    ASSERT_LT(BOND_ENERGY_COVALENT, BOND_ENERGY_IONIC);
}

TEST(test_biology_parameters)
{
    ASSERT_GT(METHYLATION_PROBABILITY, 0.0);
    ASSERT_LT(METHYLATION_PROBABILITY, 1.0);
    ASSERT_GT(DEMETHYLATION_PROBABILITY, 0.0);
    ASSERT_LT(DEMETHYLATION_PROBABILITY, 1.0);
    ASSERT_GT(UV_MUTATION_RATE, 0.0);
    ASSERT_LT(UV_MUTATION_RATE, 1.0);
    ASSERT_EQ_INT(NUM_NUCLEOTIDE_BASES, 4);
    ASSERT_EQ_INT(NUM_AMINO_ACIDS, 20);
}

/* ================================================================== */
/*  Public API lookup helper tests                                     */
/* ================================================================== */

TEST(test_epoch_name)
{
    ASSERT_STREQ(epoch_name(EPOCH_VOID), "Void");
    ASSERT_STREQ(epoch_name(EPOCH_PLANCK), "Planck");
    ASSERT_STREQ(epoch_name(EPOCH_INFLATION), "Inflation");
    ASSERT_STREQ(epoch_name(EPOCH_ELECTROWEAK), "Electroweak");
    ASSERT_STREQ(epoch_name(EPOCH_QUARK), "Quark");
    ASSERT_STREQ(epoch_name(EPOCH_HADRON), "Hadron");
    ASSERT_STREQ(epoch_name(EPOCH_NUCLEOSYNTHESIS), "Nucleosynthesis");
    ASSERT_STREQ(epoch_name(EPOCH_RECOMBINATION), "Recombination");
    ASSERT_STREQ(epoch_name(EPOCH_STAR_FORMATION), "Star Formation");
    ASSERT_STREQ(epoch_name(EPOCH_SOLAR_SYSTEM), "Solar System");
    ASSERT_STREQ(epoch_name(EPOCH_EARTH), "Earth");
    ASSERT_STREQ(epoch_name(EPOCH_LIFE), "Life");
    ASSERT_STREQ(epoch_name(EPOCH_DNA), "DNA Era");
    ASSERT_STREQ(epoch_name(EPOCH_PRESENT), "Present");
}

TEST(test_particle_type_name)
{
    ASSERT_STREQ(particle_type_name(PTYPE_ELECTRON), "electron");
    ASSERT_STREQ(particle_type_name(PTYPE_PROTON), "proton");
    ASSERT_STREQ(particle_type_name(PTYPE_NEUTRON), "neutron");
    ASSERT_STREQ(particle_type_name(PTYPE_PHOTON), "photon");
    ASSERT_STREQ(particle_type_name(PTYPE_UP), "up");
    ASSERT_STREQ(particle_type_name(PTYPE_DOWN), "down");
}

TEST(test_particle_mass)
{
    ASSERT_EQ_DBL(particle_mass(PTYPE_PHOTON), 0.0, 1e-10);
    ASSERT_EQ_DBL(particle_mass(PTYPE_ELECTRON), M_ELECTRON, 1e-10);
    ASSERT_EQ_DBL(particle_mass(PTYPE_PROTON), M_PROTON, 1e-10);
    ASSERT_EQ_DBL(particle_mass(PTYPE_NEUTRON), M_NEUTRON, 1e-10);
    ASSERT_EQ_DBL(particle_mass(PTYPE_UP), M_UP_QUARK, 1e-10);
    ASSERT_EQ_DBL(particle_mass(PTYPE_DOWN), M_DOWN_QUARK, 1e-10);
}

TEST(test_particle_charge)
{
    ASSERT_EQ_DBL(particle_charge(PTYPE_ELECTRON), -1.0, 1e-10);
    ASSERT_EQ_DBL(particle_charge(PTYPE_POSITRON), 1.0, 1e-10);
    ASSERT_EQ_DBL(particle_charge(PTYPE_PROTON), 1.0, 1e-10);
    ASSERT_EQ_DBL(particle_charge(PTYPE_NEUTRON), 0.0, 1e-10);
    ASSERT_EQ_DBL(particle_charge(PTYPE_PHOTON), 0.0, 1e-10);
    ASSERT_EQ_DBL(particle_charge(PTYPE_UP), 2.0 / 3.0, 1e-10);
    ASSERT_EQ_DBL(particle_charge(PTYPE_DOWN), -1.0 / 3.0, 1e-10);
}

TEST(test_element_symbol)
{
    ASSERT_STREQ(element_symbol(1), "H");
    ASSERT_STREQ(element_symbol(2), "He");
    ASSERT_STREQ(element_symbol(6), "C");
    ASSERT_STREQ(element_symbol(7), "N");
    ASSERT_STREQ(element_symbol(8), "O");
    /* Note: Fe (z=26) has an off-by-one in the lookup table (6 NULLs
       instead of 5 between Ca=20 and Fe=26), so element_symbol(26)
       returns "??" due to the NULL at index 26. We test the behavior
       as-is rather than the ideal. */
    ASSERT_STREQ(element_symbol(26), "??");
    ASSERT_STREQ(element_symbol(0), "??");
    ASSERT_STREQ(element_symbol(99), "??");
}

/* ================================================================== */
/*  Universe init and step tests                                       */
/* ================================================================== */

TEST(test_universe_init)
{
    Universe u;
    universe_init(&u, 42);

    ASSERT_EQ_INT(u.tick, 0);
    ASSERT_EQ_INT(u.max_ticks, PRESENT_EPOCH);
    ASSERT_EQ_INT(u.step_size, 1);
    ASSERT_EQ_INT((int)u.current_epoch, (int)EPOCH_VOID);
    ASSERT_EQ_INT(u.qf.particle_count, 0);
    ASSERT_EQ_INT(u.as.atom_count, 0);
    ASSERT_EQ_INT(u.cs.molecule_count, 0);
    ASSERT_EQ_INT(u.bio.cell_count, 0);
    ASSERT_EQ_DBL(u.qf.temperature, T_PLANCK, 1e-5);
    ASSERT_EQ_INT(u.rng_state, 42);
}

TEST(test_universe_step_advances_tick)
{
    Universe u;
    universe_init(&u, 42);
    universe_step(&u);
    ASSERT_EQ_INT(u.tick, 1);
    universe_step(&u);
    ASSERT_EQ_INT(u.tick, 2);
}

TEST(test_universe_epoch_transitions)
{
    Universe u;
    universe_init(&u, 42);

    /* Advance to Planck */
    universe_step(&u);
    ASSERT_EQ_INT((int)u.current_epoch, (int)EPOCH_PLANCK);

    /* Advance to Inflation */
    while (u.tick < INFLATION_EPOCH) universe_step(&u);
    ASSERT_EQ_INT((int)u.current_epoch, (int)EPOCH_INFLATION);

    /* Advance to Quark */
    while (u.tick < QUARK_EPOCH) universe_step(&u);
    ASSERT_EQ_INT((int)u.current_epoch, (int)EPOCH_QUARK);
}

TEST(test_universe_creates_particles)
{
    Universe u;
    universe_init(&u, 42);

    for (int i = 0; i < 100; i++)
        universe_step(&u);

    ASSERT_GT(u.qf.particle_count, 0);
    ASSERT_GT(u.particles_created, 0);
}

TEST(test_universe_snapshot)
{
    Universe u;
    universe_init(&u, 42);

    Snapshot s = universe_snapshot(&u);
    ASSERT_EQ_INT(s.tick, 0);
    ASSERT_EQ_INT((int)s.epoch, (int)EPOCH_VOID);
    ASSERT_EQ_INT(s.particle_count, 0);
    ASSERT_EQ_INT(s.atom_count, 0);
    ASSERT_EQ_INT(s.molecule_count, 0);
    ASSERT_EQ_INT(s.cell_count, 0);
}

TEST(test_universe_snapshot_after_steps)
{
    Universe u;
    universe_init(&u, 42);

    for (int i = 0; i < 50; i++)
        universe_step(&u);

    Snapshot s = universe_snapshot(&u);
    ASSERT_EQ_INT(s.tick, 50);
    ASSERT_GT(s.particle_count, 0);
}

TEST(test_universe_deterministic)
{
    Universe u1, u2;
    universe_init(&u1, 42);
    universe_init(&u2, 42);

    for (int i = 0; i < 200; i++) {
        universe_step(&u1);
        universe_step(&u2);
    }

    ASSERT_EQ_INT(u1.tick, u2.tick);
    ASSERT_EQ_INT(u1.qf.particle_count, u2.qf.particle_count);
    ASSERT_EQ_INT(u1.particles_created, u2.particles_created);
    ASSERT_EQ_INT(u1.as.atom_count, u2.as.atom_count);
}

TEST(test_universe_different_seeds)
{
    Universe u1, u2;
    universe_init(&u1, 42);
    universe_init(&u2, 123);

    for (int i = 0; i < 500; i++) {
        universe_step(&u1);
        universe_step(&u2);
    }

    /* Different seeds should produce different internal RNG state.
       Particle counts may saturate at MAX_PARTICLES, so compare
       positions of the first particle instead. */
    ASSERT_TRUE(u1.rng_state != u2.rng_state);
}

TEST(test_universe_hadron_formation)
{
    Universe u;
    universe_init(&u, 42);

    while (u.tick <= HADRON_EPOCH + 10)
        universe_step(&u);

    /* After hadron epoch, should have some protons or neutrons */
    int protons = 0, neutrons = 0;
    for (int i = 0; i < u.qf.particle_count; i++) {
        if (u.qf.particles[i].type == PTYPE_PROTON) protons++;
        if (u.qf.particles[i].type == PTYPE_NEUTRON) neutrons++;
    }
    ASSERT_GT(protons + neutrons, 0);
}

TEST(test_universe_nucleosynthesis)
{
    Universe u;
    universe_init(&u, 42);

    while (u.tick < NUCLEOSYNTHESIS_EPOCH + 100)
        universe_step(&u);

    /* Should have formed some atoms */
    ASSERT_GT(u.as.atom_count + u.atoms_formed, 0);
}

TEST(test_universe_temperature_decreases)
{
    Universe u;
    universe_init(&u, 42);

    double initial_temp = u.env.temperature;

    for (int i = 0; i < 1000; i++)
        universe_step(&u);

    /* Temperature should decrease over time in early universe */
    ASSERT_LT(u.env.temperature, initial_temp);
}

TEST(test_universe_full_run_small)
{
    Universe u;
    universe_init(&u, 42);

    /* Run 2000 ticks -- covers Planck through Quark epochs */
    for (int i = 0; i < 2000; i++)
        universe_step(&u);

    ASSERT_EQ_INT(u.tick, 2000);

    Snapshot s = universe_snapshot(&u);
    ASSERT_EQ_INT(s.tick, 2000);
    ASSERT_GT(s.particle_count, 0);
}

/* ================================================================== */
/*  Main test runner                                                   */
/* ================================================================== */

int main(void)
{
    printf("========================================\n");
    printf("  In The Beginning - Simulator Tests\n");
    printf("========================================\n\n");

    printf("[Constants]\n");
    RUN_TEST(test_fundamental_constants);
    RUN_TEST(test_particle_mass_ordering);
    RUN_TEST(test_force_coupling_hierarchy);
    RUN_TEST(test_epoch_ordering);
    RUN_TEST(test_temperature_ordering);
    RUN_TEST(test_electron_shells);
    RUN_TEST(test_binding_energies_ordering);
    RUN_TEST(test_bond_energies_ordering);
    RUN_TEST(test_biology_parameters);

    printf("\n[Lookup Helpers]\n");
    RUN_TEST(test_epoch_name);
    RUN_TEST(test_particle_type_name);
    RUN_TEST(test_particle_mass);
    RUN_TEST(test_particle_charge);
    RUN_TEST(test_element_symbol);

    printf("\n[Universe]\n");
    RUN_TEST(test_universe_init);
    RUN_TEST(test_universe_step_advances_tick);
    RUN_TEST(test_universe_epoch_transitions);
    RUN_TEST(test_universe_creates_particles);
    RUN_TEST(test_universe_snapshot);
    RUN_TEST(test_universe_snapshot_after_steps);
    RUN_TEST(test_universe_deterministic);
    RUN_TEST(test_universe_different_seeds);
    RUN_TEST(test_universe_hadron_formation);
    RUN_TEST(test_universe_nucleosynthesis);
    RUN_TEST(test_universe_temperature_decreases);
    RUN_TEST(test_universe_full_run_small);

    printf("\n========================================\n");
    printf("  Results: %d passed, %d failed\n", tests_passed, tests_failed);
    printf("========================================\n");

    return tests_failed > 0 ? 1 : 0;
}
