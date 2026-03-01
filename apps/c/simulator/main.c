/*
 * main.c - CLI entry point for the cosmic evolution simulator.
 *
 * Creates a Universe, runs the simulation through all 13 cosmic epochs
 * from the Planck era to present day, and prints ASCII output showing
 * physics data at each stage.
 */
#include "universe.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

/* ------------------------------------------------------------------ */
/* ASCII art and display helpers                                       */
/* ------------------------------------------------------------------ */

static void print_banner(void)
{
    printf("\n");
    printf("  ============================================================\n");
    printf("  |                                                          |\n");
    printf("  |        IN THE BEGINNING: Cosmic Evolution Simulator      |\n");
    printf("  |        From the Big Bang to Life                         |\n");
    printf("  |                                                          |\n");
    printf("  |        C Implementation                                  |\n");
    printf("  |                                                          |\n");
    printf("  ============================================================\n");
    printf("\n");
}

static void print_separator(void)
{
    printf("  ------------------------------------------------------------\n");
}

static void print_epoch_header(EpochId id, int start_tick, int end_tick)
{
    printf("\n");
    print_separator();

    /* Epoch-specific ASCII art */
    switch (id) {
    case EPOCH_PLANCK:
        printf("  *                        .                               \n");
        printf("             .         *         .      *                  \n");
        printf("       .            SINGULARITY            .              \n");
        break;
    case EPOCH_INFLATION:
        printf("      .  *  .  *  .  *  .  *  .  *  .  *  .  *  .       \n");
        printf("   *  .  *  . EXPONENTIAL EXPANSION  .  *  .  *  .  *    \n");
        printf("      .  *  .  *  .  *  .  *  .  *  .  *  .  *  .       \n");
        break;
    case EPOCH_ELECTROWEAK:
        printf("     ~~/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/~~                   \n");
        printf("     ~~  SYMMETRY BREAKING  ~~                           \n");
        printf("     ~~/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/~~                   \n");
        break;
    case EPOCH_QUARK:
        printf("     q q q g g q q q g g q q q g g q q q                \n");
        printf("     g QUARK-GLUON PLASMA g                              \n");
        printf("     q q q g g q q q g g q q q g g q q q                \n");
        break;
    case EPOCH_HADRON:
        printf("     (uud) (udd) (uud) (udd) (uud) (udd)               \n");
        printf("       p     n     p     n     p     n                   \n");
        printf("     QUARKS CONFINE INTO HADRONS                         \n");
        break;
    case EPOCH_NUCLEOSYNTHESIS:
        printf("     H  H  He  H  H  He  H  H  He  H  H                \n");
        printf("       PRIMORDIAL NUCLEOSYNTHESIS                        \n");
        printf("     H  He  H  H  He  H  H  He  H  H  He               \n");
        break;
    case EPOCH_RECOMBINATION:
        printf("     e- + p+ -> H    e- + p+ -> H    e- + p+ -> H       \n");
        printf("         THE UNIVERSE BECOMES TRANSPARENT                \n");
        printf("     ~~~~~~~~~ COSMIC MICROWAVE BACKGROUND ~~~~~~~~~     \n");
        break;
    case EPOCH_STAR_FORMATION:
        printf("         *           *           *           *           \n");
        printf("        /|\\         /|\\         /|\\         /|\\       \n");
        printf("       * | *  FIRST STARS IGNITE  * | *                  \n");
        break;
    case EPOCH_SOLAR_SYSTEM:
        printf("                    .  *  .                              \n");
        printf("              .  * . Sun  . *  .                         \n");
        printf("         o  .  o  .  @  .  o  .  O                      \n");
        printf("           SOLAR SYSTEM FORMS                            \n");
        break;
    case EPOCH_EARTH:
        printf("              ,~~~~,                                     \n");
        printf("            ,~ Earth ~,                                  \n");
        printf("           ( volcanic! )                                 \n");
        printf("            `~,    ,~'                                   \n");
        printf("              `~~~~'                                     \n");
        break;
    case EPOCH_LIFE:
        printf("           ~~~ hydrothermal vents ~~~                    \n");
        printf("          {  } {  } {  } {  } {  }                      \n");
        printf("           FIRST PROTOCELLS EMERGE                       \n");
        break;
    case EPOCH_DNA:
        printf("          ...ATGCATGCATGCATGC...                         \n");
        printf("          ...TACGTACGTACGTACG...                         \n");
        printf("            DNA REPLICATION BEGINS                       \n");
        break;
    case EPOCH_PRESENT:
        printf("           ,--------,                                    \n");
        printf("          / COMPLEX  \\                                  \n");
        printf("         |   LIFE     |                                  \n");
        printf("          \\ THRIVES  /                                  \n");
        printf("           `--------'                                    \n");
        break;
    default:
        break;
    }

    printf("\n");
    printf("  EPOCH %d/%d: %s\n", id + 1, EPOCH_COUNT, universe_epoch_name(id));
    printf("  Ticks: %d -> %d\n", start_tick, end_tick);
    print_separator();
}

