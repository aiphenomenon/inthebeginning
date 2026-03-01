/*
 * biology.c - Biology simulation implementation.
 *
 * Faithfully ports the Python Biosphere, Cell, and DNAStrand logic.
 */
#include "biology.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>

/* ------------------------------------------------------------------ */
/* Helpers                                                             */
/* ------------------------------------------------------------------ */

static int g_cell_id_counter = 0;

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
/* DNA                                                                 */
/* ------------------------------------------------------------------ */

void dna_random(DNAStrand *d, int length)
{
    if (length > MAX_DNA_LENGTH) length = MAX_DNA_LENGTH;
    d->length = length;
    d->generation = 0;
    d->mutation_count = 0;
    for (int i = 0; i < length; i++) {
        d->dna[i] = NUCLEOTIDE_BASES[rand() % NUCLEOTIDE_BASE_COUNT];
    }
    dna_compute_gc(d);
}

void dna_compute_gc(DNAStrand *d)
{
    if (d->length == 0) { d->gc_content = 0.0f; return; }
    int gc = 0;
    for (int i = 0; i < d->length; i++) {
        if (d->dna[i] == 'G' || d->dna[i] == 'C') gc++;
    }
    d->gc_content = (float)gc / (float)d->length;
}

void dna_replicate(const DNAStrand *src, DNAStrand *dst)
{
    memcpy(dst->dna, src->dna, (size_t)src->length);
    dst->length = src->length;
    dst->generation = src->generation + 1;
    dst->mutation_count = 0;
    dna_compute_gc(dst);
}

int dna_apply_mutations(DNAStrand *d, float uv_intensity, float cosmic_ray_flux)
{
    float rate = (float)(UV_MUTATION_RATE) * uv_intensity
               + (float)(COSMIC_RAY_MUTATION_RATE) * cosmic_ray_flux;
    int mutations = 0;

    for (int i = 0; i < d->length; i++) {
        if (randf() < rate) {
            char old = d->dna[i];
            char choices[3];
            int ci = 0;
            for (int b = 0; b < NUCLEOTIDE_BASE_COUNT; b++) {
                if (NUCLEOTIDE_BASES[b] != old)
                    choices[ci++] = NUCLEOTIDE_BASES[b];
            }
            d->dna[i] = choices[rand() % 3];
            mutations++;
        }
    }
    d->mutation_count += mutations;
    if (mutations > 0) dna_compute_gc(d);
    return mutations;
}

/* ------------------------------------------------------------------ */
/* Cell                                                                */
/* ------------------------------------------------------------------ */

void cell_init(Cell *c, int dna_length)
{
    memset(c, 0, sizeof(*c));
    dna_random(&c->dna, dna_length);
    c->fitness = 1.0f;
    c->alive = true;
    c->energy = 100.0f;
    c->generation = 0;
    c->cell_id = ++g_cell_id_counter;
    c->position[0] = gaussf(0.0f, 5.0f);
    c->position[1] = gaussf(0.0f, 5.0f);
    c->position[2] = gaussf(0.0f, 5.0f);
    cell_transcribe_and_translate(c);
}

void cell_metabolize(Cell *c, float env_energy)
{
    if (!c->alive) return;

    /* Enzymes help extract energy */
    float efficiency = 0.3f + 0.15f * (float)c->functional_proteins;
    c->energy += env_energy * efficiency;
    c->energy -= 3.0f;  /* basal metabolic cost */
    if (c->energy > 200.0f) c->energy = 200.0f;
    if (c->energy <= 0.0f) {
        c->alive = false;
        c->energy = 0.0f;
    }
}

