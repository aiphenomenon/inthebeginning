package Biology;

# Biology simulation - DNA, RNA, proteins, and epigenetics.
#
# Models:
# - DNA strand assembly from nucleotides
# - RNA transcription
# - Protein translation via codon table
# - Epigenetic modifications (methylation, histone acetylation)
# - Cell division with mutation
# - Natural selection pressure

use strict;
use warnings;
use POSIX qw();
use List::Util qw(sum min max);

use Constants qw(
    @NUCLEOTIDE_BASES @RNA_BASES %CODON_TABLE @AMINO_ACIDS
    $METHYLATION_PROBABILITY $DEMETHYLATION_PROBABILITY
    $HISTONE_ACETYLATION_PROB $HISTONE_DEACETYLATION_PROB
    $CHROMATIN_REMODEL_ENERGY $UV_MUTATION_RATE
    $COSMIC_RAY_MUTATION_RATE $K_B
);

# ============================================================
# EpigeneticMark
# ============================================================
package EpigeneticMark;

sub new {
    my ($class, %args) = @_;
    return bless {
        position         => $args{position},
        mark_type        => $args{mark_type},        # "methylation", "acetylation", etc
        active           => exists $args{active} ? $args{active} : 1,
        generation_added => $args{generation_added} // 0,
    }, $class;
}

sub to_compact {
    my ($self) = @_;
    my $m = uc(substr($self->{mark_type}, 0, 1));
    my $state = $self->{active} ? '+' : '-';
    return "$m$self->{position}$state";
}

# ============================================================
# Gene
# ============================================================
package Gene;
use List::Util qw(min max);
use Constants qw(@NUCLEOTIDE_BASES);

sub new {
    my ($class, %args) = @_;
    my $self = bless {
        name             => $args{name},
        sequence         => $args{sequence}         || [],
        start_pos        => $args{start_pos}        // 0,
        end_pos          => $args{end_pos}          // 0,
        expression_level => $args{expression_level} // 1.0,
        epigenetic_marks => $args{epigenetic_marks} || [],
        essential        => $args{essential}        // 0,
    }, $class;
    return $self;
}

sub length {
    my ($self) = @_;
    return scalar @{$self->{sequence}};
}

sub is_silenced {
    my ($self) = @_;
    my $methyl_count = 0;
    for my $m (@{$self->{epigenetic_marks}}) {
        $methyl_count++ if $m->{mark_type} eq 'methylation' && $m->{active};
    }
    return $methyl_count > $self->length() * 0.3 ? 1 : 0;
}

sub methylate {
    my ($self, $position, $generation) = @_;
    $generation //= 0;
    if ($position >= 0 && $position < $self->length()) {
        push @{$self->{epigenetic_marks}}, EpigeneticMark->new(
            position         => $position,
            mark_type        => 'methylation',
            generation_added => $generation,
        );
        $self->_update_expression();
    }
}

sub demethylate {
    my ($self, $position) = @_;
    $self->{epigenetic_marks} = [
        grep {
            !($_->{position} == $position && $_->{mark_type} eq 'methylation')
        } @{$self->{epigenetic_marks}}
    ];
    $self->_update_expression();
}

sub acetylate {
    my ($self, $position, $generation) = @_;
    $generation //= 0;
    push @{$self->{epigenetic_marks}}, EpigeneticMark->new(
        position         => $position,
        mark_type        => 'acetylation',
        generation_added => $generation,
    );
    $self->_update_expression();
}

sub _update_expression {
    my ($self) = @_;
    my $methyl = 0;
    my $acetyl = 0;
    for my $m (@{$self->{epigenetic_marks}}) {
        $methyl++ if $m->{mark_type} eq 'methylation'  && $m->{active};
        $acetyl++ if $m->{mark_type} eq 'acetylation'  && $m->{active};
    }
    my $len = $self->length() || 1;
    my $suppression = min(1.0, $methyl / $len * 3);
    my $activation  = min(1.0, $acetyl / $len * 5);
    $self->{expression_level} = max(0.0, min(1.0, 1.0 - $suppression + $activation));
}

sub transcribe {
    my ($self) = @_;
    return () if $self->is_silenced();
    my @rna;
    for my $base (@{$self->{sequence}}) {
        if ($base eq 'T') {
            push @rna, 'U';
        } else {
            push @rna, $base;
        }
    }
    return @rna;
}

