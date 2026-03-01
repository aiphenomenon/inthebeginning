package com.inthebeginning

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.animation.AnimatedContentTransitionScope
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.compose.viewModel
import com.inthebeginning.simulator.SimulationState
import com.inthebeginning.simulator.Universe
import com.inthebeginning.ui.SettingsScreen
import com.inthebeginning.ui.SimulationScreen
import com.inthebeginning.ui.VisualizationStyle
import com.inthebeginning.ui.theme.InTheBeginningTheme
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch

/**
 * ViewModel managing the Universe simulation lifecycle.
 *
 * Runs the simulation loop on [Dispatchers.Default] to keep the UI responsive,
 * and exposes the state as a [StateFlow] for Compose to collect.
 */
class SimulationViewModel : ViewModel() {

    private val universe = Universe()

    /** Observable simulation state. */
    val state: StateFlow<SimulationState> = universe.state

    /** The background job driving the simulation loop. */
    private var simulationJob: Job? = null

    /** Whether the simulation loop is actively running. */
    val isRunning: Boolean get() = simulationJob?.isActive == true

    init {
        universe.reset()
    }

    /**
     * Toggle between running and paused states.
     */
    fun togglePlayPause() {
        if (isRunning) {
            pause()
        } else {
            play()
        }
    }

    /**
     * Start or resume the simulation loop.
     */
    fun play() {
        if (universe.completed) return
        if (isRunning) return

        simulationJob = viewModelScope.launch(Dispatchers.Default) {
            while (isActive && !universe.completed) {
                universe.step()
                // Small delay to yield to the UI thread and control frame rate
                delay(16L) // ~60 fps state updates
            }
        }
    }

    /**
     * Pause the simulation loop.
     */
    fun pause() {
        simulationJob?.cancel()
        simulationJob = null
        universe.pause()
    }

    /**
     * Reset the simulation to initial state.
     */
    fun reset() {
        pause()
        universe.reset()
    }

    /**
     * Update the simulation speed (ticks advanced per step).
     */
    fun setSpeed(ticksPerStep: Int) {
        universe.ticksPerStep = ticksPerStep.coerceIn(10, 2000)
    }

    override fun onCleared() {
        super.onCleared()
        simulationJob?.cancel()
    }
}

/**
 * Main Activity hosting the Compose UI.
 */
class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        setContent {
            InTheBeginningTheme(darkTheme = true) {
                InTheBeginningApp()
            }
        }
    }
}

/**
 * Navigation destinations.
 */
private enum class Screen {
    SIMULATION,
    SETTINGS
}

/**
 * Root composable for the application.
 * Manages navigation between the simulation and settings screens.
 */
@Composable
fun InTheBeginningApp(
    viewModel: SimulationViewModel = viewModel()
) {
    val state by viewModel.state.collectAsState()

    var currentScreen by remember { mutableStateOf(Screen.SIMULATION) }
    var seed by remember { mutableStateOf("42") }
    var speed by remember { mutableIntStateOf(100) }
    var vizStyle by remember { mutableStateOf(VisualizationStyle.CANVAS) }

    when (currentScreen) {
        Screen.SIMULATION -> {
            SimulationScreen(
                state = state,
                onPlayPause = { viewModel.togglePlayPause() },
                onReset = { viewModel.reset() },
                onSpeedChange = { ticks ->
                    speed = ticks
                    viewModel.setSpeed(ticks)
                },
                onSettingsClick = {
                    currentScreen = Screen.SETTINGS
                }
            )
        }
        Screen.SETTINGS -> {
            SettingsScreen(
                currentSeed = seed,
                currentSpeed = speed,
                currentStyle = vizStyle,
                onSeedChange = { newSeed -> seed = newSeed },
                onSpeedChange = { ticks ->
                    speed = ticks
                    viewModel.setSpeed(ticks)
                },
                onStyleChange = { style -> vizStyle = style },
                onBack = { currentScreen = Screen.SIMULATION }
            )
        }
    }
}
