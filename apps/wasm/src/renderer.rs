//! WebGPU renderer for the cosmic simulator.
//!
//! Draws particles, atoms, molecules, and cells as instanced billboard
//! quads with circular fragment masking and epoch-derived colours.

use bytemuck::{Pod, Zeroable};
use wgpu::util::DeviceExt;

use crate::constants::epoch_background_color;
use crate::universe::Universe;

// ---------------------------------------------------------------------------
// GPU-side types
// ---------------------------------------------------------------------------

/// Uniform block uploaded once per frame.
#[repr(C)]
#[derive(Copy, Clone, Pod, Zeroable)]
pub struct Uniforms {
    pub projection: [[f32; 4]; 4],
    pub bg_color: [f32; 4],
}

/// Per-instance data for a single renderable object.
#[repr(C)]
#[derive(Copy, Clone, Pod, Zeroable)]
pub struct InstanceData {
    pub position: [f32; 3],
    pub _pad0: f32,
    pub color: [f32; 4],
    pub size: f32,
    pub _pad1: [f32; 3],
}

// ---------------------------------------------------------------------------
// Renderer
// ---------------------------------------------------------------------------

pub struct Renderer {
    pub device: wgpu::Device,
    pub queue: wgpu::Queue,
    pub surface: wgpu::Surface<'static>,
    pub surface_config: wgpu::SurfaceConfiguration,
    pub pipeline: wgpu::RenderPipeline,
    pub uniform_buffer: wgpu::Buffer,
    pub uniform_bind_group: wgpu::BindGroup,
    pub quad_vertex_buffer: wgpu::Buffer,
    pub instance_buffer: wgpu::Buffer,
    pub max_instances: usize,
}

