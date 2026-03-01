/**
 * Biology simulation - DNA, RNA, proteins, and epigenetics.
 *
 * Models:
 * - DNA strand assembly from nucleotides
 * - RNA transcription
 * - Protein translation via codon table
 * - Epigenetic modifications (methylation, histone acetylation)
 * - Cell division with mutation
 * - Natural selection pressure
 */

import {
    NUCLEOTIDE_BASES, RNA_BASES, CODON_TABLE, AMINO_ACIDS,
    METHYLATION_PROBABILITY, DEMETHYLATION_PROBABILITY,
    HISTONE_ACETYLATION_PROB, HISTONE_DEACETYLATION_PROB,
    CHROMATIN_REMODEL_ENERGY, UV_MUTATION_RATE,
    COSMIC_RAY_MUTATION_RATE, K_B,
} from './constants.js';

import { Molecule, ChemicalSystem } from './chemistry.js';


// === EpigeneticMark ===

export class EpigeneticMark {
    /** An epigenetic modification at a specific genomic position. */
    constructor(position, markType, active = true, generationAdded = 0) {
        this.position = position;
        this.markType = markType;  // "methylation", "acetylation", "phosphorylation"
        this.active = active;
        this.generationAdded = generationAdded;
    }

    toCompact() {
        const m = this.markType[0].toUpperCase();
        const state = this.active ? "+" : "-";
        return `${m}${this.position}${state}`;
    }
}


// === Gene ===

export class Gene {
    /** A gene: a segment of DNA that encodes a protein. */
    constructor({
        name,
        sequence = [],
        startPos = 0,
        endPos = 0,
        expressionLevel = 1.0,
        epigeneticMarks = [],
        essential = false,
    } = {}) {
        this.name = name;
        this.sequence = [...sequence];
        this.startPos = startPos;
        this.endPos = endPos;
        this.expressionLevel = expressionLevel;
        this.epigeneticMarks = epigeneticMarks.map(m =>
            m instanceof EpigeneticMark ? m : new EpigeneticMark(m.position, m.markType, m.active, m.generationAdded)
        );
        this.essential = essential;
    }

    get length() {
        return this.sequence.length;
    }

    /** Gene is silenced if heavily methylated. */
    get isSilenced() {
        const methylCount = this.epigeneticMarks.filter(
            m => m.markType === "methylation" && m.active
        ).length;
        return methylCount > this.length * 0.3;
    }

    /** Add methylation mark. */
    methylate(position, generation = 0) {
        if (position >= 0 && position < this.length) {
            this.epigeneticMarks.push(new EpigeneticMark(
                position,
                "methylation",
                true,
                generation,
            ));
            this._updateExpression();
        }
    }

    /** Remove methylation mark. */
    demethylate(position) {
        this.epigeneticMarks = this.epigeneticMarks.filter(
            m => !(m.position === position && m.markType === "methylation")
        );
        this._updateExpression();
    }

    /** Add histone acetylation (increases expression). */
    acetylate(position, generation = 0) {
        this.epigeneticMarks.push(new EpigeneticMark(
            position,
            "acetylation",
            true,
            generation,
        ));
        this._updateExpression();
    }

    /** Update expression level based on epigenetic marks. */
    _updateExpression() {
        const methyl = this.epigeneticMarks.filter(
            m => m.markType === "methylation" && m.active
        ).length;
        const acetyl = this.epigeneticMarks.filter(
            m => m.markType === "acetylation" && m.active
        ).length;
        // Methylation suppresses, acetylation activates
        const suppression = Math.min(1.0, methyl / Math.max(1, this.length) * 3);
        const activation = Math.min(1.0, acetyl / Math.max(1, this.length) * 5);
        this.expressionLevel = Math.max(0.0, Math.min(1.0,
            1.0 - suppression + activation));
    }

    /** Transcribe DNA to mRNA (T -> U). */
    transcribe() {
        if (this.isSilenced) return [];
        const rna = [];
        for (const base of this.sequence) {
            rna.push(base === "T" ? "U" : base);
        }
        return rna;
    }

    /** Apply random point mutations. Returns mutation count. */
    mutate(rate = 0.001) {
        let mutations = 0;
        for (let i = 0; i < this.length; i++) {
            if (Math.random() < rate) {
                const old = this.sequence[i];
                const choices = NUCLEOTIDE_BASES.filter(b => b !== old);
                this.sequence[i] = choices[Math.floor(Math.random() * choices.length)];
                mutations++;
            }
        }
        return mutations;
    }

    toCompact() {
        let seq = this.sequence.slice(0, 20).join("");
        if (this.length > 20) seq += `...(${this.length})`;
        const marks = this.epigeneticMarks.slice(0, 5).map(m => m.toCompact()).join("");
        return `G:${this.name}[${seq}]e=${this.expressionLevel.toFixed(2)}{${marks}}`;
    }
}


