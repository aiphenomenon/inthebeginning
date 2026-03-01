package simulator

import (
	"fmt"
	"math"
	"math/rand"
	"sort"
	"sync/atomic"
)

// EpigeneticMark represents an epigenetic modification at a specific genomic position.
type EpigeneticMark struct {
	Position        int
	MarkType        string // "methylation", "acetylation", "phosphorylation"
	Active          bool
	GenerationAdded int
}

// Gene represents a gene: a segment of DNA that encodes a protein.
type Gene struct {
	Name            string
	Sequence        []string // List of bases
	StartPos        int
	EndPos          int
	ExpressionLevel float64 // 0.0 = silenced, 1.0 = fully active
	EpigeneticMarks []EpigeneticMark
	Essential       bool
}

// NewGene creates a new gene.
func NewGene(name string, sequence []string, startPos, endPos int, essential bool) *Gene {
	g := &Gene{
		Name:            name,
		Sequence:        sequence,
		StartPos:        startPos,
		EndPos:          endPos,
		ExpressionLevel: 1.0,
		EpigeneticMarks: make([]EpigeneticMark, 0),
		Essential:       essential,
	}
	return g
}

// Length returns the gene length.
func (g *Gene) Length() int {
	return len(g.Sequence)
}

// IsSilenced returns true if the gene is heavily methylated.
func (g *Gene) IsSilenced() bool {
	methylCount := 0
	for _, m := range g.EpigeneticMarks {
		if m.MarkType == "methylation" && m.Active {
			methylCount++
		}
	}
	return float64(methylCount) > float64(g.Length())*0.3
}

// Methylate adds a methylation mark.
func (g *Gene) Methylate(position, generation int) {
	if position >= 0 && position < g.Length() {
		g.EpigeneticMarks = append(g.EpigeneticMarks, EpigeneticMark{
			Position:        position,
			MarkType:        "methylation",
			Active:          true,
			GenerationAdded: generation,
		})
		g.updateExpression()
	}
}

// Demethylate removes a methylation mark at a position.
func (g *Gene) Demethylate(position int) {
	filtered := g.EpigeneticMarks[:0]
	for _, m := range g.EpigeneticMarks {
		if !(m.Position == position && m.MarkType == "methylation") {
			filtered = append(filtered, m)
		}
	}
	g.EpigeneticMarks = filtered
	g.updateExpression()
}

// Acetylate adds histone acetylation.
func (g *Gene) Acetylate(position, generation int) {
	g.EpigeneticMarks = append(g.EpigeneticMarks, EpigeneticMark{
		Position:        position,
		MarkType:        "acetylation",
		Active:          true,
		GenerationAdded: generation,
	})
	g.updateExpression()
}

func (g *Gene) updateExpression() {
	methyl := 0
	acetyl := 0
	for _, m := range g.EpigeneticMarks {
		if m.MarkType == "methylation" && m.Active {
			methyl++
		}
		if m.MarkType == "acetylation" && m.Active {
			acetyl++
		}
	}
	length := g.Length()
	if length == 0 {
		length = 1
	}
	suppression := math.Min(1.0, float64(methyl)/float64(length)*3)
	activation := math.Min(1.0, float64(acetyl)/float64(length)*5)
	g.ExpressionLevel = math.Max(0.0, math.Min(1.0, 1.0-suppression+activation))
}

// Transcribe converts DNA to mRNA (T -> U).
func (g *Gene) Transcribe() []string {
	if g.IsSilenced() {
		return nil
	}
	rna := make([]string, len(g.Sequence))
	for i, base := range g.Sequence {
		if base == "T" {
			rna[i] = "U"
		} else {
			rna[i] = base
		}
	}
	return rna
}

