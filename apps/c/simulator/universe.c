/*
 * universe.c - Universe orchestrator implementation.
 *
 * Drives the simulation through 13 cosmic epochs, coordinating
 * quantum fields, atomic systems, chemistry, biology, and the
 * environment at each tick.
 */
#include "universe.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

/* ------------------------------------------------------------------ */
/* Epoch table                                                         */
/* ------------------------------------------------------------------ */

static const EpochDescriptor EPOCHS[EPOCH_COUNT] = {
    { EPOCH_PLANCK,          "Planck",              0,          PLANCK_EPOCH          },
    { EPOCH_INFLATION,       "Inflation",           PLANCK_EPOCH,          INFLATION_EPOCH       },
    { EPOCH_ELECTROWEAK,     "Electroweak",         INFLATION_EPOCH,       ELECTROWEAK_EPOCH     },
    { EPOCH_QUARK,           "Quark",               ELECTROWEAK_EPOCH,     QUARK_EPOCH           },
    { EPOCH_HADRON,          "Hadron",              QUARK_EPOCH,           HADRON_EPOCH          },
    { EPOCH_NUCLEOSYNTHESIS, "Nucleosynthesis",     HADRON_EPOCH,          NUCLEOSYNTHESIS_EPOCH },
    { EPOCH_RECOMBINATION,   "Recombination",       NUCLEOSYNTHESIS_EPOCH, RECOMBINATION_EPOCH   },
    { EPOCH_STAR_FORMATION,  "Star Formation",      RECOMBINATION_EPOCH,   STAR_FORMATION_EPOCH  },
    { EPOCH_SOLAR_SYSTEM,    "Solar System",        STAR_FORMATION_EPOCH,  SOLAR_SYSTEM_EPOCH    },
    { EPOCH_EARTH,           "Earth Formation",     SOLAR_SYSTEM_EPOCH,    EARTH_EPOCH           },
    { EPOCH_LIFE,            "Origin of Life",      EARTH_EPOCH,           LIFE_EPOCH            },
    { EPOCH_DNA,             "DNA & Genetics",      LIFE_EPOCH,            DNA_EPOCH             },
    { EPOCH_PRESENT,         "Present Day",         DNA_EPOCH,             PRESENT_EPOCH         },
};

const EpochDescriptor *universe_epoch_table(void)
{
    return EPOCHS;
}

/* ------------------------------------------------------------------ */
/* Helpers                                                             */
/* ------------------------------------------------------------------ */

static float randf(void)
{
    return (float)rand() / (float)RAND_MAX;
}

EpochId universe_epoch_at_tick(int tick)
{
    for (int i = EPOCH_COUNT - 1; i >= 0; i--) {
        if (tick >= EPOCHS[i].start_tick)
            return EPOCHS[i].id;
    }
    return EPOCH_PLANCK;
}

const char *universe_epoch_name(EpochId id)
{
    if (id >= 0 && id < EPOCH_COUNT)
        return EPOCHS[id].name;
    return "Unknown";
}

void universe_log_event(Universe *u, const char *msg)
{
    if (u->event_count >= MAX_EVENTS) {
        /* Shift events to make room */
        memmove(&u->events[0], &u->events[1],
                (size_t)(MAX_EVENTS - 1) * sizeof(SimEvent));
        u->event_count = MAX_EVENTS - 1;
    }
    SimEvent *e = &u->events[u->event_count];
    e->tick  = u->current_tick;
    e->epoch = u->current_epoch;
    strncpy(e->message, msg, sizeof(e->message) - 1);
    e->message[sizeof(e->message) - 1] = '\0';
    u->event_count++;
}

/* ------------------------------------------------------------------ */
/* Init / Free                                                         */
/* ------------------------------------------------------------------ */

void universe_init(Universe *u, bool verbose)
{
    memset(u, 0, sizeof(*u));
    u->verbose       = verbose;
    u->current_tick  = 0;
    u->current_epoch = EPOCH_COUNT; /* sentinel: first step triggers Planck entry */
    u->event_count   = 0;

    qf_init(&u->quantum, T_PLANCK);
    as_init(&u->atomic);
    cs_init(&u->chemistry, &u->atomic);
    /* Biosphere is initialized later when life epoch begins */
    env_init(&u->environment);
}