// === DNAStrand ===

const COMPLEMENT = { "A": "T", "T": "A", "G": "C", "C": "G" };

export class DNAStrand {
    /** A double-stranded DNA molecule. */
    constructor({
        sequence = [],
        genes = [],
        generation = 0,
        mutationCount = 0,
    } = {}) {
        this.sequence = [...sequence];
        this.genes = genes;
        this.generation = generation;
        this.mutationCount = mutationCount;
    }

    get length() {
        return this.sequence.length;
    }

    get complementaryStrand() {
        return this.sequence.map(b => COMPLEMENT[b] || "N");
    }

    get gcContent() {
        if (this.sequence.length === 0) return 0.0;
        const gc = this.sequence.filter(b => b === "G" || b === "C").length;
        return gc / this.sequence.length;
    }

    /** Generate a random DNA strand with genes. */
    static randomStrand(length, numGenes = 3) {
        const sequence = [];
        for (let i = 0; i < length; i++) {
            sequence.push(NUCLEOTIDE_BASES[Math.floor(Math.random() * NUCLEOTIDE_BASES.length)]);
        }
        const strand = new DNAStrand({ sequence });

        // Place genes along the strand
        const geneLen = Math.floor(length / (numGenes + 1));
        for (let i = 0; i < numGenes; i++) {
            const start = i * geneLen + Math.floor(Math.random() * Math.floor(geneLen / 4));
            let end = start + Math.floor(geneLen / 2);
            if (end > length) end = length;

            const gene = new Gene({
                name: `gene_${i}`,
                sequence: sequence.slice(start, end),
                startPos: start,
                endPos: end,
                essential: (i === 0),  // First gene is essential
            });
            strand.genes.push(gene);
        }

        return strand;
    }

    /** Semi-conservative replication with possible errors. */
    replicate() {
        const newSequence = [...this.sequence];
        const newGenes = [];

        for (const gene of this.genes) {
            const newMarks = [];
            for (const m of gene.epigeneticMarks) {
                // Some marks lost in replication
                if (Math.random() < 0.7) {
                    newMarks.push(new EpigeneticMark(
                        m.position,
                        m.markType,
                        m.active && Math.random() < 0.8,
                        m.generationAdded,
                    ));
                }
            }

            const newGene = new Gene({
                name: gene.name,
                sequence: [...gene.sequence],
                startPos: gene.startPos,
                endPos: gene.endPos,
                essential: gene.essential,
                epigeneticMarks: newMarks,
            });
            newGene._updateExpression();
            newGenes.push(newGene);
        }

        return new DNAStrand({
            sequence: newSequence,
            genes: newGenes,
            generation: this.generation + 1,
        });
    }

    /** Apply environmental mutations. */
    applyMutations(uvIntensity = 0.0, cosmicRayFlux = 0.0) {
        let totalMutations = 0;
        const rate = UV_MUTATION_RATE * uvIntensity
            + COSMIC_RAY_MUTATION_RATE * cosmicRayFlux;

        for (const gene of this.genes) {
            const m = gene.mutate(rate);
            totalMutations += m;
        }

        // Also mutate non-genic regions
        for (let i = 0; i < this.length; i++) {
            if (Math.random() < rate) {
                const old = this.sequence[i];
                const choices = NUCLEOTIDE_BASES.filter(b => b !== old);
                this.sequence[i] = choices[Math.floor(Math.random() * choices.length)];
                totalMutations++;
            }
        }

        this.mutationCount += totalMutations;
        return totalMutations;
    }

    /** Environmental epigenetic modifications. */
    applyEpigeneticChanges(temperature, generation = 0) {
        for (const gene of this.genes) {
            // Methylation
            if (Math.random() < METHYLATION_PROBABILITY) {
                const pos = Math.floor(Math.random() * Math.max(1, gene.length));
                gene.methylate(pos, generation);
            }

            // Demethylation
            if (Math.random() < DEMETHYLATION_PROBABILITY) {
                if (gene.epigeneticMarks.length > 0) {
                    const methyls = gene.epigeneticMarks.filter(
                        m => m.markType === "methylation"
                    );
                    if (methyls.length > 0) {
                        const mark = methyls[Math.floor(Math.random() * methyls.length)];
                        gene.demethylate(mark.position);
                    }
                }
            }

            // Histone acetylation (temperature-dependent)
            const thermalFactor = Math.min(2.0, temperature / 300.0);
            if (Math.random() < HISTONE_ACETYLATION_PROB * thermalFactor) {
                const pos = Math.floor(Math.random() * Math.max(1, gene.length));
                gene.acetylate(pos, generation);
            }

            // Histone deacetylation
            if (Math.random() < HISTONE_DEACETYLATION_PROB) {
                const acetyls = gene.epigeneticMarks.filter(
                    m => m.markType === "acetylation"
                );
                if (acetyls.length > 0) {
                    const mark = acetyls[Math.floor(Math.random() * acetyls.length)];
                    mark.active = false;
                    gene._updateExpression();
                }
            }
        }
    }

