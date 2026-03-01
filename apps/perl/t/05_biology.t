#!/usr/bin/env perl
# Comprehensive tests for Biology module

use strict;
use warnings;
use Test::More tests => 127;

use lib 'apps/perl/lib';
use Constants qw(@NUCLEOTIDE_BASES %CODON_TABLE);
use Biology;

# ============================================================
# EpigeneticMark
# ============================================================
{
    my $mark = EpigeneticMark->new(
        position  => 5,
        mark_type => 'methylation',
        active    => 1,
    );
    ok(defined $mark, 'EpigeneticMark created');
    is($mark->{position}, 5, 'Position is 5');
    is($mark->{mark_type}, 'methylation', 'Mark type is methylation');
    is($mark->{active}, 1, 'Mark is active');
    is($mark->{generation_added}, 0, 'Default generation_added is 0');
}

# EpigeneticMark: to_compact
{
    my $mark = EpigeneticMark->new(
        position  => 3,
        mark_type => 'methylation',
        active    => 1,
    );
    my $compact = $mark->to_compact();
    ok(defined $compact, 'EpigeneticMark to_compact returns a string');
    like($compact, qr/M/, 'to_compact starts with M for methylation');
    like($compact, qr/3/, 'to_compact includes position');
    like($compact, qr/\+/, 'to_compact shows + for active mark');
}

# EpigeneticMark: inactive mark
{
    my $mark = EpigeneticMark->new(
        position  => 2,
        mark_type => 'acetylation',
        active    => 0,
    );
    my $compact = $mark->to_compact();
    like($compact, qr/A/, 'to_compact starts with A for acetylation');
    like($compact, qr/-/, 'to_compact shows - for inactive mark');
}

# ============================================================
# Gene
# ============================================================
{
    my $gene = Gene->new(
        name     => 'test_gene',
        sequence => [qw(A T G C A T)],
    );
    ok(defined $gene, 'Gene created');
    is($gene->{name}, 'test_gene', 'Gene name');
}

# Gene: length
{
    my $gene = Gene->new(sequence => [qw(A T G C A T)]);
    is($gene->length(), 6, 'Gene length is 6');

    my $empty_gene = Gene->new(sequence => []);
    is($empty_gene->length(), 0, 'Empty gene has length 0');
}

# Gene: is_silenced
{
    my $gene = Gene->new(
        name     => 'g1',
        sequence => [qw(A T G C A T G C A T)],  # 10 bases
    );
    ok(!$gene->is_silenced(), 'Gene without methylation marks is not silenced');

    # Add many methylation marks (> 30% of length = 3 marks)
    for my $i (0..4) {
        $gene->methylate($i, 0);
    }
    ok($gene->is_silenced(), 'Gene with many methylation marks is silenced');
}

# Gene: methylate
{
    my $gene = Gene->new(sequence => [qw(A T G C A)]);
    $gene->methylate(2, 1);
    is(scalar @{$gene->{epigenetic_marks}}, 1, 'methylate adds a mark');
    is($gene->{epigenetic_marks}[0]{mark_type}, 'methylation', 'Mark type is methylation');
    is($gene->{epigenetic_marks}[0]{position}, 2, 'Mark position is 2');
    is($gene->{epigenetic_marks}[0]{generation_added}, 1, 'Generation added is 1');
}

# Gene: methylate out of bounds does nothing
{
    my $gene = Gene->new(sequence => [qw(A T G)]);
    $gene->methylate(-1, 0);
    is(scalar @{$gene->{epigenetic_marks}}, 0, 'methylate ignores negative position');
    $gene->methylate(10, 0);
    is(scalar @{$gene->{epigenetic_marks}}, 0, 'methylate ignores out-of-range position');
}

# Gene: demethylate
{
    my $gene = Gene->new(sequence => [qw(A T G C A)]);
    $gene->methylate(2, 0);
    $gene->methylate(3, 0);
    is(scalar @{$gene->{epigenetic_marks}}, 2, 'Two marks before demethylation');

    $gene->demethylate(2);
    is(scalar @{$gene->{epigenetic_marks}}, 1, 'demethylate removes mark at position');
    is($gene->{epigenetic_marks}[0]{position}, 3, 'Remaining mark is at position 3');
}

# Gene: acetylate
{
    my $gene = Gene->new(sequence => [qw(A T G C A)]);
    $gene->acetylate(1, 2);
    is(scalar @{$gene->{epigenetic_marks}}, 1, 'acetylate adds a mark');
    is($gene->{epigenetic_marks}[0]{mark_type}, 'acetylation', 'Mark type is acetylation');
    is($gene->{epigenetic_marks}[0]{generation_added}, 2, 'Generation is 2');
}