void universe_free(Universe *u)
{
    qf_free(&u->quantum);
    as_free(&u->atomic);
    cs_free(&u->chemistry);
    if (u->biosphere.cells != NULL)
        bio_free(&u->biosphere);
}

/* ------------------------------------------------------------------ */
/* Epoch transition handlers                                           */
/* ------------------------------------------------------------------ */

static void on_enter_planck(Universe *u)
{
    env_set_epoch_planck(&u->environment);
    universe_log_event(u, "The universe begins: a singularity of infinite density");
}

static void on_enter_inflation(Universe *u)
{
    env_set_epoch_inflation(&u->environment);
    universe_log_event(u, "Cosmic inflation: space expands exponentially");

    /* Seed initial quantum fluctuations */
    for (int i = 0; i < 20; i++) {
        float energy = (float)(u->environment.temperature * SIM_K_B * 10.0);
        qf_pair_production(&u->quantum, energy);
    }
}

static void on_enter_electroweak(Universe *u)
{
    env_set_epoch_electroweak(&u->environment);
    u->quantum.temperature = T_ELECTROWEAK;
    universe_log_event(u, "Electroweak symmetry breaking: W/Z bosons acquire mass");
}

static void on_enter_quark(Universe *u)
{
    env_set_epoch_quark(&u->environment);
    u->quantum.temperature = T_QUARK_HADRON * 10.0;
    universe_log_event(u, "Quark epoch: quark-gluon plasma fills the universe");

    /* Generate more quarks */
    for (int i = 0; i < 30; i++) {
        float energy = (float)(u->environment.temperature * SIM_K_B);
        qf_pair_production(&u->quantum, energy);
    }
}

static void on_enter_hadron(Universe *u)
{
    env_set_epoch_hadron(&u->environment);
    u->quantum.temperature = T_QUARK_HADRON;
    universe_log_event(u, "Hadron epoch: quarks confine into protons and neutrons");

    int hadrons = qf_quark_confinement(&u->quantum);
    if (hadrons > 0) {
        char buf[128];
        snprintf(buf, sizeof(buf), "Quark confinement formed %d hadrons", hadrons);
        universe_log_event(u, buf);
    }
}

static void on_enter_nucleosynthesis(Universe *u)
{
    env_set_epoch_nucleosynthesis(&u->environment);
    u->quantum.temperature = T_NUCLEOSYNTHESIS;
    universe_log_event(u, "Big Bang nucleosynthesis: hydrogen and helium form");

    int protons  = qf_particle_count(&u->quantum, PTYPE_PROTON);
    int neutrons = qf_particle_count(&u->quantum, PTYPE_NEUTRON);
    int formed   = as_nucleosynthesis(&u->atomic, protons, neutrons);

    if (formed > 0) {
        char buf[128];
        snprintf(buf, sizeof(buf), "Nucleosynthesis created %d light nuclei (H, He)", formed);
        universe_log_event(u, buf);
    }
}

static void on_enter_recombination(Universe *u)
{
    env_set_epoch_recombination(&u->environment);
    u->atomic.temperature = T_RECOMBINATION;
    universe_log_event(u, "Recombination: electrons bind to nuclei, universe becomes transparent");

    int atoms = as_recombination(&u->atomic, &u->quantum);
    if (atoms > 0) {
        char buf[128];
        snprintf(buf, sizeof(buf), "Recombination captured %d atoms from plasma", atoms);
        universe_log_event(u, buf);
    }
}

static void on_enter_star_formation(Universe *u)
{
    env_set_epoch_star_formation(&u->environment);
    universe_log_event(u, "First stars ignite: stellar nucleosynthesis begins");

    int heavier = as_stellar_nucleosynthesis(&u->atomic, T_STELLAR_CORE);
    if (heavier > 0) {
        char buf[128];
        snprintf(buf, sizeof(buf), "Stellar fusion created %d heavier elements (C, N, O)", heavier);
        universe_log_event(u, buf);
    }
}

