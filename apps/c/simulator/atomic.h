/*
 * atomic.h - Atomic physics: atoms, electron shells, nucleosynthesis,
 *            recombination, stellar nucleosynthesis, element counts.
 */
#ifndef SIM_ATOMIC_H
#define SIM_ATOMIC_H

#include "constants.h"
#include "quantum.h"
#include <stdbool.h>

/* Element info */
typedef struct {
    int         atomic_number;
    const char *symbol;
    const char *name;
    int         group;
    int         period;
    float       electronegativity;
} ElementInfo;

const ElementInfo *element_lookup(int z);

/* Atom */
typedef struct {
    int   atomic_number;
    int   mass_number;
    int   electron_count;
    float position[3];
    float velocity[3];
    int   bond_ids[MAX_BONDS];
    int   bond_count;
    int   atom_id;
    float ionization_energy;
} Atom;

/* Atomic system */
typedef struct {
    Atom  *atoms;
    int    count;
    int    capacity;
    double temperature;
    int    bonds_formed;
    int    bonds_broken;
} AtomicSystem;

/* -- Atom helpers -- */
void        atom_init(Atom *a, int atomic_number, int mass_number,
                      const float pos[3]);
const char *atom_symbol(const Atom *a);
float       atom_electronegativity(const Atom *a);
int         atom_valence_electrons(const Atom *a);
int         atom_needs_electrons(const Atom *a);
bool        atom_is_noble_gas(const Atom *a);
bool        atom_can_bond(const Atom *a);
float       atom_distance(const Atom *a, const Atom *b);

/* -- Atomic system API -- */
void  as_init(AtomicSystem *as);
void  as_free(AtomicSystem *as);
int   as_add_atom(AtomicSystem *as, const Atom *a);
int   as_nucleosynthesis(AtomicSystem *as, int protons, int neutrons);
int   as_recombination(AtomicSystem *as, QuantumField *qf);
int   as_stellar_nucleosynthesis(AtomicSystem *as, double temperature);
void  as_element_counts(const AtomicSystem *as, int counts[/*>=27*/]);

#endif /* SIM_ATOMIC_H */
