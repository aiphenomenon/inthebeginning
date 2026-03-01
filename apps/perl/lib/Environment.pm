package Environment;

# Environmental effects simulation.
#
# Models random environmental perturbations that affect the evolution
# of the universe from quantum to biological scales:
# - Temperature gradients and thermal fluctuations
# - Radiation (UV, cosmic rays, stellar winds)
# - Geological events (volcanic, tectonic)
# - Atmospheric composition changes
# - Day/night cycles and seasonal variations

use strict;
use warnings;
use POSIX qw();
use List::Util qw(min max);

use Constants qw(
    $T_PLANCK $T_CMB $T_EARTH_SURFACE $T_STELLAR_CORE
    $UV_MUTATION_RATE $COSMIC_RAY_MUTATION_RATE
    $RADIATION_DAMAGE_THRESHOLD $THERMAL_FLUCTUATION $K_B $PI
);

# ============================================================
# EnvironmentalEvent
# ============================================================
package EnvironmentalEvent;

sub new {
    my ($class, %args) = @_;
    return bless {
        event_type    => $args{event_type},
        intensity     => $args{intensity},
        duration      => $args{duration},       # ticks
        position      => $args{position}      || [0.0, 0.0, 0.0],
        tick_occurred => $args{tick_occurred}  // 0,
    }, $class;
}

sub to_compact {
    my ($self) = @_;
    return sprintf("Ev:%s(i=%.2f,d=%d)",
        $self->{event_type}, $self->{intensity}, $self->{duration});
}

# ============================================================
# Environment
# ============================================================
package Environment;

sub new {
    my ($class, %args) = @_;
    return bless {
        temperature        => $args{initial_temperature} // $T_PLANCK,
        uv_intensity       => 0.0,
        cosmic_ray_flux    => 0.0,
        stellar_wind       => 0.0,
        atmospheric_density => 0.0,
        water_availability => 0.0,
        day_night_cycle    => 0.0,   # 0-1, 0=midnight, 0.5=noon
        season             => 0.0,   # 0-1, 0=winter, 0.5=summer
        events             => [],
        event_history      => [],
        tick               => 0,
    }, $class;
}

# Gaussian random helper
sub _gauss {
    my ($mean, $stddev) = @_;
    $mean   //= 0;
    $stddev //= 1;
    my $u1 = rand() || 1e-20;
    my $u2 = rand();
    my $z = sqrt(-2.0 * log($u1)) * cos(2.0 * $PI * $u2);
    return $mean + $stddev * $z;
}

sub update {
    my ($self, $epoch) = @_;
    $self->{tick}++;

    # Temperature evolution (logarithmic cooling)
    if ($epoch < 1000) {
        # Early universe: rapid cooling
        $self->{temperature} = $T_PLANCK * exp(-$epoch / 200);
    } elsif ($epoch < 50000) {
        # Pre-recombination
        $self->{temperature} = max($T_CMB, $T_PLANCK * exp(-$epoch / 200));
    } elsif ($epoch < 200000) {
        # Post-recombination to star formation
        $self->{temperature} = $T_CMB + _gauss(0, 0.5);
    } else {
        # Planet era
        $self->{temperature} = $T_EARTH_SURFACE + _gauss(0, 5);
        # Day/night
        $self->{day_night_cycle} = ($self->{tick} % 100) / 100.0;
        my $temp_mod = 10 * sin($self->{day_night_cycle} * 2 * $PI);
        $self->{temperature} += $temp_mod;
        # Seasons
        $self->{season} = ($self->{tick} % 1000) / 1000.0;
        my $season_mod = 15 * sin($self->{season} * 2 * $PI);
        $self->{temperature} += $season_mod;
    }

    # UV intensity (appears with stars)
    if ($epoch > 100000) {
        my $base_uv = 1.0;
        if ($self->{day_night_cycle} > 0.25 && $self->{day_night_cycle} < 0.75) {
            $self->{uv_intensity} = $base_uv * sin(
                ($self->{day_night_cycle} - 0.25) * 2 * $PI
            );
        } else {
            $self->{uv_intensity} = 0.0;
        }
    } else {
        $self->{uv_intensity} = 0.0;
    }

    # Cosmic ray flux
    if ($epoch > 10000) {
        # exponential variate
        my $lambda = 10.0;
        $self->{cosmic_ray_flux} = 0.1 + (-1.0 / $lambda) * log(rand() || 1e-20);
    } else {
        $self->{cosmic_ray_flux} = 1.0;  # High in early universe
    }

    # Atmospheric density (grows with planet formation)
    if ($epoch > 210000) {
        $self->{atmospheric_density} = min(1.0, ($epoch - 210000) / 50000);
        # Atmosphere shields from UV
        $self->{uv_intensity}    *= (1 - $self->{atmospheric_density} * 0.7);
        $self->{cosmic_ray_flux} *= (1 - $self->{atmospheric_density} * 0.5);
    }

    # Water availability
    if ($epoch > 220000) {
        $self->{water_availability} = min(1.0, ($epoch - 220000) / 30000);
    }

    # Random events
    $self->_generate_events($epoch);

    # Process active events
    $self->_process_events();
}

