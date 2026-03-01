/*
 * chemistry.h - Molecular assembly and chemical reactions.
 *
 * Models formation of molecules from atoms: water, methane, ammonia,
 * amino acids, nucleotides, and catalyzed reactions.
 */
#ifndef SIM_CHEMISTRY_H
#define SIM_CHEMISTRY_H

#include "constants.h"
#include "atomic.h"
#include <stdbool.h>

/* Molecule types */
typedef enum {
    MOL_WATER = 0,
    MOL_METHANE,
    MOL_AMMONIA,
    MOL_AMINO_ACID,
    MOL_NUCLEOTIDE,
    MOL_OTHER,
    MOL_TYPE_COUNT
} MoleculeType;

/* Molecule */
typedef struct {
    MoleculeType type;
    float        position[3];
    int          atom_count;      /* how many atoms it consumed */
    int          molecule_id;
    char         name[32];
    bool         is_organic;
} Molecule;

/* Chemical system */
typedef struct {
    AtomicSystem *atomic;     /* borrowed pointer */
    Molecule     *molecules;
    int           count;
    int           capacity;
    int           water_count;
    int           amino_acid_count;
    int           nucleotide_count;
    int           reactions_occurred;
} ChemicalSystem;

/* -- API -- */
void  cs_init(ChemicalSystem *cs, AtomicSystem *as);
void  cs_free(ChemicalSystem *cs);
int   cs_form_water(ChemicalSystem *cs);
int   cs_form_methane(ChemicalSystem *cs);
int   cs_form_ammonia(ChemicalSystem *cs);
int   cs_catalyzed_reaction(ChemicalSystem *cs, double temperature,
                            bool catalyst_present);

#endif /* SIM_CHEMISTRY_H */
