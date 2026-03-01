package Chemistry;

# Chemistry simulation - molecular assembly and reactions.
#
# Models formation of molecules from atoms: water, amino acids,
# nucleotides, and other biomolecules essential for life.
# Chemical reactions are driven by energy, catalysis, and concentration.

use strict;
use warnings;

use Constants qw(
    $K_B $BOND_ENERGY_COVALENT $BOND_ENERGY_HYDROGEN
    $BOND_ENERGY_VAN_DER_WAALS @AMINO_ACIDS
);

# ============================================================
# Molecule
# ============================================================
package Molecule;

my $_mol_id_counter = 0;

sub new {
    my ($class, %args) = @_;
    $_mol_id_counter++;
    my $self = bless {
        atoms            => $args{atoms}            || [],
        name             => $args{name}             // '',
        formula          => $args{formula}          // '',
        molecule_id      => $_mol_id_counter,
        energy           => $args{energy}           // 0.0,
        position         => $args{position}         || [0.0, 0.0, 0.0],
        is_organic       => $args{is_organic}       // 0,
        functional_groups => $args{functional_groups} || [],
    }, $class;

    if (!$self->{formula} && @{$self->{atoms}}) {
        $self->_compute_formula();
    }

    return $self;
}

sub _compute_formula {
    my ($self) = @_;
    my %counts;
    for my $atom (@{$self->{atoms}}) {
        my $sym = $atom->symbol();
        $counts{$sym}++;
    }

    # Standard chemistry ordering: C, H, then alphabetical
    my @parts;
    for my $sym ('C', 'H') {
        if (exists $counts{$sym}) {
            my $n = delete $counts{$sym};
            push @parts, $n > 1 ? "$sym$n" : $sym;
        }
    }
    for my $sym (sort keys %counts) {
        my $n = $counts{$sym};
        push @parts, $n > 1 ? "$sym$n" : $sym;
    }
    $self->{formula} = join('', @parts);

    # Check if organic
    my $has_c = grep { $_->{atomic_number} == 6 } @{$self->{atoms}};
    my $has_h = grep { $_->{atomic_number} == 1 } @{$self->{atoms}};
    $self->{is_organic} = ($has_c && $has_h) ? 1 : 0;
}

sub molecular_weight {
    my ($self) = @_;
    my $total = 0;
    for my $a (@{$self->{atoms}}) {
        $total += $a->{mass_number};
    }
    return $total;
}

sub atom_count {
    my ($self) = @_;
    return scalar @{$self->{atoms}};
}

sub to_compact {
    my ($self) = @_;
    my $label = $self->{name} || $self->{formula};
    return sprintf("%s(mw=%d)", $label, $self->molecular_weight());
}

# ============================================================
# ChemicalReaction
# ============================================================
package ChemicalReaction;

sub new {
    my ($class, %args) = @_;
    return bless {
        reactants         => $args{reactants}         || [],
        products          => $args{products}          || [],
        activation_energy => $args{activation_energy} // 1.0,
        delta_h           => $args{delta_h}           // 0.0,
        name              => $args{name}              // '',
    }, $class;
}

sub can_proceed {
    my ($self, $temperature) = @_;
    my $thermal_energy = $K_B * $temperature;
    return 0 if $thermal_energy <= 0;
    my $rate = exp(-$self->{activation_energy} / $thermal_energy);
    return rand() < $rate ? 1 : 0;
}

sub to_compact {
    my ($self) = @_;
    my $r = join('+', @{$self->{reactants}});
    my $p = join('+', @{$self->{products}});
    return sprintf("%s->%s(Ea=%.1f,dH=%.1f)",
        $r, $p, $self->{activation_energy}, $self->{delta_h});
}

# ============================================================
# ChemicalSystem
# ============================================================
package ChemicalSystem;

sub new {
    my ($class, %args) = @_;
    return bless {
        atomic             => $args{atomic_system},
        molecules          => [],
        reactions_occurred => 0,
        water_count        => 0,
        amino_acid_count   => 0,
        nucleotide_count   => 0,
    }, $class;
}