sub _generate_events {
    my ($self, $epoch) = @_;

    # Volcanic activity
    if ($epoch > 210000 && rand() < 0.005) {
        push @{$self->{events}}, EnvironmentalEvent->new(
            event_type    => 'volcanic',
            intensity     => 0.5 + rand() * 2.5,
            duration      => 10 + int(rand(91)),
            tick_occurred => $self->{tick},
        );
    }

    # Asteroid impact
    if (rand() < 0.0001) {
        push @{$self->{events}}, EnvironmentalEvent->new(
            event_type    => 'asteroid',
            intensity     => 1.0 + rand() * 9.0,
            duration      => 50 + int(rand(451)),
            tick_occurred => $self->{tick},
        );
    }

    # Solar flare
    if ($epoch > 100000 && rand() < 0.01) {
        push @{$self->{events}}, EnvironmentalEvent->new(
            event_type    => 'solar_flare',
            intensity     => 0.1 + rand() * 1.9,
            duration      => 5 + int(rand(16)),
            tick_occurred => $self->{tick},
        );
    }

    # Ice age
    if ($epoch > 250000 && rand() < 0.001) {
        push @{$self->{events}}, EnvironmentalEvent->new(
            event_type    => 'ice_age',
            intensity     => 0.5 + rand() * 1.0,
            duration      => 500 + int(rand(1501)),
            tick_occurred => $self->{tick},
        );
    }
}

sub _process_events {
    my ($self) = @_;
    my @active;
    for my $event (@{$self->{events}}) {
        my $elapsed = $self->{tick} - $event->{tick_occurred};
        if ($elapsed < $event->{duration}) {
            push @active, $event;
            $self->_apply_event($event);
        } else {
            push @{$self->{event_history}}, $event;
        }
    }
    $self->{events} = \@active;
}

sub _apply_event {
    my ($self, $event) = @_;

    if ($event->{event_type} eq 'volcanic') {
        $self->{temperature} += $event->{intensity} * 2;
        $self->{atmospheric_density} = min(1.0, $self->{atmospheric_density} + 0.01);
        $self->{uv_intensity} *= 0.9;  # Ash blocks UV
    }
    elsif ($event->{event_type} eq 'asteroid') {
        $self->{temperature}     -= $event->{intensity} * 5;  # Nuclear winter
        $self->{cosmic_ray_flux} += $event->{intensity};
        $self->{uv_intensity}    *= 0.5;
    }
    elsif ($event->{event_type} eq 'solar_flare') {
        $self->{uv_intensity}    += $event->{intensity};
        $self->{cosmic_ray_flux} += $event->{intensity} * 0.5;
    }
    elsif ($event->{event_type} eq 'ice_age') {
        $self->{temperature}        -= $event->{intensity} * 20;
        $self->{water_availability} *= 0.8;
    }
}

sub get_radiation_dose {
    my ($self) = @_;
    return $self->{uv_intensity} + $self->{cosmic_ray_flux} + $self->{stellar_wind};
}

sub is_habitable {
    my ($self) = @_;
    return (
        $self->{temperature} > 200
        && $self->{temperature} < 400
        && $self->{water_availability} > 0.1
        && $self->get_radiation_dose() < $RADIATION_DAMAGE_THRESHOLD
    ) ? 1 : 0;
}

sub thermal_energy {
    my ($self) = @_;
    # Scaled to provide meaningful energy in habitable range.
    # At ~300K, returns ~30 units (enough to sustain cell metabolism).
    if ($self->{temperature} < 100 || $self->{temperature} > 500) {
        return 0.1;
    }
    return max(0.1, $self->{temperature} * 0.1);
}

sub to_compact {
    my ($self) = @_;
    my $hab = $self->is_habitable() ? 'Y' : 'N';
    return sprintf("Env[T=%.1f UV=%.3f CR=%.3f atm=%.2f H2O=%.2f hab=%s ev=%d]",
        $self->{temperature},
        $self->{uv_intensity},
        $self->{cosmic_ray_flux},
        $self->{atmospheric_density},
        $self->{water_availability},
        $hab,
        scalar(@{$self->{events}}));
}

1;