// Mutate applies random point mutations. Returns mutation count.
func (g *Gene) Mutate(rate float64, rng *rand.Rand) int {
	mutations := 0
	for i := 0; i < g.Length(); i++ {
		if rng.Float64() < rate {
			old := g.Sequence[i]
			choices := make([]string, 0, 3)
			for _, b := range NucleotideBases {
				if b != old {
					choices = append(choices, b)
				}
			}
			g.Sequence[i] = choices[rng.Intn(len(choices))]
			mutations++
		}
	}
	return mutations
}

// DNAStrand represents a double-stranded DNA molecule.
type DNAStrand struct {
	Sequence      []string
	Genes         []*Gene
	Generation    int
	MutationCount int
}

// complement maps for DNA base pairing.
var complement = map[string]string{
	"A": "T", "T": "A", "G": "C", "C": "G",
}

// Length returns the DNA strand length.
func (d *DNAStrand) Length() int {
	return len(d.Sequence)
}

// GCContent returns the GC content fraction.
func (d *DNAStrand) GCContent() float64 {
	if len(d.Sequence) == 0 {
		return 0.0
	}
	gc := 0
	for _, b := range d.Sequence {
		if b == "G" || b == "C" {
			gc++
		}
	}
	return float64(gc) / float64(len(d.Sequence))
}

// RandomStrand generates a random DNA strand with genes.
func RandomStrand(length, numGenes int, rng *rand.Rand) *DNAStrand {
	sequence := make([]string, length)
	for i := range sequence {
		sequence[i] = NucleotideBases[rng.Intn(len(NucleotideBases))]
	}
	strand := &DNAStrand{Sequence: sequence, Genes: make([]*Gene, 0, numGenes)}

	geneLen := length / (numGenes + 1)
	for i := 0; i < numGenes; i++ {
		quarter := geneLen / 4
		if quarter < 1 {
			quarter = 1
		}
		start := i*geneLen + rng.Intn(quarter)
		end := start + geneLen/2
		if end > length {
			end = length
		}

		geneSeq := make([]string, end-start)
		copy(geneSeq, sequence[start:end])

		gene := NewGene(
			fmt.Sprintf("gene_%d", i),
			geneSeq,
			start,
			end,
			i == 0, // first gene is essential
		)
		strand.Genes = append(strand.Genes, gene)
	}

	return strand
}

// Replicate performs semi-conservative replication with possible errors.
func (d *DNAStrand) Replicate(rng *rand.Rand) *DNAStrand {
	newSeq := make([]string, len(d.Sequence))
	copy(newSeq, d.Sequence)

	newGenes := make([]*Gene, 0, len(d.Genes))
	for _, gene := range d.Genes {
		geneSeq := make([]string, len(gene.Sequence))
		copy(geneSeq, gene.Sequence)

		// Epigenetic marks can be partially inherited
		marks := make([]EpigeneticMark, 0)
		for _, m := range gene.EpigeneticMarks {
			if rng.Float64() < 0.7 { // Some marks lost in replication
				marks = append(marks, EpigeneticMark{
					Position:        m.Position,
					MarkType:        m.MarkType,
					Active:          m.Active && rng.Float64() < 0.8,
					GenerationAdded: m.GenerationAdded,
				})
			}
		}

		newGene := NewGene(gene.Name, geneSeq, gene.StartPos, gene.EndPos, gene.Essential)
		newGene.EpigeneticMarks = marks
		newGene.updateExpression()
		newGenes = append(newGenes, newGene)
	}

	return &DNAStrand{
		Sequence:   newSeq,
		Genes:      newGenes,
		Generation: d.Generation + 1,
	}
}

