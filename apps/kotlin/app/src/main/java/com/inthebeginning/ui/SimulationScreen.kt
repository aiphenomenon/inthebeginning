package com.inthebeginning.ui

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectTransformGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Pause
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.FilledIconButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButtonDefaults
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.rotate
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.inthebeginning.simulator.Constants
import com.inthebeginning.simulator.SimulationState
import com.inthebeginning.ui.theme.LifeGreen
import com.inthebeginning.ui.theme.NeutronBlue
import com.inthebeginning.ui.theme.NovaCyan
import com.inthebeginning.ui.theme.PlasmaPink
import com.inthebeginning.ui.theme.RadiationAmber
import com.inthebeginning.ui.theme.RedShift
import com.inthebeginning.ui.theme.SolarGold
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.min
import kotlin.math.sin

/**
 * Main simulation screen composable.
 */
@Composable
fun SimulationScreen(
    state: SimulationState,
    onPlayPause: () -> Unit,
    onReset: () -> Unit,
    onSpeedChange: (Int) -> Unit,
    onSettingsClick: () -> Unit = {},
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .padding(16.dp)
    ) {
        // Header: epoch name and progress
        EpochHeader(state)

        Spacer(modifier = Modifier.height(12.dp))

        // Canvas visualization
        CosmicCanvas(
            state = state,
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f)
                .clip(RoundedCornerShape(16.dp))
        )

        Spacer(modifier = Modifier.height(12.dp))

        // Stats cards
        StatsRow(state)

        Spacer(modifier = Modifier.height(12.dp))

        // Event log
        EventLog(
            events = state.events,
            modifier = Modifier
                .fillMaxWidth()
                .weight(0.4f)
        )

        Spacer(modifier = Modifier.height(12.dp))

        // Controls
        ControlBar(
            running = state.running,
            completed = state.completed,
            onPlayPause = onPlayPause,
            onReset = onReset,
            onSpeedChange = onSpeedChange,
            onSettingsClick = onSettingsClick
        )
    }
}

/**
 * Header displaying current epoch name and overall progress.
 */
@Composable
private fun EpochHeader(state: SimulationState) {
    val epochColor by animateColorAsState(
        targetValue = epochToColor(state.currentEpoch.name),
        animationSpec = tween(durationMillis = 800),
        label = "epochColor"
    )

    Column(
        modifier = Modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = state.currentEpoch.name,
            style = MaterialTheme.typography.headlineMedium,
            color = epochColor,
            fontWeight = FontWeight.Bold
        )

        Text(
            text = state.currentEpoch.description,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center
        )

        Spacer(modifier = Modifier.height(8.dp))

        LinearProgressIndicator(
            progress = { (state.tick.toFloat() / Constants.PRESENT_EPOCH).coerceIn(0f, 1f) },
            modifier = Modifier
                .fillMaxWidth()
                .height(6.dp)
                .clip(RoundedCornerShape(3.dp)),
            color = epochColor,
            trackColor = MaterialTheme.colorScheme.surfaceVariant,
        )

        Text(
            text = "Tick ${state.tick} / ${Constants.PRESENT_EPOCH}",
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(top = 4.dp)
        )
    }
}

/**
 * Canvas-based cosmic visualization that changes based on epoch.
 * Supports pinch-to-zoom and pan gestures for interactive exploration.
 */
