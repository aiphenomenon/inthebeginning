// AudioEngine.swift
// InTheBeginning
//
// AVAudioEngine-based sonification of the cosmic simulation.
// Maps epochs to audio characteristics (pitch, timbre, volume),
// plays short tones on particle creation, and chord changes
// on epoch transitions.

#if canImport(AVFoundation)
import AVFoundation
import Foundation

// MARK: - Audio Engine

final class AudioEngine: ObservableObject {
    // MARK: - State

    @Published var isEnabled: Bool = false {
        didSet {
            if isEnabled {
                startEngine()
            } else {
                stopEngine()
            }
        }
    }

    // MARK: - AVAudioEngine

    private let engine = AVAudioEngine()
    private var toneNodes: [AVAudioSourceNode] = []
    private var mixerNode: AVAudioMixerNode?
    private var isRunning = false
    private var currentPhase: [Double] = [0, 0, 0, 0]

    // MARK: - Epoch Audio State

    private var currentEpoch: Epoch = .planck
    private var baseFrequency: Double = 220.0
    private var chordFrequencies: [Double] = [220.0, 277.18, 329.63, 440.0]
    private var amplitude: Double = 0.0
    private var targetAmplitude: Double = 0.15
    private var toneDecay: Double = 0.0

    // MARK: - Tone Queue

    private var pendingTones: [(frequency: Double, duration: Double)] = []
    private let toneQueueLock = NSLock()

    // MARK: - Sample Rate

    private var sampleRate: Double = 44100.0

    // MARK: - Init

    init() {
        setupAudioSession()
    }

    deinit {
        stopEngine()
    }

    // MARK: - Audio Session

    private func setupAudioSession() {
        #if os(iOS) || os(tvOS)
        let session = AVAudioSession.sharedInstance()
        do {
            try session.setCategory(.ambient, mode: .default)
            try session.setActive(true)
        } catch {
            print("AudioEngine: Failed to configure audio session: \(error)")
        }
        #endif
    }

    // MARK: - Engine Control

    private func startEngine() {
        guard !isRunning else { return }

        sampleRate = engine.outputNode.outputFormat(forBus: 0).sampleRate
        if sampleRate <= 0 { sampleRate = 44100.0 }

        let format = AVAudioFormat(
            standardFormatWithSampleRate: sampleRate,
            channels: 1
        )!

        // Create source nodes for chord tones (4 voices)
        let mixer = AVAudioMixerNode()
        engine.attach(mixer)
        self.mixerNode = mixer

        for i in 0..<4 {
            let voiceIndex = i
            let sourceNode = AVAudioSourceNode { [weak self] _, _, frameCount, audioBufferList -> OSStatus in
                guard let self = self else { return noErr }

                let ablPointer = UnsafeMutableAudioBufferListPointer(audioBufferList)
                let freq = self.chordFrequencies[voiceIndex]
                let amp = self.amplitude
                let sr = self.sampleRate
                let phaseIncrement = 2.0 * Double.pi * freq / sr

                for frame in 0..<Int(frameCount) {
                    self.currentPhase[voiceIndex] += phaseIncrement
                    if self.currentPhase[voiceIndex] > 2.0 * Double.pi {
                        self.currentPhase[voiceIndex] -= 2.0 * Double.pi
                    }

                    // Generate sine wave with slight harmonic content
                    let sine = sin(self.currentPhase[voiceIndex])
                    let harmonic = sin(self.currentPhase[voiceIndex] * 2.0) * 0.3
                    let sample = Float((sine + harmonic) * amp * 0.25)

                    for buffer in ablPointer {
                        let buf = UnsafeMutableBufferPointer<Float>(buffer)
                        buf[frame] = sample
                    }
                }

                return noErr
            }

            engine.attach(sourceNode)
            engine.connect(sourceNode, to: mixer, format: format)
            toneNodes.append(sourceNode)
        }

        engine.connect(mixer, to: engine.mainMixerNode, format: format)
        engine.mainMixerNode.outputVolume = 0.3

        do {
            try engine.start()
            isRunning = true
        } catch {
            print("AudioEngine: Failed to start engine: \(error)")
        }
    }