static void print_progress_bar(int current, int total, int width)
{
    if (total <= 0) total = 1;
    int filled = (current * width) / total;
    if (filled > width) filled = width;

    printf("  [");
    for (int i = 0; i < width; i++) {
        if (i < filled)
            putchar('#');
        else
            putchar('.');
    }
    printf("] %d%%\n", (current * 100) / total);
}

/* ------------------------------------------------------------------ */
/* Report printers                                                     */
/* ------------------------------------------------------------------ */

static void print_quantum_state(const QuantumField *qf)
{
    printf("  Quantum Field:\n");
    printf("    Temperature:     %.2e K\n", qf->temperature);
    printf("    Particles:       %d\n", qf->count);
    printf("    Total energy:    %.2f SU\n", (double)qf_total_energy(qf));
    printf("    Protons:         %d\n", qf_particle_count(qf, PTYPE_PROTON));
    printf("    Neutrons:        %d\n", qf_particle_count(qf, PTYPE_NEUTRON));
    printf("    Electrons:       %d\n", qf_particle_count(qf, PTYPE_ELECTRON));
    printf("    Photons:         %d\n", qf_particle_count(qf, PTYPE_PHOTON));
    printf("    Created total:   %d\n", qf->total_created);
    printf("    Annihilated:     %d\n", qf->total_annihilated);
}

static void print_atomic_state(const AtomicSystem *as)
{
    printf("  Atomic System:\n");
    printf("    Total atoms:     %d\n", as->count);

    int counts[27];
    as_element_counts(as, counts);
    if (counts[1] > 0)  printf("    Hydrogen (H):    %d\n", counts[1]);
    if (counts[2] > 0)  printf("    Helium (He):     %d\n", counts[2]);
    if (counts[6] > 0)  printf("    Carbon (C):      %d\n", counts[6]);
    if (counts[7] > 0)  printf("    Nitrogen (N):    %d\n", counts[7]);
    if (counts[8] > 0)  printf("    Oxygen (O):      %d\n", counts[8]);
    if (counts[26] > 0) printf("    Iron (Fe):       %d\n", counts[26]);
}

static void print_chemistry_state(const ChemicalSystem *cs)
{
    printf("  Chemistry:\n");
    printf("    Molecules:       %d\n", cs->count);
    printf("    Water:           %d\n", cs->water_count);
    printf("    Amino acids:     %d\n", cs->amino_acid_count);
    printf("    Nucleotides:     %d\n", cs->nucleotide_count);
    printf("    Reactions:       %d\n", cs->reactions_occurred);
}

static void print_biology_state(const Biosphere *bio)
{
    printf("  Biosphere:\n");
    printf("    Living cells:    %d\n", bio->count);
    printf("    Generation:      %d\n", bio->generation);
    printf("    Total born:      %d\n", bio->total_born);
    printf("    Total died:      %d\n", bio->total_died);
    printf("    Avg fitness:     %.4f\n", (double)bio_average_fitness(bio));
    printf("    Total mutations: %d\n", bio_total_mutations(bio));
}

static void print_environment_state(const Environment *env)
{
    printf("  Environment:\n");
    printf("    Temperature:     %.2e K\n", env->temperature);
    printf("    Radiation:       %.2e\n", env->radiation_level);
    printf("    UV intensity:    %.2f\n", (double)env->uv_intensity);
    printf("    Cosmic rays:     %.2f\n", (double)env->cosmic_ray_flux);
    printf("    Energy avail:    %.2f\n", (double)env->available_energy);
    if (env->water_fraction > 0.0f)
        printf("    Water coverage:  %.0f%%\n", (double)(env->water_fraction * 100.0f));
    if (env->has_magnetic_field)
        printf("    Magnetic field:  YES\n");
    if (env->has_ozone_layer)
        printf("    Ozone layer:     YES\n");

    char atmo[256];
    env_atmosphere_summary(env, atmo, (int)sizeof(atmo));
    printf("    Atmosphere:      %s\n", atmo);
}

static void print_events(const Universe *u, int from_event)
{
    if (u->event_count <= from_event) return;
    printf("  Events:\n");
    for (int i = from_event; i < u->event_count; i++) {
        printf("    [tick %6d] %s\n", u->events[i].tick, u->events[i].message);
    }
}

/* ------------------------------------------------------------------ */
/* Main simulation driver with verbose output                          */
/* ------------------------------------------------------------------ */

