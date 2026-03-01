#!/usr/bin/env php
<?php

declare(strict_types=1);

/**
 * In The Beginning — Cosmic Simulation (PHP)
 * Simulates the universe from the Big Bang through the emergence of life.
 */

require_once __DIR__ . '/simulator/Universe.php';

/**
 * Run AST self-introspection on all PHP source files in the app directory.
 *
 * Scans simulate.php and simulator/*.php, counts lines, bytes, function
 * definitions, and class definitions, then prints a formatted summary table.
 */
function runAstIntrospection(): void
{
    echo "\n\033[1m\033[36m=== AST Self-Introspection: PHP App ===\033[0m\n\n";

    // Collect all .php files: top-level + simulator/
    $appDir = __DIR__;
    $files = [];

    // Top-level .php files
    foreach (glob($appDir . '/*.php') as $f) {
        $files[] = $f;
    }

    // simulator/*.php files
    foreach (glob($appDir . '/simulator/*.php') as $f) {
        $files[] = $f;
    }

    sort($files);

    $totalLines = 0;
    $totalBytes = 0;
    $totalFunctions = 0;
    $totalClasses = 0;

    // Table header
    printf("  %-32s %6s %8s %6s %8s\n", 'File', 'Lines', 'Bytes', 'Funcs', 'Classes');
    printf("  %s %s %s %s %s\n",
        str_repeat("\xe2\x94\x80", 32),
        str_repeat("\xe2\x94\x80", 6),
        str_repeat("\xe2\x94\x80", 8),
        str_repeat("\xe2\x94\x80", 6),
        str_repeat("\xe2\x94\x80", 8)
    );

    foreach ($files as $filepath) {
        $src = file_get_contents($filepath);
        if ($src === false) {
            continue;
        }

        $lines = substr_count($src, "\n") + 1;
        $bytes = filesize($filepath);
        $relPath = str_replace($appDir . '/', '', $filepath);

        // Count function definitions (function keyword followed by a name)
        preg_match_all('/\bfunction\s+\w+\s*\(/', $src, $funcMatches);
        $funcCount = count($funcMatches[0]);

        // Count class definitions
        preg_match_all('/\bclass\s+\w+/', $src, $classMatches);
        $classCount = count($classMatches[0]);

        $totalLines += $lines;
        $totalBytes += $bytes;
        $totalFunctions += $funcCount;
        $totalClasses += $classCount;

        printf("  %-32s %6d %8d %6d %8d\n", $relPath, $lines, $bytes, $funcCount, $classCount);
    }

    // Table footer
    printf("  %s %s %s %s %s\n",
        str_repeat("\xe2\x94\x80", 32),
        str_repeat("\xe2\x94\x80", 6),
        str_repeat("\xe2\x94\x80", 8),
        str_repeat("\xe2\x94\x80", 6),
        str_repeat("\xe2\x94\x80", 8)
    );
    printf("  %-32s %6d %8d %6d %8d\n", 'TOTAL', $totalLines, $totalBytes, $totalFunctions, $totalClasses);
    echo "\n";
}

// Handle --ast-introspect flag before running simulation
if (in_array('--ast-introspect', $argv ?? [], true)) {
    runAstIntrospection();
    exit(0);
}

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