static void on_enter_solar_system(Universe *u)
{
    env_set_epoch_solar_system(&u->environment);
    universe_log_event(u, "Solar system forms from collapsing molecular cloud");

    /* Additional stellar nucleosynthesis for enrichment */
    int more = as_stellar_nucleosynthesis(&u->atomic, T_STELLAR_CORE * 0.8);
    (void)more;

    /* Form basic molecules */
    int water   = cs_form_water(&u->chemistry);
    int methane = cs_form_methane(&u->chemistry);
    int ammonia = cs_form_ammonia(&u->chemistry);

    if (water + methane + ammonia > 0) {
        char buf[128];
        snprintf(buf, sizeof(buf),
                 "Molecular cloud: %d water, %d methane, %d ammonia formed",
                 water, methane, ammonia);
        universe_log_event(u, buf);
    }
}

static void on_enter_earth(Universe *u)
{
    env_set_epoch_earth(&u->environment);
    universe_log_event(u, "Earth forms: volcanic outgassing creates early atmosphere");

    /* Catalyzed prebiotic chemistry */
    for (int i = 0; i < 50; i++) {
        cs_catalyzed_reaction(&u->chemistry, u->environment.temperature,
                              randf() < 0.3f);
    }

    if (u->chemistry.amino_acid_count > 0) {
        char buf[128];
        snprintf(buf, sizeof(buf), "Prebiotic chemistry: %d amino acids, %d nucleotides",
                 u->chemistry.amino_acid_count, u->chemistry.nucleotide_count);
        universe_log_event(u, buf);
    }
}

static void on_enter_life(Universe *u)
{
    env_set_epoch_life(&u->environment);
    universe_log_event(u, "First protocells emerge in hydrothermal vents");

    /* Initialize biosphere with a small population */
    bio_init(&u->biosphere, 8, 64);

    char buf[128];
    snprintf(buf, sizeof(buf), "Biosphere seeded with %d protocells", u->biosphere.count);
    universe_log_event(u, buf);
}

static void on_enter_dna(Universe *u)
{
    env_set_epoch_dna(&u->environment);
    universe_log_event(u, "DNA replication and genetic code established");
}

static void on_enter_present(Universe *u)
{
    env_set_epoch_present(&u->environment);
    universe_log_event(u, "Present day: complex life thrives on Earth");
}

/* Epoch entry dispatch */
typedef void (*EpochEntryFn)(Universe *);

static const EpochEntryFn EPOCH_ENTRY[EPOCH_COUNT] = {
    on_enter_planck,
    on_enter_inflation,
    on_enter_electroweak,
    on_enter_quark,
    on_enter_hadron,
    on_enter_nucleosynthesis,
    on_enter_recombination,
    on_enter_star_formation,
    on_enter_solar_system,
    on_enter_earth,
    on_enter_life,
    on_enter_dna,
    on_enter_present,
};

/* ------------------------------------------------------------------ */
/* Per-tick logic                                                       */
/* ------------------------------------------------------------------ */

static void tick_quantum(Universe *u)
{
    /* Vacuum fluctuations and evolution in early epochs */
    if (u->current_epoch <= EPOCH_HADRON) {
        for (int i = 0; i < 3; i++) {
            qf_vacuum_fluctuation(&u->quantum);
        }
        qf_evolve(&u->quantum, 0.1f);
    }

    /* Continued quark confinement during hadron epoch */
    if (u->current_epoch == EPOCH_HADRON) {
        qf_quark_confinement(&u->quantum);
    }
}

static void tick_atomic(Universe *u)
{
    /* Stellar nucleosynthesis during star-related epochs */
    if (u->current_epoch >= EPOCH_STAR_FORMATION &&
        u->current_epoch <= EPOCH_SOLAR_SYSTEM) {
        if (u->current_tick % 1000 == 0) {
            as_stellar_nucleosynthesis(&u->atomic, T_STELLAR_CORE * 0.5);
        }
    }
}