// ApplyMutations applies environmental mutations.
func (d *DNAStrand) ApplyMutations(uvIntensity, cosmicRayFlux float64, rng *rand.Rand) int {
	totalMutations := 0
	rate := UVMutationRate*uvIntensity + CosmicRayMutationRate*cosmicRayFlux

	for _, gene := range d.Genes {
		m := gene.Mutate(rate, rng)
		totalMutations += m
	}

	// Also mutate non-genic regions
	for i := 0; i < d.Length(); i++ {
		if rng.Float64() < rate {
			old := d.Sequence[i]
			choices := make([]string, 0, 3)
			for _, b := range NucleotideBases {
				if b != old {
					choices = append(choices, b)
				}
			}
			d.Sequence[i] = choices[rng.Intn(len(choices))]
			totalMutations++
		}
	}

	d.MutationCount += totalMutations
	return totalMutations
}

// ApplyEpigeneticChanges applies environmental epigenetic modifications.
func (d *DNAStrand) ApplyEpigeneticChanges(temperature float64, generation int, rng *rand.Rand) {
	for _, gene := range d.Genes {
		// Methylation
		if rng.Float64() < MethylationProbability {
			gLen := gene.Length()
			if gLen == 0 {
				gLen = 1
			}
			pos := rng.Intn(gLen)
			gene.Methylate(pos, generation)
		}

		// Demethylation
		if rng.Float64() < DemethylationProbability {
			var methyls []EpigeneticMark
			for _, m := range gene.EpigeneticMarks {
				if m.MarkType == "methylation" {
					methyls = append(methyls, m)
				}
			}
			if len(methyls) > 0 {
				mark := methyls[rng.Intn(len(methyls))]
				gene.Demethylate(mark.Position)
			}
		}

		// Histone acetylation (temperature-dependent)
		thermalFactor := math.Min(2.0, temperature/300.0)
		if rng.Float64() < HistoneAcetylationProb*thermalFactor {
			gLen := gene.Length()
			if gLen == 0 {
				gLen = 1
			}
			pos := rng.Intn(gLen)
			gene.Acetylate(pos, generation)
		}

		// Histone deacetylation
		if rng.Float64() < HistoneDeacetylationProb {
			var acetyls []*EpigeneticMark
			for i := range gene.EpigeneticMarks {
				if gene.EpigeneticMarks[i].MarkType == "acetylation" {
					acetyls = append(acetyls, &gene.EpigeneticMarks[i])
				}
			}
			if len(acetyls) > 0 {
				mark := acetyls[rng.Intn(len(acetyls))]
				mark.Active = false
				gene.updateExpression()
			}
		}
	}
}

// TranslateMRNA translates mRNA to protein (amino acid sequence).
func TranslateMRNA(mrna []string) []string {
	var protein []string
	i := 0
	started := false

	for i+2 < len(mrna) {
		codon := mrna[i] + mrna[i+1] + mrna[i+2]
		aa, ok := CodonTable[codon]

		if aa == "Met" && !started {
			started = true
			protein = append(protein, aa)
		} else if started {
			if aa == "STOP" {
				break
			} else if ok {
				protein = append(protein, aa)
			}
		}
		i += 3
	}

	return protein
}

// Protein represents a chain of amino acids.
type Protein struct {
	AminoAcids []string
	Name       string
	Function   string // "enzyme", "structural", "signaling"
	Folded     bool
	Active     bool
}

// NewProtein creates a new protein.
func NewProtein(aminoAcids []string, name, function string) *Protein {
	return &Protein{
		AminoAcids: aminoAcids,
		Name:       name,
		Function:   function,
		Active:     true,
	}
}

// Length returns the protein length.
func (p *Protein) Length() int {
	return len(p.AminoAcids)
}

// Fold performs simplified protein folding.
func (p *Protein) Fold(rng *rand.Rand) bool {
	if p.Length() < 3 {
		p.Folded = false
		return false
	}
	foldProb := math.Min(0.9, 0.5+0.1*math.Log(float64(p.Length()+1)))
	p.Folded = rng.Float64() < foldProb
	return p.Folded
}

// cellIDGen is the global cell ID counter.
var cellIDGen atomic.Int64

// Cell represents a cell with DNA, RNA, and proteins.
type Cell struct {
	DNA        *DNAStrand
	Proteins   []*Protein
	Fitness    float64
	Alive      bool
	Generation int
	Energy     float64
	ID         int64
	rng        *rand.Rand
}

