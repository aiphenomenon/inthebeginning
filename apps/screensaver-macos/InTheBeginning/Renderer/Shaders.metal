// Shaders.metal
// InTheBeginning – macOS Screensaver
//
// Metal shader functions for particle rendering.
// Vertex shader positions and sizes instanced particles;
// fragment shader draws circular points with alpha blending.

#include <metal_stdlib>
using namespace metal;

// MARK: - Uniforms

struct Uniforms {
    float4x4 projection;      // Orthographic projection matrix
    float4   epochColor;       // Current epoch tint (r, g, b, a)
    float    time;             // Elapsed time for animation
    float    fadeAlpha;        // Transition fade between epochs (0..1)
    float    viewportWidth;    // Screen width in points
    float    viewportHeight;   // Screen height in points
};

// MARK: - Per-Instance Data

struct ParticleInstance {
    float2 position;           // Screen-space position
    float  size;               // Point size in pixels
    float  _pad0;              // Padding for alignment
    float4 color;              // RGBA color
};

// MARK: - Vertex Output

struct VertexOut {
    float4 position [[position]];
    float  pointSize [[point_size]];
    float4 color;
    float  glowFactor;        // 0 = glow pass, 1 = core pass
};

// MARK: - Progress Bar Instance

struct BarVertex {
    float2 position;
    float4 color;
};

// MARK: - Bar Vertex Output

struct BarVertexOut {
    float4 position [[position]];
    float4 color;
};

// MARK: - Vertex Functions

/// Particle vertex shader: positions instanced point sprites.
vertex VertexOut particleVertex(
    uint vertexID       [[vertex_id]],
    uint instanceID     [[instance_id]],
    constant Uniforms &uniforms [[buffer(0)]],
    constant ParticleInstance *instances [[buffer(1)]]
) {
    ParticleInstance inst = instances[instanceID];

    float4 pos = uniforms.projection * float4(inst.position, 0.0, 1.0);

    VertexOut out;
    out.position = pos;
    out.pointSize = inst.size;
    out.color = inst.color;
    out.color.a *= uniforms.fadeAlpha;
    out.glowFactor = 1.0;
    return out;
}

/// Glow vertex shader: renders the same particles as larger, dimmer point sprites.
vertex VertexOut glowVertex(
    uint vertexID       [[vertex_id]],
    uint instanceID     [[instance_id]],
    constant Uniforms &uniforms [[buffer(0)]],
    constant ParticleInstance *instances [[buffer(1)]]
) {
    ParticleInstance inst = instances[instanceID];

    float4 pos = uniforms.projection * float4(inst.position, 0.0, 1.0);

    VertexOut out;
    out.position = pos;
    out.pointSize = inst.size * 2.5;
    out.color = inst.color;
    out.color.a *= uniforms.fadeAlpha * 0.2;
    out.glowFactor = 0.0;
    return out;
}

/// Simple vertex shader for the progress bar and HUD quads.
vertex BarVertexOut barVertex(
    uint vertexID [[vertex_id]],
    constant Uniforms &uniforms [[buffer(0)]],
    constant BarVertex *vertices [[buffer(1)]]
) {
    BarVertex v = vertices[vertexID];

    BarVertexOut out;
    out.position = uniforms.projection * float4(v.position, 0.0, 1.0);
    out.color = v.color;
    return out;
}

// MARK: - Fragment Functions

/// Particle fragment shader: draws circular point sprites with soft edges.
fragment float4 particleFragment(
    VertexOut in [[stage_in]],
    float2 pointCoord [[point_coord]]
) {
    // Distance from center of point sprite (0..1 range, center = 0.5,0.5)
    float2 centered = pointCoord - float2(0.5);
    float dist = length(centered) * 2.0;   // 0 at center, 1 at edge

    // Discard pixels outside the circle
    if (dist > 1.0) {
        discard_fragment();
    }

    // Smooth falloff for both core and glow
    float alpha;
    if (in.glowFactor > 0.5) {
        // Core: sharp circle with slight soft edge
        alpha = 1.0 - smoothstep(0.7, 1.0, dist);
    } else {
        // Glow: gaussian-like falloff
        alpha = exp(-3.0 * dist * dist);
    }

    float4 color = in.color;
    color.a *= alpha;
    return color;
}

/// Flat fragment shader for the progress bar quads.
fragment float4 barFragment(
    BarVertexOut in [[stage_in]]
) {
    return in.color;
}