sub mutate {
    my ($self, $rate) = @_;
    $rate //= 0.001;
    my $mutations = 0;
    for my $i (0 .. $self->length() - 1) {
        if (rand() < $rate) {
            my $old = $self->{sequence}[$i];
            my @choices = grep { $_ ne $old } @NUCLEOTIDE_BASES;
            $self->{sequence}[$i] = $choices[int(rand(scalar @choices))];
            $mutations++;
        }
    }
    return $mutations;
}

sub to_compact {
    my ($self) = @_;
    my $seq = join('', @{$self->{sequence}}[0 .. min(19, $self->length() - 1)]);
    if ($self->length() > 20) {
        $seq .= sprintf("...(%d)", $self->length());
    }
    my @mark_strs;
    my $limit = min(4, $#{$self->{epigenetic_marks}});
    for my $i (0 .. $limit) {
        push @mark_strs, $self->{epigenetic_marks}[$i]->to_compact();
    }
    my $marks = join('', @mark_strs);
    return sprintf("G:%s[%s]e=%.2f{%s}",
        $self->{name}, $seq, $self->{expression_level}, $marks);
}

# ============================================================
# DNAStrand
# ============================================================
package DNAStrand;
use List::Util qw(min max);
use Constants qw(
    @NUCLEOTIDE_BASES $UV_MUTATION_RATE $COSMIC_RAY_MUTATION_RATE
    $METHYLATION_PROBABILITY $DEMETHYLATION_PROBABILITY
    $HISTONE_ACETYLATION_PROB $HISTONE_DEACETYLATION_PROB
);

my %COMPLEMENT = ('A' => 'T', 'T' => 'A', 'G' => 'C', 'C' => 'G');

sub new {
    my ($class, %args) = @_;
    return bless {
        sequence       => $args{sequence}       || [],
        genes          => $args{genes}          || [],
        generation     => $args{generation}     // 0,
        mutation_count => $args{mutation_count} // 0,
    }, $class;
}

sub length {
    my ($self) = @_;
    return scalar @{$self->{sequence}};
}

sub complementary_strand {
    my ($self) = @_;
    return [ map { $COMPLEMENT{$_} // 'N' } @{$self->{sequence}} ];
}

sub gc_content {
    my ($self) = @_;
    return 0.0 unless @{$self->{sequence}};
    my $gc = grep { $_ eq 'G' || $_ eq 'C' } @{$self->{sequence}};
    return $gc / scalar(@{$self->{sequence}});
}

sub random_strand {
    my ($class, $length, $num_genes) = @_;
    $num_genes //= 3;
    my @sequence = map { $NUCLEOTIDE_BASES[int(rand(scalar @NUCLEOTIDE_BASES))] } (1..$length);
    my $strand = $class->new(sequence => \@sequence);

    # Place genes along the strand
    my $gene_len = int($length / ($num_genes + 1));
    for my $i (0 .. $num_genes - 1) {
        my $start = $i * $gene_len + int(rand($gene_len / 4 + 1));
        my $end   = $start + int($gene_len / 2);
        $end = $length if $end > $length;

        my @gene_seq = @sequence[$start .. $end - 1];
        my $gene = Gene->new(
            name      => "gene_$i",
            sequence  => \@gene_seq,
            start_pos => $start,
            end_pos   => $end,
            essential => ($i == 0 ? 1 : 0),   # First gene is essential
        );
        push @{$strand->{genes}}, $gene;
    }

    return $strand;
}

sub replicate {
    my ($self) = @_;
    my @new_sequence = @{$self->{sequence}};
    my @new_genes;

    for my $gene (@{$self->{genes}}) {
        my @inherited_marks;
        for my $m (@{$gene->{epigenetic_marks}}) {
            next unless rand() < 0.7;  # Some marks lost in replication
            push @inherited_marks, EpigeneticMark->new(
                position         => $m->{position},
                mark_type        => $m->{mark_type},
                active           => ($m->{active} && rand() < 0.8) ? 1 : 0,
                generation_added => $m->{generation_added},
            );
        }

        my $new_gene = Gene->new(
            name             => $gene->{name},
            sequence         => [@{$gene->{sequence}}],
            start_pos        => $gene->{start_pos},
            end_pos          => $gene->{end_pos},
            essential        => $gene->{essential},
            epigenetic_marks => \@inherited_marks,
        );
        $new_gene->_update_expression();
        push @new_genes, $new_gene;
    }

    return DNAStrand->new(
        sequence   => \@new_sequence,
        genes      => \@new_genes,
        generation => $self->{generation} + 1,
    );
}

sub apply_mutations {
    my ($self, $uv_intensity, $cosmic_ray_flux) = @_;
    $uv_intensity   //= 0.0;
    $cosmic_ray_flux //= 0.0;
    my $total_mutations = 0;
    my $rate = $UV_MUTATION_RATE * $uv_intensity
             + $COSMIC_RAY_MUTATION_RATE * $cosmic_ray_flux;

    for my $gene (@{$self->{genes}}) {
        $total_mutations += $gene->mutate($rate);
    }

    # Also mutate non-genic regions
    for my $i (0 .. $self->length() - 1) {
        if (rand() < $rate) {
            my $old = $self->{sequence}[$i];
            my @choices = grep { $_ ne $old } @NUCLEOTIDE_BASES;
            $self->{sequence}[$i] = $choices[int(rand(scalar @choices))];
            $total_mutations++;
        }
    }

    $self->{mutation_count} += $total_mutations;
    return $total_mutations;
}

sub apply_epigenetic_changes {
    my ($self, $temperature, $generation) = @_;
    $generation //= 0;

    for my $gene (@{$self->{genes}}) {
        # Methylation
        if (rand() < $METHYLATION_PROBABILITY) {
            my $gene_len = $gene->length();
            my $pos = int(rand(max(1, $gene_len)));
            $gene->methylate($pos, $generation);
        }

        # Demethylation
        if (rand() < $DEMETHYLATION_PROBABILITY) {
            if (@{$gene->{epigenetic_marks}}) {
                my @methyls = grep { $_->{mark_type} eq 'methylation' }
                              @{$gene->{epigenetic_marks}};
                if (@methyls) {
                    my $mark = $methyls[int(rand(scalar @methyls))];
                    $gene->demethylate($mark->{position});
                }
            }
        }

        # Histone acetylation (temperature-dependent)
        my $thermal_factor = min(2.0, $temperature / 300.0);
        if (rand() < $HISTONE_ACETYLATION_PROB * $thermal_factor) {
            my $gene_len = $gene->length();
            my $pos = int(rand(max(1, $gene_len)));
            $gene->acetylate($pos, $generation);
        }

        # Histone deacetylation
        if (rand() < $HISTONE_DEACETYLATION_PROB) {
            my @acetyls = grep { $_->{mark_type} eq 'acetylation' }
                          @{$gene->{epigenetic_marks}};
            if (@acetyls) {
                my $mark = $acetyls[int(rand(scalar @acetyls))];
                $mark->{active} = 0;
                $gene->_update_expression();
            }
        }
    }
}

sub to_compact {
    my ($self) = @_;
    my $len = $self->length();
    my $show = min(29, $len - 1);
    my $seq = join('', @{$self->{sequence}}[0 .. $show]);
    if ($len > 30) {
        $seq .= sprintf("...(%d)", $len);
    }
    my @gene_strs;
    my $glimit = min(4, $#{$self->{genes}});
    for my $i (0 .. $glimit) {
        push @gene_strs, $self->{genes}[$i]->to_compact();
    }
    my $genes = join('|', @gene_strs);
    return sprintf("DNA[gen=%d mut=%d gc=%.2f %s]{%s}",
        $self->{generation}, $self->{mutation_count},
        $self->gc_content(), $seq, $genes);
}

# ============================================================
# translate_mrna - free function
# ============================================================
package Biology;
use Constants qw(%CODON_TABLE);

sub translate_mrna {
    my (@mrna) = @_;
    # If called with array ref, dereference
    if (ref($mrna[0]) eq 'ARRAY') {
        @mrna = @{$mrna[0]};
    }
    my @protein;
    my $i = 0;
    my $started = 0;

    while ($i + 2 < scalar @mrna) {
        my $codon = $mrna[$i] . $mrna[$i+1] . $mrna[$i+2];
        my $aa = $CODON_TABLE{$codon};

        if (defined $aa && $aa eq 'Met' && !$started) {
            $started = 1;
            push @protein, $aa;
        } elsif ($started) {
            if (defined $aa && $aa eq 'STOP') {
                last;
            } elsif (defined $aa) {
                push @protein, $aa;
            }
        }
        $i += 3;
    }

    return @protein;
}

# ============================================================
# Protein
# ============================================================
package Protein;
use List::Util qw(min);

sub new {
    my ($class, %args) = @_;
    my $self = bless {
        amino_acids => $args{amino_acids} || [],
        name        => $args{name}        // '',
        function    => $args{function}    // '',    # "enzyme", "structural", "signaling"
        folded      => $args{folded}      // 0,
        active      => exists $args{active} ? $args{active} : 1,
    }, $class;
    return $self;
}

sub length {
    my ($self) = @_;
    return scalar @{$self->{amino_acids}};
}

sub fold {
    my ($self) = @_;
    if ($self->length() < 3) {
        $self->{folded} = 0;
        return 0;
    }
    my $fold_prob = min(0.9, 0.5 + 0.1 * log($self->length() + 1));
    $self->{folded} = rand() < $fold_prob ? 1 : 0;
    return $self->{folded};
}

sub to_compact {
    my ($self) = @_;
    my $limit = min(9, $self->length() - 1);
    my $seq = join('-', @{$self->{amino_acids}}[0 .. $limit]);
    if ($self->length() > 10) {
        $seq .= sprintf("...(%d)", $self->length());
    }
    my $f = $self->{folded} ? 'Y' : 'N';
    return sprintf("P:%s[%s]f=%s", $self->{name}, $seq, $f);
}

# ============================================================
# Cell
# ============================================================
package Cell;
use List::Util qw(min);

my $_cell_id_counter = 0;

sub new {
    my ($class, %args) = @_;
    $_cell_id_counter++;
    my $self = bless {
        dna        => $args{dna} || DNAStrand->random_strand(100),
        proteins   => $args{proteins}   || [],
        fitness    => $args{fitness}     // 1.0,
        alive      => exists $args{alive} ? $args{alive} : 1,
        generation => $args{generation}  // 0,
        energy     => $args{energy}      // 100.0,
        cell_id    => $_cell_id_counter,
    }, $class;
    return $self;
}

sub transcribe_and_translate {
    my ($self) = @_;
    my @new_proteins;
    my @functions = ('enzyme', 'structural', 'signaling');

    for my $gene (@{$self->{dna}{genes}}) {
        next if $gene->{expression_level} < 0.1;  # Silenced

        # Transcribe
        my @mrna = $gene->transcribe();
        next unless @mrna;

        # Translate
        my @aa_seq = Biology::translate_mrna(\@mrna);
        next unless @aa_seq;

        # Probability of producing protein scales with expression
        next if rand() > $gene->{expression_level};

        my $protein = Protein->new(
            amino_acids => \@aa_seq,
            name        => "protein_$gene->{name}",
            function    => $functions[int(rand(scalar @functions))],
        );
        $protein->fold();
        push @new_proteins, $protein;
        push @{$self->{proteins}}, $protein;
    }

    return @new_proteins;
}

sub metabolize {
    my ($self, $environment_energy) = @_;
    $environment_energy //= 10.0;

    my $enzyme_count = 0;
    for my $p (@{$self->{proteins}}) {
        $enzyme_count++ if $p->{function} eq 'enzyme' && $p->{folded} && $p->{active};
    }
    my $efficiency = 0.3 + 0.15 * $enzyme_count;
    $self->{energy} += $environment_energy * $efficiency;
    $self->{energy} -= 3.0;  # Basal metabolic cost
    $self->{energy} = 200.0 if $self->{energy} > 200.0;

    if ($self->{energy} <= 0) {
        $self->{alive} = 0;
    }
}

sub divide {
    my ($self) = @_;
    return undef unless $self->{alive} && $self->{energy} >= 50.0;

    my $new_dna = $self->{dna}->replicate();
    $self->{energy} /= 2;

    my $daughter = Cell->new(
        dna        => $new_dna,
        generation => $self->{generation} + 1,
        energy     => $self->{energy},
    );

    $daughter->transcribe_and_translate();
    return $daughter;
}

sub compute_fitness {
    my ($self) = @_;
    if (!$self->{alive}) {
        $self->{fitness} = 0.0;
        return 0.0;
    }

    # Essential genes must be active
    my $essential_active = 1;
    for my $g (@{$self->{dna}{genes}}) {
        if ($g->{essential} && $g->is_silenced()) {
            $essential_active = 0;
            last;
        }
    }
    unless ($essential_active) {
        $self->{fitness} = 0.1;
        return 0.1;
    }

    # Fitness from proteins
    my $functional_proteins = 0;
    for my $p (@{$self->{proteins}}) {
        $functional_proteins++ if $p->{folded} && $p->{active};
    }
    my $num_genes = scalar(@{$self->{dna}{genes}}) || 1;
    my $protein_fitness = min(1.0, $functional_proteins / $num_genes);

    # Fitness from energy
    my $energy_fitness = min(1.0, $self->{energy} / 100.0);

    # GC content near 0.5 is optimal
    my $gc_fitness = 1.0 - abs($self->{dna}->gc_content() - 0.5) * 2;

    $self->{fitness} = $protein_fitness * 0.4 + $energy_fitness * 0.3
                     + $gc_fitness * 0.3;
    return $self->{fitness};
}

sub to_compact {
    my ($self) = @_;
    my $state = $self->{alive} ? 'alive' : 'dead';
    return sprintf("Cell#%d[gen=%d fit=%.2f E=%.0f prot=%d %s]",
        $self->{cell_id}, $self->{generation}, $self->{fitness},
        $self->{energy}, scalar(@{$self->{proteins}}), $state);
}

# ============================================================
# Biosphere
# ============================================================
package Biosphere;
use List::Util qw(max);

sub new {
    my ($class, %args) = @_;
    my $initial_cells = $args{initial_cells} // 5;
    my $dna_length    = $args{dna_length}    // 90;

    my $self = bless {
        cells       => [],
        generation  => 0,
        total_born  => 0,
        total_died  => 0,
        dna_length  => $dna_length,
    }, $class;

    for (1 .. $initial_cells) {
        my $cell = Cell->new(
            dna => DNAStrand->random_strand($dna_length, 3),
        );
        $cell->transcribe_and_translate();
        push @{$self->{cells}}, $cell;
        $self->{total_born}++;
    }

    return $self;
}

sub step {
    my ($self, %args) = @_;
    my $environment_energy = $args{environment_energy} // 10.0;
    my $uv_intensity       = $args{uv_intensity}       // 0.0;
    my $cosmic_ray_flux    = $args{cosmic_ray_flux}    // 0.0;
    my $temperature        = $args{temperature}        // 300.0;

    $self->{generation}++;

    # Metabolize
    for my $cell (@{$self->{cells}}) {
        $cell->metabolize($environment_energy);
    }

    # Apply mutations
    for my $cell (@{$self->{cells}}) {
        if ($cell->{alive}) {
            $cell->{dna}->apply_mutations($uv_intensity, $cosmic_ray_flux);
            $cell->{dna}->apply_epigenetic_changes($temperature, $self->{generation});
        }
    }

    # Transcribe/translate
    for my $cell (@{$self->{cells}}) {
        if ($cell->{alive}) {
            $cell->transcribe_and_translate();
        }
    }

    # Compute fitness
    for my $cell (@{$self->{cells}}) {
        $cell->compute_fitness();
    }

    # Selection and reproduction
    my @alive_cells = grep { $_->{alive} } @{$self->{cells}};
    if (@alive_cells) {
        @alive_cells = sort { $b->{fitness} <=> $a->{fitness} } @alive_cells;
        my $cutoff = max(1, int(scalar(@alive_cells) / 2));
        my @new_cells;
        for my $cell (@alive_cells[0 .. $cutoff - 1]) {
            my $daughter = $cell->divide();
            if ($daughter) {
                push @new_cells, $daughter;
                $self->{total_born}++;
            }
        }
        push @{$self->{cells}}, @new_cells;
    }

    # Remove dead cells
    my @dead = grep { !$_->{alive} } @{$self->{cells}};
    $self->{total_died} += scalar @dead;
    $self->{cells} = [ grep { $_->{alive} } @{$self->{cells}} ];

    # Population cap
    if (scalar(@{$self->{cells}}) > 100) {
        my @sorted = sort { $b->{fitness} <=> $a->{fitness} } @{$self->{cells}};
        my @overflow = @sorted[100 .. $#sorted];
        $self->{total_died} += scalar @overflow;
        $self->{cells} = [ @sorted[0 .. 99] ];
    }
}

sub average_fitness {
    my ($self) = @_;
    return 0.0 unless @{$self->{cells}};
    my $total = 0;
    $total += $_->{fitness} for @{$self->{cells}};
    return $total / scalar(@{$self->{cells}});
}

sub average_gc_content {
    my ($self) = @_;
    return 0.0 unless @{$self->{cells}};
    my $total = 0;
    $total += $_->{dna}->gc_content() for @{$self->{cells}};
    return $total / scalar(@{$self->{cells}});
}

sub total_mutations {
    my ($self) = @_;
    my $total = 0;
    $total += $_->{dna}{mutation_count} for @{$self->{cells}};
    return $total;
}

sub to_compact {
    my ($self) = @_;
    return sprintf("Bio[gen=%d pop=%d fit=%.3f gc=%.2f born=%d died=%d mut=%d]",
        $self->{generation}, scalar(@{$self->{cells}}),
        $self->average_fitness(), $self->average_gc_content(),
        $self->{total_born}, $self->{total_died},
        $self->total_mutations());
}

1;