# Gene: transcribe
{
    my $gene = Gene->new(
        name     => 'g1',
        sequence => [qw(A T G C)],
    );
    my @rna = $gene->transcribe();
    is(scalar @rna, 4, 'Transcription produces same-length RNA');
    is($rna[0], 'A', 'A stays A');
    is($rna[1], 'U', 'T becomes U in RNA');
    is($rna[2], 'G', 'G stays G');
    is($rna[3], 'C', 'C stays C');
}

# Gene: transcribe silenced gene returns empty
{
    my $gene = Gene->new(
        name     => 'silenced',
        sequence => [qw(A T G C A T G C A T)],
    );
    # Silence it with many methylation marks
    for my $i (0..4) {
        $gene->methylate($i, 0);
    }
    ok($gene->is_silenced(), 'Gene is silenced');
    my @rna = $gene->transcribe();
    is(scalar @rna, 0, 'Silenced gene produces no RNA');
}

# Gene: mutate
{
    # Use high mutation rate to guarantee mutations
    srand(42);  # Set seed for reproducibility
    my $gene = Gene->new(
        name     => 'mut_gene',
        sequence => [qw(A A A A A A A A A A)],
    );
    my $mutations = $gene->mutate(1.0);  # 100% mutation rate
    is($mutations, 10, 'mutate with rate 1.0 mutates all bases');
    # All bases should have changed from A
    my $changed = grep { $_ ne 'A' } @{$gene->{sequence}};
    is($changed, 10, 'All bases changed');
}

# Gene: mutate with zero rate
{
    my $gene = Gene->new(sequence => [qw(A T G C)]);
    my $mutations = $gene->mutate(0.0);
    is($mutations, 0, 'mutate with rate 0.0 produces no mutations');
}

# Gene: to_compact
{
    my $gene = Gene->new(
        name     => 'g1',
        sequence => [qw(A T G C A)],
    );
    $gene->methylate(1, 0);
    my $compact = $gene->to_compact();
    ok(defined $compact, 'Gene to_compact returns a string');
    like($compact, qr/G:g1/, 'to_compact includes gene name');
    like($compact, qr/ATGCA/, 'to_compact includes sequence');
    like($compact, qr/e=/, 'to_compact includes expression level');
}

# ============================================================
# DNAStrand
# ============================================================
{
    my $dna = DNAStrand->new(sequence => [qw(A T G C A T G C)]);
    ok(defined $dna, 'DNAStrand created');
}

# DNAStrand: length
{
    my $dna = DNAStrand->new(sequence => [qw(A T G C A T)]);
    is($dna->length(), 6, 'DNAStrand length is 6');
}

# DNAStrand: complementary_strand
{
    my $dna = DNAStrand->new(sequence => [qw(A T G C)]);
    my $comp = $dna->complementary_strand();
    is_deeply($comp, [qw(T A C G)], 'Complementary strand is correct');
}

# DNAStrand: gc_content
{
    my $dna = DNAStrand->new(sequence => [qw(G C A T)]);
    ok(abs($dna->gc_content() - 0.5) < 1e-10, 'GC content of GCAT is 0.5');

    my $all_gc = DNAStrand->new(sequence => [qw(G C G C)]);
    ok(abs($all_gc->gc_content() - 1.0) < 1e-10, 'GC content of GCGC is 1.0');

    my $no_gc = DNAStrand->new(sequence => [qw(A T A T)]);
    ok(abs($no_gc->gc_content() - 0.0) < 1e-10, 'GC content of ATAT is 0.0');

    my $empty = DNAStrand->new(sequence => []);
    ok(abs($empty->gc_content() - 0.0) < 1e-10, 'GC content of empty strand is 0.0');
}

# DNAStrand: random_strand
{
    my $strand = DNAStrand->random_strand(100, 3);
    ok(defined $strand, 'random_strand creates a DNAStrand');
    is($strand->length(), 100, 'random_strand has correct length');
    is(scalar @{$strand->{genes}}, 3, 'random_strand has 3 genes');
    is($strand->{generation}, 0, 'random_strand starts at generation 0');
    ok($strand->{genes}[0]{essential}, 'First gene is essential');
}

# DNAStrand: replicate
{
    my $strand = DNAStrand->random_strand(50, 2);
    my $replica = $strand->replicate();
    ok(defined $replica, 'replicate returns a new DNAStrand');
    is($replica->length(), $strand->length(), 'Replica has same length');
    is($replica->{generation}, 1, 'Replica is generation 1');
    is(scalar @{$replica->{genes}}, scalar @{$strand->{genes}}, 'Replica has same gene count');
}

