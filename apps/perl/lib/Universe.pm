package Universe;

# Universe orchestrator - runs the full cosmic simulation through 13 epochs.

use strict;
use warnings;
use POSIX qw(floor);
use List::Util qw(min max sum);

use Constants qw(
    $PLANCK_EPOCH $INFLATION_EPOCH $ELECTROWEAK_EPOCH $QUARK_EPOCH
    $HADRON_EPOCH $NUCLEOSYNTHESIS_EPOCH $RECOMBINATION_EPOCH
    $STAR_FORMATION_EPOCH $SOLAR_SYSTEM_EPOCH $EARTH_EPOCH
    $LIFE_EPOCH $DNA_EPOCH $PRESENT_EPOCH
    $T_PLANCK $T_ELECTROWEAK $T_QUARK_HADRON $T_NUCLEOSYNTHESIS
    $T_RECOMBINATION $T_CMB $T_EARTH_SURFACE $C $HBAR $G $K_B
);
use Quantum;
use Atomic;
use Chemistry;
use Biology;
use Environment;

sub new {
    my ($class, %args) = @_;
    my $ticks_per_epoch = $args{ticks_per_epoch} || 100;
    return bless {
        ticks_per_epoch => $ticks_per_epoch,
        current_epoch   => 0,
        current_tick    => 0,
        temperature     => $T_PLANCK,
        scale_factor    => 1e-35,
        quantum_field   => undef,
        atomic_system   => undef,
        chemical_system => undef,
        biosphere       => undef,
        environment     => undef,
        stats           => {
            particles_created  => 0,
            atoms_formed       => 0,
            molecules_formed   => 0,
            lifeforms_created  => 0,
        },
        epoch_names => [
            'Planck',
            'Inflation',
            'Electroweak',
            'Quark-Gluon Plasma',
            'Hadron',
            'Nucleosynthesis',
            'Recombination',
            'Star Formation',
            'Solar System',
            'Earth Formation',
            'Life Emergence',
            'DNA Evolution',
            'Present Day',
        ],
    }, $class;
}

sub epoch_name {
    my ($self) = @_;
    return $self->{epoch_names}[$self->{current_epoch}] || 'Unknown';
}

sub _cool_temperature {
    my ($self) = @_;
    my $epoch = $self->{current_epoch};
    my @targets = (
        $T_PLANCK, 1e27, $T_ELECTROWEAK, $T_QUARK_HADRON,
        1e10, $T_NUCLEOSYNTHESIS, $T_RECOMBINATION,
        1e6, 5778, $T_EARTH_SURFACE, 300, 298, 295,
    );
    my $target = $targets[$epoch] || 295;
    my $cooling_rate = 0.05 + 0.02 * $epoch;
    $self->{temperature} += ($target - $self->{temperature}) * $cooling_rate;
}

sub _expand_space {
    my ($self) = @_;
    my $epoch = $self->{current_epoch};
    if ($epoch == 1) {
        $self->{scale_factor} *= 1e3;    # inflation
    } elsif ($epoch < 7) {
        $self->{scale_factor} *= 1.5;
    } else {
        $self->{scale_factor} *= 1.01;
    }
}

sub run_epoch {
    my ($self, $epoch_idx) = @_;
    $self->{current_epoch} = $epoch_idx;
    my $name = $self->epoch_name();

    for my $tick (1 .. $self->{ticks_per_epoch}) {
        $self->{current_tick} = $tick;
        $self->_cool_temperature();
        $self->_expand_space();

        # Update environment
        if (defined $self->{environment}) {
            $self->{environment}->update($epoch_idx * $self->{ticks_per_epoch} + $tick);
        }

        if ($epoch_idx <= 3 && defined $self->{quantum_field}) {
            $self->{quantum_field}->step($self->{temperature});
            $self->{stats}{particles_created} = scalar @{$self->{quantum_field}{particles} || []};
        }
        if ($epoch_idx >= 5 && $epoch_idx <= 7 && defined $self->{atomic_system}) {
            $self->{atomic_system}->step($self->{temperature});
            $self->{stats}{atoms_formed} = scalar @{$self->{atomic_system}{atoms} || []};
        }
        if ($epoch_idx >= 8 && $epoch_idx <= 10 && defined $self->{chemical_system}) {
            $self->{chemical_system}->step($self->{temperature});
            $self->{stats}{molecules_formed} = scalar @{$self->{chemical_system}{molecules} || []};
        }
        if ($epoch_idx >= 10 && defined $self->{biosphere}) {
            my $env = $self->{environment};
            $self->{biosphere}->step(
                temperature        => $self->{temperature},
                environment_energy => $env ? $env->thermal_energy() : 10.0,
                uv_intensity       => $env ? $env->{uv_intensity} : 0.0,
                cosmic_ray_flux    => $env ? $env->{cosmic_ray_flux} : 0.0,
            );
            $self->{stats}{lifeforms_created} = scalar @{$self->{biosphere}{cells} || []};
        }
    }

    return {
        epoch       => $name,
        temperature => $self->{temperature},
        scale       => $self->{scale_factor},
        stats       => { %{$self->{stats}} },
    };
}

sub run {
    my ($self, %args) = @_;
    my $callback = $args{on_epoch_complete};
    my @results;

    # Initialize subsystems
    $self->{quantum_field}   = QuantumField->new();
    $self->{atomic_system}   = AtomicSystem->new();
    $self->{environment}     = Environment->new();
    $self->{chemical_system} = ChemicalSystem->new(
        atomic_system => $self->{atomic_system},
    );
    $self->{biosphere}       = Biosphere->new();

    for my $epoch_idx (0 .. 12) {
        my $result = $self->run_epoch($epoch_idx);
        push @results, $result;
        $callback->($result) if $callback;
    }

    return \@results;
}

1;
