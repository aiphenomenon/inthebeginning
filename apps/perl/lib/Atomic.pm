package Atomic;

# Atomic physics simulation.
#
# Models atoms with electron shells, ionization, chemical bonding potential,
# and the periodic table. Atoms emerge from the quantum/nuclear level
# when temperature drops below recombination threshold.

use strict;
use warnings;
use POSIX qw();
use List::Util qw(sum);

use Constants qw(
    @ELECTRON_SHELLS $BOND_ENERGY_COVALENT $BOND_ENERGY_IONIC
    $BOND_ENERGY_HYDROGEN $T_RECOMBINATION $E_CHARGE $HBAR
    $M_ELECTRON $ALPHA $C $K_B
);

# Periodic table data: atomic_number => [symbol, name, group, period, electronegativity]
my %ELEMENTS = (
     1 => ['H',  'Hydrogen',   1,  1, 2.20],
     2 => ['He', 'Helium',    18,  1, 0.0],
     3 => ['Li', 'Lithium',    1,  2, 0.98],
     4 => ['Be', 'Beryllium',  2,  2, 1.57],
     5 => ['B',  'Boron',     13,  2, 2.04],
     6 => ['C',  'Carbon',    14,  2, 2.55],
     7 => ['N',  'Nitrogen',  15,  2, 3.04],
     8 => ['O',  'Oxygen',    16,  2, 3.44],
     9 => ['F',  'Fluorine',  17,  2, 3.98],
    10 => ['Ne', 'Neon',      18,  2, 0.0],
    11 => ['Na', 'Sodium',     1,  3, 0.93],
    12 => ['Mg', 'Magnesium',  2,  3, 1.31],
    13 => ['Al', 'Aluminum',  13,  3, 1.61],
    14 => ['Si', 'Silicon',   14,  3, 1.90],
    15 => ['P',  'Phosphorus',15,  3, 2.19],
    16 => ['S',  'Sulfur',    16,  3, 2.58],
    17 => ['Cl', 'Chlorine',  17,  3, 3.16],
    18 => ['Ar', 'Argon',     18,  3, 0.0],
    19 => ['K',  'Potassium',  1,  4, 0.82],
    20 => ['Ca', 'Calcium',    2,  4, 1.00],
    26 => ['Fe', 'Iron',       8,  4, 1.83],
);

sub get_element { return $ELEMENTS{$_[0]} }

# ============================================================
# ElectronShell
# ============================================================
package ElectronShell;

sub new {
    my ($class, %args) = @_;
    return bless {
        n             => $args{n},
        max_electrons => $args{max_electrons},
        electrons     => $args{electrons} // 0,
    }, $class;
}

sub full  { return $_[0]->{electrons} >= $_[0]->{max_electrons} }
sub empty { return $_[0]->{electrons} == 0 }

sub add_electron {
    my ($self) = @_;
    return 0 if $self->full();
    $self->{electrons}++;
    return 1;
}

sub remove_electron {
    my ($self) = @_;
    return 0 if $self->empty();
    $self->{electrons}--;
    return 1;
}

# ============================================================
# Atom
# ============================================================
package Atom;
use Constants qw(@ELECTRON_SHELLS $BOND_ENERGY_COVALENT $BOND_ENERGY_IONIC);

my $_atom_id_counter = 0;

sub new {
    my ($class, %args) = @_;
    $_atom_id_counter++;
    my $self = bless {
        atomic_number     => $args{atomic_number},
        mass_number       => $args{mass_number}       // 0,
        electron_count    => $args{electron_count}     // 0,
        position          => $args{position}           || [0.0, 0.0, 0.0],
        velocity          => $args{velocity}           || [0.0, 0.0, 0.0],
        shells            => $args{shells}             || [],
        bonds             => $args{bonds}              || [],
        atom_id           => $_atom_id_counter,
        ionization_energy => 0.0,
    }, $class;

    if ($self->{mass_number} == 0) {
        $self->{mass_number} = $self->{atomic_number} * 2;
        $self->{mass_number} = 1 if $self->{atomic_number} == 1;
    }

    if ($self->{electron_count} == 0) {
        $self->{electron_count} = $self->{atomic_number};  # Neutral atom
    }

    if (!@{$self->{shells}}) {
        $self->_build_shells();
    }

    $self->_compute_ionization_energy();
    return $self;
}

