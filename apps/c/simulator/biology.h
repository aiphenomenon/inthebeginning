/*
 * biology.h - Biology simulation: DNA, cells, mutation, selection.
 *
 * Models DNA strands, gene expression, epigenetic modifications,
 * cell division with mutation, metabolism, and natural selection.
 */
#ifndef SIM_BIOLOGY_H
#define SIM_BIOLOGY_H

#include "constants.h"
#include <stdbool.h>

/* DNA strand */
typedef struct {
    char dna[MAX_DNA_LENGTH];   /* A, T, G, C */
    int  length;
    int  generation;
    int  mutation_count;
    float gc_content;           /* cached */
} DNAStrand;

/* Cell */
typedef struct {
    DNAStrand dna;
    float     fitness;
    float     position[3];
    float     energy;
    bool      alive;
    int       generation;
    int       cell_id;
    int       protein_count;       /* simplified protein tracking */
    int       functional_proteins; /* folded & active */
} Cell;

/* Biosphere */
typedef struct {
    Cell *cells;
    int   count;
    int   capacity;
    int   generation;
    int   total_born;
    int   total_died;
    int   dna_length;
} Biosphere;

/* -- DNA -- */
void  dna_random(DNAStrand *d, int length);
void  dna_replicate(const DNAStrand *src, DNAStrand *dst);
int   dna_apply_mutations(DNAStrand *d, float uv_intensity, float cosmic_ray_flux);
void  dna_compute_gc(DNAStrand *d);

/* -- Cell -- */
void  cell_init(Cell *c, int dna_length);
void  cell_metabolize(Cell *c, float env_energy);
void  cell_transcribe_and_translate(Cell *c);
void  cell_compute_fitness(Cell *c);
bool  bio_cell_divide(const Cell *parent, Cell *daughter);

/* -- Biosphere -- */
void  bio_init(Biosphere *bio, int initial_cells, int dna_length);
void  bio_free(Biosphere *bio);
void  bio_step(Biosphere *bio, float env_energy, float uv_intensity,
               float cosmic_ray_flux, float temperature);
float bio_average_fitness(const Biosphere *bio);
int   bio_total_mutations(const Biosphere *bio);

#endif /* SIM_BIOLOGY_H */
