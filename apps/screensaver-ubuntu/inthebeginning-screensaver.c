/*
 * inthebeginning-screensaver.c
 *
 * A standalone X11/OpenGL screensaver for Ubuntu/Linux that simulates
 * the universe from the Big Bang through the emergence of life.
 *
 * Can be used as:
 *   1. Standalone fullscreen app (default)
 *   2. XScreenSaver hack (with -root flag)
 *   3. Window mode (with -window flag for testing)
 *
 * Build: make
 * Run:   ./inthebeginning-screensaver
 */

#define _POSIX_C_SOURCE 199309L

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <unistd.h>
#include <signal.h>

/*
 * Include our simulator BEFORE X11 headers to avoid the X11 `Atom`
 * typedef conflicting with our `Atom` struct.  We then #define Atom
 * away for X11 usage.
 */
#include "simulator/universe.h"

/* Hide X11's Atom typedef which would conflict */
#define Atom X11Atom

/* X11 */
#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/keysym.h>

/* OpenGL */
#include <GL/gl.h>
#include <GL/glx.h>

/* Restore Atom for our usage */
#undef Atom

/* ------------------------------------------------------------------ */
/*  Configuration                                                      */
/* ------------------------------------------------------------------ */

#define TARGET_FPS         30
#define TICKS_PER_FRAME    2
#define MAX_DRAW_PARTICLES 2048

/* Color scheme per epoch (R, G, B) */
static const float epoch_colors[][3] = {
    {1.0f, 1.0f, 1.0f},    /* VOID - white */
    {0.9f, 0.7f, 1.0f},    /* PLANCK - violet */
    {1.0f, 0.9f, 0.5f},    /* INFLATION - gold */
    {0.5f, 0.8f, 1.0f},    /* ELECTROWEAK - blue */
    {1.0f, 0.4f, 0.2f},    /* QUARK - orange-red */
    {0.8f, 0.3f, 0.3f},    /* HADRON - red */
    {0.9f, 0.6f, 0.2f},    /* NUCLEOSYNTHESIS - amber */
    {0.3f, 0.5f, 0.9f},    /* RECOMBINATION - cool blue */
    {1.0f, 0.8f, 0.3f},    /* STAR FORMATION - stellar gold */
    {0.6f, 0.4f, 0.2f},    /* SOLAR SYSTEM - brown */
    {0.2f, 0.6f, 0.8f},    /* EARTH - ocean blue */
    {0.1f, 0.8f, 0.3f},    /* LIFE - green */
    {0.2f, 0.9f, 0.4f},    /* DNA - bright green */
    {0.3f, 0.7f, 1.0f},    /* PRESENT - sky blue */
};

/* ------------------------------------------------------------------ */
/*  Global state                                                       */
/* ------------------------------------------------------------------ */

static volatile int running = 1;
static Universe universe;
static Snapshot snap;

static Display *dpy = NULL;
static Window   x11win;
static GLXContext glctx;
static int win_width = 800, win_height = 600;
static int fullscreen_mode = 1;
static int use_root = 0;

/* ------------------------------------------------------------------ */
/*  Signal handler                                                     */
/* ------------------------------------------------------------------ */

static void handle_signal(int sig)
{
    (void)sig;
    running = 0;
}

/* ------------------------------------------------------------------ */
/*  OpenGL initialization                                              */
/* ------------------------------------------------------------------ */

static void gl_init(void)
{
    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    glEnable(GL_POINT_SMOOTH);
    glHint(GL_POINT_SMOOTH_HINT, GL_NICEST);
    glClearColor(0.0f, 0.0f, 0.02f, 1.0f);
}

static void gl_resize(int w, int h)
{
    win_width = w;
    win_height = h;
    glViewport(0, 0, w, h);
    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();
    double aspect = (double)w / (double)(h > 0 ? h : 1);
    glOrtho(-aspect, aspect, -1.0, 1.0, -1.0, 1.0);
    glMatrixMode(GL_MODELVIEW);
    glLoadIdentity();
}

