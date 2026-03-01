package simulator

import (
	"math"
	"math/rand"
)

// EnvironmentalEvent represents a discrete environmental event.
type EnvironmentalEvent struct {
	EventType    string
	Intensity    float64
	Duration     int // ticks
	Position     [3]float64
	TickOccurred int
}

// Environment represents the physical environment that affects all simulation levels.
type Environment struct {
	Temperature       float64
	UVIntensity       float64
	CosmicRayFlux     float64
	StellarWind       float64
	AtmosphericDensity float64
	WaterAvailability float64
	DayNightCycle     float64 // 0-1, 0=midnight, 0.5=noon
	Season            float64 // 0-1, 0=winter, 0.5=summer
	Events            []EnvironmentalEvent
	EventHistory      []EnvironmentalEvent
	Tick              int
	rng               *rand.Rand
}

// NewEnvironment creates a new environment.
func NewEnvironment(initialTemperature float64, rng *rand.Rand) *Environment {
	return &Environment{
		Temperature:  initialTemperature,
		Events:       make([]EnvironmentalEvent, 0),
		EventHistory: make([]EnvironmentalEvent, 0),
		rng:          rng,
	}
}

// Update updates the environment based on cosmic epoch.
func (env *Environment) Update(epoch int) {
	env.Tick++

	// Temperature evolution (logarithmic cooling)
	if epoch < 1000 {
		// Early universe: rapid cooling
		env.Temperature = TPlanck * math.Exp(-float64(epoch)/200.0)
	} else if epoch < 50000 {
		// Pre-recombination
		env.Temperature = math.Max(TCMB, TPlanck*math.Exp(-float64(epoch)/200.0))
	} else if epoch < 200000 {
		// Post-recombination to star formation
		env.Temperature = TCMB + env.rng.NormFloat64()*0.5
	} else {
		// Planet era
		env.Temperature = TEarthSurface + env.rng.NormFloat64()*5
		// Day/night
		env.DayNightCycle = float64(env.Tick%100) / 100.0
		tempMod := 10 * math.Sin(env.DayNightCycle*2*PI)
		env.Temperature += tempMod
		// Seasons
		env.Season = float64(env.Tick%1000) / 1000.0
		seasonMod := 15 * math.Sin(env.Season*2*PI)
		env.Temperature += seasonMod
	}

	// UV intensity (appears with stars)
	if epoch > 100000 {
		baseUV := 1.0
		if env.DayNightCycle > 0.25 && env.DayNightCycle < 0.75 {
			env.UVIntensity = baseUV * math.Sin((env.DayNightCycle-0.25)*2*PI)
		} else {
			env.UVIntensity = 0.0
		}
	} else {
		env.UVIntensity = 0.0
	}

	// Cosmic ray flux
	if epoch > 10000 {
		env.CosmicRayFlux = 0.1 + env.rng.ExpFloat64()/10.0
	} else {
		env.CosmicRayFlux = 1.0 // High in early universe
	}

	// Atmospheric density (grows with planet formation)
	if epoch > 210000 {
		env.AtmosphericDensity = math.Min(1.0, float64(epoch-210000)/50000.0)
		env.UVIntensity *= (1 - env.AtmosphericDensity*0.7)
		env.CosmicRayFlux *= (1 - env.AtmosphericDensity*0.5)
	}

	// Water availability
	if epoch > 220000 {
		env.WaterAvailability = math.Min(1.0, float64(epoch-220000)/30000.0)
	}

	// Random events
	env.generateEvents(epoch)

	// Process active events
	env.processEvents()
}

func (env *Environment) generateEvents(epoch int) {
	// Volcanic activity
	if epoch > 210000 && env.rng.Float64() < 0.005 {
		env.Events = append(env.Events, EnvironmentalEvent{
			EventType:    "volcanic",
			Intensity:    env.rng.Float64()*2.5 + 0.5,
			Duration:     env.rng.Intn(90) + 10,
			TickOccurred: env.Tick,
		})
	}

	// Asteroid impact
	if env.rng.Float64() < 0.0001 {
		env.Events = append(env.Events, EnvironmentalEvent{
			EventType:    "asteroid",
			Intensity:    env.rng.Float64()*9.0 + 1.0,
			Duration:     env.rng.Intn(450) + 50,
			TickOccurred: env.Tick,
		})
	}

	// Solar flare
	if epoch > 100000 && env.rng.Float64() < 0.01 {
		env.Events = append(env.Events, EnvironmentalEvent{
			EventType:    "solar_flare",
			Intensity:    env.rng.Float64()*1.9 + 0.1,
			Duration:     env.rng.Intn(15) + 5,
			TickOccurred: env.Tick,
		})
	}

	// Ice age
	if epoch > 250000 && env.rng.Float64() < 0.001 {
		env.Events = append(env.Events, EnvironmentalEvent{
			EventType:    "ice_age",
			Intensity:    env.rng.Float64()*1.0 + 0.5,
			Duration:     env.rng.Intn(1500) + 500,
			TickOccurred: env.Tick,
		})
	}
}

func (env *Environment) processEvents() {
	active := make([]EnvironmentalEvent, 0, len(env.Events))
	for _, event := range env.Events {
		elapsed := env.Tick - event.TickOccurred
		if elapsed < event.Duration {
			active = append(active, event)
			env.applyEvent(event)
		} else {
			env.EventHistory = append(env.EventHistory, event)
		}
	}
	env.Events = active
}

func (env *Environment) applyEvent(event EnvironmentalEvent) {
	switch event.EventType {
	case "volcanic":
		env.Temperature += event.Intensity * 2
		env.AtmosphericDensity = math.Min(1.0, env.AtmosphericDensity+0.01)
		env.UVIntensity *= 0.9

	case "asteroid":
		env.Temperature -= event.Intensity * 5
		env.CosmicRayFlux += event.Intensity
		env.UVIntensity *= 0.5

	case "solar_flare":
		env.UVIntensity += event.Intensity
		env.CosmicRayFlux += event.Intensity * 0.5

	case "ice_age":
		env.Temperature -= event.Intensity * 20
		env.WaterAvailability *= 0.8
	}
}

// RadiationDose returns total radiation dose from all sources.
func (env *Environment) RadiationDose() float64 {
	return env.UVIntensity + env.CosmicRayFlux + env.StellarWind
}

// IsHabitable checks if conditions support life.
func (env *Environment) IsHabitable() bool {
	return env.Temperature > 200 && env.Temperature < 400 &&
		env.WaterAvailability > 0.1 &&
		env.RadiationDose() < RadiationDamageThreshold
}

// ThermalEnergy returns available thermal energy for biological processes.
func (env *Environment) ThermalEnergy() float64 {
	if env.Temperature < 100 || env.Temperature > 500 {
		return 0.1
	}
	val := env.Temperature * 0.1
	if val < 0.1 {
		return 0.1
	}
	return val
}