sub _build_shells {
    my ($self) = @_;
    $self->{shells} = [];
    my $remaining = $self->{electron_count};
    for my $i (0 .. $#ELECTRON_SHELLS) {
        last if $remaining <= 0;
        my $max_e = $ELECTRON_SHELLS[$i];
        my $e = $remaining < $max_e ? $remaining : $max_e;
        push @{$self->{shells}}, ElectronShell->new(
            n             => $i + 1,
            max_electrons => $max_e,
            electrons     => $e,
        );
        $remaining -= $e;
    }
}

sub _compute_ionization_energy {
    my ($self) = @_;
    if (!@{$self->{shells}} || $self->{shells}[-1]->empty()) {
        $self->{ionization_energy} = 0.0;
        return;
    }
    my $n     = $self->{shells}[-1]{n};
    my $inner = 0;
    for my $i (0 .. $#{$self->{shells}} - 1) {
        $inner += $self->{shells}[$i]{electrons};
    }
    my $z_eff = $self->{atomic_number} - $inner;
    $self->{ionization_energy} = 13.6 * $z_eff ** 2 / $n ** 2;
}

sub symbol {
    my ($self) = @_;
    my $elem = Atomic::get_element($self->{atomic_number});
    return $elem ? $elem->[0] : "E$self->{atomic_number}";
}

sub name {
    my ($self) = @_;
    my $elem = Atomic::get_element($self->{atomic_number});
    return $elem ? $elem->[1] : "Element-$self->{atomic_number}";
}

sub electronegativity {
    my ($self) = @_;
    my $elem = Atomic::get_element($self->{atomic_number});
    return $elem ? $elem->[4] : 1.0;
}

sub charge {
    my ($self) = @_;
    return $self->{atomic_number} - $self->{electron_count};
}

sub valence_electrons {
    my ($self) = @_;
    return 0 unless @{$self->{shells}};
    return $self->{shells}[-1]{electrons};
}

sub needs_electrons {
    my ($self) = @_;
    return 0 unless @{$self->{shells}};
    my $shell = $self->{shells}[-1];
    return $shell->{max_electrons} - $shell->{electrons};
}

sub is_noble_gas {
    my ($self) = @_;
    return 0 unless @{$self->{shells}};
    return $self->{shells}[-1]->full();
}

sub is_ion {
    my ($self) = @_;
    return $self->charge() != 0 ? 1 : 0;
}

sub ionize {
    my ($self) = @_;
    return 0 if $self->{electron_count} <= 0;
    $self->{electron_count}--;
    $self->_build_shells();
    $self->_compute_ionization_energy();
    return 1;
}

sub capture_electron {
    my ($self) = @_;
    $self->{electron_count}++;
    $self->_build_shells();
    $self->_compute_ionization_energy();
    return 1;
}

sub can_bond_with {
    my ($self, $other) = @_;
    return 0 if $self->is_noble_gas() || $other->is_noble_gas();
    return 0 if scalar(@{$self->{bonds}}) >= 4 || scalar(@{$other->{bonds}}) >= 4;
    return 1;
}

sub bond_type {
    my ($self, $other) = @_;
    my $diff = abs($self->electronegativity() - $other->electronegativity());
    return 'ionic'          if $diff > 1.7;
    return 'polar_covalent' if $diff > 0.4;
    return 'covalent';
}

sub bond_energy {
    my ($self, $other) = @_;
    my $btype = $self->bond_type($other);
    return $BOND_ENERGY_IONIC                               if $btype eq 'ionic';
    return ($BOND_ENERGY_COVALENT + $BOND_ENERGY_IONIC) / 2 if $btype eq 'polar_covalent';
    return $BOND_ENERGY_COVALENT;
}

