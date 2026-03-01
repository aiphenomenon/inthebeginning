/*
 * atomic.c - Atomic physics implementation.
 *
 * Models atoms with electron shells, nucleosynthesis,
 * recombination, and stellar nucleosynthesis.
 */
#include "atomic.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>

/* ------------------------------------------------------------------ */
/* Helpers                                                             */
/* ------------------------------------------------------------------ */

static int g_atom_id_counter = 0;

static float randf(void)
{
    return (float)rand() / (float)RAND_MAX;
}

static float gaussf(float mean, float stddev)
{
    float u1 = randf();
    float u2 = randf();
    if (u1 < 1e-10f) u1 = 1e-10f;
    float z = sqrtf(-2.0f * logf(u1)) * cosf(2.0f * (float)SIM_PI * u2);
    return mean + stddev * z;
}

/* ------------------------------------------------------------------ */
/* Element table                                                       */
/* ------------------------------------------------------------------ */

static const ElementInfo ELEMENTS[] = {
    { 1, "H",  "Hydrogen",   1, 1, 2.20f},
    { 2, "He", "Helium",    18, 1, 0.00f},
    { 3, "Li", "Lithium",    1, 2, 0.98f},
    { 4, "Be", "Beryllium",  2, 2, 1.57f},
    { 5, "B",  "Boron",     13, 2, 2.04f},
    { 6, "C",  "Carbon",    14, 2, 2.55f},
    { 7, "N",  "Nitrogen",  15, 2, 3.04f},
    { 8, "O",  "Oxygen",    16, 2, 3.44f},
    { 9, "F",  "Fluorine",  17, 2, 3.98f},
    {10, "Ne", "Neon",       18, 2, 0.00f},
    {11, "Na", "Sodium",      1, 3, 0.93f},
    {12, "Mg", "Magnesium",   2, 3, 1.31f},
    {13, "Al", "Aluminum",   13, 3, 1.61f},
    {14, "Si", "Silicon",    14, 3, 1.90f},
    {15, "P",  "Phosphorus", 15, 3, 2.19f},
    {16, "S",  "Sulfur",     16, 3, 2.58f},
    {17, "Cl", "Chlorine",   17, 3, 3.16f},
    {18, "Ar", "Argon",      18, 3, 0.00f},
    {19, "K",  "Potassium",   1, 4, 0.82f},
    {20, "Ca", "Calcium",     2, 4, 1.00f},
    {26, "Fe", "Iron",        8, 4, 1.83f},
    { 0, NULL, NULL,          0, 0, 0.00f}  /* sentinel */
};

const ElementInfo *element_lookup(int z)
{
    for (int i = 0; ELEMENTS[i].symbol != NULL; i++) {
        if (ELEMENTS[i].atomic_number == z)
            return &ELEMENTS[i];
    }
    return NULL;
}

/* ------------------------------------------------------------------ */
/* Electron shell helpers                                              */
/* ------------------------------------------------------------------ */

/* Compute valence and needs for a given electron count */
static void shell_info(int electron_count, int *valence_out, int *needs_out,
                       int *last_shell_max)
{
    int remaining = electron_count;
    int valence = 0;
    int shell_max = 0;
    for (int i = 0; i < ELECTRON_SHELL_COUNT; i++) {
        if (remaining <= 0) break;
        shell_max = ELECTRON_SHELLS[i];
        int in_shell = (remaining < shell_max) ? remaining : shell_max;
        valence = in_shell;
        remaining -= in_shell;
    }
    if (valence_out) *valence_out = valence;
    if (last_shell_max) *last_shell_max = shell_max;
    if (needs_out) *needs_out = shell_max - valence;
}

static float compute_ionization_energy(int atomic_number, int electron_count)
{
    if (electron_count == 0) return 0.0f;

    /* Count inner-shell electrons to estimate Z_eff */
    int remaining = electron_count;
    int inner_electrons = 0;
    int n = 0;
    for (int i = 0; i < ELECTRON_SHELL_COUNT; i++) {
        if (remaining <= 0) break;
        int in_shell = (remaining < ELECTRON_SHELLS[i]) ? remaining : ELECTRON_SHELLS[i];
        remaining -= in_shell;
        n = i + 1;
        if (remaining > 0) inner_electrons += in_shell;
    }
    float z_eff = (float)(atomic_number - inner_electrons);
    if (z_eff < 1.0f) z_eff = 1.0f;
    return 13.6f * z_eff * z_eff / (float)(n * n);
}

/* ------------------------------------------------------------------ */
/* Atom                                                                */
/* ------------------------------------------------------------------ */