    toCompact() {
        let seq = this.sequence.slice(0, 30).join("");
        if (this.length > 30) seq += `...(${this.length})`;
        const genes = this.genes.slice(0, 5).map(g => g.toCompact()).join("|");
        return (
            `DNA[gen=${this.generation} mut=${this.mutationCount} `
            + `gc=${this.gcContent.toFixed(2)} ${seq}]{${genes}}`
        );
    }
}


// === translate mRNA ===

export function translateMrna(mrna) {
    /** Translate mRNA to protein (amino acid sequence). */
    const protein = [];
    let i = 0;
    let started = false;

    while (i + 2 < mrna.length) {
        const codon = mrna[i] + mrna[i + 1] + mrna[i + 2];
        const aa = CODON_TABLE[codon];

        if (aa === "Met" && !started) {
            started = true;
            protein.push(aa);
        } else if (started) {
            if (aa === "STOP") break;
            if (aa) protein.push(aa);
        }
        i += 3;
    }

    return protein;
}


// === Protein ===

export class Protein {
    /** A protein: a chain of amino acids. */
    constructor({
        aminoAcids = [],
        name = "",
        func = "",  // "enzyme", "structural", "signaling"
        folded = false,
        active = true,
    } = {}) {
        this.aminoAcids = [...aminoAcids];
        this.name = name;
        this.function = func;
        this.folded = folded;
        this.active = active;
    }

    get length() {
        return this.aminoAcids.length;
    }

    /** Simplified protein folding - probability based on length. */
    fold() {
        if (this.length < 3) {
            this.folded = false;
            return false;
        }
        const foldProb = Math.min(0.9, 0.5 + 0.1 * Math.log(this.length + 1));
        this.folded = Math.random() < foldProb;
        return this.folded;
    }

    toCompact() {
        let seq = this.aminoAcids.slice(0, 10).join("-");
        if (this.length > 10) seq += `...(${this.length})`;
        return `P:${this.name}[${seq}]f=${this.folded ? "Y" : "N"}`;
    }
}


// === Cell ===

let cellIdCounter = 0;

export class Cell {
    /** A cell with DNA, RNA, and proteins. */
    constructor({
        dna = null,
        proteins = [],
        fitness = 1.0,
        alive = true,
        generation = 0,
        energy = 100.0,
    } = {}) {
        this.dna = dna || DNAStrand.randomStrand(100);
        this.proteins = [...proteins];
        this.fitness = fitness;
        this.alive = alive;
        this.generation = generation;
        this.energy = energy;

        cellIdCounter++;
        this.cellId = cellIdCounter;
    }

    /** Central dogma: DNA -> mRNA -> Protein. */
    transcribeAndTranslate() {
        const newProteins = [];
        for (const gene of this.dna.genes) {
            if (gene.expressionLevel < 0.1) continue;  // Silenced

            // Transcribe
            const mrna = gene.transcribe();
            if (mrna.length === 0) continue;

            // Translate
            const aaSeq = translateMrna(mrna);
            if (aaSeq.length === 0) continue;

            // Probability of producing protein scales with expression
            if (Math.random() > gene.expressionLevel) continue;

            const functions = ["enzyme", "structural", "signaling"];
            const protein = new Protein({
                aminoAcids: aaSeq,
                name: `protein_${gene.name}`,
                func: functions[Math.floor(Math.random() * functions.length)],
            });
            protein.fold();
            newProteins.push(protein);
            this.proteins.push(protein);
        }
        return newProteins;
    }

    /** Basic metabolism: consume energy, produce waste. */
    metabolize(environmentEnergy = 10.0) {
        // Enzymes help extract energy
        const enzymeCount = this.proteins.filter(
            p => p.function === "enzyme" && p.folded && p.active
        ).length;
        const efficiency = 0.3 + 0.15 * enzymeCount;
        this.energy += environmentEnergy * efficiency;
        this.energy -= 3.0;  // Basal metabolic cost
        this.energy = Math.min(this.energy, 200.0);  // Energy cap

        if (this.energy <= 0) {
            this.alive = false;
        }
    }

    /** Cell division with DNA replication and possible mutation. */
    divide() {
        if (!this.alive || this.energy < 50.0) return null;

        const newDna = this.dna.replicate();
        this.energy /= 2;  // Split energy

        const daughter = new Cell({
            dna: newDna,
            generation: this.generation + 1,
            energy: this.energy,
        });

        // Daughter transcribes its own proteins
        daughter.transcribeAndTranslate();

        return daughter;
    }