@Composable
private fun CosmicCanvas(
    state: SimulationState,
    modifier: Modifier = Modifier
) {
    val infiniteTransition = rememberInfiniteTransition(label = "cosmic")

    val rotationAngle by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = 360f,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMillis = 20000, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "rotation"
    )

    val pulseScale by infiniteTransition.animateFloat(
        initialValue = 0.8f,
        targetValue = 1.2f,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMillis = 2000, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "pulse"
    )

    // Pinch-to-zoom and pan state
    var zoomLevel by remember { mutableFloatStateOf(1.0f) }
    var panOffsetX by remember { mutableFloatStateOf(0f) }
    var panOffsetY by remember { mutableFloatStateOf(0f) }

    val epochColor = epochToColor(state.currentEpoch.name)

    Canvas(
        modifier = modifier
            .background(
                Brush.radialGradient(
                    colors = listOf(
                        epochColor.copy(alpha = 0.15f),
                        Color.Black
                    )
                )
            )
            .pointerInput(Unit) {
                detectTransformGestures { _, pan, gestureZoom, _ ->
                    zoomLevel = (zoomLevel * gestureZoom).coerceIn(0.3f, 5.0f)
                    panOffsetX += pan.x
                    panOffsetY += pan.y
                }
            }
    ) {
        val center = Offset(
            size.width / 2f + panOffsetX,
            size.height / 2f + panOffsetY
        )
        val radius = min(size.width, size.height) / 3f * zoomLevel

        when {
            state.tick <= Constants.INFLATION_EPOCH -> {
                drawBigBang(center, radius, pulseScale, epochColor)
            }
            state.tick <= Constants.HADRON_EPOCH -> {
                drawParticleField(center, radius, rotationAngle, state, epochColor)
            }
            state.tick <= Constants.RECOMBINATION_EPOCH -> {
                drawNucleosynthesis(center, radius, rotationAngle, state, epochColor)
            }
            state.tick <= Constants.STAR_FORMATION_EPOCH -> {
                drawRecombination(center, radius, pulseScale, epochColor)
            }
            state.tick <= Constants.EARTH_EPOCH -> {
                drawStarField(center, radius, rotationAngle, state, epochColor)
            }
            state.tick <= Constants.LIFE_EPOCH -> {
                drawPlanet(center, radius, rotationAngle, state, epochColor)
            }
            else -> {
                drawBiosphere(center, radius, rotationAngle, state, epochColor, pulseScale)
            }
        }
    }
}

/**
 * Draw the initial Big Bang singularity / inflation visualization.
 */
private fun DrawScope.drawBigBang(
    center: Offset,
    radius: Float,
    pulse: Float,
    color: Color
) {
    // Central bright point
    val innerRadius = radius * 0.1f * pulse
    drawCircle(
        brush = Brush.radialGradient(
            colors = listOf(Color.White, color, Color.Transparent),
            center = center,
            radius = innerRadius * 3
        ),
        radius = innerRadius * 3,
        center = center
    )

    // Expanding rings
    for (i in 1..5) {
        val ringRadius = radius * i * 0.15f * pulse
        drawCircle(
            color = color.copy(alpha = 0.3f / i),
            radius = ringRadius,
            center = center,
            style = Stroke(width = 2f)
        )
    }
}

/**
 * Draw the quark-gluon plasma / particle field.
 */
private fun DrawScope.drawParticleField(
    center: Offset,
    radius: Float,
    rotation: Float,
    state: SimulationState,
    color: Color
) {
    val totalParticles = state.particleCounts.values.sum().coerceAtLeast(1)
    val particleCount = totalParticles.coerceAtMost(100)

    rotate(rotation * 0.5f, pivot = center) {
        for (i in 0 until particleCount) {
            val angle = (i.toFloat() / particleCount) * 2f * PI.toFloat()
            val dist = radius * (0.2f + (i % 5) * 0.15f)
            val x = center.x + cos(angle) * dist
            val y = center.y + sin(angle) * dist
            val particleRadius = 3f + (i % 3) * 2f
            val particleColor = when (i % 4) {
                0 -> PlasmaPink
                1 -> NeutronBlue
                2 -> SolarGold
                else -> color
            }
            drawCircle(
                color = particleColor.copy(alpha = 0.8f),
                radius = particleRadius,
                center = Offset(x, y)
            )
        }
    }

    // Gluon field lines
    for (i in 0..7) {
        val startAngle = (i * 45f + rotation) * PI.toFloat() / 180f
        val endAngle = ((i + 3) * 45f + rotation) * PI.toFloat() / 180f
        drawLine(
            color = color.copy(alpha = 0.2f),
            start = Offset(
                center.x + cos(startAngle) * radius * 0.3f,
                center.y + sin(startAngle) * radius * 0.3f
            ),
            end = Offset(
                center.x + cos(endAngle) * radius * 0.6f,
                center.y + sin(endAngle) * radius * 0.6f
            ),
            strokeWidth = 1f
        )
    }
}

