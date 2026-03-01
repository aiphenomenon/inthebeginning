package Quantum;

# Quantum and subatomic physics simulation.
#
# Models quantum fields, particles, wave functions, superposition,
# entanglement (simplified), and the quark-hadron transition.

use strict;
use warnings;
use POSIX qw(fmod);
use List::Util qw(sum);

use Constants qw(
    $HBAR $C $M_UP_QUARK $M_DOWN_QUARK $M_ELECTRON $M_PROTON
    $M_NEUTRON $M_PHOTON $M_NEUTRINO $STRONG_COUPLING $EM_COUPLING
    $WEAK_COUPLING $ALPHA $E_CHARGE $PI $T_PLANCK $T_ELECTROWEAK
    $T_QUARK_HADRON $NUCLEAR_RADIUS
);

# ============================================================
# Particle types, spins, colors
# ============================================================

# Particle type constants
use constant {
    PT_UP       => 'up',
    PT_DOWN     => 'down',
    PT_ELECTRON => 'electron',
    PT_POSITRON => 'positron',
    PT_NEUTRINO => 'neutrino',
    PT_PHOTON   => 'photon',
    PT_GLUON    => 'gluon',
    PT_W_BOSON  => 'W',
    PT_Z_BOSON  => 'Z',
    PT_PROTON   => 'proton',
    PT_NEUTRON  => 'neutron',
};

use constant {
    SPIN_UP   => 0.5,
    SPIN_DOWN => -0.5,
};

use constant {
    COLOR_RED        => 'r',
    COLOR_GREEN      => 'g',
    COLOR_BLUE       => 'b',
    COLOR_ANTI_RED   => 'ar',
    COLOR_ANTI_GREEN => 'ag',
    COLOR_ANTI_BLUE  => 'ab',
};

my %PARTICLE_MASSES = (
    PT_UP()       => $M_UP_QUARK,
    PT_DOWN()     => $M_DOWN_QUARK,
    PT_ELECTRON() => $M_ELECTRON,
    PT_POSITRON() => $M_ELECTRON,
    PT_NEUTRINO() => $M_NEUTRINO,
    PT_PHOTON()   => $M_PHOTON,
    PT_GLUON()    => $M_PHOTON,
    PT_PROTON()   => $M_PROTON,
    PT_NEUTRON()  => $M_NEUTRON,
);

my %PARTICLE_CHARGES = (
    PT_UP()       =>  2.0 / 3.0,
    PT_DOWN()     => -1.0 / 3.0,
    PT_ELECTRON() => -1.0,
    PT_POSITRON() =>  1.0,
    PT_NEUTRINO() =>  0.0,
    PT_PHOTON()   =>  0.0,
    PT_GLUON()    =>  0.0,
    PT_PROTON()   =>  1.0,
    PT_NEUTRON()  =>  0.0,
);

# ============================================================
# Helper: Gaussian random (Box-Muller transform)
# ============================================================
sub _gauss {
    my ($mean, $stddev) = @_;
    $mean   //= 0;
    $stddev //= 1;
    my $u1 = rand() || 1e-20;  # avoid log(0)
    my $u2 = rand();
    my $z = sqrt(-2.0 * log($u1)) * cos(2.0 * $PI * $u2);
    return $mean + $stddev * $z;
}

# ============================================================
# WaveFunction - simplified quantum wave function
# ============================================================
package WaveFunction;
use POSIX qw(fmod);
use Constants qw($HBAR $PI);

sub new {
    my ($class, %args) = @_;
    my $self = bless {
        amplitude => $args{amplitude} // 1.0,
        phase     => $args{phase}     // 0.0,
        coherent  => exists $args{coherent} ? $args{coherent} : 1,
    }, $class;
    return $self;
}

sub probability {
    my ($self) = @_;
    return $self->{amplitude} ** 2;
}

sub evolve {
    my ($self, $dt, $energy) = @_;
    if ($self->{coherent}) {
        $self->{phase} += $energy * $dt / $HBAR;
        $self->{phase} = fmod($self->{phase}, 2 * $PI);
    }
}

