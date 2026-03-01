package com.inthebeginning.renderer

import android.opengl.GLES20
import android.opengl.GLSurfaceView
import android.opengl.Matrix
import com.inthebeginning.simulator.RenderableEntity
import com.inthebeginning.simulator.Snapshot
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.FloatBuffer
import javax.microedition.khronos.egl.EGLConfig
import javax.microedition.khronos.opengles.GL10

/**
 * OpenGL ES 2.0 renderer for the cosmic simulation.
 *
 * Renders particles, atoms, molecules, and cells as instanced circles
 * using a single quad with a circular fragment shader. This approach is
 * significantly more performant than Canvas when the entity count is high.
 */
class SimulationRenderer : GLSurfaceView.Renderer {

    // Current snapshot to render (set from UI thread, read on GL thread)
    @Volatile
    var snapshot: Snapshot? = null

    // Zoom and pan state
    @Volatile
    var zoom: Float = 1.0f

    @Volatile
    var panX: Float = 0.0f

    @Volatile
    var panY: Float = 0.0f

    // Matrices
    private val projectionMatrix = FloatArray(16)
    private val viewMatrix = FloatArray(16)
    private val mvpMatrix = FloatArray(16)
    private val modelMatrix = FloatArray(16)
    private val tempMatrix = FloatArray(16)

    // Shader program
    private var programId = 0

    // Attribute and uniform locations
    private var aPositionLoc = 0
    private var uMvpMatrixLoc = 0
    private var uColorLoc = 0
    private var uPointSizeLoc = 0

    // Unit quad vertex buffer (two triangles forming a point sprite)
    private lateinit var quadVertexBuffer: FloatBuffer

    // Screen dimensions
    private var screenWidth = 1
    private var screenHeight = 1

    // Vertex shader: transforms position and passes through point size
    private val vertexShaderSource = """
        uniform mat4 uMVPMatrix;
        uniform float uPointSize;
        attribute vec4 aPosition;
        void main() {
            gl_Position = uMVPMatrix * aPosition;
            gl_PointSize = uPointSize;
        }
    """.trimIndent()

    // Fragment shader: renders soft circles with glow
    private val fragmentShaderSource = """
        precision mediump float;
        uniform vec4 uColor;
        void main() {
            // Convert point coordinate to circle
            vec2 coord = gl_PointCoord - vec2(0.5);
            float dist = length(coord);

            // Discard fragments outside the circle
            if (dist > 0.5) discard;

            // Soft edge with glow
            float alpha = smoothstep(0.5, 0.2, dist) * uColor.a;
            // Inner brightness
            float brightness = 1.0 + smoothstep(0.3, 0.0, dist) * 0.5;

            gl_FragColor = vec4(uColor.rgb * brightness, alpha);
        }
    """.trimIndent()

    override fun onSurfaceCreated(gl: GL10?, config: EGLConfig?) {
        // Dark cosmic background
        GLES20.glClearColor(0.04f, 0.04f, 0.07f, 1.0f)

        // Enable blending for transparency
        GLES20.glEnable(GLES20.GL_BLEND)
        GLES20.glBlendFunc(GLES20.GL_SRC_ALPHA, GLES20.GL_ONE_MINUS_SRC_ALPHA)

        // Compile shaders and link program
        val vertexShader = compileShader(GLES20.GL_VERTEX_SHADER, vertexShaderSource)
        val fragmentShader = compileShader(GLES20.GL_FRAGMENT_SHADER, fragmentShaderSource)
        programId = GLES20.glCreateProgram().also { program ->
            GLES20.glAttachShader(program, vertexShader)
            GLES20.glAttachShader(program, fragmentShader)
            GLES20.glLinkProgram(program)
        }

        // Get attribute and uniform locations
        aPositionLoc = GLES20.glGetAttribLocation(programId, "aPosition")
        uMvpMatrixLoc = GLES20.glGetUniformLocation(programId, "uMVPMatrix")
        uColorLoc = GLES20.glGetUniformLocation(programId, "uColor")
        uPointSizeLoc = GLES20.glGetUniformLocation(programId, "uPointSize")

        // Create a single point vertex (we use GL_POINTS for instancing)
        val quadCoords = floatArrayOf(0.0f, 0.0f, 0.0f)
        quadVertexBuffer = ByteBuffer.allocateDirect(quadCoords.size * 4)
            .order(ByteOrder.nativeOrder())
            .asFloatBuffer()
            .put(quadCoords)
        quadVertexBuffer.position(0)
    }

    override fun onSurfaceChanged(gl: GL10?, width: Int, height: Int) {
        GLES20.glViewport(0, 0, width, height)
        screenWidth = width
        screenHeight = height

        val aspect = width.toFloat() / height.toFloat()
        Matrix.orthoM(projectionMatrix, 0, -aspect * 100f, aspect * 100f, -100f, 100f, -1f, 1f)
        Matrix.setLookAtM(viewMatrix, 0, 0f, 0f, 1f, 0f, 0f, 0f, 0f, 1f, 0f)
    }

    override fun onDrawFrame(gl: GL10?) {
        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT)