    /** Compute cell fitness based on functional proteins and DNA integrity. */
    computeFitness() {
        if (!this.alive) {
            this.fitness = 0.0;
            return 0.0;
        }

        // Essential genes must be active
        const essentialActive = this.dna.genes
            .filter(g => g.essential)
            .every(g => !g.isSilenced);
        if (!essentialActive) {
            this.fitness = 0.1;
            return 0.1;
        }

        // Fitness from proteins
        const functionalProteins = this.proteins.filter(
            p => p.folded && p.active
        ).length;
        const proteinFitness = Math.min(1.0,
            functionalProteins / Math.max(1, this.dna.genes.length));

        // Fitness from energy
        const energyFitness = Math.min(1.0, this.energy / 100.0);

        // GC content near 0.5 is optimal
        const gcFitness = 1.0 - Math.abs(this.dna.gcContent - 0.5) * 2;

        this.fitness = proteinFitness * 0.4 + energyFitness * 0.3 + gcFitness * 0.3;
        return this.fitness;
    }

    toCompact() {
        return (
            `Cell#${this.cellId}[gen=${this.generation} `
            + `fit=${this.fitness.toFixed(2)} E=${this.energy.toFixed(0)} `
            + `prot=${this.proteins.length} `
            + `${this.alive ? "alive" : "dead"}]`
        );
    }
}

/** Reset cell ID counter (useful for tests). */
export function resetCellIdCounter() {
    cellIdCounter = 0;
}


// === Biosphere ===

export class Biosphere {
    /** Collection of cells with population dynamics. */
    constructor(initialCells = 5, dnaLength = 90) {
        this.cells = [];
        this.generation = 0;
        this.totalBorn = 0;
        this.totalDied = 0;
        this.dnaLength = dnaLength;

        for (let i = 0; i < initialCells; i++) {
            const cell = new Cell({
                dna: DNAStrand.randomStrand(dnaLength, 3),
            });
            cell.transcribeAndTranslate();
            this.cells.push(cell);
            this.totalBorn++;
        }
    }

    /** One generation step. */
    step(environmentEnergy = 10.0, uvIntensity = 0.0,
         cosmicRayFlux = 0.0, temperature = 300.0) {
        this.generation++;

        // Metabolize
        for (const cell of this.cells) {
            cell.metabolize(environmentEnergy);
        }

        // Apply mutations
        for (const cell of this.cells) {
            if (cell.alive) {
                cell.dna.applyMutations(uvIntensity, cosmicRayFlux);
                cell.dna.applyEpigeneticChanges(temperature, this.generation);
            }
        }

        // Transcribe/translate (clear old proteins to prevent unbounded growth)
        for (const cell of this.cells) {
            if (cell.alive) {
                cell.proteins = [];
                cell.transcribeAndTranslate();
            }
        }

        // Compute fitness
        for (const cell of this.cells) {
            cell.computeFitness();
        }

        // Selection and reproduction
        const aliveCells = this.cells.filter(c => c.alive);
        if (aliveCells.length > 0) {
            // Top 50% reproduce
            aliveCells.sort((a, b) => b.fitness - a.fitness);
            const cutoff = Math.max(1, Math.floor(aliveCells.length / 2));
            const newCells = [];
            for (const cell of aliveCells.slice(0, cutoff)) {
                const daughter = cell.divide();
                if (daughter) {
                    newCells.push(daughter);
                    this.totalBorn++;
                }
            }
            this.cells.push(...newCells);
        }

        // Remove dead cells
        const dead = this.cells.filter(c => !c.alive);
        this.totalDied += dead.length;
        this.cells = this.cells.filter(c => c.alive);

        // Population cap
        if (this.cells.length > 100) {
            this.cells.sort((a, b) => b.fitness - a.fitness);
            const overflow = this.cells.slice(100);
            this.totalDied += overflow.length;
            this.cells = this.cells.slice(0, 100);
        }
    }

    averageFitness() {
        if (this.cells.length === 0) return 0.0;
        return this.cells.reduce((s, c) => s + c.fitness, 0) / this.cells.length;
    }

    averageGcContent() {
        if (this.cells.length === 0) return 0.0;
        return this.cells.reduce((s, c) => s + c.dna.gcContent, 0) / this.cells.length;
    }

    totalMutations() {
        return this.cells.reduce((s, c) => s + c.dna.mutationCount, 0);
    }

    toCompact() {
        return (
            `Bio[gen=${this.generation} pop=${this.cells.length} `
            + `fit=${this.averageFitness().toFixed(3)} `
            + `gc=${this.averageGcContent().toFixed(2)} `
            + `born=${this.totalBorn} died=${this.totalDied} `
            + `mut=${this.totalMutations()}]`
        );
    }
}
