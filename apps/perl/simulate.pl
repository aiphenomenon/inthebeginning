#!/usr/bin/env perl
# In The Beginning - Cosmic Simulation
# Simulates the universe from the Big Bang through the emergence of life.

use strict;
use warnings;
use FindBin qw($Bin);
use lib "$Bin/lib";
use Time::HiRes qw(time);

use Universe;

sub main {
    print "=" x 70, "\n";
    print "  IN THE BEGINNING — Cosmic Simulation (Perl)\n";
    print "  From the Big Bang to the emergence of life\n";
    print "=" x 70, "\n\n";

    my $start = time();
    my $universe = Universe->new(ticks_per_epoch => 50);

    my $epoch_counter = 0;
    my $results = $universe->run(
        on_epoch_complete => sub {
            my ($result) = @_;
            my $epoch = $result->{epoch};
            my $temp  = $result->{temperature};
            my $scale = $result->{scale};
            my $stats = $result->{stats};

            printf "  [%2d] %-22s  T=%.2e K  Scale=%.2e\n",
                   $epoch_counter++, $epoch, $temp, $scale;
            printf "       Particles: %d  Atoms: %d  Molecules: %d  Life: %d\n",
                   $stats->{particles_created} || 0,
                   $stats->{atoms_formed} || 0,
                   $stats->{molecules_formed} || 0,
                   $stats->{lifeforms_created} || 0;
        }
    );

    my $elapsed = time() - $start;
    print "\n", "-" x 70, "\n";
    printf "Simulation complete in %.3f seconds\n", $elapsed;
    printf "Final temperature: %.2f K\n", $universe->{temperature};
    printf "Total epochs simulated: %d\n", scalar @$results;
    print "-" x 70, "\n";
}

main();