/**
 * Draw nucleosynthesis era: nuclei forming.
 */
private fun DrawScope.drawNucleosynthesis(
    center: Offset,
    radius: Float,
    rotation: Float,
    state: SimulationState,
    color: Color
) {
    // Background glow
    drawCircle(
        brush = Brush.radialGradient(
            colors = listOf(color.copy(alpha = 0.1f), Color.Transparent),
            center = center,
            radius = radius * 1.5f
        ),
        radius = radius * 1.5f,
        center = center
    )

    // Hydrogen atoms (small)
    val hCount = (state.elementCounts["H"] ?: 0).coerceAtMost(40)
    for (i in 0 until hCount) {
        val angle = (i.toFloat() / hCount) * 2f * PI.toFloat() + rotation * 0.01f
        val dist = radius * (0.4f + (i % 3) * 0.2f)
        drawCircle(
            color = NeutronBlue.copy(alpha = 0.7f),
            radius = 4f,
            center = Offset(
                center.x + cos(angle) * dist,
                center.y + sin(angle) * dist
            )
        )
    }

    // Helium atoms (larger, golden)
    val heCount = (state.elementCounts["He"] ?: 0).coerceAtMost(20)
    rotate(rotation * 0.3f, pivot = center) {
        for (i in 0 until heCount) {
            val angle = (i.toFloat() / heCount.coerceAtLeast(1)) * 2f * PI.toFloat()
            val dist = radius * 0.5f
            drawCircle(
                color = SolarGold.copy(alpha = 0.8f),
                radius = 8f,
                center = Offset(
                    center.x + cos(angle) * dist,
                    center.y + sin(angle) * dist
                )
            )
        }
    }
}

/**
 * Draw the recombination era: CMB release.
 */
private fun DrawScope.drawRecombination(
    center: Offset,
    radius: Float,
    pulse: Float,
    color: Color
) {
    // CMB radiation pattern (concentric fading circles)
    for (i in 1..10) {
        val ringRadius = radius * i * 0.1f * pulse
        val alpha = (0.4f / i).coerceAtLeast(0.02f)
        drawCircle(
            color = RadiationAmber.copy(alpha = alpha),
            radius = ringRadius,
            center = center,
            style = Stroke(width = 3f)
        )
    }

    // Scattered photons
    for (i in 0..20) {
        val angle = (i * 17f) * PI.toFloat() / 180f
        val dist = radius * (0.3f + (i % 5) * 0.15f) * pulse
        drawCircle(
            color = SolarGold.copy(alpha = 0.5f),
            radius = 2f,
            center = Offset(
                center.x + cos(angle) * dist,
                center.y + sin(angle) * dist
            )
        )
    }
}

/**
 * Draw star formation: stars and nebulae.
 */
private fun DrawScope.drawStarField(
    center: Offset,
    radius: Float,
    rotation: Float,
    state: SimulationState,
    color: Color
) {
    // Nebula background
    drawCircle(
        brush = Brush.radialGradient(
            colors = listOf(
                NebulaPurpleCanvas.copy(alpha = 0.15f),
                NeutronBlue.copy(alpha = 0.05f),
                Color.Transparent
            ),
            center = center,
            radius = radius * 1.2f
        ),
        radius = radius * 1.2f,
        center = center
    )

    // Stars
    val starCount = 30
    for (i in 0 until starCount) {
        val angle = (i.toFloat() / starCount) * 2f * PI.toFloat() + rotation * 0.005f
        val dist = radius * (0.2f + (i * 7 % 10) * 0.08f)
        val starSize = 2f + (i % 4) * 1.5f
        val starColor = when (i % 3) {
            0 -> Color.White
            1 -> NeutronBlue
            else -> SolarGold
        }
        drawCircle(
            color = starColor.copy(alpha = 0.9f),
            radius = starSize,
            center = Offset(
                center.x + cos(angle) * dist,
                center.y + sin(angle) * dist
            )
        )

        // Star glow
        drawCircle(
            color = starColor.copy(alpha = 0.2f),
            radius = starSize * 3f,
            center = Offset(
                center.x + cos(angle) * dist,
                center.y + sin(angle) * dist
            )
        )
    }
}