sub collapse {
    my ($self) = @_;
    my $result = rand() < $self->probability() ? 1 : 0;
    $self->{amplitude} = $result ? 1.0 : 0.0;
    $self->{coherent}  = 0;
    return $result;
}

sub superpose {
    my ($self, $other) = @_;
    my $phase_diff   = $self->{phase} - $other->{phase};
    my $combined_amp = sqrt(
        $self->{amplitude} ** 2 + $other->{amplitude} ** 2
        + 2 * $self->{amplitude} * $other->{amplitude} * cos($phase_diff)
    );
    $combined_amp = 1.0 if $combined_amp > 1.0;
    my $combined_phase = ($self->{phase} + $other->{phase}) / 2;
    return WaveFunction->new(
        amplitude => $combined_amp,
        phase     => $combined_phase,
        coherent  => 1,
    );
}

sub to_compact {
    my ($self) = @_;
    return sprintf("\x{03c8}(%.3f\x{2220}%.2f)", $self->{amplitude}, $self->{phase});
}

# ============================================================
# Particle
# ============================================================
package Particle;
use Constants qw($C $PI $HBAR);

my $_particle_id_counter = 0;

sub new {
    my ($class, %args) = @_;
    $_particle_id_counter++;
    my $self = bless {
        particle_type   => $args{particle_type},
        position        => $args{position}    || [0.0, 0.0, 0.0],
        momentum        => $args{momentum}    || [0.0, 0.0, 0.0],
        spin            => $args{spin}        // Quantum::SPIN_UP,
        color           => $args{color},                             # undef if no color
        wave_fn         => $args{wave_fn}     || WaveFunction->new(),
        entangled_with  => $args{entangled_with},                    # undef
        particle_id     => $_particle_id_counter,
    }, $class;
    return $self;
}

sub mass {
    my ($self) = @_;
    return $PARTICLE_MASSES{$self->{particle_type}} // 0.0;
}

sub charge {
    my ($self) = @_;
    return $PARTICLE_CHARGES{$self->{particle_type}} // 0.0;
}

sub energy {
    my ($self) = @_;
    my $p2 = 0;
    for my $p (@{$self->{momentum}}) {
        $p2 += $p ** 2;
    }
    return sqrt($p2 * $C ** 2 + ($self->mass() * $C ** 2) ** 2);
}

sub wavelength {
    my ($self) = @_;
    my $p2 = 0;
    for my $pi (@{$self->{momentum}}) {
        $p2 += $pi ** 2;
    }
    my $p = sqrt($p2);
    if ($p < 1e-20) {
        return 9**9**9;  # Perl's infinity
    }
    return 2 * $PI * $HBAR / $p;
}

sub to_compact {
    my ($self) = @_;
    return sprintf("%s[%.1f,%.1f,%.1f]s=%s",
        $self->{particle_type},
        $self->{position}[0], $self->{position}[1], $self->{position}[2],
        $self->{spin});
}

# ============================================================
# EntangledPair
# ============================================================
package EntangledPair;

sub new {
    my ($class, %args) = @_;
    return bless {
        particle_a => $args{particle_a},
        particle_b => $args{particle_b},
        bell_state => $args{bell_state} // 'phi+',
    }, $class;
}

sub measure_a {
    my ($self) = @_;
    if (rand() < 0.5) {
        $self->{particle_a}{spin} = Quantum::SPIN_UP;
        $self->{particle_b}{spin} = Quantum::SPIN_DOWN;
    } else {
        $self->{particle_a}{spin} = Quantum::SPIN_DOWN;
        $self->{particle_b}{spin} = Quantum::SPIN_UP;
    }
    $self->{particle_a}{wave_fn}{coherent} = 0;
    $self->{particle_b}{wave_fn}{coherent} = 0;
    return $self->{particle_a}{spin};
}

# ============================================================
# QuantumField
# ============================================================
package QuantumField;
use Constants qw($T_PLANCK $T_QUARK_HADRON $M_ELECTRON $M_PROTON $C);