// NewCell creates a new cell.
func NewCell(dna *DNAStrand, generation int, rng *rand.Rand) *Cell {
	return &Cell{
		DNA:        dna,
		Proteins:   make([]*Protein, 0),
		Fitness:    1.0,
		Alive:      true,
		Generation: generation,
		Energy:     100.0,
		ID:         cellIDGen.Add(1),
		rng:        rng,
	}
}

// TranscribeAndTranslate implements the central dogma: DNA -> mRNA -> Protein.
func (c *Cell) TranscribeAndTranslate() []*Protein {
	var newProteins []*Protein
	functions := []string{"enzyme", "structural", "signaling"}

	for _, gene := range c.DNA.Genes {
		if gene.ExpressionLevel < 0.1 {
			continue
		}

		mrna := gene.Transcribe()
		if len(mrna) == 0 {
			continue
		}

		aaSeq := TranslateMRNA(mrna)
		if len(aaSeq) == 0 {
			continue
		}

		if c.rng.Float64() > gene.ExpressionLevel {
			continue
		}

		protein := NewProtein(aaSeq, "protein_"+gene.Name, functions[c.rng.Intn(len(functions))])
		protein.Fold(c.rng)
		newProteins = append(newProteins, protein)
		c.Proteins = append(c.Proteins, protein)
	}

	return newProteins
}

// Metabolize performs basic metabolism.
func (c *Cell) Metabolize(environmentEnergy float64) {
	enzymeCount := 0
	for _, p := range c.Proteins {
		if p.Function == "enzyme" && p.Folded && p.Active {
			enzymeCount++
		}
	}
	efficiency := 0.3 + 0.15*float64(enzymeCount)
	c.Energy += environmentEnergy * efficiency
	c.Energy -= 3.0 // Basal metabolic cost
	if c.Energy > 200.0 {
		c.Energy = 200.0
	}
	if c.Energy <= 0 {
		c.Alive = false
	}
}

// Divide performs cell division with DNA replication.
func (c *Cell) Divide() *Cell {
	if !c.Alive || c.Energy < 50.0 {
		return nil
	}

	newDNA := c.DNA.Replicate(c.rng)
	c.Energy /= 2

	daughter := NewCell(newDNA, c.Generation+1, c.rng)
	daughter.Energy = c.Energy
	daughter.TranscribeAndTranslate()

	return daughter
}

// ComputeFitness computes cell fitness based on functional proteins and DNA integrity.
func (c *Cell) ComputeFitness() float64 {
	if !c.Alive {
		c.Fitness = 0.0
		return 0.0
	}

	// Essential genes must be active
	essentialActive := true
	for _, g := range c.DNA.Genes {
		if g.Essential && g.IsSilenced() {
			essentialActive = false
			break
		}
	}
	if !essentialActive {
		c.Fitness = 0.1
		return 0.1
	}

	// Fitness from proteins
	functionalProteins := 0
	for _, p := range c.Proteins {
		if p.Folded && p.Active {
			functionalProteins++
		}
	}
	numGenes := len(c.DNA.Genes)
	if numGenes == 0 {
		numGenes = 1
	}
	proteinFitness := math.Min(1.0, float64(functionalProteins)/float64(numGenes))

	// Fitness from energy
	energyFitness := math.Min(1.0, c.Energy/100.0)

	// GC content near 0.5 is optimal
	gcFitness := 1.0 - math.Abs(c.DNA.GCContent()-0.5)*2

	c.Fitness = proteinFitness*0.4 + energyFitness*0.3 + gcFitness*0.3
	return c.Fitness
}

// Biosphere is a collection of cells with population dynamics.
type Biosphere struct {
	Cells      []*Cell
	Generation int
	TotalBorn  int
	TotalDied  int
	DNALength  int
	rng        *rand.Rand
}