void atom_init(Atom *a, int atomic_number, int mass_number, const float pos[3])
{
    memset(a, 0, sizeof(*a));
    a->atomic_number = atomic_number;
    a->mass_number   = mass_number > 0 ? mass_number
                     : (atomic_number == 1 ? 1 : atomic_number * 2);
    a->electron_count = atomic_number; /* neutral */
    if (pos) {
        a->position[0] = pos[0];
        a->position[1] = pos[1];
        a->position[2] = pos[2];
    }
    a->bond_count = 0;
    a->atom_id = ++g_atom_id_counter;
    a->ionization_energy = compute_ionization_energy(atomic_number, a->electron_count);
}

const char *atom_symbol(const Atom *a)
{
    const ElementInfo *e = element_lookup(a->atomic_number);
    return e ? e->symbol : "??";
}

float atom_electronegativity(const Atom *a)
{
    const ElementInfo *e = element_lookup(a->atomic_number);
    return e ? e->electronegativity : 1.0f;
}

int atom_valence_electrons(const Atom *a)
{
    int v = 0;
    shell_info(a->electron_count, &v, NULL, NULL);
    return v;
}

int atom_needs_electrons(const Atom *a)
{
    int n = 0;
    shell_info(a->electron_count, NULL, &n, NULL);
    return n;
}

bool atom_is_noble_gas(const Atom *a)
{
    int valence = 0, shell_max = 0;
    shell_info(a->electron_count, &valence, NULL, &shell_max);
    return valence >= shell_max;
}

bool atom_can_bond(const Atom *a)
{
    if (atom_is_noble_gas(a)) return false;
    if (a->bond_count >= 4)   return false;
    return true;
}

float atom_distance(const Atom *a, const Atom *b)
{
    float dx = a->position[0] - b->position[0];
    float dy = a->position[1] - b->position[1];
    float dz = a->position[2] - b->position[2];
    return sqrtf(dx*dx + dy*dy + dz*dz);
}

/* ------------------------------------------------------------------ */
/* AtomicSystem                                                        */
/* ------------------------------------------------------------------ */

void as_init(AtomicSystem *as)
{
    as->capacity    = 128;
    as->count       = 0;
    as->atoms       = (Atom *)calloc((size_t)as->capacity, sizeof(Atom));
    as->temperature = T_RECOMBINATION;
    as->bonds_formed  = 0;
    as->bonds_broken  = 0;
}

void as_free(AtomicSystem *as)
{
    free(as->atoms);
    as->atoms = NULL;
    as->count = 0;
    as->capacity = 0;
}

static void as_ensure_capacity(AtomicSystem *as, int needed)
{
    if (as->count + needed <= as->capacity) return;
    int new_cap = as->capacity * 2;
    while (new_cap < as->count + needed) new_cap *= 2;
    if (new_cap > MAX_ATOMS) new_cap = MAX_ATOMS;
    as->atoms = (Atom *)realloc(as->atoms, (size_t)new_cap * sizeof(Atom));
    as->capacity = new_cap;
}

int as_add_atom(AtomicSystem *as, const Atom *a)
{
    if (as->count >= MAX_ATOMS) return -1;
    as_ensure_capacity(as, 1);
    int idx = as->count;
    as->atoms[idx] = *a;
    as->count++;
    return idx;
}

int as_nucleosynthesis(AtomicSystem *as, int protons, int neutrons)
{
    int formed = 0;

    /* Helium-4: 2p + 2n */
    while (protons >= 2 && neutrons >= 2 && as->count < MAX_ATOMS) {
        float pos[3] = { gaussf(0,10), gaussf(0,10), gaussf(0,10) };
        Atom he;
        atom_init(&he, 2, 4, pos);
        as_add_atom(as, &he);
        protons  -= 2;
        neutrons -= 2;
        formed++;
    }

    /* Remaining protons -> hydrogen */
    while (protons > 0 && as->count < MAX_ATOMS) {
        float pos[3] = { gaussf(0,10), gaussf(0,10), gaussf(0,10) };
        Atom h;
        atom_init(&h, 1, 1, pos);
        as_add_atom(as, &h);
        protons--;
        formed++;
    }

    return formed;
}

int as_recombination(AtomicSystem *as, QuantumField *qf)
{
    if (as->temperature > T_RECOMBINATION) return 0;

    int formed = 0;

    /* Collect proton and electron indices */
    for (int i = 0; i < qf->count && as->count < MAX_ATOMS; i++) {
        if (qf->particles[i].type != PTYPE_PROTON) continue;

        /* Find an electron */
        int ei = -1;
        for (int j = 0; j < qf->count; j++) {
            if (qf->particles[j].type == PTYPE_ELECTRON) {
                ei = j;
                break;
            }
        }
        if (ei < 0) break;

        Atom h;
        atom_init(&h, 1, 1, qf->particles[i].position);

        as_add_atom(as, &h);
        formed++;

        /* Remove electron first (higher index) then proton to avoid shift issues */
        if (ei > i) {
            qf_remove_particle(qf, ei);
            qf_remove_particle(qf, i);
        } else {
            qf_remove_particle(qf, i);
            qf_remove_particle(qf, ei);
        }
        /* After removal, indices shift; restart scan */
        i = -1; /* will be incremented to 0 */
    }

    return formed;
}