sub distance_to {
    my ($self, $other) = @_;
    my $d2 = 0;
    for my $i (0..2) {
        $d2 += ($self->{position}[$i] - $other->{position}[$i]) ** 2;
    }
    return sqrt($d2);
}

sub to_compact {
    my ($self) = @_;
    my $charge_str = '';
    my $ch = $self->charge();
    if ($ch > 0) { $charge_str = "+$ch"; }
    elsif ($ch < 0) { $charge_str = "$ch"; }
    my $shells_str = join('.', map { $_->{electrons} } @{$self->{shells}});
    return sprintf("%s%d%s[%s]b%d",
        $self->symbol(), $self->{mass_number}, $charge_str,
        $shells_str, scalar(@{$self->{bonds}}));
}

# ============================================================
# AtomicSystem
# ============================================================
package AtomicSystem;
use Constants qw($T_RECOMBINATION $K_B);
use Quantum;

sub new {
    my ($class, %args) = @_;
    return bless {
        atoms          => [],
        temperature    => $args{temperature} // $T_RECOMBINATION,
        free_electrons => [],
        bonds_formed   => 0,
        bonds_broken   => 0,
    }, $class;
}

sub recombination {
    my ($self, $field) = @_;

    return () if $self->{temperature} > $T_RECOMBINATION;

    my @new_atoms;
    my @protons  = grep { $_->{particle_type} eq Quantum::PT_PROTON }  @{$field->{particles}};
    my @electrons = grep { $_->{particle_type} eq Quantum::PT_ELECTRON } @{$field->{particles}};

    for my $proton (@protons) {
        last unless @electrons;
        my $electron = pop @electrons;
        my $atom = Atom->new(
            atomic_number => 1,
            mass_number   => 1,
            position      => [@{$proton->{position}}],
            velocity      => [@{$proton->{momentum}}],
        );
        push @new_atoms, $atom;
        push @{$self->{atoms}}, $atom;

        $field->{particles} = [ grep { $_ != $proton && $_ != $electron } @{$field->{particles}} ];
    }

    return @new_atoms;
}

sub nucleosynthesis {
    my ($self, $protons, $neutrons) = @_;
    my @new_atoms;

    # Helium-4: 2 protons + 2 neutrons
    while ($protons >= 2 && $neutrons >= 2) {
        my $he = Atom->new(
            atomic_number => 2,
            mass_number   => 4,
            position      => [ map { Quantum::_gauss(0, 10) } (0..2) ],
        );
        push @new_atoms, $he;
        push @{$self->{atoms}}, $he;
        $protons  -= 2;
        $neutrons -= 2;
    }

    # Remaining protons become hydrogen
    for (1..$protons) {
        my $h = Atom->new(
            atomic_number => 1,
            mass_number   => 1,
            position      => [ map { Quantum::_gauss(0, 10) } (0..2) ],
        );
        push @new_atoms, $h;
        push @{$self->{atoms}}, $h;
    }

    return @new_atoms;
}