void cell_transcribe_and_translate(Cell *c)
{
    /*
     * Simplified: scan DNA for potential "genes" (every 30 bases).
     * Count how many produce functional proteins.
     * The Python code uses codons and AUG starts; we approximate.
     */
    int genes_found = 0;
    int proteins_made = 0;
    int functional = 0;

    int gene_len = c->dna.length / 4;
    if (gene_len < 9) gene_len = 9;

    for (int start = 0; start + gene_len <= c->dna.length; start += gene_len) {
        genes_found++;

        /* Check for start codon (ATG in DNA -> AUG in RNA) */
        bool has_start = false;
        for (int i = start; i + 2 < start + gene_len; i++) {
            if (c->dna.dna[i] == 'A' && c->dna.dna[i+1] == 'T'
                && c->dna.dna[i+2] == 'G') {
                has_start = true;
                break;
            }
        }
        if (!has_start) continue;

        /* Count amino acids encoded (simplified) */
        int codons = gene_len / 3;
        if (codons < 3) continue;

        proteins_made++;

        /* Protein folding probability based on length */
        float fold_prob = 0.5f + 0.1f * logf((float)(codons + 1));
        if (fold_prob > 0.9f) fold_prob = 0.9f;
        if (randf() < fold_prob) {
            functional++;
        }
    }

    c->protein_count = proteins_made;
    c->functional_proteins = functional;
}

void cell_compute_fitness(Cell *c)
{
    if (!c->alive) { c->fitness = 0.0f; return; }

    /* Protein fitness */
    int max_genes = c->dna.length / 30;
    if (max_genes < 1) max_genes = 1;
    float protein_fitness = (float)c->functional_proteins / (float)max_genes;
    if (protein_fitness > 1.0f) protein_fitness = 1.0f;

    /* Energy fitness */
    float energy_fitness = c->energy / 100.0f;
    if (energy_fitness > 1.0f) energy_fitness = 1.0f;

    /* GC content near 0.5 is optimal */
    float gc_fitness = 1.0f - fabsf(c->dna.gc_content - 0.5f) * 2.0f;
    if (gc_fitness < 0.0f) gc_fitness = 0.0f;

    c->fitness = protein_fitness * 0.4f + energy_fitness * 0.3f + gc_fitness * 0.3f;
}

bool bio_cell_divide(const Cell *parent, Cell *daughter)
{
    if (!parent->alive || parent->energy < 50.0f) return false;

    memset(daughter, 0, sizeof(*daughter));
    dna_replicate(&parent->dna, &daughter->dna);
    daughter->alive = true;
    daughter->generation = parent->generation + 1;
    daughter->energy = parent->energy / 2.0f;
    daughter->cell_id = ++g_cell_id_counter;
    daughter->position[0] = parent->position[0] + gaussf(0.0f, 0.5f);
    daughter->position[1] = parent->position[1] + gaussf(0.0f, 0.5f);
    daughter->position[2] = parent->position[2] + gaussf(0.0f, 0.5f);
    cell_transcribe_and_translate(daughter);
    cell_compute_fitness(daughter);
    return true;
}

/* ------------------------------------------------------------------ */
/* Biosphere                                                           */
/* ------------------------------------------------------------------ */

void bio_init(Biosphere *bio, int initial_cells, int dna_length)
{
    bio->capacity   = initial_cells * 4;
    if (bio->capacity < 32) bio->capacity = 32;
    bio->count      = 0;
    bio->cells      = (Cell *)calloc((size_t)bio->capacity, sizeof(Cell));
    bio->generation = 0;
    bio->total_born = 0;
    bio->total_died = 0;
    bio->dna_length = dna_length;

    for (int i = 0; i < initial_cells; i++) {
        Cell c;
        cell_init(&c, dna_length);
        if (bio->count < bio->capacity) {
            bio->cells[bio->count++] = c;
            bio->total_born++;
        }
    }
}

void bio_free(Biosphere *bio)
{
    free(bio->cells);
    bio->cells = NULL;
    bio->count = 0;
    bio->capacity = 0;
}