int as_stellar_nucleosynthesis(AtomicSystem *as, double temperature)
{
    if (temperature < 1e3) return 0;

    int formed = 0;

    /* Triple-alpha: 3 He -> C */
    {
        int he_indices[MAX_ATOMS];
        int n_he = 0;
        for (int i = 0; i < as->count; i++) {
            if (as->atoms[i].atomic_number == 2 && n_he < MAX_ATOMS)
                he_indices[n_he++] = i;
        }
        while (n_he >= 3 && randf() < 0.01f && as->count < MAX_ATOMS) {
            /* Remove 3 heliums (from end of list to avoid index issues) */
            int r2 = he_indices[--n_he];
            int r1 = he_indices[--n_he];
            int r0 = he_indices[--n_he];
            /* Sort descending for safe removal */
            if (r0 < r1) { int t = r0; r0 = r1; r1 = t; }
            if (r0 < r2) { int t = r0; r0 = r2; r2 = t; }
            if (r1 < r2) { int t = r1; r1 = r2; r2 = t; }

            /* r0 > r1 > r2: remove in descending order */
            float pos[3] = { gaussf(0,5), gaussf(0,5), gaussf(0,5) };
            /* Remove from back */
            if (r0 < as->count) { as->atoms[r0] = as->atoms[--as->count]; }
            if (r1 < as->count) { as->atoms[r1] = as->atoms[--as->count]; }
            if (r2 < as->count) { as->atoms[r2] = as->atoms[--as->count]; }

            Atom c;
            atom_init(&c, 6, 12, pos);
            as_add_atom(as, &c);
            formed++;

            /* Rebuild he_indices */
            n_he = 0;
            for (int i = 0; i < as->count; i++) {
                if (as->atoms[i].atomic_number == 2 && n_he < MAX_ATOMS)
                    he_indices[n_he++] = i;
            }
        }
    }

    /* C + He -> O */
    while (randf() < 0.02f && as->count < MAX_ATOMS) {
        int ci = -1, hi = -1;
        for (int i = 0; i < as->count; i++) {
            if (as->atoms[i].atomic_number == 6 && ci < 0) ci = i;
            if (as->atoms[i].atomic_number == 2 && hi < 0) hi = i;
        }
        if (ci < 0 || hi < 0) break;

        float pos[3];
        pos[0] = as->atoms[ci].position[0];
        pos[1] = as->atoms[ci].position[1];
        pos[2] = as->atoms[ci].position[2];

        /* Remove in descending order */
        int first = ci > hi ? ci : hi;
        int second = ci > hi ? hi : ci;
        as->atoms[first]  = as->atoms[--as->count];
        if (second < as->count)
            as->atoms[second] = as->atoms[--as->count];

        Atom o;
        atom_init(&o, 8, 16, pos);
        as_add_atom(as, &o);
        formed++;
    }

    /* O + He -> N (simplified chain) */
    if (randf() < 0.005f && as->count < MAX_ATOMS) {
        int oi = -1, hi = -1;
        for (int i = 0; i < as->count; i++) {
            if (as->atoms[i].atomic_number == 8 && oi < 0) oi = i;
            if (as->atoms[i].atomic_number == 2 && hi < 0) hi = i;
        }
        if (oi >= 0 && hi >= 0) {
            float pos[3];
            pos[0] = as->atoms[oi].position[0];
            pos[1] = as->atoms[oi].position[1];
            pos[2] = as->atoms[oi].position[2];

            int first  = oi > hi ? oi : hi;
            int second = oi > hi ? hi : oi;
            as->atoms[first] = as->atoms[--as->count];
            if (second < as->count)
                as->atoms[second] = as->atoms[--as->count];

            Atom n;
            atom_init(&n, 7, 14, pos);
            as_add_atom(as, &n);
            formed++;
        }
    }

    return formed;
}

void as_element_counts(const AtomicSystem *as, int counts[])
{
    /* counts array must be at least 27 elements (index 0..26) */
    memset(counts, 0, 27 * sizeof(int));
    for (int i = 0; i < as->count; i++) {
        int z = as->atoms[i].atomic_number;
        if (z >= 0 && z <= 26) counts[z]++;
    }
}