    private func stopEngine() {
        guard isRunning else { return }
        engine.stop()

        for node in toneNodes {
            engine.detach(node)
        }
        toneNodes.removeAll()

        if let mixer = mixerNode {
            engine.detach(mixer)
            mixerNode = nil
        }

        isRunning = false
        amplitude = 0.0
    }

    // MARK: - Epoch Transition

    /// Update audio for a new epoch. Triggers a chord change.
    func transitionToEpoch(_ epoch: Epoch) {
        guard isEnabled else { return }

        let previousEpoch = currentEpoch
        currentEpoch = epoch

        if epoch != previousEpoch {
            updateChordForEpoch(epoch)
            // Brief amplitude swell for transition
            targetAmplitude = 0.25
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { [weak self] in
                self?.targetAmplitude = 0.15
            }
        }
    }

    /// Update audio parameters each simulation frame.
    func update(particleCount: Int, temperature: Double, epoch: Epoch) {
        guard isEnabled && isRunning else { return }

        if epoch != currentEpoch {
            transitionToEpoch(epoch)
        }

        // Smoothly interpolate amplitude toward target
        amplitude += (targetAmplitude - amplitude) * 0.05

        // Modulate base frequency slightly based on temperature
        let tempFactor = 1.0 + log10(max(1.0, temperature)) * 0.01
        for i in 0..<chordFrequencies.count {
            let baseFreq = epochChordBase(epoch)[i]
            chordFrequencies[i] = baseFreq * tempFactor
        }
    }

    /// Play a short tone for particle creation events.
    func playParticleTone(frequency: Double = 880.0) {
        guard isEnabled && isRunning else { return }

        // Briefly boost amplitude for event feedback
        let prevTarget = targetAmplitude
        targetAmplitude = min(0.35, targetAmplitude + 0.1)
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) { [weak self] in
            self?.targetAmplitude = prevTarget
        }
    }

    // MARK: - Epoch Chord Mapping

    private func updateChordForEpoch(_ epoch: Epoch) {
        chordFrequencies = epochChordBase(epoch)
    }

    /// Return the four chord frequencies for each epoch, mapping
    /// cosmic evolution to a musical journey.
    private func epochChordBase(_ epoch: Epoch) -> [Double] {
        switch epoch {
        case .planck:
            // Dense, low cluster (chaos)
            return [55.0, 58.27, 61.74, 110.0]
        case .inflation:
            // Rising sweep
            return [82.41, 110.0, 146.83, 164.81]
        case .electroweak:
            // Open fifths (symmetry breaking)
            return [110.0, 164.81, 220.0, 329.63]
        case .quark:
            // Tritone tension
            return [146.83, 207.65, 293.66, 415.30]
        case .hadron:
            // Resolving to minor
            return [164.81, 196.0, 246.94, 329.63]
        case .nucleosynthesis:
            // Major chord building
            return [196.0, 246.94, 293.66, 392.0]
        case .recombination:
            // Suspended, spacious
            return [220.0, 293.66, 329.63, 440.0]
        case .starFormation:
            // Bright major
            return [261.63, 329.63, 392.0, 523.25]
        case .solarSystem:
            // Rich, warm
            return [293.66, 369.99, 440.0, 587.33]
        case .earth:
            // Lydian brightness
            return [329.63, 415.30, 493.88, 659.25]
        case .life:
            // Gentle, organic
            return [349.23, 440.0, 523.25, 698.46]
        case .dna:
            // Complex harmony
            return [392.0, 493.88, 587.33, 783.99]
        case .present:
            // Full, resolved major
            return [440.0, 554.37, 659.25, 880.0]
        }
    }
}
#endif