/**
 * Draw a planet (Earth) with atmosphere.
 */
private fun DrawScope.drawPlanet(
    center: Offset,
    radius: Float,
    rotation: Float,
    state: SimulationState,
    color: Color
) {
    val planetRadius = radius * 0.5f

    // Atmosphere glow
    drawCircle(
        brush = Brush.radialGradient(
            colors = listOf(
                NeutronBlue.copy(alpha = 0.2f),
                Color.Transparent
            ),
            center = center,
            radius = planetRadius * 1.5f
        ),
        radius = planetRadius * 1.5f,
        center = center
    )

    // Planet body
    drawCircle(
        brush = Brush.linearGradient(
            colors = if (state.hasLiquidWater) {
                listOf(NeutronBlue, LifeGreen.copy(alpha = 0.5f), SolarGold.copy(alpha = 0.3f))
            } else {
                listOf(RedShift, RadiationAmber, SolarGold.copy(alpha = 0.5f))
            }
        ),
        radius = planetRadius,
        center = center
    )

    // Surface features (rotating)
    rotate(rotation * 0.1f, pivot = center) {
        for (i in 0..5) {
            val featureAngle = (i * 60f) * PI.toFloat() / 180f
            val featureDist = planetRadius * 0.3f
            drawCircle(
                color = if (state.hasLiquidWater) {
                    NeutronBlue.copy(alpha = 0.4f)
                } else {
                    RedShift.copy(alpha = 0.3f)
                },
                radius = planetRadius * 0.15f,
                center = Offset(
                    center.x + cos(featureAngle) * featureDist,
                    center.y + sin(featureAngle) * featureDist
                )
            )
        }
    }

    // Orbiting star background
    for (i in 0..15) {
        val angle = (i * 24f + rotation * 0.02f) * PI.toFloat() / 180f
        val dist = radius * (0.8f + (i % 3) * 0.15f)
        drawCircle(
            color = Color.White.copy(alpha = 0.5f),
            radius = 1.5f,
            center = Offset(
                center.x + cos(angle) * dist,
                center.y + sin(angle) * dist
            )
        )
    }
}

/**
 * Draw the biosphere: life visualization with DNA helices and cells.
 */