static void run_simulation(bool verbose)
{
    Universe u;
    universe_init(&u, verbose);

    print_banner();
    printf("  Initializing simulation...\n");
    printf("  Total simulation span: %d ticks (Planck era -> Present)\n", PRESENT_EPOCH);
    printf("  Epochs: %d\n\n", EPOCH_COUNT);

    const EpochDescriptor *table = universe_epoch_table();
    EpochId last_reported_epoch = EPOCH_COUNT; /* sentinel */

    /* First step will trigger Planck epoch entry via universe_step */
    while (u.current_tick <= PRESENT_EPOCH) {
        int events_before = u.event_count;
        EpochId epoch_before = u.current_epoch;

        universe_step(&u);

        EpochId current = u.current_epoch;

        /* Print epoch header when entering a new epoch */
        if (current != last_reported_epoch) {
            print_epoch_header(current, table[current].start_tick,
                               table[current].end_tick);
            last_reported_epoch = current;

            /* Print events generated by this epoch transition */
            print_events(&u, events_before);
            printf("\n");

            /* Print relevant subsystem state */
            if (current <= EPOCH_HADRON) {
                print_quantum_state(&u.quantum);
            }
            if (current >= EPOCH_NUCLEOSYNTHESIS && u.atomic.count > 0) {
                print_atomic_state(&u.atomic);
            }
            if (current >= EPOCH_SOLAR_SYSTEM && u.chemistry.count > 0) {
                print_chemistry_state(&u.chemistry);
            }
            if (current >= EPOCH_LIFE && u.biosphere.cells != NULL) {
                print_biology_state(&u.biosphere);
            }
            print_environment_state(&u.environment);
            printf("\n");

            /* Print overall progress */
            print_progress_bar(u.current_tick, PRESENT_EPOCH, 50);
            printf("\n");
        }

        /* Advance tick with variable step size */
        EpochId after = u.current_epoch;
        int step;
        switch (after) {
        case EPOCH_PLANCK:          step = 1;    break;
        case EPOCH_INFLATION:       step = 1;    break;
        case EPOCH_ELECTROWEAK:     step = 10;   break;
        case EPOCH_QUARK:           step = 100;  break;
        case EPOCH_HADRON:          step = 500;  break;
        case EPOCH_NUCLEOSYNTHESIS: step = 500;  break;
        case EPOCH_RECOMBINATION:   step = 5000; break;
        case EPOCH_STAR_FORMATION:  step = 5000; break;
        case EPOCH_SOLAR_SYSTEM:    step = 1000; break;
        case EPOCH_EARTH:           step = 1000; break;
        case EPOCH_LIFE:            step = 2000; break;
        case EPOCH_DNA:             step = 2000; break;
        case EPOCH_PRESENT:         step = 2000; break;
        default:                    step = 1000; break;
        }

        /* Ensure we land on epoch boundaries */
        int next_boundary = PRESENT_EPOCH + 1;
        for (int i = 0; i < EPOCH_COUNT; i++) {
            if (table[i].start_tick > u.current_tick &&
                table[i].start_tick < next_boundary) {
                next_boundary = table[i].start_tick;
            }
        }

        int target = u.current_tick + step;
        if (target > next_boundary) target = next_boundary;
        if (target > PRESENT_EPOCH) target = PRESENT_EPOCH + 1;
        u.current_tick = target;

        (void)epoch_before;
    }

    /* ---- Final summary ---- */
    printf("\n");
    print_separator();
    printf("\n");
    printf("  ============================================================\n");
    printf("  |                  SIMULATION COMPLETE                      |\n");
    printf("  ============================================================\n");
    printf("\n");

    printf("  === FINAL STATE ===\n\n");
    print_quantum_state(&u.quantum);
    printf("\n");
    print_atomic_state(&u.atomic);
    printf("\n");
    print_chemistry_state(&u.chemistry);
    printf("\n");
    if (u.biosphere.cells != NULL) {
        print_biology_state(&u.biosphere);
        printf("\n");
    }
    print_environment_state(&u.environment);
    printf("\n");

    printf("  === EVENT LOG ===\n\n");
    for (int i = 0; i < u.event_count; i++) {
        printf("    [tick %6d | %-18s] %s\n",
               u.events[i].tick,
               universe_epoch_name(u.events[i].epoch),
               u.events[i].message);
    }
    printf("\n");

    print_separator();
    printf("  Simulation finished: %d ticks, %d events logged.\n",
           PRESENT_EPOCH, u.event_count);
    print_separator();
    printf("\n");

    universe_free(&u);
}

/* ------------------------------------------------------------------ */
/* Entry point                                                         */
/* ------------------------------------------------------------------ */

static void print_usage(const char *prog)
{
    printf("Usage: %s [options]\n", prog);
    printf("Options:\n");
    printf("  -v, --verbose    Enable verbose output\n");
    printf("  -s, --seed NUM   Set random seed (default: time-based)\n");
    printf("  -h, --help       Show this help\n");
}

int main(int argc, char *argv[])
{
    bool verbose = false;
    unsigned int seed = (unsigned int)time(NULL);

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-v") == 0 || strcmp(argv[i], "--verbose") == 0) {
            verbose = true;
        } else if ((strcmp(argv[i], "-s") == 0 || strcmp(argv[i], "--seed") == 0)
                   && i + 1 < argc) {
            seed = (unsigned int)atoi(argv[++i]);
        } else if (strcmp(argv[i], "-h") == 0 || strcmp(argv[i], "--help") == 0) {
            print_usage(argv[0]);
            return 0;
        } else {
            fprintf(stderr, "Unknown option: %s\n", argv[i]);
            print_usage(argv[0]);
            return 1;
        }
    }

    srand(seed);
    (void)verbose; /* verbose flag available for future use */
    run_simulation(verbose);

    return 0;
}
