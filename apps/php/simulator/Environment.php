<?php

declare(strict_types=1);

require_once __DIR__ . '/Constants.php';

/**
 * Environmental effects simulation.
 *
 * Models temperature, radiation, geological and atmospheric effects
 * that influence cosmic and biological evolution.
 */

/**
 * A discrete environmental event (e.g., volcanic eruption, meteor impact).
 *
 * Records the event type, intensity, duration, spatial position, and
 * simulation tick at which it occurred.
 */
class EnvironmentalEvent
{
    /**
     * Create a new environmental event.
     *
     * @param string  $eventType    Type of event (e.g., 'volcanic', 'impact').
     * @param float   $intensity    Event intensity from 0.0 to 1.0.
     * @param int     $duration     Duration in simulation ticks.
     * @param float[] $position     3D position [x, y, z] where the event occurs.
     * @param int     $tickOccurred Simulation tick when the event started.
     */
    public function __construct(
        public readonly string $eventType,
        public readonly float $intensity,
        public readonly int $duration,
        public readonly array $position = [0.0, 0.0, 0.0],
        public readonly int $tickOccurred = 0,
    ) {}

    /**
     * Get a compact string representation of this event.
     *
     * @return string Formatted event descriptor.
     */
    public function toCompact(): string
    {
        return sprintf('Event(%s,i=%.2f,d=%d)', $this->eventType, $this->intensity, $this->duration);
    }
}

/**
 * The planetary environment simulation.
 *
 * Models temperature, radiation levels, atmospheric pressure and composition,
 * volcanic activity, and atmospheric evolution. Tracks environmental events
 * and drives conditions toward habitability.
 */
class Environment
{
    /** @var float Surface temperature in simulation Kelvin. */
    public float $temperature;

    /** @var float Radiation level (decays over time from initial 1.0). */
    public float $radiation;

    /** @var float Atmospheric pressure in atmospheres. */
    public float $pressure;
    /** @var array<string, float> */
    public array $atmosphere;
    /** @var EnvironmentalEvent[] */
    public array $events = [];
    public int $tick = 0;

    /**
     * Create a new environment with default primordial conditions.
     *
     * @param float $temperature Initial temperature (defaults to Planck temperature).
     */
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

    /**
     * Advance the environment by one simulation tick.
     *
     * Updates temperature, decays radiation, may generate volcanic events,
     * and evolves the atmosphere toward Earth-like composition at low temperatures.
     *
     * @param float $temperature The new temperature for this tick.
     */
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

    /**
     * Get a summary of the current environmental state.
     *
     * @return array{temperature: float, radiation: float, pressure: float, atmosphere: array, events: int}
     */
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