impl Renderer {
    /// Create the renderer from a pre-acquired adapter, device, and surface.
    pub fn new(
        adapter: &wgpu::Adapter,
        device: wgpu::Device,
        queue: wgpu::Queue,
        surface: wgpu::Surface<'static>,
        width: u32,
        height: u32,
    ) -> Self {
        // -- surface configuration ------------------------------------------
        let surface_caps = surface.get_capabilities(adapter);
        let format = surface_caps
            .formats
            .iter()
            .copied()
            .find(|f| f.is_srgb())
            .unwrap_or(surface_caps.formats[0]);
        let surface_config = wgpu::SurfaceConfiguration {
            usage: wgpu::TextureUsages::RENDER_ATTACHMENT,
            format,
            width,
            height,
            present_mode: wgpu::PresentMode::Fifo,
            desired_maximum_frame_latency: 2,
            alpha_mode: wgpu::CompositeAlphaMode::Opaque,
            view_formats: vec![],
        };
        surface.configure(&device, &surface_config);

        // -- shader ---------------------------------------------------------
        let shader_src = include_str!("shaders/particle.wgsl");
        let shader = device.create_shader_module(wgpu::ShaderModuleDescriptor {
            label: Some("particle_shader"),
            source: wgpu::ShaderSource::Wgsl(shader_src.into()),
        });

        // -- uniform buffer + bind group ------------------------------------
        let uniforms = Uniforms {
            projection: ortho_matrix(30.0, width as f32 / height as f32),
            bg_color: [0.0, 0.0, 0.02, 1.0],
        };
        let uniform_buffer = device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
            label: Some("uniform_buffer"),
            contents: bytemuck::cast_slice(&[uniforms]),
            usage: wgpu::BufferUsages::UNIFORM | wgpu::BufferUsages::COPY_DST,
        });

        let bind_group_layout = device.create_bind_group_layout(&wgpu::BindGroupLayoutDescriptor {
            label: Some("uniform_bgl"),
            entries: &[wgpu::BindGroupLayoutEntry {
                binding: 0,
                visibility: wgpu::ShaderStages::VERTEX | wgpu::ShaderStages::FRAGMENT,
                ty: wgpu::BindingType::Buffer {
                    ty: wgpu::BufferBindingType::Uniform,
                    has_dynamic_offset: false,
                    min_binding_size: None,
                },
                count: None,
            }],
        });
        let uniform_bind_group = device.create_bind_group(&wgpu::BindGroupDescriptor {
            label: Some("uniform_bg"),
            layout: &bind_group_layout,
            entries: &[wgpu::BindGroupEntry {
                binding: 0,
                resource: uniform_buffer.as_entire_binding(),
            }],
        });

        let pipeline_layout = device.create_pipeline_layout(&wgpu::PipelineLayoutDescriptor {
            label: Some("pipeline_layout"),
            bind_group_layouts: &[&bind_group_layout],
            immediate_size: 0,
        });

        // -- quad vertices (triangle-strip, 4 corners) ----------------------
        let quad_verts: [[f32; 2]; 4] = [
            [-1.0, -1.0],
            [ 1.0, -1.0],
            [-1.0,  1.0],
            [ 1.0,  1.0],
        ];
        let quad_vertex_buffer = device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
            label: Some("quad_vb"),
            contents: bytemuck::cast_slice(&quad_verts),
            usage: wgpu::BufferUsages::VERTEX,
        });

        // -- instance buffer ------------------------------------------------
        let max_instances: usize = 2048;
        let instance_buffer = device.create_buffer(&wgpu::BufferDescriptor {
            label: Some("instance_buffer"),
            size: (max_instances * std::mem::size_of::<InstanceData>()) as u64,
            usage: wgpu::BufferUsages::VERTEX | wgpu::BufferUsages::COPY_DST,
            mapped_at_creation: false,
        });

        // -- render pipeline ------------------------------------------------
        let pipeline = device.create_render_pipeline(&wgpu::RenderPipelineDescriptor {
            label: Some("particle_pipeline"),
            layout: Some(&pipeline_layout),
            vertex: wgpu::VertexState {
                module: &shader,
                entry_point: Some("vs_main"),
                compilation_options: Default::default(),
                buffers: &[
                    // Slot 0: per-vertex quad corners
                    wgpu::VertexBufferLayout {
                        array_stride: (2 * std::mem::size_of::<f32>()) as u64,
                        step_mode: wgpu::VertexStepMode::Vertex,
                        attributes: &[wgpu::VertexAttribute {
                            format: wgpu::VertexFormat::Float32x2,
                            offset: 0,
                            shader_location: 0,
                        }],
                    },
                    // Slot 1: per-instance data
                    wgpu::VertexBufferLayout {
                        array_stride: std::mem::size_of::<InstanceData>() as u64,
                        step_mode: wgpu::VertexStepMode::Instance,
                        attributes: &[
                            // inst_pos (location 1)
                            wgpu::VertexAttribute {
                                format: wgpu::VertexFormat::Float32x3,
                                offset: 0,
                                shader_location: 1,
                            },
                            // inst_color (location 2)
                            wgpu::VertexAttribute {
                                format: wgpu::VertexFormat::Float32x4,
                                offset: 16, // after pos(12) + pad(4)
                                shader_location: 2,
                            },
                            // inst_size (location 3)
                            wgpu::VertexAttribute {
                                format: wgpu::VertexFormat::Float32,
                                offset: 32, // after pos(12)+pad(4)+color(16)
                                shader_location: 3,
                            },
                        ],
                    },
                ],
            },
            primitive: wgpu::PrimitiveState {
                topology: wgpu::PrimitiveTopology::TriangleStrip,
                strip_index_format: None,
                front_face: wgpu::FrontFace::Ccw,
                cull_mode: None,
                polygon_mode: wgpu::PolygonMode::Fill,
                unclipped_depth: false,
                conservative: false,
            },
            depth_stencil: None,
            multisample: wgpu::MultisampleState::default(),
            fragment: Some(wgpu::FragmentState {
                module: &shader,
                entry_point: Some("fs_main"),
                compilation_options: Default::default(),
                targets: &[Some(wgpu::ColorTargetState {
                    format,
                    blend: Some(wgpu::BlendState {
                        color: wgpu::BlendComponent {
                            src_factor: wgpu::BlendFactor::SrcAlpha,
                            dst_factor: wgpu::BlendFactor::OneMinusSrcAlpha,
                            operation: wgpu::BlendOperation::Add,
                        },
                        alpha: wgpu::BlendComponent {
                            src_factor: wgpu::BlendFactor::One,
                            dst_factor: wgpu::BlendFactor::OneMinusSrcAlpha,
                            operation: wgpu::BlendOperation::Add,
                        },
                    }),
                    write_mask: wgpu::ColorWrites::ALL,
                })],
            }),
            multiview_mask: None,
            cache: None,
        });

        Self {
            device,
            queue,
            surface,
            surface_config,
            pipeline,
            uniform_buffer,
            uniform_bind_group,
            quad_vertex_buffer,
            instance_buffer,
            max_instances,
        }
    }

    /// Resize the surface when the canvas changes dimensions.
    pub fn resize(&mut self, width: u32, height: u32) {
        if width == 0 || height == 0 {
            return;
        }
        self.surface_config.width = width;
        self.surface_config.height = height;
        self.surface.configure(&self.device, &self.surface_config);

        // Update projection
        let aspect = width as f32 / height as f32;
        let uniforms = Uniforms {
            projection: ortho_matrix(30.0, aspect),
            bg_color: [0.0, 0.0, 0.02, 1.0],
        };
        self.queue.write_buffer(
            &self.uniform_buffer,
            0,
            bytemuck::cast_slice(&[uniforms]),
        );
    }

    /// Collect renderable instances from the universe state and draw.
    pub fn render(&mut self, universe: &Universe) -> Result<(), wgpu::SurfaceError> {
        let instances = Self::collect_instances(universe);
        let instance_count = instances.len().min(self.max_instances);

        if instance_count > 0 {
            self.queue.write_buffer(
                &self.instance_buffer,
                0,
                bytemuck::cast_slice(&instances[..instance_count]),
            );
        }

        // Update uniform background colour from epoch
        let bg = epoch_background_color(universe.tick);
        let aspect = self.surface_config.width as f32 / self.surface_config.height as f32;
        let uniforms = Uniforms {
            projection: ortho_matrix(30.0, aspect),
            bg_color: [bg[0], bg[1], bg[2], 1.0],
        };
        self.queue.write_buffer(
            &self.uniform_buffer,
            0,
            bytemuck::cast_slice(&[uniforms]),
        );

        let output = self.surface.get_current_texture()?;
        let view = output
            .texture
            .create_view(&wgpu::TextureViewDescriptor::default());

        let mut encoder = self
            .device
            .create_command_encoder(&wgpu::CommandEncoderDescriptor {
                label: Some("render_encoder"),
            });

        {
            let mut pass = encoder.begin_render_pass(&wgpu::RenderPassDescriptor {
                label: Some("render_pass"),
                color_attachments: &[Some(wgpu::RenderPassColorAttachment {
                    view: &view,
                    resolve_target: None,
                    ops: wgpu::Operations {
                        load: wgpu::LoadOp::Clear(wgpu::Color {
                            r: bg[0] as f64 * 0.02,
                            g: bg[1] as f64 * 0.02,
                            b: bg[2] as f64 * 0.05,
                            a: 1.0,
                        }),
                        store: wgpu::StoreOp::Store,
                    },
                    depth_slice: None,
                })],
                depth_stencil_attachment: None,
                timestamp_writes: None,
                occlusion_query_set: None,
                multiview_mask: None,
            });

            if instance_count > 0 {
                pass.set_pipeline(&self.pipeline);
                pass.set_bind_group(0, &self.uniform_bind_group, &[]);
                pass.set_vertex_buffer(0, self.quad_vertex_buffer.slice(..));
                pass.set_vertex_buffer(1, self.instance_buffer.slice(..));
                pass.draw(0..4, 0..instance_count as u32);
            }
        }

        self.queue.submit(std::iter::once(encoder.finish()));
        output.present();
        Ok(())
    }

    // -----------------------------------------------------------------------
    // Instance collection
    // -----------------------------------------------------------------------

    fn collect_instances(universe: &Universe) -> Vec<InstanceData> {
        let mut out = Vec::with_capacity(512);

        // -- Particles (quantum field) --
        for p in &universe.quantum_field.particles {
            let col = p.particle_type.render_color();
            let sz = p.particle_type.render_size();
            out.push(InstanceData {
                position: [
                    p.position[0] as f32,
                    p.position[1] as f32,
                    p.position[2] as f32,
                ],
                _pad0: 0.0,
                color: col,
                size: sz,
                _pad1: [0.0; 3],
            });
        }

        // -- Atoms --
        for a in &universe.atomic_system.atoms {
            let col = a.render_color();
            let sz = a.render_size();
            out.push(InstanceData {
                position: [
                    a.position[0] as f32,
                    a.position[1] as f32,
                    a.position[2] as f32,
                ],
                _pad0: 0.0,
                color: col,
                size: sz,
                _pad1: [0.0; 3],
            });
        }

        // -- Molecules --
        if let Some(ref chem) = universe.chemical_system {
            for mol in &chem.molecules {
                let col = mol.render_color();
                let sz = 12.0;
                out.push(InstanceData {
                    position: [
                        mol.position[0] as f32,
                        mol.position[1] as f32,
                        mol.position[2] as f32,
                    ],
                    _pad0: 0.0,
                    color: col,
                    size: sz,
                    _pad1: [0.0; 3],
                });
            }
        }

        // -- Cells --
        if let Some(ref bio) = universe.biosphere {
            for cell in &bio.cells {
                let col = cell.render_color();
                let sz = cell.render_size();
                out.push(InstanceData {
                    position: [
                        cell.position[0] as f32,
                        cell.position[1] as f32,
                        cell.position[2] as f32,
                    ],
                    _pad0: 0.0,
                    color: col,
                    size: sz,
                    _pad1: [0.0; 3],
                });
            }
        }

        out
    }
}

// ---------------------------------------------------------------------------
// Projection helper
// ---------------------------------------------------------------------------

/// Orthographic projection matrix.  `half_extent` controls the visible
/// world-space range on the shorter axis; aspect ratio stretches the
/// longer axis.
fn ortho_matrix(half_extent: f32, aspect: f32) -> [[f32; 4]; 4] {
    let (hw, hh) = if aspect >= 1.0 {
        (half_extent * aspect, half_extent)
    } else {
        (half_extent, half_extent / aspect)
    };
    // Map  x: -hw..hw  -> -1..1
    //      y: -hh..hh  -> -1..1
    //      z: -100..100 -> 0..1   (wgpu clip-space z)
    [
        [1.0 / hw, 0.0,      0.0,         0.0],
        [0.0,      1.0 / hh, 0.0,         0.0],
        [0.0,      0.0,      1.0 / 200.0, 0.0],
        [0.0,      0.0,      0.5,         1.0],
    ]
}