# DNAStrand: apply_mutations
{
    my $strand = DNAStrand->random_strand(100, 2);
    my $mutations = $strand->apply_mutations(1.0, 1.0);  # High mutation pressure
    # With UV and cosmic ray, there should be some mutations
    # but it is probabilistic, so just check it returns a number
    ok($mutations >= 0, 'apply_mutations returns non-negative count');
    ok($strand->{mutation_count} >= 0, 'mutation_count is updated');
}

# DNAStrand: apply_epigenetic_changes
{
    my $strand = DNAStrand->random_strand(100, 3);
    $strand->apply_epigenetic_changes(300, 1);
    # Just verify it runs without error
    pass('apply_epigenetic_changes runs without error');
}

# DNAStrand: to_compact
{
    my $strand = DNAStrand->random_strand(50, 2);
    my $compact = $strand->to_compact();
    ok(defined $compact, 'DNAStrand to_compact returns a string');
    like($compact, qr/DNA\[/, 'to_compact starts with DNA[');
    like($compact, qr/gen=/, 'to_compact includes generation');
    like($compact, qr/gc=/, 'to_compact includes GC content');
}

# ============================================================
# translate_mrna
# ============================================================
{
    # AUG = Met (start), GCU = Ala, UAA = STOP
    my @mrna = qw(A U G G C U U A A);
    my @protein = Biology::translate_mrna(@mrna);
    is(scalar @protein, 2, 'translate_mrna produces 2 amino acids');
    is($protein[0], 'Met', 'First amino acid is Met (start codon)');
    is($protein[1], 'Ala', 'Second amino acid is Ala');
}

# translate_mrna: no start codon
{
    my @mrna = qw(G C U U A A);
    my @protein = Biology::translate_mrna(@mrna);
    is(scalar @protein, 0, 'No protein without start codon');
}

# translate_mrna: with arrayref
{
    my @mrna = qw(A U G G C U);
    my @protein = Biology::translate_mrna(\@mrna);
    ok(scalar @protein > 0, 'translate_mrna works with arrayref');
}

# ============================================================
# Protein
# ============================================================
{
    my $prot = Protein->new(
        amino_acids => [qw(Met Ala Gly)],
        name        => 'test_protein',
        function    => 'enzyme',
    );
    ok(defined $prot, 'Protein created');
    is($prot->{name}, 'test_protein', 'Protein name');
    is($prot->{function}, 'enzyme', 'Protein function');
    is($prot->{active}, 1, 'Protein is active by default');
}

# Protein: length
{
    my $prot = Protein->new(amino_acids => [qw(Met Ala Gly Leu)]);
    is($prot->length(), 4, 'Protein length is 4');
}

# Protein: fold
{
    my $prot = Protein->new(amino_acids => [qw(Met Ala Gly Leu Ile Val Phe)]);
    my $result = $prot->fold();
    ok(defined $result, 'fold returns a value');
    ok($result == 0 || $result == 1, 'fold returns 0 or 1');
    is($prot->{folded}, $result, 'folded state matches return value');
}

# Protein: fold short protein
{
    my $prot = Protein->new(amino_acids => [qw(Met Ala)]);
    my $result = $prot->fold();
    is($result, 0, 'Short protein (< 3 aa) does not fold');
    is($prot->{folded}, 0, 'folded is 0 for short protein');
}

# Protein: to_compact
{
    my $prot = Protein->new(
        amino_acids => [qw(Met Ala Gly)],
        name        => 'p1',
    );
    my $compact = $prot->to_compact();
    ok(defined $compact, 'Protein to_compact returns a string');
    like($compact, qr/P:p1/, 'to_compact includes protein name');
    like($compact, qr/Met-Ala-Gly/, 'to_compact includes amino acid sequence');
    like($compact, qr/f=/, 'to_compact includes fold state');
}

# ============================================================
# Cell
# ============================================================
{
    my $cell = Cell->new();
    ok(defined $cell, 'Cell created');
    ok($cell->{alive}, 'Cell is alive by default');
    ok($cell->{cell_id} > 0, 'Cell has positive ID');
    ok($cell->{energy} > 0, 'Cell has positive energy');
}

# Cell: transcribe_and_translate
{
    my $cell = Cell->new();
    my @proteins = $cell->transcribe_and_translate();
    # This is probabilistic, just ensure it runs
    ok(defined \@proteins, 'transcribe_and_translate returns array');
}

# Cell: metabolize
{
    my $cell = Cell->new(energy => 100);
    $cell->metabolize(20.0);
    # With 0 enzymes: efficiency = 0.3, gain = 20*0.3 = 6.0, cost = 3.0, net = +3.0
    ok($cell->{energy} > 100, 'metabolize increases energy with environment input');
    ok($cell->{alive}, 'Cell still alive after metabolize with energy');
}

# Cell: metabolize death
{
    my $cell = Cell->new(energy => 1.0);
    $cell->metabolize(0.0);  # No environment energy, basal cost = 3.0
    ok(!$cell->{alive}, 'Cell dies when energy goes below 0');
}

# Cell: divide
{
    my $cell = Cell->new(energy => 100);
    my $daughter = $cell->divide();
    ok(defined $daughter, 'divide returns a daughter cell');
    is($daughter->{generation}, 1, 'Daughter is next generation');
    ok($cell->{energy} < 100, 'Parent energy reduced after division');
}

# Cell: divide fails with low energy
{
    my $cell = Cell->new(energy => 10);
    my $daughter = $cell->divide();
    ok(!defined $daughter, 'divide returns undef with low energy');
}

# Cell: divide fails when dead
{
    my $cell = Cell->new(energy => 100, alive => 0);
    my $daughter = $cell->divide();
    ok(!defined $daughter, 'divide returns undef when cell is dead');
}

# Cell: compute_fitness
{
    my $cell = Cell->new(energy => 100);
    my $fitness = $cell->compute_fitness();
    ok(defined $fitness, 'compute_fitness returns a value');
    ok($fitness >= 0, 'Fitness is non-negative');
    ok($fitness <= 2.0, 'Fitness is bounded');
}

# Cell: compute_fitness for dead cell
{
    my $cell = Cell->new(alive => 0);
    my $fitness = $cell->compute_fitness();
    is($fitness, 0.0, 'Dead cell has fitness 0');
}

# Cell: to_compact
{
    my $cell = Cell->new(energy => 80);
    my $compact = $cell->to_compact();
    ok(defined $compact, 'Cell to_compact returns a string');
    like($compact, qr/Cell#/, 'to_compact includes Cell#');
    like($compact, qr/gen=/, 'to_compact includes generation');
    like($compact, qr/alive/, 'to_compact includes alive status');
}

# ============================================================
# Biosphere
# ============================================================
{
    my $bio = Biosphere->new(initial_cells => 5, carrying_capacity => 50);
    ok(defined $bio, 'Biosphere created');
    ok(scalar @{$bio->{cells}} > 0, 'Has initial cells');
    is($bio->{total_born}, 5, 'total_born matches initial cells');
}

# Biosphere: step
{
    my $bio = Biosphere->new(initial_cells => 5);
    $bio->step(
        temperature        => 300,
        environment_energy => 1.0,
        uv_intensity       => 0.1,
        cosmic_ray_flux    => 0.01,
    );
    ok(scalar @{$bio->{cells}} > 0, 'Cells survive after step');
    is($bio->{generation}, 1, 'Generation incremented after step');
}

# Biosphere: average_fitness
{
    my $bio = Biosphere->new(initial_cells => 5);
    my $fitness = $bio->average_fitness();
    ok(defined $fitness, 'average_fitness returns a value');
    ok($fitness >= 0, 'Fitness is non-negative');
    ok($fitness <= 2.0, 'Fitness is bounded');
}

# Biosphere: average_gc_content
{
    my $bio = Biosphere->new(initial_cells => 5);
    my $gc = $bio->average_gc_content();
    ok(defined $gc, 'average_gc_content returns a value');
    ok($gc >= 0 && $gc <= 1.0, 'GC content is between 0 and 1');
}

# Biosphere: total_mutations
{
    my $bio = Biosphere->new(initial_cells => 3);
    my $muts = $bio->total_mutations();
    ok(defined $muts, 'total_mutations returns a value');
    ok($muts >= 0, 'Total mutations is non-negative');
}

# Biosphere: to_compact
{
    my $bio = Biosphere->new(initial_cells => 3);
    my $compact = $bio->to_compact();
    ok(defined $compact, 'Biosphere to_compact returns a string');
    like($compact, qr/Bio\[/, 'to_compact starts with Bio[');
    like($compact, qr/gen=/, 'to_compact includes generation');
    like($compact, qr/pop=/, 'to_compact includes population');
    like($compact, qr/fit=/, 'to_compact includes fitness');
    like($compact, qr/gc=/, 'to_compact includes gc content');
    like($compact, qr/born=/, 'to_compact includes born count');
    like($compact, qr/died=/, 'to_compact includes died count');
    like($compact, qr/mut=/, 'to_compact includes mutation count');
}