sub new {
    my ($class, %args) = @_;
    return bless {
        temperature       => $args{temperature} // $T_PLANCK,
        particles         => [],
        entangled_pairs   => [],
        vacuum_energy     => 0.0,
        total_created     => 0,
        total_annihilated => 0,
    }, $class;
}

sub pair_production {
    my ($self, $energy) = @_;

    return undef if $energy < 2 * $M_ELECTRON * $C ** 2;

    my ($p_type, $ap_type);
    if ($energy >= 2 * $M_PROTON * $C ** 2 && rand() < 0.1) {
        $p_type  = Quantum::PT_UP;
        $ap_type = Quantum::PT_DOWN;
    } else {
        $p_type  = Quantum::PT_ELECTRON;
        $ap_type = Quantum::PT_POSITRON;
    }

    my @direction = map { Quantum::_gauss(0, 1) } (0..2);
    my $norm = sqrt($direction[0]**2 + $direction[1]**2 + $direction[2]**2) || 1.0;
    my $p_momentum = $energy / (2 * $C);

    my $particle = Particle->new(
        particle_type => $p_type,
        momentum      => [ map { $_ / $norm * $p_momentum } @direction ],
        spin          => Quantum::SPIN_UP,
    );
    my $antiparticle = Particle->new(
        particle_type => $ap_type,
        momentum      => [ map { -$_ / $norm * $p_momentum } @direction ],
        spin          => Quantum::SPIN_DOWN,
    );

    $particle->{entangled_with}     = $antiparticle->{particle_id};
    $antiparticle->{entangled_with} = $particle->{particle_id};

    push @{$self->{particles}}, $particle, $antiparticle;
    push @{$self->{entangled_pairs}}, EntangledPair->new(
        particle_a => $particle,
        particle_b => $antiparticle,
    );
    $self->{total_created} += 2;

    return ($particle, $antiparticle);
}

sub annihilate {
    my ($self, $p1, $p2) = @_;
    my $energy = $p1->energy() + $p2->energy();

    $self->{particles} = [ grep { $_ != $p1 && $_ != $p2 } @{$self->{particles}} ];
    $self->{total_annihilated} += 2;
    $self->{vacuum_energy} += $energy * 0.01;

    my $photon1 = Particle->new(
        particle_type => Quantum::PT_PHOTON,
        momentum      => [$energy / (2 * $C), 0, 0],
    );
    my $photon2 = Particle->new(
        particle_type => Quantum::PT_PHOTON,
        momentum      => [-$energy / (2 * $C), 0, 0],
    );
    push @{$self->{particles}}, $photon1, $photon2;
    return $energy;
}

sub quark_confinement {
    my ($self) = @_;

    return () if $self->{temperature} > $T_QUARK_HADRON;

    my @hadrons;
    my @ups   = grep { $_->{particle_type} eq Quantum::PT_UP }   @{$self->{particles}};
    my @downs = grep { $_->{particle_type} eq Quantum::PT_DOWN } @{$self->{particles}};

    # Form protons (uud)
    while (@ups >= 2 && @downs >= 1) {
        my $u1 = pop @ups;
        my $u2 = pop @ups;
        my $d1 = pop @downs;

        $u1->{color} = Quantum::COLOR_RED;
        $u2->{color} = Quantum::COLOR_GREEN;
        $d1->{color} = Quantum::COLOR_BLUE;

        my $proton = Particle->new(
            particle_type => Quantum::PT_PROTON,
            position      => [@{$u1->{position}}],
            momentum      => [
                $u1->{momentum}[0] + $u2->{momentum}[0] + $d1->{momentum}[0],
                $u1->{momentum}[1] + $u2->{momentum}[1] + $d1->{momentum}[1],
                $u1->{momentum}[2] + $u2->{momentum}[2] + $d1->{momentum}[2],
            ],
        );

        for my $q ($u1, $u2, $d1) {
            $self->{particles} = [ grep { $_ != $q } @{$self->{particles}} ];
        }
        push @{$self->{particles}}, $proton;
        push @hadrons, $proton;
    }

    # Form neutrons (udd)
    while (@ups >= 1 && @downs >= 2) {
        my $u1 = pop @ups;
        my $d1 = pop @downs;
        my $d2 = pop @downs;

        $u1->{color} = Quantum::COLOR_RED;
        $d1->{color} = Quantum::COLOR_GREEN;
        $d2->{color} = Quantum::COLOR_BLUE;

        my $neutron = Particle->new(
            particle_type => Quantum::PT_NEUTRON,
            position      => [@{$u1->{position}}],
            momentum      => [
                $u1->{momentum}[0] + $d1->{momentum}[0] + $d2->{momentum}[0],
                $u1->{momentum}[1] + $d1->{momentum}[1] + $d2->{momentum}[1],
                $u1->{momentum}[2] + $d1->{momentum}[2] + $d2->{momentum}[2],
            ],
        );

        for my $q ($u1, $d1, $d2) {
            $self->{particles} = [ grep { $_ != $q } @{$self->{particles}} ];
        }
        push @{$self->{particles}}, $neutron;
        push @hadrons, $neutron;
    }

    return @hadrons;
}

