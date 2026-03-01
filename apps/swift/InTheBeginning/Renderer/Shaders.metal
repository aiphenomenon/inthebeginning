// Shaders.metal
// InTheBeginning
//
// Metal shaders for rendering cosmic simulation entities.
// Vertex shader positions and sizes instanced points.
// Fragment shader draws circular points with soft alpha edges.

#include <metal_stdlib>
using namespace metal;

// MARK: - Uniform Structures

struct Uniforms {
    float4x4 projectionMatrix;
    float4x4 modelViewMatrix;
    float4   epochColor;
    float    pointSizeScale;
    float    aspectRatio;
    float    time;
    float    padding;
};

struct InstanceData {
    float3 position;
    float4 color;
    float  size;
    float  category;   // 0=particle, 1=atom, 2=molecule, 3=cell
    float2 padding;
};

// MARK: - Vertex Output

struct VertexOut {
    float4 position [[position]];
    float4 color;
    float  pointSize [[point_size]];
    float  category;
    float  time;
};

// MARK: - Vertex Shader

vertex VertexOut vertexShader(
    uint vertexID [[vertex_id]],
    constant Uniforms &uniforms [[buffer(0)]],
    constant InstanceData *instances [[buffer(1)]]
) {
    VertexOut out;

    InstanceData instance = instances[vertexID];

    // Transform position
    float4 worldPos = float4(instance.position, 1.0);
    float4 viewPos = uniforms.modelViewMatrix * worldPos;
    out.position = uniforms.projectionMatrix * viewPos;

    // Pass through color, modulated slightly by epoch ambient
    float4 baseColor = instance.color;
    float4 epochTint = uniforms.epochColor;
    out.color = float4(
        mix(baseColor.rgb, epochTint.rgb, 0.1),
        baseColor.a
    );

    // Point size with global scale
    out.pointSize = max(1.0, instance.size * uniforms.pointSizeScale);

    out.category = instance.category;
    out.time = uniforms.time;

    return out;
}

// MARK: - Fragment Shader

fragment float4 fragmentShader(
    VertexOut in [[stage_in]],
    float2 pointCoord [[point_coord]],
    constant Uniforms &uniforms [[buffer(0)]]
) {
    // Distance from center of point sprite (0..1 range)
    float2 centered = pointCoord - float2(0.5, 0.5);
    float dist = length(centered) * 2.0;

    // Discard pixels outside the circle
    if (dist > 1.0) {
        discard_fragment();
    }

    float4 color = in.color;

    // Category-based rendering
    if (in.category < 0.5) {
        // Particles: soft circular glow
        float alpha = 1.0 - smoothstep(0.0, 1.0, dist);
        // Add subtle pulsing for quantum particles
        float pulse = 0.85 + 0.15 * sin(in.time * 3.0 + in.position.x * 0.1);
        color.a *= alpha * pulse;
    }
    else if (in.category < 1.5) {
        // Atoms: solid core with soft edge
        float core = 1.0 - smoothstep(0.0, 0.6, dist);
        float edge = 1.0 - smoothstep(0.6, 1.0, dist);
        float alpha = max(core, edge * 0.4);
        color.a *= alpha;
    }
    else if (in.category < 2.5) {
        // Molecules: slightly elongated/structured look
        float alpha = 1.0 - smoothstep(0.0, 0.8, dist);
        // Add subtle internal structure
        float structure = 0.8 + 0.2 * sin(dist * 8.0);
        color.rgb *= structure;
        color.a *= alpha;
    }
    else {
        // Cells: membrane-like ring around solid core
        float core = 1.0 - smoothstep(0.0, 0.5, dist);
        float membrane = smoothstep(0.65, 0.75, dist) * (1.0 - smoothstep(0.85, 1.0, dist));
        float alpha = max(core * 0.8, membrane * 0.6);
        // Slightly shift membrane color
        if (membrane > core) {
            color.rgb = mix(color.rgb, float3(0.6, 0.9, 0.7), 0.3);
        }
        color.a *= alpha;
    }

    return color;
}