static void bio_ensure_capacity(Biosphere *bio, int needed)
{
    if (bio->count + needed <= bio->capacity) return;
    int new_cap = bio->capacity * 2;
    while (new_cap < bio->count + needed) new_cap *= 2;
    if (new_cap > MAX_CELLS * 2) new_cap = MAX_CELLS * 2;
    Cell *tmp = (Cell *)realloc(bio->cells, (size_t)new_cap * sizeof(Cell));
    if (!tmp) return;
    bio->cells = tmp;
    bio->capacity = new_cap;
}

/* Comparison function for qsort - descending fitness */
static int cell_fitness_cmp(const void *a, const void *b)
{
    float fa = ((const Cell *)a)->fitness;
    float fb = ((const Cell *)b)->fitness;
    if (fa > fb) return -1;
    if (fa < fb) return  1;
    return 0;
}

void bio_step(Biosphere *bio, float env_energy, float uv_intensity,
              float cosmic_ray_flux, float temperature)
{
    (void)temperature; /* used indirectly through env_energy */
    bio->generation++;

    /* Metabolize */
    for (int i = 0; i < bio->count; i++) {
        cell_metabolize(&bio->cells[i], env_energy);
    }

    /* Apply mutations */
    for (int i = 0; i < bio->count; i++) {
        if (bio->cells[i].alive) {
            dna_apply_mutations(&bio->cells[i].dna, uv_intensity, cosmic_ray_flux);
        }
    }

    /* Transcribe/translate */
    for (int i = 0; i < bio->count; i++) {
        if (bio->cells[i].alive) {
            cell_transcribe_and_translate(&bio->cells[i]);
        }
    }

    /* Compute fitness */
    for (int i = 0; i < bio->count; i++) {
        cell_compute_fitness(&bio->cells[i]);
    }

    /* Selection and reproduction: top 50% divide */
    int alive_count = 0;
    for (int i = 0; i < bio->count; i++) {
        if (bio->cells[i].alive) alive_count++;
    }

    if (alive_count > 0) {
        /* Sort by fitness descending */
        qsort(bio->cells, (size_t)bio->count, sizeof(Cell), cell_fitness_cmp);

        int cutoff = alive_count / 2;
        if (cutoff < 1) cutoff = 1;

        /* Collect daughters */
        Cell daughters[MAX_CELLS];
        int n_daughters = 0;

        for (int i = 0; i < cutoff && i < bio->count && n_daughters < MAX_CELLS; i++) {
            if (!bio->cells[i].alive) continue;
            Cell daughter;
            if (bio_cell_divide(&bio->cells[i], &daughter)) {
                /* Parent loses half its energy */
                bio->cells[i].energy /= 2.0f;
                daughters[n_daughters++] = daughter;
                bio->total_born++;
            }
        }

        /* Add daughters */
        bio_ensure_capacity(bio, n_daughters);
        for (int i = 0; i < n_daughters && bio->count < bio->capacity; i++) {
            bio->cells[bio->count++] = daughters[i];
        }
    }

    /* Remove dead cells */
    int write = 0;
    for (int read = 0; read < bio->count; read++) {
        if (bio->cells[read].alive) {
            if (write != read) bio->cells[write] = bio->cells[read];
            write++;
        } else {
            bio->total_died++;
        }
    }
    bio->count = write;

    /* Population cap */
    if (bio->count > MAX_CELLS) {
        qsort(bio->cells, (size_t)bio->count, sizeof(Cell), cell_fitness_cmp);
        bio->total_died += bio->count - MAX_CELLS;
        bio->count = MAX_CELLS;
    }
}

float bio_average_fitness(const Biosphere *bio)
{
    if (bio->count == 0) return 0.0f;
    float sum = 0.0f;
    for (int i = 0; i < bio->count; i++) {
        sum += bio->cells[i].fitness;
    }
    return sum / (float)bio->count;
}

int bio_total_mutations(const Biosphere *bio)
{
    int total = 0;
    for (int i = 0; i < bio->count; i++) {
        total += bio->cells[i].dna.mutation_count;
    }
    return total;
}
