// MetalRenderer.swift
// InTheBeginning
//
// Metal-based renderer for the cosmic simulation.
// Renders particles, atoms, molecules, and cells as instanced
// point sprites with epoch-based color palettes.

#if canImport(MetalKit)
import MetalKit
import simd

// MARK: - Uniform Buffer Layout

/// Uniforms passed to the GPU each frame.
struct SimulationUniforms {
    var projectionMatrix: simd_float4x4
    var modelViewMatrix: simd_float4x4
    var epochColor: SIMD4<Float>
    var pointSizeScale: Float
    var aspectRatio: Float
    var time: Float
    var padding: Float = 0
}

/// Per-instance data for each rendered entity.
struct InstanceData {
    var position: SIMD3<Float>
    var color: SIMD4<Float>
    var size: Float
    var category: Float   // 0=particle, 1=atom, 2=molecule, 3=cell
    var padding: SIMD2<Float> = .zero
}

// MARK: - Metal Renderer

final class MetalRenderer: NSObject, MTKViewDelegate {
    // MARK: - Metal State

    private let device: MTLDevice
    private let commandQueue: MTLCommandQueue
    private var pipelineState: MTLRenderPipelineState?
    private var uniformBuffer: MTLBuffer?
    private var instanceBuffer: MTLBuffer?
    private var instanceCount: Int = 0

    // MARK: - Configuration

    private var viewportSize: CGSize = .zero
    private var time: Float = 0.0
    private var currentEpochColor: SIMD4<Float> = SIMD4<Float>(1, 1, 1, 1)
    private var pointSizeScale: Float = 1.0

    // MARK: - Data

    private var pendingEntities: [RenderableEntity] = []
    private var currentEpoch: Epoch = .planck

    // MARK: - Constants

    private let maxInstances = 4096
    private let uniformsSize = MemoryLayout<SimulationUniforms>.stride
    private let instanceStride = MemoryLayout<InstanceData>.stride

    // MARK: - Init

    init?(mtkView: MTKView) {
        guard let device = mtkView.device ?? MTLCreateSystemDefaultDevice() else {
            return nil
        }

        self.device = device
        mtkView.device = device

        guard let queue = device.makeCommandQueue() else {
            return nil
        }
        self.commandQueue = queue

        super.init()

        mtkView.delegate = self
        mtkView.colorPixelFormat = .bgra8Unorm
        mtkView.clearColor = MTLClearColor(red: 0, green: 0, blue: 0, alpha: 1)
        mtkView.depthStencilPixelFormat = .invalid
        mtkView.preferredFramesPerSecond = 60

        setupPipeline(mtkView: mtkView)
        setupBuffers()
    }

    // MARK: - Pipeline Setup

    private func setupPipeline(mtkView: MTKView) {
        guard let library = device.makeDefaultLibrary() else {
            // Fallback: try loading from bundle
            let bundle = Bundle.main
            guard let libraryURL = bundle.url(forResource: "default", withExtension: "metallib"),
                  let library = try? device.makeLibrary(URL: libraryURL) else {
                print("MetalRenderer: Failed to load shader library")
                return
            }
            buildPipeline(library: library, mtkView: mtkView)
            return
        }
        buildPipeline(library: library, mtkView: mtkView)
    }

    private func buildPipeline(library: MTLLibrary, mtkView: MTKView) {
        let descriptor = MTLRenderPipelineDescriptor()
        descriptor.label = "Particle Pipeline"
        descriptor.vertexFunction = library.makeFunction(name: "vertexShader")
        descriptor.fragmentFunction = library.makeFunction(name: "fragmentShader")

        descriptor.colorAttachments[0].pixelFormat = mtkView.colorPixelFormat

        // Enable alpha blending for particles
        descriptor.colorAttachments[0].isBlendingEnabled = true
        descriptor.colorAttachments[0].sourceRGBBlendFactor = .sourceAlpha
        descriptor.colorAttachments[0].destinationRGBBlendFactor = .oneMinusSourceAlpha
        descriptor.colorAttachments[0].sourceAlphaBlendFactor = .one
        descriptor.colorAttachments[0].destinationAlphaBlendFactor = .oneMinusSourceAlpha

        do {
            pipelineState = try device.makeRenderPipelineState(descriptor: descriptor)
        } catch {
            print("MetalRenderer: Failed to create pipeline state: \(error)")
        }
    }

