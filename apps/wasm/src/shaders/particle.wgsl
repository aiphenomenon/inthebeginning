// ============================================================================
// Particle shader for "In The Beginning" cosmic simulator
//
// Renders particles, atoms, molecules, and cells as circular billboard
// points with per-instance colour and size.
// ============================================================================

// ---------- uniforms --------------------------------------------------------

struct Uniforms {
    projection: mat4x4<f32>,  // orthographic or perspective projection
    bg_color:   vec4<f32>,    // epoch background tint (unused in shader; kept for alignment)
};

@group(0) @binding(0)
var<uniform> u: Uniforms;

// ---------- vertex I/O ------------------------------------------------------

struct VertexInput {
    // Per-vertex (quad corners)
    @location(0) quad_pos: vec2<f32>,   // -1..1 for each corner

    // Per-instance
    @location(1) inst_pos:   vec3<f32>, // world position
    @location(2) inst_color: vec4<f32>, // RGBA colour
    @location(3) inst_size:  f32,       // point radius in pixels
};

struct VertexOutput {
    @builtin(position) clip_pos: vec4<f32>,
    @location(0) color:         vec4<f32>,
    @location(1) uv:            vec2<f32>,  // quad UV for circle mask
};

// ---------- vertex shader ---------------------------------------------------

@vertex
fn vs_main(in: VertexInput) -> VertexOutput {
    var out: VertexOutput;

    // Project world position to clip space
    let center = u.projection * vec4<f32>(in.inst_pos, 1.0);

    // Offset by quad corner scaled by point size (in clip-space pixels).
    // Divide inst_size by a reference resolution half-width to keep
    // sizes roughly consistent.  400.0 is a reasonable default for an
    // 800-px-wide viewport.
    let pixel_scale = in.inst_size / 400.0;
    let offset = vec2<f32>(in.quad_pos.x * pixel_scale,
                           in.quad_pos.y * pixel_scale);

    out.clip_pos = vec4<f32>(center.xy + offset * center.w, center.z, center.w);
    out.color    = in.inst_color;
    out.uv       = in.quad_pos;  // -1..1

    return out;
}

// ---------- fragment shader -------------------------------------------------

@fragment
fn fs_main(in: VertexOutput) -> @location(0) vec4<f32> {
    // Circular point: discard outside unit circle
    let dist = length(in.uv);
    if dist > 1.0 {
        discard;
    }

    // Soft edge with smooth alpha falloff
    let edge = 1.0 - smoothstep(0.7, 1.0, dist);

    // Slight glow in the centre
    let glow = exp(-dist * dist * 3.0) * 0.35;

    var col = in.color;
    col = vec4<f32>(col.rgb + glow, col.a * edge);

    return col;
}