/* ------------------------------------------------------------------ */
/*  Rendering                                                          */
/* ------------------------------------------------------------------ */

static void draw_particles(const Universe *u)
{
    int count = u->qf.particle_count;
    if (count <= 0) return;
    int step = count > MAX_DRAW_PARTICLES ? count / MAX_DRAW_PARTICLES : 1;

    const float *ec = epoch_colors[snap.epoch < EPOCH_COUNT ? snap.epoch : 0];

    glPointSize(3.0f);
    glBegin(GL_POINTS);
    for (int i = 0; i < count; i += step) {
        if (!u->qf.particles[i].alive) continue;
        float x = (float)(u->qf.particles[i].position[0]);
        float y = (float)(u->qf.particles[i].position[1]);
        float alpha = 0.5f + 0.5f * (float)u->qf.particles[i].wave_fn.amplitude;
        glColor4f(ec[0], ec[1], ec[2], alpha);
        glVertex2f(x, y);
    }
    glEnd();
}

static void draw_atoms(const Universe *u)
{
    int count = u->as.atom_count;
    if (count <= 0) return;

    glPointSize(5.0f);
    glBegin(GL_POINTS);
    for (int i = 0; i < count && i < 512; i++) {
        if (!u->as.atoms[i].alive) continue;
        float x = (float)(u->as.atoms[i].position[0]);
        float y = (float)(u->as.atoms[i].position[1]);
        float r = 0.3f + 0.7f * ((float)u->as.atoms[i].atomic_number / 26.0f);
        glColor4f(r, 0.6f, 1.0f - r, 0.8f);
        glVertex2f(x, y);
    }
    glEnd();
}

static void draw_molecules(const Universe *u)
{
    int count = u->cs.molecule_count;
    if (count <= 0) return;

    glPointSize(7.0f);
    glBegin(GL_POINTS);
    for (int i = 0; i < count && i < 256; i++) {
        if (!u->cs.molecules[i].alive) continue;
        float x = (float)(u->cs.molecules[i].position[0]);
        float y = (float)(u->cs.molecules[i].position[1]);
        glColor4f(0.2f, 0.8f, 0.4f, 0.9f);
        glVertex2f(x, y);
    }
    glEnd();
}

static void draw_cells(const Universe *u)
{
    int count = u->bio.cell_count;
    if (count <= 0) return;

    for (int i = 0; i < count && i < 128; i++) {
        if (!u->bio.cells[i].alive) continue;
        float fitness = (float)(u->bio.cells[i].fitness);
        /* Position cells in a grid pattern since Cell has no position field */
        float x = -0.8f + (float)(i % 16) * 0.1f;
        float y = -0.4f + (float)(i / 16) * 0.1f;
        float size = 8.0f + fitness * 4.0f;

        glPointSize(size);
        glBegin(GL_POINTS);
        glColor4f(0.1f, 0.9f * fitness, 0.3f, 0.85f);
        glVertex2f(x, y);
        glEnd();
    }
}

static void draw_epoch_label(void)
{
    float progress = (float)snap.epoch / (float)(EPOCH_COUNT - 1);
    const float *ec = epoch_colors[snap.epoch < EPOCH_COUNT ? snap.epoch : 0];

    glBegin(GL_QUADS);
    glColor4f(ec[0], ec[1], ec[2], 0.3f);
    double aspect = (double)win_width / (double)(win_height > 0 ? win_height : 1);
    glVertex2f((float)(-aspect), 0.95f);
    glVertex2f((float)(-aspect + 2.0 * aspect * progress), 0.95f);
    glVertex2f((float)(-aspect + 2.0 * aspect * progress), 1.0f);
    glVertex2f((float)(-aspect), 1.0f);
    glEnd();
}

static void render(const Universe *u)
{
    glClear(GL_COLOR_BUFFER_BIT);

    draw_epoch_label();
    draw_particles(u);
    draw_atoms(u);
    draw_molecules(u);
    draw_cells(u);

    glXSwapBuffers(dpy, x11win);
}

/* ------------------------------------------------------------------ */
/*  X11 / GLX window creation                                          */
/* ------------------------------------------------------------------ */