    // MARK: - Buffer Setup

    private func setupBuffers() {
        uniformBuffer = device.makeBuffer(
            length: uniformsSize,
            options: .storageModeShared
        )

        instanceBuffer = device.makeBuffer(
            length: instanceStride * maxInstances,
            options: .storageModeShared
        )
    }

    // MARK: - Update Data

    /// Update the entities to render on the next frame.
    func update(entities: [RenderableEntity], epoch: Epoch) {
        pendingEntities = entities
        currentEpoch = epoch
        currentEpochColor = epochAmbientColor(epoch)
    }

    /// Update the point size scaling.
    func setPointSizeScale(_ scale: Float) {
        pointSizeScale = scale
    }

    // MARK: - Instance Buffer Update

    private func updateInstanceBuffer() {
        guard let buffer = instanceBuffer else { return }

        let entities = pendingEntities
        instanceCount = min(entities.count, maxInstances)

        let ptr = buffer.contents().bindMemory(to: InstanceData.self, capacity: maxInstances)

        for i in 0..<instanceCount {
            let entity = entities[i]
            let categoryValue: Float
            switch entity.category {
            case .particle: categoryValue = 0.0
            case .atom:     categoryValue = 1.0
            case .molecule: categoryValue = 2.0
            case .cell:     categoryValue = 3.0
            }

            ptr[i] = InstanceData(
                position: SIMD3<Float>(
                    Float(entity.position.x),
                    Float(entity.position.y),
                    Float(entity.position.z)
                ),
                color: entity.color,
                size: entity.radius * pointSizeScale,
                category: categoryValue
            )
        }
    }

    // MARK: - Uniform Update

    private func updateUniforms() {
        guard let buffer = uniformBuffer else { return }

        let aspect = viewportSize.width > 0
            ? Float(viewportSize.width / viewportSize.height)
            : 1.0

        let projection = orthographicProjection(
            left: -100.0 * aspect,
            right: 100.0 * aspect,
            bottom: -100.0,
            top: 100.0,
            near: -100.0,
            far: 100.0
        )

        let modelView = simd_float4x4(1.0)  // Identity

        var uniforms = SimulationUniforms(
            projectionMatrix: projection,
            modelViewMatrix: modelView,
            epochColor: currentEpochColor,
            pointSizeScale: pointSizeScale,
            aspectRatio: aspect,
            time: time
        )

        memcpy(buffer.contents(), &uniforms, uniformsSize)
    }

    // MARK: - MTKViewDelegate

    func mtkView(_ view: MTKView, drawableSizeWillChange size: CGSize) {
        viewportSize = size
    }

    func draw(in view: MTKView) {
        time += 1.0 / 60.0

        updateInstanceBuffer()
        updateUniforms()

        guard instanceCount > 0,
              let pipeline = pipelineState,
              let descriptor = view.currentRenderPassDescriptor,
              let drawable = view.currentDrawable,
              let commandBuffer = commandQueue.makeCommandBuffer(),
              let encoder = commandBuffer.makeRenderCommandEncoder(descriptor: descriptor)
        else {
            return
        }

        // Set clear color based on epoch
        let bg = epochBackgroundColor(currentEpoch)
        descriptor.colorAttachments[0].clearColor = MTLClearColor(
            red: Double(bg.x), green: Double(bg.y),
            blue: Double(bg.z), alpha: 1.0
        )

        encoder.setRenderPipelineState(pipeline)
        encoder.setVertexBuffer(uniformBuffer, offset: 0, index: 0)
        encoder.setVertexBuffer(instanceBuffer, offset: 0, index: 1)
        encoder.setFragmentBuffer(uniformBuffer, offset: 0, index: 0)

        // Draw all instances as points
        encoder.drawPrimitives(
            type: .point,
            vertexStart: 0,
            vertexCount: instanceCount
        )

        encoder.endEncoding()
        commandBuffer.present(drawable)
        commandBuffer.commit()
    }