private fun DrawScope.drawBiosphere(
    center: Offset,
    radius: Float,
    rotation: Float,
    state: SimulationState,
    color: Color,
    pulse: Float
) {
    // Planet in background
    drawPlanet(center, radius * 0.6f, rotation, state, color)

    // DNA double helix overlay
    val helixPoints = 40
    val helixRadius = radius * 0.15f
    val helixHeight = radius * 1.2f
    val helixStartY = center.y - helixHeight / 2f

    for (i in 0 until helixPoints) {
        val t = i.toFloat() / helixPoints
        val y = helixStartY + t * helixHeight
        val angle = t * 4f * PI.toFloat() + rotation * 0.02f

        // Strand 1
        val x1 = center.x + radius * 0.6f + cos(angle) * helixRadius
        drawCircle(
            color = NovaCyan.copy(alpha = 0.7f),
            radius = 3f,
            center = Offset(x1, y)
        )

        // Strand 2
        val x2 = center.x + radius * 0.6f + cos(angle + PI.toFloat()) * helixRadius
        drawCircle(
            color = PlasmaPink.copy(alpha = 0.7f),
            radius = 3f,
            center = Offset(x2, y)
        )

        // Base pair rungs
        if (i % 4 == 0) {
            drawLine(
                color = SolarGold.copy(alpha = 0.3f),
                start = Offset(x1, y),
                end = Offset(x2, y),
                strokeWidth = 1.5f
            )
        }
    }

    // Cells (population visualization)
    val cellCount = state.populationSize.coerceAtMost(30)
    for (i in 0 until cellCount) {
        val angle = (i.toFloat() / cellCount.coerceAtLeast(1)) * 2f * PI.toFloat() + rotation * 0.01f
        val dist = radius * (0.3f + (i % 4) * 0.1f) * pulse * 0.8f
        val cellRadius = 5f + (state.averageFitness.toFloat() * 3f).coerceAtMost(10f)
        val cellOffset = Offset(
            center.x - radius * 0.3f + cos(angle) * dist,
            center.y + sin(angle) * dist
        )

        // Cell membrane
        drawCircle(
            color = LifeGreen.copy(alpha = 0.5f),
            radius = cellRadius,
            center = cellOffset,
            style = Stroke(width = 1.5f)
        )

        // Cell interior
        drawCircle(
            color = LifeGreen.copy(alpha = 0.15f),
            radius = cellRadius * 0.8f,
            center = cellOffset
        )

        // Nucleus
        drawCircle(
            color = NovaCyan.copy(alpha = 0.6f),
            radius = cellRadius * 0.3f,
            center = cellOffset
        )
    }
}

// Canvas-compatible purple constant (avoids import clash with theme)
private val NebulaPurpleCanvas = Color(0xFF6B3FA0)

/**
 * Map epoch name to a display color.
 */
private fun epochToColor(epochName: String): Color = when (epochName) {
    "Planck" -> Color.White
    "Inflation" -> PlasmaPink
    "Electroweak" -> RadiationAmber
    "Quark" -> RedShift
    "Hadron" -> SolarGold
    "Nucleosynthesis" -> NeutronBlue
    "Recombination" -> RadiationAmber
    "Star Formation" -> SolarGold
    "Solar System" -> NovaCyan
    "Earth" -> NeutronBlue
    "Life" -> LifeGreen
    "DNA Era" -> NovaCyan
    "Present" -> LifeGreen
    else -> Color.White
}

/**
 * Row of stat cards showing key metrics.
 */
@Composable
private fun StatsRow(state: SimulationState) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        StatCard(
            label = "Temp",
            value = formatTemperature(state.temperature),
            color = temperatureColor(state.temperature),
            modifier = Modifier.weight(1f)
        )
        StatCard(
            label = "Particles",
            value = "${state.particleCounts.values.sum()}",
            color = NeutronBlue,
            modifier = Modifier.weight(1f)
        )
        StatCard(
            label = "Elements",
            value = "${state.elementCounts.size}",
            color = SolarGold,
            modifier = Modifier.weight(1f)
        )
        StatCard(
            label = "Life",
            value = "${state.populationSize}",
            color = LifeGreen,
            modifier = Modifier.weight(1f)
        )
    }
}

/**
 * A single stat card.
 */
@Composable
private fun StatCard(
    label: String,
    value: String,
    color: Color,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier,
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.7f)
        ),
        shape = RoundedCornerShape(12.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(8.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = value,
                style = MaterialTheme.typography.titleMedium,
                color = color,
                fontWeight = FontWeight.Bold,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis
            )
            Text(
                text = label,
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

/**
 * Scrollable event log.
 */
@Composable
private fun EventLog(
    events: List<String>,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier,
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface
        ),
        shape = RoundedCornerShape(12.dp)
    ) {
        Column(modifier = Modifier.padding(12.dp)) {
            Text(
                text = "Event Log",
                style = MaterialTheme.typography.titleSmall,
                color = MaterialTheme.colorScheme.primary,
                fontWeight = FontWeight.SemiBold
            )

            Spacer(modifier = Modifier.height(4.dp))

            if (events.isEmpty()) {
                Text(
                    text = "Press Play to begin the simulation...",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            } else {
                LazyColumn {
                    items(events.reversed()) { event ->
                        Text(
                            text = event,
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.8f),
                            modifier = Modifier.padding(vertical = 2.dp),
                            maxLines = 2,
                            overflow = TextOverflow.Ellipsis
                        )
                    }
                }
            }
        }
    }
}