static int create_window(void)
{
    dpy = XOpenDisplay(NULL);
    if (!dpy) {
        fprintf(stderr, "Cannot open X display\n");
        return -1;
    }

    int screen = DefaultScreen(dpy);

    int attribs[] = {
        GLX_RGBA,
        GLX_DOUBLEBUFFER,
        GLX_RED_SIZE, 8,
        GLX_GREEN_SIZE, 8,
        GLX_BLUE_SIZE, 8,
        GLX_ALPHA_SIZE, 8,
        GLX_DEPTH_SIZE, 24,
        None
    };

    XVisualInfo *vi = glXChooseVisual(dpy, screen, attribs);
    if (!vi) {
        fprintf(stderr, "No suitable GLX visual found\n");
        return -1;
    }

    if (use_root) {
        x11win = RootWindow(dpy, screen);
        XWindowAttributes xwa;
        XGetWindowAttributes(dpy, x11win, &xwa);
        win_width = xwa.width;
        win_height = xwa.height;
    } else {
        Colormap cmap = XCreateColormap(dpy, RootWindow(dpy, screen), vi->visual, AllocNone);
        XSetWindowAttributes swa;
        swa.colormap = cmap;
        swa.event_mask = ExposureMask | KeyPressMask | StructureNotifyMask;
        swa.override_redirect = fullscreen_mode ? True : False;

        if (fullscreen_mode) {
            win_width = DisplayWidth(dpy, screen);
            win_height = DisplayHeight(dpy, screen);
        }

        x11win = XCreateWindow(dpy, RootWindow(dpy, screen),
                               0, 0, (unsigned)win_width, (unsigned)win_height, 0,
                               vi->depth, InputOutput, vi->visual,
                               CWColormap | CWEventMask | CWOverrideRedirect, &swa);

        XMapWindow(dpy, x11win);
        XStoreName(dpy, x11win, "In The Beginning - Cosmic Screensaver");

        if (fullscreen_mode) {
            XGrabKeyboard(dpy, x11win, True, GrabModeAsync, GrabModeAsync, CurrentTime);
        }
    }

    glctx = glXCreateContext(dpy, vi, NULL, GL_TRUE);
    glXMakeCurrent(dpy, x11win, glctx);
    XFree(vi);

    return 0;
}

static void destroy_window(void)
{
    if (glctx) {
        glXMakeCurrent(dpy, None, NULL);
        glXDestroyContext(dpy, glctx);
    }
    if (dpy) {
        if (!use_root) XDestroyWindow(dpy, x11win);
        XCloseDisplay(dpy);
    }
}

/* ------------------------------------------------------------------ */
/*  Main                                                               */
/* ------------------------------------------------------------------ */