    // MARK: - Projection Matrix

    private func orthographicProjection(
        left: Float, right: Float,
        bottom: Float, top: Float,
        near: Float, far: Float
    ) -> simd_float4x4 {
        let sx = 2.0 / (right - left)
        let sy = 2.0 / (top - bottom)
        let sz = -2.0 / (far - near)
        let tx = -(right + left) / (right - left)
        let ty = -(top + bottom) / (top - bottom)
        let tz = -(far + near) / (far - near)

        return simd_float4x4(
            SIMD4<Float>(sx, 0,  0,  0),
            SIMD4<Float>(0,  sy, 0,  0),
            SIMD4<Float>(0,  0,  sz, 0),
            SIMD4<Float>(tx, ty, tz, 1)
        )
    }

    // MARK: - Epoch Colors

    private func epochAmbientColor(_ epoch: Epoch) -> SIMD4<Float> {
        switch epoch {
        case .planck:          return SIMD4<Float>(1.0, 1.0, 0.9, 1.0)
        case .inflation:       return SIMD4<Float>(1.0, 0.8, 0.4, 1.0)
        case .electroweak:     return SIMD4<Float>(0.9, 0.5, 0.2, 1.0)
        case .quark:           return SIMD4<Float>(0.8, 0.2, 0.2, 1.0)
        case .hadron:          return SIMD4<Float>(0.6, 0.1, 0.3, 1.0)
        case .nucleosynthesis: return SIMD4<Float>(0.4, 0.1, 0.5, 1.0)
        case .recombination:   return SIMD4<Float>(0.2, 0.1, 0.5, 1.0)
        case .starFormation:   return SIMD4<Float>(0.1, 0.2, 0.6, 1.0)
        case .solarSystem:     return SIMD4<Float>(0.2, 0.4, 0.7, 1.0)
        case .earth:           return SIMD4<Float>(0.1, 0.4, 0.6, 1.0)
        case .life:            return SIMD4<Float>(0.1, 0.5, 0.3, 1.0)
        case .dna:             return SIMD4<Float>(0.2, 0.6, 0.3, 1.0)
        case .present:         return SIMD4<Float>(0.2, 0.7, 0.5, 1.0)
        }
    }

    private func epochBackgroundColor(_ epoch: Epoch) -> SIMD3<Float> {
        switch epoch {
        case .planck:          return SIMD3<Float>(0.15, 0.12, 0.08)
        case .inflation:       return SIMD3<Float>(0.12, 0.06, 0.02)
        case .electroweak:     return SIMD3<Float>(0.08, 0.03, 0.05)
        case .quark:           return SIMD3<Float>(0.06, 0.01, 0.04)
        case .hadron:          return SIMD3<Float>(0.04, 0.00, 0.04)
        case .nucleosynthesis: return SIMD3<Float>(0.03, 0.00, 0.05)
        case .recombination:   return SIMD3<Float>(0.02, 0.01, 0.04)
        case .starFormation:   return SIMD3<Float>(0.01, 0.01, 0.03)
        case .solarSystem:     return SIMD3<Float>(0.02, 0.02, 0.04)
        case .earth:           return SIMD3<Float>(0.00, 0.03, 0.06)
        case .life:            return SIMD3<Float>(0.00, 0.03, 0.04)
        case .dna:             return SIMD3<Float>(0.01, 0.03, 0.04)
        case .present:         return SIMD3<Float>(0.01, 0.02, 0.05)
        }
    }
}

// MARK: - simd_float4x4 Identity Extension

extension simd_float4x4 {
    /// Creates an identity matrix.
    init(_ scalar: Float) {
        self.init(
            SIMD4<Float>(scalar, 0, 0, 0),
            SIMD4<Float>(0, scalar, 0, 0),
            SIMD4<Float>(0, 0, scalar, 0),
            SIMD4<Float>(0, 0, 0, scalar)
        )
    }
}
#endif
