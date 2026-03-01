/*
 * chemistry.c - Molecular assembly and chemical reactions.
 *
 * Faithfully ports the Python ChemicalSystem logic.
 */
#include "chemistry.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

/* ------------------------------------------------------------------ */
/* Helpers                                                             */
/* ------------------------------------------------------------------ */

static int g_mol_id_counter = 0;

static float randf(void)
{
    return (float)rand() / (float)RAND_MAX;
}

/* Find first unbonded atom of given atomic_number. Returns index or -1. */
static int find_unbonded(const AtomicSystem *as, int atomic_number, int max_bonds)
{
    for (int i = 0; i < as->count; i++) {
        if (as->atoms[i].atomic_number == atomic_number
            && as->atoms[i].bond_count < max_bonds)
            return i;
    }
    return -1;
}

/* Count unbonded atoms of given Z */
static int count_unbonded(const AtomicSystem *as, int z, int max_bonds)
{
    int n = 0;
    for (int i = 0; i < as->count; i++) {
        if (as->atoms[i].atomic_number == z && as->atoms[i].bond_count < max_bonds)
            n++;
    }
    return n;
}

/* ------------------------------------------------------------------ */
/* Chemical system                                                     */
/* ------------------------------------------------------------------ */

void cs_init(ChemicalSystem *cs, AtomicSystem *as)
{
    cs->atomic    = as;
    cs->capacity  = 64;
    cs->count     = 0;
    cs->molecules = (Molecule *)calloc((size_t)cs->capacity, sizeof(Molecule));
    cs->water_count         = 0;
    cs->amino_acid_count    = 0;
    cs->nucleotide_count    = 0;
    cs->reactions_occurred  = 0;
}

void cs_free(ChemicalSystem *cs)
{
    free(cs->molecules);
    cs->molecules = NULL;
    cs->count = 0;
    cs->capacity = 0;
}

static int cs_add_molecule(ChemicalSystem *cs, const Molecule *m)
{
    if (cs->count >= MAX_MOLECULES) return -1;
    if (cs->count >= cs->capacity) {
        int new_cap = cs->capacity * 2;
        if (new_cap > MAX_MOLECULES) new_cap = MAX_MOLECULES;
        Molecule *tmp = (Molecule *)realloc(cs->molecules,
                                            (size_t)new_cap * sizeof(Molecule));
        if (!tmp) return -1;
        cs->molecules = tmp;
        cs->capacity = new_cap;
    }
    int idx = cs->count;
    cs->molecules[idx] = *m;
    cs->molecules[idx].molecule_id = ++g_mol_id_counter;
    cs->count++;
    return idx;
}

/* Mark atoms as bonded (simplified: just increment bond_count) */
static void mark_bonded(AtomicSystem *as, int idx)
{
    if (idx >= 0 && idx < as->count) {
        as->atoms[idx].bond_count++;
    }
}

int cs_form_water(ChemicalSystem *cs)
{
    AtomicSystem *as = cs->atomic;
    int formed = 0;

    for (;;) {
        /* Need 2 H (unbonded) + 1 O (bonds < 2) */
        int n_h = count_unbonded(as, 1, 1);  /* H with 0 bonds */
        int n_o = count_unbonded(as, 8, 2);   /* O with < 2 bonds */
        if (n_h < 2 || n_o < 1) break;
        if (cs->count >= MAX_MOLECULES) break;

        int h1 = find_unbonded(as, 1, 1);
        mark_bonded(as, h1);
        int h2 = find_unbonded(as, 1, 1);
        mark_bonded(as, h2);
        int oi = find_unbonded(as, 8, 2);
        mark_bonded(as, oi);
        mark_bonded(as, oi); /* O gets 2 bonds */

        Molecule w = {0};
        w.type = MOL_WATER;
        w.atom_count = 3;
        strncpy(w.name, "water", sizeof(w.name) - 1);
        if (oi >= 0) {
            w.position[0] = as->atoms[oi].position[0];
            w.position[1] = as->atoms[oi].position[1];
            w.position[2] = as->atoms[oi].position[2];
        }
        cs_add_molecule(cs, &w);
        cs->water_count++;
        formed++;
    }
    return formed;
}

int cs_form_methane(ChemicalSystem *cs)
{
    AtomicSystem *as = cs->atomic;
    int formed = 0;

    for (;;) {
        int n_c = count_unbonded(as, 6, 1);
        int n_h = count_unbonded(as, 1, 1);
        if (n_c < 1 || n_h < 4) break;
        if (cs->count >= MAX_MOLECULES) break;

        int ci = find_unbonded(as, 6, 1);
        for (int b = 0; b < 4; b++) mark_bonded(as, ci);

        for (int b = 0; b < 4; b++) {
            int hi = find_unbonded(as, 1, 1);
            mark_bonded(as, hi);
        }

        Molecule m = {0};
        m.type = MOL_METHANE;
        m.atom_count = 5;
        m.is_organic = true;
        strncpy(m.name, "methane", sizeof(m.name) - 1);
        if (ci >= 0) {
            m.position[0] = as->atoms[ci].position[0];
            m.position[1] = as->atoms[ci].position[1];
            m.position[2] = as->atoms[ci].position[2];
        }
        cs_add_molecule(cs, &m);
        formed++;
    }
    return formed;
}