sub form_water {
    my ($self) = @_;
    my @waters;
    my @hydrogens = grep { $_->{atomic_number} == 1 && !@{$_->{bonds}} }
                         @{$self->{atomic}{atoms}};
    my @oxygens   = grep { $_->{atomic_number} == 8 && scalar(@{$_->{bonds}}) < 2 }
                         @{$self->{atomic}{atoms}};

    while (@hydrogens >= 2 && @oxygens) {
        my $h1 = pop @hydrogens;
        my $h2 = pop @hydrogens;
        my $o  = pop @oxygens;

        my $water = Molecule->new(
            atoms    => [$h1, $h2, $o],
            name     => 'water',
            position => [@{$o->{position}}],
        );
        push @waters, $water;
        push @{$self->{molecules}}, $water;
        $self->{water_count}++;

        push @{$h1->{bonds}}, $o->{atom_id};
        push @{$h2->{bonds}}, $o->{atom_id};
        push @{$o->{bonds}}, $h1->{atom_id}, $h2->{atom_id};
    }

    return @waters;
}

sub form_methane {
    my ($self) = @_;
    my @methanes;
    my @carbons   = grep { $_->{atomic_number} == 6 && !@{$_->{bonds}} }
                         @{$self->{atomic}{atoms}};
    my @hydrogens = grep { $_->{atomic_number} == 1 && !@{$_->{bonds}} }
                         @{$self->{atomic}{atoms}};

    while (@carbons && @hydrogens >= 4) {
        my $c  = pop @carbons;
        my @hs = splice(@hydrogens, -4);

        my $methane = Molecule->new(
            atoms    => [$c, @hs],
            name     => 'methane',
            position => [@{$c->{position}}],
        );
        push @methanes, $methane;
        push @{$self->{molecules}}, $methane;

        for my $h (@hs) {
            push @{$c->{bonds}}, $h->{atom_id};
            push @{$h->{bonds}}, $c->{atom_id};
        }
    }

    return @methanes;
}

sub form_ammonia {
    my ($self) = @_;
    my @ammonias;
    my @nitrogens = grep { $_->{atomic_number} == 7 && !@{$_->{bonds}} }
                         @{$self->{atomic}{atoms}};
    my @hydrogens = grep { $_->{atomic_number} == 1 && !@{$_->{bonds}} }
                         @{$self->{atomic}{atoms}};

    while (@nitrogens && @hydrogens >= 3) {
        my $n  = pop @nitrogens;
        my @hs = splice(@hydrogens, -3);

        my $ammonia = Molecule->new(
            atoms    => [$n, @hs],
            name     => 'ammonia',
            position => [@{$n->{position}}],
        );
        push @ammonias, $ammonia;
        push @{$self->{molecules}}, $ammonia;

        for my $h (@hs) {
            push @{$n->{bonds}}, $h->{atom_id};
            push @{$h->{bonds}}, $n->{atom_id};
        }
    }

    return @ammonias;
}

sub form_amino_acid {
    my ($self, $aa_type) = @_;
    $aa_type //= 'Gly';

    my @carbons   = grep { $_->{atomic_number} == 6 && !@{$_->{bonds}} }
                         @{$self->{atomic}{atoms}};
    my @hydrogens = grep { $_->{atomic_number} == 1 && !@{$_->{bonds}} }
                         @{$self->{atomic}{atoms}};
    my @oxygens   = grep { $_->{atomic_number} == 8 && scalar(@{$_->{bonds}}) < 2 }
                         @{$self->{atomic}{atoms}};
    my @nitrogens = grep { $_->{atomic_number} == 7 && !@{$_->{bonds}} }
                         @{$self->{atomic}{atoms}};

    return undef if @carbons < 2 || @hydrogens < 5;
    return undef if @oxygens < 2 || @nitrogens < 1;

    my @atoms;
    push @atoms, pop @carbons   for 1..2;
    push @atoms, pop @hydrogens for 1..5;
    push @atoms, pop @oxygens   for 1..2;
    push @atoms, pop @nitrogens;

    my $aa = Molecule->new(
        atoms            => \@atoms,
        name             => $aa_type,
        position         => [@{$atoms[0]->{position}}],
        is_organic       => 1,
        functional_groups => ['amino', 'carboxyl'],
    );
    push @{$self->{molecules}}, $aa;
    $self->{amino_acid_count}++;

    # Form internal bonds
    for my $i (1 .. $#atoms) {
        push @{$atoms[0]->{bonds}}, $atoms[$i]->{atom_id};
        push @{$atoms[$i]->{bonds}}, $atoms[0]->{atom_id};
    }

    return $aa;
}

