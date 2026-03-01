// MetalRenderer.swift
// InTheBeginning – macOS Screensaver
//
// Metal-based renderer for the cosmic evolution screensaver.
// Draws particles, atoms, molecules, and cells as instanced point sprites
// with glow effects, epoch-based color palettes, and a progress bar HUD.

import Metal
import MetalKit
import simd

// MARK: - GPU Structures (must match Shaders.metal)

/// Uniform buffer passed to every draw call.
struct Uniforms {
    var projection: simd_float4x4
    var epochColor: SIMD4<Float>
    var time: Float
    var fadeAlpha: Float
    var viewportWidth: Float
    var viewportHeight: Float
}

/// Per-instance data for each particle point sprite.
struct ParticleInstance {
    var position: SIMD2<Float>
    var size: Float
    var _pad0: Float
    var color: SIMD4<Float>
}

/// Vertex for the progress bar / HUD quads.
struct BarVertex {
    var position: SIMD2<Float>
    var color: SIMD4<Float>
}

// MARK: - MetalRenderer

final class MetalRenderer {

    // MARK: Metal Objects

    private let device: MTLDevice
    private let commandQueue: MTLCommandQueue
    private let particlePipeline: MTLRenderPipelineState
    private let glowPipeline: MTLRenderPipelineState
    private let barPipeline: MTLRenderPipelineState

    // MARK: Buffers

    private var uniformBuffer: MTLBuffer?
    private var instanceBuffer: MTLBuffer?
    private var barVertexBuffer: MTLBuffer?

    // MARK: State

    private var startTime: CFTimeInterval = CACurrentMediaTime()
    private var previousEpoch: Epoch = .planck
    private var fadeAlpha: Float = 1.0
    private var fadeTarget: Float = 1.0
    private let maxInstances = kMaxRenderableParticles + kMaxRenderableAtoms + kMaxRenderableAtoms + kMaxRenderableCells
    private let maxBarVertices = 64

    // MARK: Initialization

    init(device: MTLDevice, pixelFormat: MTLPixelFormat) throws {
        self.device = device

        guard let queue = device.makeCommandQueue() else {
            throw RendererError.commandQueueCreationFailed
        }
        self.commandQueue = queue

        // Load shader library from the bundle containing this class
        let bundle = Bundle(for: MetalRenderer.self)
        let library: MTLLibrary
        if let defaultLib = try? device.makeDefaultLibrary(bundle: bundle) {
            library = defaultLib
        } else if let defaultLib = device.makeDefaultLibrary() {
            library = defaultLib
        } else {
            throw RendererError.shaderLibraryNotFound
        }

        // Build pipeline states
        self.particlePipeline = try MetalRenderer.buildPointPipeline(
            device: device, library: library, pixelFormat: pixelFormat,
            vertexFunction: "particleVertex", fragmentFunction: "particleFragment"
        )
        self.glowPipeline = try MetalRenderer.buildPointPipeline(
            device: device, library: library, pixelFormat: pixelFormat,
            vertexFunction: "glowVertex", fragmentFunction: "particleFragment"
        )
        self.barPipeline = try MetalRenderer.buildBarPipeline(
            device: device, library: library, pixelFormat: pixelFormat
        )

        // Pre-allocate buffers
        let instanceSize = MemoryLayout<ParticleInstance>.stride * maxInstances
        self.instanceBuffer = device.makeBuffer(length: instanceSize, options: .storageModeShared)
        self.uniformBuffer = device.makeBuffer(length: MemoryLayout<Uniforms>.stride, options: .storageModeShared)
        let barSize = MemoryLayout<BarVertex>.stride * maxBarVertices
        self.barVertexBuffer = device.makeBuffer(length: barSize, options: .storageModeShared)
    }

    // MARK: Pipeline Builders

