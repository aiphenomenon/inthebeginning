#!/usr/bin/env php
<?php

declare(strict_types=1);

/**
 * In The Beginning — Cosmic Simulation (PHP)
 * Simulates the universe from the Big Bang through the emergence of life.
 */

require_once __DIR__ . '/simulator/Universe.php';

function main(): void
{
    echo str_repeat('=', 70) . "\n";
    echo "  IN THE BEGINNING — Cosmic Simulation (PHP)\n";
    echo "  From the Big Bang to the emergence of life\n";
    echo str_repeat('=', 70) . "\n\n";

    $start = microtime(true);
    $universe = new Universe(ticksPerEpoch: 50);

    $results = $universe->run(function (int $idx, array $result): void {
        $epoch = $result['epoch'];
        $temp = $result['temperature'];
        $scale = $result['scale'];
        $stats = $result['stats'];

        printf("  [%2d] %-22s  T=%.2e K  Scale=%.2e\n", $idx, $epoch, $temp, $scale);
        printf("       Particles: %d  Atoms: %d  Molecules: %d  Life: %d\n",
            $stats['particles_created'],
            $stats['atoms_formed'],
            $stats['molecules_formed'],
            $stats['lifeforms_created']
        );
    });

    $elapsed = microtime(true) - $start;
    echo "\n" . str_repeat('-', 70) . "\n";
    printf("Simulation complete in %.3f seconds\n", $elapsed);
    printf("Final temperature: %.2f K\n", $universe->temperature);
    printf("Total epochs simulated: %d\n", count($results));
    echo str_repeat('-', 70) . "\n";
}

main();