sub form_nucleotide {
    my ($self, $base) = @_;
    $base //= 'A';

    my @carbons   = grep { $_->{atomic_number} == 6 && !@{$_->{bonds}} }
                         @{$self->{atomic}{atoms}};
    my @hydrogens = grep { $_->{atomic_number} == 1 && !@{$_->{bonds}} }
                         @{$self->{atomic}{atoms}};
    my @oxygens   = grep { $_->{atomic_number} == 8 && scalar(@{$_->{bonds}}) < 2 }
                         @{$self->{atomic}{atoms}};
    my @nitrogens = grep { $_->{atomic_number} == 7 && !@{$_->{bonds}} }
                         @{$self->{atomic}{atoms}};

    return undef if @carbons < 5 || @hydrogens < 8;
    return undef if @oxygens < 4 || @nitrogens < 2;

    my @atoms;
    push @atoms, pop @carbons   for 1..5;
    push @atoms, pop @hydrogens for 1..8;
    push @atoms, pop @oxygens   for 1..4;
    push @atoms, pop @nitrogens for 1..2;

    my $nuc = Molecule->new(
        atoms            => \@atoms,
        name             => "nucleotide-$base",
        position         => [@{$atoms[0]->{position}}],
        is_organic       => 1,
        functional_groups => ['sugar', 'phosphate', 'base'],
    );
    push @{$self->{molecules}}, $nuc;
    $self->{nucleotide_count}++;

    for my $i (1 .. $#atoms) {
        push @{$atoms[0]->{bonds}}, $atoms[$i]->{atom_id};
        push @{$atoms[$i]->{bonds}}, $atoms[0]->{atom_id};
    }

    return $nuc;
}

sub catalyzed_reaction {
    my ($self, $temperature, $catalyst_present) = @_;
    $catalyst_present //= 0;
    my $formed = 0;
    my $ea_factor = $catalyst_present ? 0.3 : 1.0;
    my $thermal = $K_B * $temperature;

    # Try to form amino acids
    if ($thermal > 0 && scalar(@{$self->{atomic}{atoms}}) > 10) {
        my $aa_prob = exp(-5.0 * $ea_factor / ($thermal + 1e-20));
        if (rand() < $aa_prob) {
            my $aa_type = $AMINO_ACIDS[int(rand(scalar @AMINO_ACIDS))];
            if ($self->form_amino_acid($aa_type)) {
                $formed++;
                $self->{reactions_occurred}++;
            }
        }
    }

    # Try to form nucleotides
    if ($thermal > 0 && scalar(@{$self->{atomic}{atoms}}) > 19) {
        my $nuc_prob = exp(-8.0 * $ea_factor / ($thermal + 1e-20));
        if (rand() < $nuc_prob) {
            my @bases = qw(A T G C);
            my $base = $bases[int(rand(4))];
            if ($self->form_nucleotide($base)) {
                $formed++;
                $self->{reactions_occurred}++;
            }
        }
    }

    return $formed;
}

sub molecule_census {
    my ($self) = @_;
    my %counts;
    for my $m (@{$self->{molecules}}) {
        my $key = $m->{name} || $m->{formula};
        $counts{$key}++;
    }
    return %counts;
}

sub to_compact {
    my ($self) = @_;
    my %counts = $self->molecule_census();
    my $count_str = join(',', map { "$_:$counts{$_}" } sort keys %counts);
    return sprintf("CS[mol=%d H2O=%d aa=%d nuc=%d rxn=%d %s]",
        scalar(@{$self->{molecules}}),
        $self->{water_count},
        $self->{amino_acid_count},
        $self->{nucleotide_count},
        $self->{reactions_occurred},
        $count_str);
}

1;