int cs_form_ammonia(ChemicalSystem *cs)
{
    AtomicSystem *as = cs->atomic;
    int formed = 0;

    for (;;) {
        int n_n = count_unbonded(as, 7, 1);
        int n_h = count_unbonded(as, 1, 1);
        if (n_n < 1 || n_h < 3) break;
        if (cs->count >= MAX_MOLECULES) break;

        int ni = find_unbonded(as, 7, 1);
        for (int b = 0; b < 3; b++) mark_bonded(as, ni);

        for (int b = 0; b < 3; b++) {
            int hi = find_unbonded(as, 1, 1);
            mark_bonded(as, hi);
        }

        Molecule a = {0};
        a.type = MOL_AMMONIA;
        a.atom_count = 4;
        strncpy(a.name, "ammonia", sizeof(a.name) - 1);
        if (ni >= 0) {
            a.position[0] = as->atoms[ni].position[0];
            a.position[1] = as->atoms[ni].position[1];
            a.position[2] = as->atoms[ni].position[2];
        }
        cs_add_molecule(cs, &a);
        formed++;
    }
    return formed;
}

/* Form amino acid: needs 2C + 5H + 2O + 1N (simplified glycine) */
static bool cs_form_amino_acid(ChemicalSystem *cs, const char *aa_type)
{
    AtomicSystem *as = cs->atomic;
    if (count_unbonded(as, 6, 1) < 2) return false;
    if (count_unbonded(as, 1, 1) < 5) return false;
    if (count_unbonded(as, 8, 2) < 2) return false;
    if (count_unbonded(as, 7, 1) < 1) return false;
    if (cs->count >= MAX_MOLECULES) return false;

    /* Consume atoms */
    for (int i = 0; i < 2; i++) { int ci = find_unbonded(as, 6, 1); mark_bonded(as, ci); }
    for (int i = 0; i < 5; i++) { int hi = find_unbonded(as, 1, 1); mark_bonded(as, hi); }
    for (int i = 0; i < 2; i++) { int oi = find_unbonded(as, 8, 2); mark_bonded(as, oi); }
    { int ni = find_unbonded(as, 7, 1); mark_bonded(as, ni); }

    Molecule m = {0};
    m.type = MOL_AMINO_ACID;
    m.atom_count = 10;
    m.is_organic = true;
    strncpy(m.name, aa_type, sizeof(m.name) - 1);
    cs_add_molecule(cs, &m);
    cs->amino_acid_count++;
    return true;
}

/* Form nucleotide: needs 5C + 8H + 4O + 2N (simplified) */
static bool cs_form_nucleotide(ChemicalSystem *cs, const char *base)
{
    AtomicSystem *as = cs->atomic;
    if (count_unbonded(as, 6, 1) < 5) return false;
    if (count_unbonded(as, 1, 1) < 8) return false;
    if (count_unbonded(as, 8, 2) < 4) return false;
    if (count_unbonded(as, 7, 1) < 2) return false;
    if (cs->count >= MAX_MOLECULES) return false;

    for (int i = 0; i < 5; i++) { int ci = find_unbonded(as, 6, 1); mark_bonded(as, ci); }
    for (int i = 0; i < 8; i++) { int hi = find_unbonded(as, 1, 1); mark_bonded(as, hi); }
    for (int i = 0; i < 4; i++) { int oi = find_unbonded(as, 8, 2); mark_bonded(as, oi); }
    for (int i = 0; i < 2; i++) { int ni = find_unbonded(as, 7, 1); mark_bonded(as, ni); }

    Molecule m = {0};
    m.type = MOL_NUCLEOTIDE;
    m.atom_count = 19;
    m.is_organic = true;
    snprintf(m.name, sizeof(m.name), "nuc-%s", base);
    cs_add_molecule(cs, &m);
    cs->nucleotide_count++;
    return true;
}

int cs_catalyzed_reaction(ChemicalSystem *cs, double temperature,
                          bool catalyst_present)
{
    int formed = 0;
    double ea_factor = catalyst_present ? 0.3 : 1.0;
    double thermal = SIM_K_B * temperature;

    /* Try amino acid */
    if (thermal > 0 && cs->atomic->count > 10) {
        double aa_prob = exp(-5.0 * ea_factor / (thermal + 1e-20));
        if (randf() < (float)aa_prob) {
            int idx = rand() % AMINO_ACID_COUNT;
            if (cs_form_amino_acid(cs, AMINO_ACIDS[idx])) {
                formed++;
                cs->reactions_occurred++;
            }
        }
    }

    /* Try nucleotide */
    if (thermal > 0 && cs->atomic->count > 19) {
        double nuc_prob = exp(-8.0 * ea_factor / (thermal + 1e-20));
        if (randf() < (float)nuc_prob) {
            const char *bases[] = {"A", "T", "G", "C"};
            if (cs_form_nucleotide(cs, bases[rand() % 4])) {
                formed++;
                cs->reactions_occurred++;
            }
        }
    }

    return formed;
}