static void ast_introspect(void)
{
    printf("\n\033[1;36m=== AST Self-Introspection: Ubuntu Screensaver ===\033[0m\n\n");

    /* List of source files to analyze */
    static const char *files[] = {
        "inthebeginning-screensaver.c",
        "test_simulator.c",
        "simulator/universe.h",
        "simulator/universe.c",
        "simulator/quantum.h",
        "simulator/quantum.c",
        "simulator/atomic.h",
        "simulator/atomic.c",
        "simulator/chemistry.h",
        "simulator/chemistry.c",
        "simulator/biology.h",
        "simulator/biology.c",
        "simulator/environment.h",
        "simulator/environment.c",
        "simulator/constants.h",
        NULL
    };

    int total_lines = 0, total_bytes = 0, total_funcs = 0, total_structs = 0;

    printf("  %-28s %6s %8s %6s %7s\n", "File", "Lines", "Bytes", "Funcs", "Structs");
    printf("  %-28s %6s %8s %6s %7s\n",
           "────────────────────────────", "──────", "────────", "──────", "───────");

    for (int i = 0; files[i]; i++) {
        FILE *fp = fopen(files[i], "r");
        if (!fp) continue;

        int lines = 0, funcs = 0, structs = 0;
        char line[1024];
        while (fgets(line, sizeof(line), fp)) {
            lines++;
            /* Simple heuristic: line starting with type + word + ( is a function def */
            const char *p = line;
            while (*p == ' ' || *p == '\t') p++;
            if (strstr(p, "static ") == p || strstr(p, "void ") == p ||
                strstr(p, "int ") == p || strstr(p, "float ") == p ||
                strstr(p, "double ") == p || strstr(p, "char ") == p ||
                strstr(p, "unsigned ") == p || strstr(p, "long ") == p ||
                strstr(p, "const ") == p) {
                if (strchr(p, '(') && !strchr(p, ';'))
                    funcs++;
            }
            if (strstr(p, "struct ") == p || strstr(p, "typedef struct") == p)
                structs++;
        }

        fseek(fp, 0, SEEK_END);
        int bytes = (int)ftell(fp);
        fclose(fp);

        total_lines += lines;
        total_bytes += bytes;
        total_funcs += funcs;
        total_structs += structs;

        printf("  %-28s %6d %8d %6d %7d\n", files[i], lines, bytes, funcs, structs);
    }

    printf("  %-28s %6s %8s %6s %7s\n",
           "────────────────────────────", "──────", "────────", "──────", "───────");
    printf("  %-28s %6d %8d %6d %7d\n", "TOTAL", total_lines, total_bytes,
           total_funcs, total_structs);
    printf("\n");
}

static void parse_args(int argc, char **argv)
{
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-root") == 0)
            use_root = 1;
        else if (strcmp(argv[i], "-window") == 0) {
            fullscreen_mode = 0;
            use_root = 0;
        } else if (strcmp(argv[i], "--ast-introspect") == 0) {
            ast_introspect();
            exit(0);
        } else if (strcmp(argv[i], "-help") == 0 || strcmp(argv[i], "--help") == 0) {
            printf("Usage: %s [-root|-window|--ast-introspect|-help]\n", argv[0]);
            printf("  -root             Draw on root window (XScreenSaver mode)\n");
            printf("  -window           Windowed mode (800x600)\n");
            printf("  --ast-introspect  Show AST self-introspection of source files\n");
            printf("  (default)         Fullscreen mode\n");
            exit(0);
        }
    }
}

int main(int argc, char **argv)
{
    parse_args(argc, argv);

    signal(SIGINT, handle_signal);
    signal(SIGTERM, handle_signal);

    if (create_window() != 0) return 1;

    gl_init();
    gl_resize(win_width, win_height);

    unsigned int seed = (unsigned int)time(NULL) ^ (unsigned int)getpid();
    universe_init(&universe, seed);

    struct timespec frame_time;
    long frame_ns = 1000000000L / TARGET_FPS;

    while (running) {
        clock_gettime(CLOCK_MONOTONIC, &frame_time);

        while (XPending(dpy)) {
            XEvent ev;
            XNextEvent(dpy, &ev);
            switch (ev.type) {
            case KeyPress: {
                KeySym ks = XLookupKeysym(&ev.xkey, 0);
                if (ks == XK_Escape || ks == XK_q) running = 0;
                break;
            }
            case ConfigureNotify:
                gl_resize(ev.xconfigure.width, ev.xconfigure.height);
                break;
            }
        }

        for (int i = 0; i < TICKS_PER_FRAME; i++)
            universe_step(&universe);

        snap = universe_snapshot(&universe);

        if (snap.epoch >= EPOCH_PRESENT) {
            seed = (unsigned int)time(NULL) ^ (unsigned int)getpid();
            universe_init(&universe, seed);
        }

        render(&universe);

        struct timespec now;
        clock_gettime(CLOCK_MONOTONIC, &now);
        long elapsed = (now.tv_sec - frame_time.tv_sec) * 1000000000L
                     + (now.tv_nsec - frame_time.tv_nsec);
        long remaining = frame_ns - elapsed;
        if (remaining > 0) {
            struct timespec sleep_time = { 0, remaining };
            nanosleep(&sleep_time, NULL);
        }
    }

    destroy_window();
    return 0;
}
