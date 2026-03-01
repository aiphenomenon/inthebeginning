package com.inthebeginning.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SegmentedButton
import androidx.compose.material3.SegmentedButtonDefaults
import androidx.compose.material3.SingleChoiceSegmentedButtonRow
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp

/**
 * Visualization style options.
 */
enum class VisualizationStyle(val label: String) {
    CANVAS("Canvas"),
    OPENGL("OpenGL"),
    MINIMAL("Minimal")
}

/**
 * Settings screen for configuring the simulation parameters.
 *
 * Provides controls for:
 * - Random seed for reproducible simulations
 * - Simulation speed (ticks per step)
 * - Visualization style (Canvas, OpenGL, Minimal)
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    currentSeed: String,
    currentSpeed: Int,
    currentStyle: VisualizationStyle,
    onSeedChange: (String) -> Unit,
    onSpeedChange: (Int) -> Unit,
    onStyleChange: (VisualizationStyle) -> Unit,
    onBack: () -> Unit
) {
    var seedText by remember { mutableStateOf(currentSeed) }
    var speedSlider by remember {
        mutableFloatStateOf(
            ((currentSpeed - 10).toFloat() / 990f).coerceIn(0f, 1f)
        )
    }
    var selectedStyleIndex by remember {
        mutableIntStateOf(VisualizationStyle.entries.indexOf(currentStyle))
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = "Settings",
                        style = MaterialTheme.typography.headlineSmall,
                        fontWeight = FontWeight.SemiBold
                    )
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = "Back"
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.background,
                    titleContentColor = MaterialTheme.colorScheme.onBackground
                )
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(horizontal = 16.dp)
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // === Seed ===
            SettingsCard(title = "Random Seed") {
                Text(
                    text = "Set a seed for reproducible simulations. " +
                            "Same seed produces the same universe.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(modifier = Modifier.height(8.dp))
                OutlinedTextField(
                    value = seedText,
                    onValueChange = { newValue ->
                        seedText = newValue
                        onSeedChange(newValue)
                    },
                    label = { Text("Seed") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )
            }

            // === Speed ===
            SettingsCard(title = "Simulation Speed") {
                Text(
                    text = "Controls how many simulation ticks are computed per frame. " +
                            "Higher values progress faster but may reduce smoothness.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(modifier = Modifier.height(8.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "Slow",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Slider(
                        value = speedSlider,
                        onValueChange = { value ->
                            speedSlider = value
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
                        text = "Fast",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                Text(
                    text = "${(10 + (speedSlider * 990)).toInt()} ticks/step",
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.align(Alignment.CenterHorizontally)
                )
            }

            // === Visualization Style ===
            SettingsCard(title = "Visualization Style") {
                Text(
                    text = "Choose the rendering approach for the simulation display.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(modifier = Modifier.height(12.dp))
                SingleChoiceSegmentedButtonRow(
                    modifier = Modifier.fillMaxWidth()
                ) {
                    VisualizationStyle.entries.forEachIndexed { index, style ->
                        SegmentedButton(
                            selected = index == selectedStyleIndex,
                            onClick = {
                                selectedStyleIndex = index
                                onStyleChange(style)
                            },
                            shape = SegmentedButtonDefaults.itemShape(
                                index = index,
                                count = VisualizationStyle.entries.size
                            )
                        ) {
                            Text(style.label)
                        }
                    }
                }
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = when (VisualizationStyle.entries[selectedStyleIndex]) {
                        VisualizationStyle.CANVAS ->
                            "Software-rendered Compose Canvas. Best compatibility."
                        VisualizationStyle.OPENGL ->
                            "Hardware-accelerated OpenGL ES 2.0. Better performance with many particles."
                        VisualizationStyle.MINIMAL ->
                            "Text-only mode. Lowest resource usage."
                    },
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            // === About ===
            SettingsCard(title = "About") {
                Text(
                    text = "In The Beginning is a cosmic evolution simulator that " +
                            "models the entire history of the universe from the Planck " +
                            "epoch through the emergence of life. It simulates quantum " +
                            "field theory, nuclear physics, chemistry, and evolutionary " +
                            "biology in a unified framework.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = "Version 1.0.0",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.6f)
                )
            }

            Spacer(modifier = Modifier.height(16.dp))
        }
    }
}

/**
 * Reusable settings card container with a title.
 */
@Composable
private fun SettingsCard(
    title: String,
    content: @Composable () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
        )
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = title,
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.primary,
                fontWeight = FontWeight.SemiBold
            )
            Spacer(modifier = Modifier.height(8.dp))
            content()
        }
    }
}
