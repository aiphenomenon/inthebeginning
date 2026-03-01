//! "In The Beginning" -- WebAssembly cosmic simulator.
//!
//! Entry point for the WASM build.  Initialises WebGPU, creates the
//! simulation universe, and runs a `requestAnimationFrame` loop that
//! steps the simulation and renders every frame.

// ============================================================================
// Module declarations -- each file in src/ is a sibling module.
// ============================================================================

pub mod constants;
pub mod quantum;
pub mod atomic;
pub mod chemistry;
pub mod biology;
pub mod environment;
pub mod universe;
pub mod renderer;

// ============================================================================
// Imports
// ============================================================================

use std::cell::RefCell;
use std::rc::Rc;

use wasm_bindgen::prelude::*;
use wasm_bindgen::JsCast;

use crate::renderer::Renderer;
use crate::universe::Universe;

// ============================================================================
// Constants
// ============================================================================

/// Simulation ticks to advance per animation frame.
const TICKS_PER_FRAME: u64 = 200;

/// Total simulation length (same as PRESENT_EPOCH from constants).
const MAX_TICKS: u64 = 300_000;

/// Random seed for reproducible runs.
const SEED: u64 = 42;

// ============================================================================
// Helpers -- request_animation_frame trampoline
// ============================================================================

fn window() -> web_sys::Window {
    web_sys::window().expect("no global `window` exists")
}

fn document() -> web_sys::Document {
    window().document().expect("should have a document")
}

fn request_animation_frame(f: &Closure<dyn FnMut()>) {
    window()
        .request_animation_frame(f.as_ref().unchecked_ref())
        .expect("should register `requestAnimationFrame`");
}

/// Update the epoch overlay in the DOM.
fn update_hud(snap: &universe::Snapshot) {
    let doc = document();

    if let Some(el) = doc.get_element_by_id("epoch-name") {
        el.set_text_content(Some(snap.epoch_name));
    }
    if let Some(el) = doc.get_element_by_id("epoch-desc") {
        el.set_text_content(Some(snap.epoch_description));
    }
    if let Some(el) = doc.get_element_by_id("epoch-progress") {
        let pct = (snap.tick as f64 / MAX_TICKS as f64 * 100.0).min(100.0);
        let _ = el
            .dyn_ref::<web_sys::HtmlElement>()
            .map(|h| h.style().set_property("width", &format!("{pct:.1}%")));
    }
    if let Some(el) = doc.get_element_by_id("stats") {
        let text = format!(
            "Tick {tick} | T {temp:.0} K | Particles {parts} | Atoms {atoms} | Molecules {mols} | Cells {cells}",
            tick = snap.tick,
            temp = snap.temperature,
            parts = snap.particle_count,
            atoms = snap.atom_count,
            mols = snap.molecule_count,
            cells = snap.cell_count,
        );
        el.set_text_content(Some(&text));
    }
}

// ============================================================================
// WASM entry point
// ============================================================================

#[wasm_bindgen(start)]
pub async fn run() {
    // --- panic hook & logger -----------------------------------------------
    console_error_panic_hook::set_once();
    console_log::init_with_level(log::Level::Info).ok();

    log::info!("In The Beginning -- initialising WebGPU");

    // --- canvas ------------------------------------------------------------
    let canvas: web_sys::HtmlCanvasElement = document()
        .get_element_by_id("canvas")
        .expect("missing <canvas id='canvas'>")
        .dyn_into()
        .expect("element is not a canvas");

    let width = canvas.client_width() as u32;
    let height = canvas.client_height() as u32;
    canvas.set_width(width);
    canvas.set_height(height);

    // --- WebGPU setup ------------------------------------------------------
    let instance = wgpu::Instance::new(&wgpu::InstanceDescriptor {
        backends: wgpu::Backends::BROWSER_WEBGPU,
        ..Default::default()
    });

    let surface_target = wgpu::SurfaceTarget::Canvas(canvas.clone());
    let surface = instance
        .create_surface(surface_target)
        .expect("failed to create surface from canvas");

    let adapter = instance
        .request_adapter(&wgpu::RequestAdapterOptions {
            power_preference: wgpu::PowerPreference::HighPerformance,
            force_fallback_adapter: false,
            compatible_surface: Some(&surface),
        })
        .await
        .expect("no suitable WebGPU adapter");

    let (device, queue) = adapter
        .request_device(&wgpu::DeviceDescriptor {
            label: Some("device"),
            required_features: wgpu::Features::empty(),
            required_limits: wgpu::Limits::downlevel_webgl2_defaults()
                .using_resolution(adapter.limits()),
            memory_hints: wgpu::MemoryHints::Performance,
            trace: wgpu::Trace::Off,
            experimental_features: wgpu::ExperimentalFeatures::default(),
        })
        .await
        .expect("failed to create device");

    // --- Renderer ----------------------------------------------------------
    let renderer = Renderer::new(&adapter, device, queue, surface, width, height);

    // --- Universe ----------------------------------------------------------
    let universe = Universe::new(SEED, MAX_TICKS);

    // --- Fade the page in --------------------------------------------------
    if let Some(el) = document().get_element_by_id("app") {
        let _ = el
            .dyn_ref::<web_sys::HtmlElement>()
            .map(|h| h.style().set_property("opacity", "1"));
    }

    // --- Animation loop ----------------------------------------------------
    let renderer = Rc::new(RefCell::new(renderer));
    let universe = Rc::new(RefCell::new(universe));
    let canvas = Rc::new(canvas);

    // The closure must own an Rc to itself so it can re-schedule.
    let f: Rc<RefCell<Option<Closure<dyn FnMut()>>>> = Rc::new(RefCell::new(None));
    let g = f.clone();

    let r = renderer.clone();
    let u = universe.clone();
    let c = canvas.clone();

    *g.borrow_mut() = Some(Closure::new(move || {
        // Handle resize
        {
            let mut ren = r.borrow_mut();
            let cw = c.client_width() as u32;
            let ch = c.client_height() as u32;
            if cw != ren.surface_config.width || ch != ren.surface_config.height {
                c.set_width(cw);
                c.set_height(ch);
                ren.resize(cw, ch);
            }
        }

        // Step simulation
        {
            let mut uni = u.borrow_mut();
            if !uni.is_complete() {
                for _ in 0..TICKS_PER_FRAME {
                    uni.step();
                    if uni.is_complete() {
                        break;
                    }
                }
            }
        }

        // Update HUD
        {
            let uni = u.borrow();
            let snap = uni.snapshot();
            update_hud(&snap);
        }

        // Render
        {
            let mut ren = r.borrow_mut();
            let uni = u.borrow();
            match ren.render(&uni) {
                Ok(()) => {}
                Err(wgpu::SurfaceError::Lost) => {
                    let w = ren.surface_config.width;
                    let h = ren.surface_config.height;
                    ren.resize(w, h);
                }
                Err(wgpu::SurfaceError::OutOfMemory) => {
                    log::error!("Out of GPU memory");
                    return; // stop the loop
                }
                Err(e) => {
                    log::warn!("Surface error: {e:?}");
                }
            }
        }

        // Schedule next frame
        request_animation_frame(f.borrow().as_ref().unwrap());
    }));

    request_animation_frame(g.borrow().as_ref().unwrap());
}