    private static func buildPointPipeline(
        device: MTLDevice, library: MTLLibrary, pixelFormat: MTLPixelFormat,
        vertexFunction: String, fragmentFunction: String
    ) throws -> MTLRenderPipelineState {
        guard let vertFn = library.makeFunction(name: vertexFunction),
              let fragFn = library.makeFunction(name: fragmentFunction) else {
            throw RendererError.shaderFunctionNotFound
        }

        let desc = MTLRenderPipelineDescriptor()
        desc.vertexFunction = vertFn
        desc.fragmentFunction = fragFn
        desc.colorAttachments[0].pixelFormat = pixelFormat

        // Alpha blending: src_alpha + (1 - src_alpha) * dst
        desc.colorAttachments[0].isBlendingEnabled = true
        desc.colorAttachments[0].sourceRGBBlendFactor = .sourceAlpha
        desc.colorAttachments[0].destinationRGBBlendFactor = .oneMinusSourceAlpha
        desc.colorAttachments[0].sourceAlphaBlendFactor = .one
        desc.colorAttachments[0].destinationAlphaBlendFactor = .oneMinusSourceAlpha

        return try device.makeRenderPipelineState(descriptor: desc)
    }

    private static func buildBarPipeline(
        device: MTLDevice, library: MTLLibrary, pixelFormat: MTLPixelFormat
    ) throws -> MTLRenderPipelineState {
        guard let vertFn = library.makeFunction(name: "barVertex"),
              let fragFn = library.makeFunction(name: "barFragment") else {
            throw RendererError.shaderFunctionNotFound
        }

        let desc = MTLRenderPipelineDescriptor()
        desc.vertexFunction = vertFn
        desc.fragmentFunction = fragFn
        desc.colorAttachments[0].pixelFormat = pixelFormat

        desc.colorAttachments[0].isBlendingEnabled = true
        desc.colorAttachments[0].sourceRGBBlendFactor = .sourceAlpha
        desc.colorAttachments[0].destinationRGBBlendFactor = .oneMinusSourceAlpha
        desc.colorAttachments[0].sourceAlphaBlendFactor = .one
        desc.colorAttachments[0].destinationAlphaBlendFactor = .oneMinusSourceAlpha

        return try device.makeRenderPipelineState(descriptor: desc)
    }

    // MARK: Render

    /// Render a simulation snapshot into the given MTKView.
    func render(snapshot: UniverseSnapshot, in view: MTKView) {
        guard let drawable = view.currentDrawable,
              let passDesc = view.currentRenderPassDescriptor else { return }

        let width = Float(view.drawableSize.width)
        let height = Float(view.drawableSize.height)

        // Handle epoch transitions with fade
        updateFade(epoch: snapshot.epoch)

        // Build uniforms
        let proj = orthographicProjection(width: width, height: height)
        let epochCol = epochPrimaryColor(snapshot.epoch)
        let elapsed = Float(CACurrentMediaTime() - startTime)

        var uniforms = Uniforms(
            projection: proj,
            epochColor: epochCol,
            time: elapsed,
            fadeAlpha: fadeAlpha,
            viewportWidth: width,
            viewportHeight: height
        )

        uniformBuffer?.contents().copyMemory(
            from: &uniforms,
            byteCount: MemoryLayout<Uniforms>.stride
        )

        // Build instance data from snapshot entities
        let instanceCount = buildInstances(snapshot: snapshot, width: width, height: height)

        // Build progress bar vertices
        let barVertexCount = buildProgressBar(
            snapshot: snapshot, width: width, height: height
        )

        // Encode commands
        guard let cmdBuf = commandQueue.makeCommandBuffer(),
              let encoder = cmdBuf.makeRenderCommandEncoder(descriptor: passDesc) else { return }

        // Pass 1: Glow layer (larger, dimmer points behind core)
        if instanceCount > 0 {
            encoder.setRenderPipelineState(glowPipeline)
            encoder.setVertexBuffer(uniformBuffer, offset: 0, index: 0)
            encoder.setVertexBuffer(instanceBuffer, offset: 0, index: 1)
            encoder.drawPrimitives(
                type: .point,
                vertexStart: 0,
                vertexCount: 1,
                instanceCount: instanceCount
            )
        }

        // Pass 2: Core particles
        if instanceCount > 0 {
            encoder.setRenderPipelineState(particlePipeline)
            encoder.setVertexBuffer(uniformBuffer, offset: 0, index: 0)
            encoder.setVertexBuffer(instanceBuffer, offset: 0, index: 1)
            encoder.drawPrimitives(
                type: .point,
                vertexStart: 0,
                vertexCount: 1,
                instanceCount: instanceCount
            )
        }

        // Pass 3: Progress bar and HUD elements
        if barVertexCount > 0 {
            encoder.setRenderPipelineState(barPipeline)
            encoder.setVertexBuffer(uniformBuffer, offset: 0, index: 0)
            encoder.setVertexBuffer(barVertexBuffer, offset: 0, index: 1)
            encoder.drawPrimitives(
                type: .triangle,
                vertexStart: 0,
                vertexCount: barVertexCount
            )
        }

        encoder.endEncoding()
        cmdBuf.present(drawable)
        cmdBuf.commit()
    }

