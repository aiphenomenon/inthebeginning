#!/usr/bin/env perl
# In The Beginning - Cosmic Simulation
# Simulates the universe from the Big Bang through the emergence of life.

use strict;
use warnings;
use FindBin qw($Bin);
use lib "$Bin/lib";
use Time::HiRes qw(time);

use Universe;

# AST Self-Introspection
if (grep { $_ eq '--ast-introspect' } @ARGV) {
    ast_introspect();
    exit 0;
}

sub ast_introspect {
    print "\n  === AST Self-Introspection: Perl App ===\n\n";

    my $lib_dir = "$Bin/lib";
    opendir(my $dh, $lib_dir) or die "Cannot open $lib_dir: $!";
    my @pm_files = sort grep { /\.pm$/ } readdir($dh);
    closedir($dh);

    # Also include this script
    my @all_files = ("$Bin/simulate.pl", map { "$lib_dir/$_" } @pm_files);

    printf "  %-22s %6s %8s %6s %6s\n", "File", "Lines", "Bytes", "Subs", "Pkgs";
    printf "  %-22s %6s %8s %6s %6s\n", '-' x 22, '-' x 6, '-' x 8, '-' x 6, '-' x 6;

    my ($total_lines, $total_bytes, $total_subs, $total_pkgs) = (0, 0, 0, 0);

    for my $file (@all_files) {
        open(my $fh, '<', $file) or next;
        my $content = do { local $/; <$fh> };
        close($fh);

        my $lines = () = $content =~ /\n/g;
        $lines++;
        my $bytes = -s $file;
        my $subs  = () = $content =~ /^sub\s+\w+/mg;
        my $pkgs  = () = $content =~ /^package\s+\w+/mg;

        (my $short = $file) =~ s{^.*/}{};
        printf "  %-22s %6d %8d %6d %6d\n", $short, $lines, $bytes, $subs, $pkgs;

        $total_lines += $lines;
        $total_bytes += $bytes;
        $total_subs  += $subs;
        $total_pkgs  += $pkgs;
    }

    printf "  %-22s %6s %8s %6s %6s\n", '-' x 22, '-' x 6, '-' x 8, '-' x 6, '-' x 6;
    printf "  %-22s %6d %8d %6d %6d\n", "TOTAL", $total_lines, $total_bytes, $total_subs, $total_pkgs;
    print "\n";
}

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