static void tick_chemistry(Universe *u)
{
    /* Molecular formation during and after solar system epoch */
    if (u->current_epoch >= EPOCH_SOLAR_SYSTEM) {
        if (u->current_tick % 500 == 0) {
            cs_form_water(&u->chemistry);
            cs_form_methane(&u->chemistry);
            cs_form_ammonia(&u->chemistry);
        }
        if (u->current_epoch >= EPOCH_EARTH && u->current_tick % 200 == 0) {
            cs_catalyzed_reaction(&u->chemistry,
                                  u->environment.temperature,
                                  randf() < 0.2f);
        }
    }
}

static void tick_biology(Universe *u)
{
    if (u->current_epoch < EPOCH_LIFE) return;
    if (u->biosphere.cells == NULL) return;

    bio_step(&u->biosphere,
             u->environment.available_energy,
             u->environment.uv_intensity,
             u->environment.cosmic_ray_flux,
             (float)u->environment.temperature);
}

/* ------------------------------------------------------------------ */
/* Main step                                                           */
/* ------------------------------------------------------------------ */

void universe_step(Universe *u)
{
    int tick = u->current_tick;

    /* Check for epoch transition */
    EpochId new_epoch = universe_epoch_at_tick(tick);
    if (new_epoch != u->current_epoch) {
        u->current_epoch = new_epoch;
        if (new_epoch >= 0 && new_epoch < EPOCH_COUNT && EPOCH_ENTRY[new_epoch]) {
            EPOCH_ENTRY[new_epoch](u);
        }
    }

    /* Update environment */
    env_update(&u->environment, tick);

    /* Tick subsystems */
    tick_quantum(u);
    tick_atomic(u);
    tick_chemistry(u);
    tick_biology(u);

    u->current_tick++;
}

/* ------------------------------------------------------------------ */
/* Full run                                                            */
/* ------------------------------------------------------------------ */

/* Step size varies by epoch to keep runtime reasonable */
static int step_size_for_epoch(EpochId id)
{
    switch (id) {
    case EPOCH_PLANCK:          return 1;
    case EPOCH_INFLATION:       return 1;
    case EPOCH_ELECTROWEAK:     return 10;
    case EPOCH_QUARK:           return 100;
    case EPOCH_HADRON:          return 500;
    case EPOCH_NUCLEOSYNTHESIS: return 500;
    case EPOCH_RECOMBINATION:   return 5000;
    case EPOCH_STAR_FORMATION:  return 5000;
    case EPOCH_SOLAR_SYSTEM:    return 1000;
    case EPOCH_EARTH:           return 1000;
    case EPOCH_LIFE:            return 2000;
    case EPOCH_DNA:             return 2000;
    case EPOCH_PRESENT:         return 2000;
    default:                    return 1000;
    }
}

void universe_run(Universe *u)
{
    /* First step will trigger Planck epoch entry automatically */
    while (u->current_tick <= PRESENT_EPOCH) {
        EpochId before = u->current_epoch;
        universe_step(u);

        /* When epoch changes, use new step size */
        EpochId after = u->current_epoch;
        int step = step_size_for_epoch(after);

        /* Jump ahead (but step through epoch boundaries precisely) */
        if (u->current_tick < PRESENT_EPOCH) {
            int next_boundary = PRESENT_EPOCH;
            for (int i = 0; i < EPOCH_COUNT; i++) {
                if (EPOCHS[i].start_tick > u->current_tick &&
                    EPOCHS[i].start_tick < next_boundary) {
                    next_boundary = EPOCHS[i].start_tick;
                }
            }
            int jump = u->current_tick + step;
            if (jump > next_boundary) jump = next_boundary;
            u->current_tick = jump;
        }

        (void)before;
    }
}

void universe_big_bounce(Universe *u)
{
    /* Free current state */
    bool was_verbose = u->verbose;
    universe_free(u);
    /* Re-initialize for a fresh cycle */
    universe_init(u, was_verbose);
}