    // MARK: Instance Building

    /// Fill the instance buffer from snapshot entities.
    /// Returns the number of instances written.
    private func buildInstances(snapshot: UniverseSnapshot, width: Float, height: Float) -> Int {
        guard let ptr = instanceBuffer?.contents().bindMemory(
            to: ParticleInstance.self, capacity: maxInstances
        ) else { return 0 }

        let worldScale = min(width, height) / (Float(kWorldRadius) * 2.0)
        let cx = width / 2.0
        let cy = height / 2.0

        var count = 0

        for entity in snapshot.entities {
            guard count < maxInstances else { break }

            let screenX = cx + Float(entity.position.x) * worldScale
            let screenY = cy + Float(entity.position.y) * worldScale

            // Cull off-screen
            guard screenX > -20 && screenX < width + 20 &&
                  screenY > -20 && screenY < height + 20 else { continue }

            let rawSize = Float(entity.size) * worldScale * 0.1
            let drawSize = max(1.5, min(rawSize, 12.0))

            ptr[count] = ParticleInstance(
                position: SIMD2<Float>(screenX, screenY),
                size: drawSize,
                _pad0: 0,
                color: SIMD4<Float>(
                    Float(entity.red),
                    Float(entity.green),
                    Float(entity.blue),
                    Float(entity.alpha)
                )
            )
            count += 1
        }

        return count
    }

    // MARK: Progress Bar

    /// Build triangles for the epoch progress bar at the top of the screen.
    /// Returns the number of vertices written.
    private func buildProgressBar(snapshot: UniverseSnapshot, width: Float, height: Float) -> Int {
        guard let ptr = barVertexBuffer?.contents().bindMemory(
            to: BarVertex.self, capacity: maxBarVertices
        ) else { return 0 }

        let barHeight: Float = 4.0
        let barY = height - barHeight
        let margin: Float = 40.0
        let barWidth = width - margin * 2.0

        // Compute progress within the full timeline (planck..present)
        let maxTick = Float(Epoch.present.rawValue)
        let progress = min(1.0, Float(snapshot.tick) / maxTick)

        let filledWidth = barWidth * progress

        // Background bar (dark, semi-transparent)
        let bgColor = SIMD4<Float>(0.2, 0.2, 0.2, 0.4)
        let fillColor = epochPrimaryColor(snapshot.epoch) * SIMD4<Float>(1, 1, 1, 0.7)

        var count = 0

        // Background quad (2 triangles = 6 vertices)
        let bgLeft = margin
        let bgRight = margin + barWidth

        ptr[count] = BarVertex(position: SIMD2(bgLeft, barY), color: bgColor); count += 1
        ptr[count] = BarVertex(position: SIMD2(bgRight, barY), color: bgColor); count += 1
        ptr[count] = BarVertex(position: SIMD2(bgLeft, barY + barHeight), color: bgColor); count += 1

        ptr[count] = BarVertex(position: SIMD2(bgRight, barY), color: bgColor); count += 1
        ptr[count] = BarVertex(position: SIMD2(bgRight, barY + barHeight), color: bgColor); count += 1
        ptr[count] = BarVertex(position: SIMD2(bgLeft, barY + barHeight), color: bgColor); count += 1

        // Filled portion (2 triangles = 6 vertices)
        if filledWidth > 0.5 {
            let fRight = margin + filledWidth

            ptr[count] = BarVertex(position: SIMD2(bgLeft, barY), color: fillColor); count += 1
            ptr[count] = BarVertex(position: SIMD2(fRight, barY), color: fillColor); count += 1
            ptr[count] = BarVertex(position: SIMD2(bgLeft, barY + barHeight), color: fillColor); count += 1

            ptr[count] = BarVertex(position: SIMD2(fRight, barY), color: fillColor); count += 1
            ptr[count] = BarVertex(position: SIMD2(fRight, barY + barHeight), color: fillColor); count += 1
            ptr[count] = BarVertex(position: SIMD2(bgLeft, barY + barHeight), color: fillColor); count += 1
        }

        // Epoch boundary markers
        let allEpochs = Epoch.allCases
        for epoch in allEpochs {
            guard count + 6 <= maxBarVertices else { break }
            let t = Float(epoch.rawValue) / maxTick
            let x = margin + barWidth * t
            let markerWidth: Float = 1.0
            let markerColor = SIMD4<Float>(0.6, 0.6, 0.6, 0.3)

            ptr[count] = BarVertex(position: SIMD2(x, barY - 1), color: markerColor); count += 1
            ptr[count] = BarVertex(position: SIMD2(x + markerWidth, barY - 1), color: markerColor); count += 1
            ptr[count] = BarVertex(position: SIMD2(x, barY + barHeight + 1), color: markerColor); count += 1

            ptr[count] = BarVertex(position: SIMD2(x + markerWidth, barY - 1), color: markerColor); count += 1
            ptr[count] = BarVertex(position: SIMD2(x + markerWidth, barY + barHeight + 1), color: markerColor); count += 1
            ptr[count] = BarVertex(position: SIMD2(x, barY + barHeight + 1), color: markerColor); count += 1
        }

        return count
    }

