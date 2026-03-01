/*
 * main.c - CLI entry point for the cosmic evolution simulator.
 *
 * Creates a Universe, runs the simulation through all 13 cosmic epochs
 * from the Planck era to present day, and prints ASCII output showing
 * physics data at each stage.
 */
#define _GNU_SOURCE
#include "universe.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <dirent.h>
#include <sys/stat.h>
#include <ctype.h>
#include <libgen.h>
#include <limits.h>

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
/* AST self-introspection                                              */
/* ------------------------------------------------------------------ */

/**
 * Count functions in a source buffer using simple heuristics.
 *
 * A "function" is detected when a line (after optional leading whitespace)
 * contains an identifier followed by '(' and the preceding token looks
 * like a return type (another identifier or '*').  This catches patterns
 * such as:
 *     void foo(...)
 *     static int bar(...)
 *     Universe *universe_init(...)
 *
 * It intentionally skips control-flow keywords (if, for, while, switch,
 * return) and macro-like identifiers that happen to precede '('.
 */
static int count_functions(const char *buf, long len)
{
    int count = 0;
    const char *keywords[] = {
        "if", "for", "while", "switch", "return", "sizeof", "typeof",
        "case", "else", NULL
    };

    const char *p = buf;
    const char *end = buf + len;

    while (p < end) {
        /* Find the start of the current line */
        const char *line_start = p;

        /* Find end of this line */
        const char *line_end = p;
        while (line_end < end && *line_end != '\n')
            line_end++;

        /* Skip leading whitespace */
        const char *s = line_start;
        while (s < line_end && (*s == ' ' || *s == '\t'))
            s++;

        /* Skip preprocessor lines and comments */
        if (s < line_end && (*s == '#' || *s == '/' || *s == '*')) {
            p = (line_end < end) ? line_end + 1 : end;
            continue;
        }

        /* Look for identifier followed by '(' on this line.
         * We scan for '(' then look backward for the function name
         * and further back for a return-type token.
         */
        const char *paren = s;
        while (paren < line_end) {
            paren = memchr(paren, '(', (size_t)(line_end - paren));
            if (!paren) break;

            /* Walk backward from '(' to find the function name */
            const char *name_end = paren;
            while (name_end > s && *(name_end - 1) == ' ')
                name_end--;

            const char *name_start = name_end;
            while (name_start > s &&
                   (isalnum((unsigned char)*(name_start - 1)) ||
                    *(name_start - 1) == '_'))
                name_start--;

            size_t name_len = (size_t)(name_end - name_start);
            if (name_len == 0) {
                paren++;
                continue;
            }

            /* Check if the name is a keyword -- skip if so */
            int is_keyword = 0;
            for (int k = 0; keywords[k] != NULL; k++) {
                if (strlen(keywords[k]) == name_len &&
                    strncmp(name_start, keywords[k], name_len) == 0) {
                    is_keyword = 1;
                    break;
                }
            }
            if (is_keyword) {
                paren++;
                continue;
            }

            /* There must be a return-type token before the function name.
             * Walk backward past spaces and look for an identifier or '*'.
             */
            const char *before = name_start;
            while (before > s && (*(before - 1) == ' ' || *(before - 1) == '\t'))
                before--;

            if (before > s &&
                (*(before - 1) == '*' ||
                 isalnum((unsigned char)*(before - 1)) ||
                 *(before - 1) == '_')) {
                count++;
            }

            /* Only count the first match per line */
            break;
        }

        p = (line_end < end) ? line_end + 1 : end;
    }

    return count;
}

/**
 * Count struct definitions in a source buffer.
 *
 * Matches occurrences of "struct" that represent a definition, including:
 *   - "struct Name {"            (named struct definition)
 *   - "typedef struct {"         (anonymous typedef'd struct)
 *   - "typedef struct Name {"    (named typedef'd struct)
 *
 * Excludes forward declarations like "struct Name;" and variable
 * declarations like "struct Name var;".
 */
static int count_structs(const char *buf, long len)
{
    int count = 0;
    const char *p = buf;
    const char *end = buf + len;
    const char *needle = "struct";
    size_t needle_len = 6;

    while (p < end) {
        const char *found = (const char *)memmem(p, (size_t)(end - p),
                                                  needle, needle_len);
        if (!found) break;

        /* Check that 'struct' is not part of a larger identifier */
        if (found > buf &&
            (isalnum((unsigned char)*(found - 1)) || *(found - 1) == '_')) {
            p = found + needle_len;
            continue;
        }
        const char *after_kw = found + needle_len;
        if (after_kw < end &&
            (isalnum((unsigned char)*after_kw) || *after_kw == '_')) {
            p = found + needle_len;
            continue;
        }

        /* Skip whitespace after "struct" */
        const char *s = after_kw;
        while (s < end && (*s == ' ' || *s == '\t'))
            s++;

        if (s >= end) break;

        /* Case 1: "struct {" -- anonymous (typically from typedef struct {) */
        if (*s == '{') {
            count++;
            p = s + 1;
            continue;
        }

        /* Case 2: "struct Name" -- check what follows the name */
        if (isalpha((unsigned char)*s) || *s == '_') {
            /* Skip the identifier */
            const char *id_end = s;
            while (id_end < end &&
                   (isalnum((unsigned char)*id_end) || *id_end == '_'))
                id_end++;

            /* Skip whitespace after identifier */
            const char *after_id = id_end;
            while (after_id < end && (*after_id == ' ' || *after_id == '\t'))
                after_id++;

            /* Count if followed by '{' (definition) */
            if (after_id < end && *after_id == '{') {
                count++;
            }
        }

        p = found + needle_len;
    }

    return count;
}

