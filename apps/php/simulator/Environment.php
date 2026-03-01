<?php

declare(strict_types=1);

require_once __DIR__ . '/Constants.php';

/**
 * Environmental effects simulation.
 *
 * Models temperature, radiation, geological and atmospheric effects
 * that influence cosmic and biological evolution.
 */

class EnvironmentalEvent
{
    public function __construct(
        public readonly string $eventType,
        public readonly float $intensity,
        public readonly int $duration,
        public readonly array $position = [0.0, 0.0, 0.0],
        public readonly int $tickOccurred = 0,
    ) {}

    public function toCompact(): string
    {
        return sprintf('Event(%s,i=%.2f,d=%d)', $this->eventType, $this->intensity, $this->duration);
    }
}

class Environment
{
    public float $temperature;
    public float $radiation;
    public float $pressure;
    /** @var array<string, float> */
    public array $atmosphere;
    /** @var EnvironmentalEvent[] */
    public array $events = [];
    public int $tick = 0;

    public function __construct(float $temperature = T_PLANCK)
    {
        $this->temperature = $temperature;
        $this->radiation = 1.0;
        $this->pressure = 1.0;
        $this->atmosphere = [
            'hydrogen' => 0.75,
            'helium' => 0.25,
            'nitrogen' => 0.0,
            'oxygen' => 0.0,
            'carbon_dioxide' => 0.0,
        ];
    }

    public function step(float $temperature): void
    {
        $this->tick++;
        $this->temperature = $temperature;
        $this->radiation = max(0.01, $this->radiation * 0.99);

        // Environmental events based on temperature regime
        if ($temperature < 1e4 && $temperature > 1000 && mt_rand(0, 100) < 5) {
            $this->events[] = new EnvironmentalEvent(
                'volcanic',
                (float)mt_rand(1, 100) / 100.0,
                mt_rand(10, 50),
                [0.0, 0.0, 0.0],
                $this->tick
            );
        }

        if ($temperature < 500 && $temperature > 200) {
            // Evolve atmosphere toward Earth-like
            $this->atmosphere['nitrogen'] = min(0.78, $this->atmosphere['nitrogen'] + 0.001);
            $this->atmosphere['oxygen'] = min(0.21, $this->atmosphere['oxygen'] + 0.0005);
            $this->atmosphere['hydrogen'] = max(0.0, $this->atmosphere['hydrogen'] - 0.001);
        }
    }

    public function getSummary(): array
    {
        return [
            'temperature' => $this->temperature,
            'radiation' => $this->radiation,
            'pressure' => $this->pressure,
            'atmosphere' => $this->atmosphere,
            'events' => count($this->events),
        ];
    }
}