    // MARK: Epoch Fade Transitions

    private func updateFade(epoch: Epoch) {
        if epoch != previousEpoch {
            // Start a fade-in when entering a new epoch
            fadeAlpha = 0.0
            fadeTarget = 1.0
            previousEpoch = epoch
        }

        // Smooth ramp toward target
        if fadeAlpha < fadeTarget {
            fadeAlpha = min(fadeTarget, fadeAlpha + 0.02)
        }
    }

    // MARK: Epoch Color Palette

    /// Primary color for each epoch (used for progress bar fill and tinting).
    /// Matches the C screensaver palette: Planck=violet, Inflation=gold, etc.
    private func epochPrimaryColor(_ epoch: Epoch) -> SIMD4<Float> {
        switch epoch {
        case .planck:          return SIMD4(0.8,  0.6,  1.0,  1.0)  // Violet
        case .inflation:       return SIMD4(1.0,  0.84, 0.0,  1.0)  // Gold
        case .electroweak:     return SIMD4(0.6,  0.3,  0.9,  1.0)  // Deep violet
        case .quark:           return SIMD4(1.0,  0.2,  0.2,  1.0)  // Red plasma
        case .hadron:          return SIMD4(0.9,  0.5,  0.2,  1.0)  // Orange
        case .nucleosynthesis: return SIMD4(0.9,  0.7,  0.3,  1.0)  // Warm yellow
        case .recombination:   return SIMD4(1.0,  0.95, 0.8,  1.0)  // Pale cream
        case .starFormation:   return SIMD4(0.3,  0.5,  1.0,  1.0)  // Blue
        case .solarSystem:     return SIMD4(0.8,  0.65, 0.2,  1.0)  // Nebula gold
        case .earth:           return SIMD4(0.2,  0.5,  0.8,  1.0)  // Ocean blue
        case .life:            return SIMD4(0.1,  0.8,  0.3,  1.0)  // Green
        case .dna:             return SIMD4(0.2,  0.9,  0.4,  1.0)  // Bright green
        case .present:         return SIMD4(0.3,  0.7,  0.9,  1.0)  // Cyan-blue
        }
    }

    // MARK: Projection

    /// Orthographic projection matrix mapping screen pixels to NDC.
    private func orthographicProjection(width: Float, height: Float) -> simd_float4x4 {
        // Map (0..width, 0..height) to (-1..1, -1..1)
        let sx: Float = 2.0 / width
        let sy: Float = 2.0 / height

        return simd_float4x4(columns: (
            SIMD4<Float>( sx,   0,    0,   0),
            SIMD4<Float>( 0,    sy,   0,   0),
            SIMD4<Float>( 0,    0,    1,   0),
            SIMD4<Float>(-1,   -1,    0,   1)
        ))
    }

    // MARK: Errors

    enum RendererError: Error {
        case commandQueueCreationFailed
        case shaderLibraryNotFound
        case shaderFunctionNotFound
    }
}