sub stellar_nucleosynthesis {
    my ($self, $temperature) = @_;
    my @new_atoms;

    return @new_atoms if $temperature < 1e3;

    my @heliums = grep { $_->{atomic_number} == 2 } @{$self->{atoms}};

    # Triple-alpha process: 3 He -> C
    while (@heliums >= 3 && rand() < 0.01) {
        for (1..3) {
            my $he = pop @heliums;
            $self->{atoms} = [ grep { $_ != $he } @{$self->{atoms}} ];
        }
        my $carbon = Atom->new(
            atomic_number => 6,
            mass_number   => 12,
            position      => [ map { Quantum::_gauss(0, 5) } (0..2) ],
        );
        push @new_atoms, $carbon;
        push @{$self->{atoms}}, $carbon;
    }

    # C + He -> O
    my @carbons = grep { $_->{atomic_number} == 6 } @{$self->{atoms}};
    @heliums    = grep { $_->{atomic_number} == 2 } @{$self->{atoms}};
    while (@carbons && @heliums && rand() < 0.02) {
        my $c  = pop @carbons;
        my $he = pop @heliums;
        $self->{atoms} = [ grep { $_ != $c && $_ != $he } @{$self->{atoms}} ];

        my $oxygen = Atom->new(
            atomic_number => 8,
            mass_number   => 16,
            position      => [@{$c->{position}}],
        );
        push @new_atoms, $oxygen;
        push @{$self->{atoms}}, $oxygen;
    }

    # O + He -> N (simplified chain)
    my @oxygens = grep { $_->{atomic_number} == 8 } @{$self->{atoms}};
    @heliums    = grep { $_->{atomic_number} == 2 } @{$self->{atoms}};
    if (@oxygens && @heliums && rand() < 0.005) {
        my $o  = $oxygens[0];
        my $he = $heliums[0];
        $self->{atoms} = [ grep { $_ != $o && $_ != $he } @{$self->{atoms}} ];

        my $nitrogen = Atom->new(
            atomic_number => 7,
            mass_number   => 14,
            position      => [@{$o->{position}}],
        );
        push @new_atoms, $nitrogen;
        push @{$self->{atoms}}, $nitrogen;
    }

    return @new_atoms;
}

sub attempt_bond {
    my ($self, $a1, $a2) = @_;
    return 0 unless $a1->can_bond_with($a2);

    my $dist = $a1->distance_to($a2);
    my $bond_dist = 2.0;

    return 0 if $dist > $bond_dist * 3;

    my $energy_barrier = $a1->bond_energy($a2);
    my $thermal_energy = $K_B * $self->{temperature};
    my $prob;
    if ($thermal_energy > 0) {
        $prob = exp(-$energy_barrier / $thermal_energy);
    } else {
        $prob = ($dist < $bond_dist) ? 1.0 : 0.0;
    }

    if (rand() < $prob) {
        push @{$a1->{bonds}}, $a2->{atom_id};
        push @{$a2->{bonds}}, $a1->{atom_id};
        $self->{bonds_formed}++;
        return 1;
    }
    return 0;
}

sub break_bond {
    my ($self, $a1, $a2) = @_;
    return 0 unless grep { $_ == $a2->{atom_id} } @{$a1->{bonds}};

    my $energy_barrier = $a1->bond_energy($a2);
    my $thermal_energy = $K_B * $self->{temperature};

    if ($thermal_energy > $energy_barrier * 0.5) {
        my $prob = exp(-$energy_barrier / ($thermal_energy + 1e-20));
        if (rand() < $prob) {
            $a1->{bonds} = [ grep { $_ != $a2->{atom_id} } @{$a1->{bonds}} ];
            $a2->{bonds} = [ grep { $_ != $a1->{atom_id} } @{$a2->{bonds}} ];
            $self->{bonds_broken}++;
            return 1;
        }
    }
    return 0;
}

sub step {
    my ($self, $temperature) = @_;
    $self->{temperature} = $temperature if defined $temperature;
    # Attempt bonds between nearby atoms
    my @atoms = @{$self->{atoms}};
    for my $i (0 .. $#atoms - 1) {
        for my $j ($i + 1 .. $#atoms) {
            last if $j > $i + 5;  # limit pairwise checks
            $self->attempt_bond($atoms[$i], $atoms[$j]);
        }
    }
}

sub cool {
    my ($self, $factor) = @_;
    $factor //= 0.999;
    $self->{temperature} *= $factor;
}

sub element_counts {
    my ($self) = @_;
    my %counts;
    for my $a (@{$self->{atoms}}) {
        my $sym = $a->symbol();
        $counts{$sym}++;
    }
    return %counts;
}

sub to_compact {
    my ($self) = @_;
    my %counts = $self->element_counts();
    my $count_str = join(',', map { "$_:$counts{$_}" } sort keys %counts);
    return sprintf("AS[T=%.1e n=%d bonds=%d %s]",
        $self->{temperature}, scalar(@{$self->{atoms}}),
        $self->{bonds_formed}, $count_str);
}

1;
