#!/usr/bin/env php
<?php

declare(strict_types=1);

/**
 * In The Beginning — PHP Snapshot Server
 *
 * Runs the simulation in the background and serves HTML snapshots.
 * Usage: php -S localhost:8080 server.php
 *
 * Endpoints:
 *   /          - HTML snapshot (auto-refreshes every 10s)
 *   /api/state - JSON snapshot of current simulation state
 *   /api/reset - Reset simulation with new seed
 */

require_once __DIR__ . '/simulator/Universe.php';

/* ------------------------------------------------------------------ */
/*  Global simulation state (persisted across requests via static)     */
/* ------------------------------------------------------------------ */

class SimulationServer
{
    private static ?Universe $universe = null;
    private static int $epochIndex = 0;
    private static array $epochResults = [];
    private static float $startTime = 0;
    private static int $seed = 0;

    public static function init(): void
    {
        if (self::$universe !== null) return;

        self::$seed = (int)(microtime(true) * 1000) % 999999;
        srand(self::$seed);
        self::$startTime = microtime(true);
        self::$universe = new Universe(ticksPerEpoch: 50);

        self::$epochResults = self::$universe->run(function (int $idx, array $result): void {
            // Results collected automatically
        });
    }

    public static function getState(): array
    {
        self::init();
        $u = self::$universe;
        $elapsed = microtime(true) - self::$startTime;

        return [
            'seed' => self::$seed,
            'elapsed_seconds' => round($elapsed, 3),
            'current_epoch' => $u->epochName(),
            'epoch_index' => $u->currentEpoch,
            'temperature' => $u->temperature,
            'scale_factor' => $u->scaleFactor,
            'stats' => $u->stats,
            'epochs' => self::$epochResults,
        ];
    }

    public static function reset(): void
    {
        self::$universe = null;
        self::init();
    }
}

/* ------------------------------------------------------------------ */
/*  Request router                                                     */
/* ------------------------------------------------------------------ */

$uri = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH);

SimulationServer::init();

if ($uri === '/api/state') {
    header('Content-Type: application/json');
    header('Access-Control-Allow-Origin: *');
    echo json_encode(SimulationServer::getState(), JSON_PRETTY_PRINT);
    exit;
}

if ($uri === '/api/reset') {
    SimulationServer::reset();
    header('Content-Type: application/json');
    echo json_encode(['status' => 'reset', 'state' => SimulationServer::getState()], JSON_PRETTY_PRINT);
    exit;
}

if ($uri === '/style.css') {
    header('Content-Type: text/css');
    readfile(__DIR__ . '/public/style.css');
    exit;
}

/* Default: HTML snapshot */
$state = SimulationServer::getState();
require __DIR__ . '/templates/snapshot.php';