sub vacuum_fluctuation {
    my ($self) = @_;
    my $prob = $self->{temperature} / $T_PLANCK;
    $prob = 0.5 if $prob > 0.5;
    if (rand() < $prob) {
        # exponential variate: -mean * ln(U)
        my $mean = $self->{temperature} * 0.001;
        $mean = 1e-20 if $mean <= 0;
        my $energy = -$mean * log(rand() || 1e-20);
        return $self->pair_production($energy);
    }
    return undef;
}

sub decohere {
    my ($self, $particle, $environment_coupling) = @_;
    $environment_coupling //= 0.1;
    if ($particle->{wave_fn}{coherent}) {
        my $decoherence_rate = $environment_coupling * $self->{temperature};
        if (rand() < $decoherence_rate) {
            $particle->{wave_fn}->collapse();
        }
    }
}

sub cool {
    my ($self, $factor) = @_;
    $factor //= 0.999;
    $self->{temperature} *= $factor;
}

sub evolve_field {
    my ($self, $dt) = @_;
    $dt //= 1.0;
    for my $p (@{$self->{particles}}) {
        my $mass = $p->mass();
        if ($mass > 0) {
            for my $i (0..2) {
                $p->{position}[$i] += $p->{momentum}[$i] / $mass * $dt;
            }
        } else {
            my $p_mag = sqrt(
                $p->{momentum}[0]**2 + $p->{momentum}[1]**2 + $p->{momentum}[2]**2
            ) || 1.0;
            for my $i (0..2) {
                $p->{position}[$i] += $p->{momentum}[$i] / $p_mag * $C * $dt;
            }
        }
        $p->{wave_fn}->evolve($dt, $p->energy());
    }
}

sub particle_count {
    my ($self) = @_;
    my %counts;
    for my $p (@{$self->{particles}}) {
        $counts{$p->{particle_type}}++;
    }
    return %counts;
}

sub total_energy {
    my ($self) = @_;
    my $total = $self->{vacuum_energy};
    for my $p (@{$self->{particles}}) {
        $total += $p->energy();
    }
    return $total;
}

sub step {
    my ($self, $temperature) = @_;
    $self->{temperature} = $temperature if defined $temperature;
    $self->vacuum_fluctuation();
    $self->evolve_field(1.0);
    for my $p (@{$self->{particles}}) {
        $self->decohere($p, 0.01);
    }
    $self->quark_confinement();
}

sub to_compact {
    my ($self) = @_;
    my %counts = $self->particle_count();
    my $count_str = join(',', map { "$_:$counts{$_}" } sort keys %counts);
    return sprintf("QF[T=%.1e E=%.1e n=%d %s]",
        $self->{temperature}, $self->total_energy(),
        scalar(@{$self->{particles}}), $count_str);
}

1;