// NewBiosphere creates a new biosphere.
func NewBiosphere(initialCells, dnaLength int, rng *rand.Rand) *Biosphere {
	bio := &Biosphere{
		Cells:     make([]*Cell, 0, 128),
		DNALength: dnaLength,
		rng:       rng,
	}

	for i := 0; i < initialCells; i++ {
		dna := RandomStrand(dnaLength, 3, rng)
		cell := NewCell(dna, 0, rng)
		cell.TranscribeAndTranslate()
		bio.Cells = append(bio.Cells, cell)
		bio.TotalBorn++
	}

	return bio
}

// Step performs one generation step.
func (bio *Biosphere) Step(environmentEnergy, uvIntensity, cosmicRayFlux, temperature float64) {
	bio.Generation++

	// Metabolize
	for _, cell := range bio.Cells {
		cell.Metabolize(environmentEnergy)
	}

	// Apply mutations
	for _, cell := range bio.Cells {
		if cell.Alive {
			cell.DNA.ApplyMutations(uvIntensity, cosmicRayFlux, bio.rng)
			cell.DNA.ApplyEpigeneticChanges(temperature, bio.Generation, bio.rng)
		}
	}

	// Transcribe/translate (clear old proteins to prevent unbounded growth)
	for _, cell := range bio.Cells {
		if cell.Alive {
			cell.Proteins = cell.Proteins[:0]
			cell.TranscribeAndTranslate()
		}
	}

	// Compute fitness
	for _, cell := range bio.Cells {
		cell.ComputeFitness()
	}

	// Selection and reproduction
	var aliveCells []*Cell
	for _, c := range bio.Cells {
		if c.Alive {
			aliveCells = append(aliveCells, c)
		}
	}

	if len(aliveCells) > 0 {
		sort.Slice(aliveCells, func(i, j int) bool {
			return aliveCells[i].Fitness > aliveCells[j].Fitness
		})
		cutoff := len(aliveCells) / 2
		if cutoff < 1 {
			cutoff = 1
		}
		var newCells []*Cell
		for _, cell := range aliveCells[:cutoff] {
			daughter := cell.Divide()
			if daughter != nil {
				newCells = append(newCells, daughter)
				bio.TotalBorn++
			}
		}
		bio.Cells = append(bio.Cells, newCells...)
	}

	// Remove dead cells
	dead := 0
	for _, c := range bio.Cells {
		if !c.Alive {
			dead++
		}
	}
	bio.TotalDied += dead

	alive := make([]*Cell, 0, len(bio.Cells))
	for _, c := range bio.Cells {
		if c.Alive {
			alive = append(alive, c)
		}
	}
	bio.Cells = alive

	// Population cap
	if len(bio.Cells) > 100 {
		sort.Slice(bio.Cells, func(i, j int) bool {
			return bio.Cells[i].Fitness > bio.Cells[j].Fitness
		})
		bio.TotalDied += len(bio.Cells) - 100
		bio.Cells = bio.Cells[:100]
	}
}

// AverageFitness returns the average fitness of all cells.
func (bio *Biosphere) AverageFitness() float64 {
	if len(bio.Cells) == 0 {
		return 0.0
	}
	total := 0.0
	for _, c := range bio.Cells {
		total += c.Fitness
	}
	return total / float64(len(bio.Cells))
}

// AverageGCContent returns the average GC content.
func (bio *Biosphere) AverageGCContent() float64 {
	if len(bio.Cells) == 0 {
		return 0.0
	}
	total := 0.0
	for _, c := range bio.Cells {
		total += c.DNA.GCContent()
	}
	return total / float64(len(bio.Cells))
}

// TotalMutations returns the total mutations across all cells.
func (bio *Biosphere) TotalMutations() int {
	total := 0
	for _, c := range bio.Cells {
		total += c.DNA.MutationCount
	}
	return total
}