/**
 * Bottom control bar with play/pause, reset, settings, and speed slider.
 */
@Composable
private fun ControlBar(
    running: Boolean,
    completed: Boolean,
    onPlayPause: () -> Unit,
    onReset: () -> Unit,
    onSpeedChange: (Int) -> Unit,
    onSettingsClick: () -> Unit = {}
) {
    var speedSlider by remember { mutableFloatStateOf(0.5f) }

    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant
        ),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(
            modifier = Modifier.padding(12.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Reset button
                FilledIconButton(
                    onClick = onReset,
                    colors = IconButtonDefaults.filledIconButtonColors(
                        containerColor = MaterialTheme.colorScheme.errorContainer,
                        contentColor = MaterialTheme.colorScheme.onErrorContainer
                    ),
                    modifier = Modifier.size(48.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.Refresh,
                        contentDescription = "Reset"
                    )
                }

                Spacer(modifier = Modifier.width(16.dp))

                // Play / Pause button
                FilledIconButton(
                    onClick = onPlayPause,
                    enabled = !completed,
                    colors = IconButtonDefaults.filledIconButtonColors(
                        containerColor = MaterialTheme.colorScheme.primary,
                        contentColor = MaterialTheme.colorScheme.onPrimary
                    ),
                    modifier = Modifier.size(64.dp)
                ) {
                    Icon(
                        imageVector = if (running) Icons.Default.Pause else Icons.Default.PlayArrow,
                        contentDescription = if (running) "Pause" else "Play",
                        modifier = Modifier.size(32.dp)
                    )
                }

                Spacer(modifier = Modifier.width(16.dp))

                // Settings button
                FilledIconButton(
                    onClick = onSettingsClick,
                    colors = IconButtonDefaults.filledIconButtonColors(
                        containerColor = MaterialTheme.colorScheme.tertiaryContainer,
                        contentColor = MaterialTheme.colorScheme.onTertiaryContainer
                    ),
                    modifier = Modifier.size(48.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.Settings,
                        contentDescription = "Settings"
                    )
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Speed slider
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Speed:",
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )

                Slider(
                    value = speedSlider,
                    onValueChange = { value ->
                        speedSlider = value
                        // Map 0..1 to ticks per step: 10..1000
                        val ticks = (10 + (value * 990)).toInt()
                        onSpeedChange(ticks)
                    },
                    modifier = Modifier
                        .weight(1f)
                        .padding(horizontal = 8.dp),
                    colors = SliderDefaults.colors(
                        thumbColor = MaterialTheme.colorScheme.primary,
                        activeTrackColor = MaterialTheme.colorScheme.primary,
                        inactiveTrackColor = MaterialTheme.colorScheme.surfaceVariant
                    )
                )

                Text(
                    text = "${(10 + (speedSlider * 990)).toInt()}",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.width(40.dp),
                    textAlign = TextAlign.End
                )
            }
        }
    }
}

// === Utility functions ===

private fun formatTemperature(temp: Double): String = when {
    temp >= 1e9 -> "${String.format("%.0f", temp / 1e9)}B K"
    temp >= 1e6 -> "${String.format("%.0f", temp / 1e6)}M K"
    temp >= 1e3 -> "${String.format("%.0f", temp / 1e3)}K K"
    temp >= 100 -> "${String.format("%.0f", temp)} K"
    else -> "${String.format("%.1f", temp)} K"
}

private fun temperatureColor(temp: Double): Color = when {
    temp > 1e6 -> PlasmaPink
    temp > 1e4 -> RadiationAmber
    temp > 1e3 -> SolarGold
    temp > 300 -> RedShift
    temp > 250 -> LifeGreen
    else -> NeutronBlue
}