/**
 * Run AST self-introspection on the simulator/ directory.
 *
 * Opens each .c and .h file, counts lines, bytes, functions, and struct
 * definitions, and prints a formatted table of results.  Follows the same
 * pattern as the Node.js runAstIntrospection() in apps/nodejs/index.js.
 */
static int run_ast_introspection(const char *prog_path)
{
    /*
     * Locate the simulator/ source directory.  Strategy:
     *   1. Try "simulator/" relative to the current working directory
     *      (the typical invocation: run from apps/c/).
     *   2. Try the directory containing the source file itself -- i.e.,
     *      resolve the binary path's parent, then check for a sibling
     *      "simulator/" directory.
     *   3. Fall back to the directory of the binary itself.
     */
    char dir_buf[PATH_MAX];
    const char *dir = NULL;
    DIR *dp = NULL;

    /* Strategy 1: "simulator/" from cwd */
    dp = opendir("simulator");
    if (dp) {
        dir = "simulator";
    }

    /* Strategy 2: relative to binary location */
    if (!dp) {
        char prog_copy[PATH_MAX];
        strncpy(prog_copy, prog_path, sizeof(prog_copy) - 1);
        prog_copy[sizeof(prog_copy) - 1] = '\0';
        char *bin_dir = dirname(prog_copy);
        snprintf(dir_buf, sizeof(dir_buf), "%s/../simulator", bin_dir);
        dp = opendir(dir_buf);
        if (dp) {
            dir = dir_buf;
        }
    }

    /* Strategy 3: dirname of binary */
    if (!dp) {
        char prog_copy[PATH_MAX];
        strncpy(prog_copy, prog_path, sizeof(prog_copy) - 1);
        prog_copy[sizeof(prog_copy) - 1] = '\0';
        char *bin_dir = dirname(prog_copy);
        dp = opendir(bin_dir);
        if (dp) {
            strncpy(dir_buf, bin_dir, sizeof(dir_buf) - 1);
            dir_buf[sizeof(dir_buf) - 1] = '\0';
            dir = dir_buf;
        }
    }

    if (!dp) {
        fprintf(stderr, "Error: cannot open simulator directory\n");
        return 1;
    }

    /* Collect matching filenames (simple static array) */
    char filenames[64][256];
    int file_count = 0;

    struct dirent *entry;
    while ((entry = readdir(dp)) != NULL && file_count < 64) {
        const char *name = entry->d_name;
        size_t nlen = strlen(name);
        if (nlen < 3) continue;

        /* Check for .c or .h extension */
        int is_c = (nlen >= 2 && strcmp(name + nlen - 2, ".c") == 0);
        int is_h = (nlen >= 2 && strcmp(name + nlen - 2, ".h") == 0);

        if (is_c || is_h) {
            strncpy(filenames[file_count], name, 255);
            filenames[file_count][255] = '\0';
            file_count++;
        }
    }
    closedir(dp);

    /* Sort filenames alphabetically */
    for (int i = 0; i < file_count - 1; i++) {
        for (int j = i + 1; j < file_count; j++) {
            if (strcmp(filenames[i], filenames[j]) > 0) {
                char tmp[256];
                memcpy(tmp, filenames[i], 256);
                memcpy(filenames[i], filenames[j], 256);
                memcpy(filenames[j], tmp, 256);
            }
        }
    }

    /* Print header */
    printf("\n");
    printf("  === AST Self-Introspection: C Simulator ===\n\n");
    printf("  %-28s %6s %8s %6s %8s\n", "File", "Lines", "Bytes", "Funcs", "Structs");
    printf("  %-28s %6s %8s %6s %8s\n",
           "----------------------------", "------", "--------",
           "------", "--------");

    long total_lines = 0;
    long total_bytes = 0;
    int total_functions = 0;
    int total_structs = 0;

    for (int i = 0; i < file_count; i++) {
        char filepath[PATH_MAX + 512];
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wformat-truncation"
        snprintf(filepath, sizeof(filepath), "%s/%s", dir, filenames[i]);
#pragma GCC diagnostic pop

        FILE *fp = fopen(filepath, "r");
        if (!fp) continue;

        /* Get file size */
        fseek(fp, 0, SEEK_END);
        long fsize = ftell(fp);
        fseek(fp, 0, SEEK_SET);

        /* Read entire file */
        char *buf = (char *)malloc((size_t)fsize + 1);
        if (!buf) {
            fclose(fp);
            continue;
        }
        size_t nread = fread(buf, 1, (size_t)fsize, fp);
        buf[nread] = '\0';
        fclose(fp);

        /* Count lines */
        long lines = 0;
        for (size_t c = 0; c < nread; c++) {
            if (buf[c] == '\n') lines++;
        }
        if (nread > 0 && buf[nread - 1] != '\n') lines++;

        /* Count functions and structs */
        int funcs = count_functions(buf, (long)nread);
        int structs = count_structs(buf, (long)nread);

        total_lines += lines;
        total_bytes += fsize;
        total_functions += funcs;
        total_structs += structs;

        printf("  %-28s %6ld %8ld %6d %8d\n",
               filenames[i], lines, fsize, funcs, structs);

        free(buf);
    }

    printf("  %-28s %6s %8s %6s %8s\n",
           "----------------------------", "------", "--------",
           "------", "--------");
    printf("  %-28s %6ld %8ld %6d %8d\n",
           "TOTAL", total_lines, total_bytes, total_functions, total_structs);
    printf("\n");

    return 0;
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
    printf("  -v, --verbose          Enable verbose output\n");
    printf("  -s, --seed NUM         Set random seed (default: time-based)\n");
    printf("      --ast-introspect   Run AST self-introspection and exit\n");
    printf("  -h, --help             Show this help\n");
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
        } else if (strcmp(argv[i], "--ast-introspect") == 0) {
            return run_ast_introspection(argv[0]);
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