        val snap = snapshot ?: return

        GLES20.glUseProgram(programId)

        // Build view-projection with zoom and pan
        Matrix.setIdentityM(modelMatrix, 0)
        Matrix.scaleM(modelMatrix, 0, zoom, zoom, 1f)
        Matrix.translateM(modelMatrix, 0, panX / zoom, -panY / zoom, 0f)

        Matrix.multiplyMM(tempMatrix, 0, viewMatrix, 0, modelMatrix, 0)
        Matrix.multiplyMM(mvpMatrix, 0, projectionMatrix, 0, tempMatrix, 0)

        GLES20.glUniformMatrix4fv(uMvpMatrixLoc, 1, false, mvpMatrix, 0)

        // Enable vertex attribute
        GLES20.glEnableVertexAttribArray(aPositionLoc)

        // Draw particles
        for (entity in snap.renderableParticles) {
            drawEntity(entity, particleColor(entity.type))
        }

        // Draw atoms
        for (entity in snap.renderableAtoms) {
            drawEntity(entity, atomColor(entity.type))
        }

        // Draw molecules
        for (entity in snap.renderableMolecules) {
            drawEntity(entity, floatArrayOf(0.15f, 0.78f, 0.85f, 0.7f))
        }

        // Draw cells
        for (entity in snap.renderableCells) {
            drawEntity(entity, floatArrayOf(0.4f, 0.73f, 0.42f, 0.8f))
        }

        GLES20.glDisableVertexAttribArray(aPositionLoc)
    }

    /**
     * Draw a single entity as a point sprite at (x, y) with the given color.
     */
    private fun drawEntity(entity: RenderableEntity, color: FloatArray) {
        // Update vertex position for this entity
        val posBuffer = ByteBuffer.allocateDirect(3 * 4)
            .order(ByteOrder.nativeOrder())
            .asFloatBuffer()
        posBuffer.put(entity.x)
        posBuffer.put(entity.y)
        posBuffer.put(0f)
        posBuffer.position(0)

        GLES20.glVertexAttribPointer(aPositionLoc, 3, GLES20.GL_FLOAT, false, 0, posBuffer)
        GLES20.glUniform4fv(uColorLoc, 1, color, 0)
        GLES20.glUniform1f(uPointSizeLoc, entity.radius * zoom * 4f)

        GLES20.glDrawArrays(GLES20.GL_POINTS, 0, 1)
    }

    /**
     * Get RGBA color array for a particle type.
     */
    private fun particleColor(type: String): FloatArray = when (type) {
        "photon" -> floatArrayOf(1.0f, 0.92f, 0.23f, 0.8f)
        "electron" -> floatArrayOf(0.13f, 0.59f, 0.95f, 0.9f)
        "positron" -> floatArrayOf(1.0f, 0.32f, 0.32f, 0.9f)
        "proton" -> floatArrayOf(1.0f, 0.60f, 0.0f, 0.9f)
        "neutron" -> floatArrayOf(0.62f, 0.62f, 0.62f, 0.8f)
        "up", "down" -> floatArrayOf(0.88f, 0.25f, 0.98f, 0.85f)
        "neutrino" -> floatArrayOf(1.0f, 1.0f, 1.0f, 0.3f)
        "gluon" -> floatArrayOf(0.0f, 0.90f, 0.46f, 0.7f)
        "W" -> floatArrayOf(0.67f, 0.0f, 1.0f, 0.8f)
        "Z" -> floatArrayOf(0.38f, 0.0f, 0.92f, 0.8f)
        else -> floatArrayOf(1.0f, 1.0f, 1.0f, 0.7f)
    }

    /**
     * Get RGBA color array for an element symbol.
     */
    private fun atomColor(symbol: String): FloatArray = when (symbol) {
        "H" -> floatArrayOf(0.88f, 0.88f, 0.88f, 0.9f)
        "He" -> floatArrayOf(1.0f, 0.98f, 0.77f, 0.85f)
        "C" -> floatArrayOf(0.26f, 0.26f, 0.26f, 0.9f)
        "N" -> floatArrayOf(0.26f, 0.65f, 0.96f, 0.9f)
        "O" -> floatArrayOf(0.94f, 0.33f, 0.31f, 0.9f)
        "Fe" -> floatArrayOf(0.75f, 0.21f, 0.05f, 0.9f)
        else -> floatArrayOf(0.47f, 0.56f, 0.61f, 0.8f)
    }

    /**
     * Compile a GLSL shader from source.
     */
    private fun compileShader(type: Int, source: String): Int {
        val shader = GLES20.glCreateShader(type)
        GLES20.glShaderSource(shader, source)
        GLES20.glCompileShader(shader)

        val status = IntArray(1)
        GLES20.glGetShaderiv(shader, GLES20.GL_COMPILE_STATUS, status, 0)
        if (status[0] == 0) {
            val log = GLES20.glGetShaderInfoLog(shader)
            GLES20.glDeleteShader(shader)
            throw RuntimeException("Shader compilation failed: $log")
        }
        return shader
    }
}
