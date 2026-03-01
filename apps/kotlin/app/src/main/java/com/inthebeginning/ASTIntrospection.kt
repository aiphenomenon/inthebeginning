package com.inthebeginning

/**
 * AST self-introspection utility for the Kotlin Android app.
 *
 * Analyzes Kotlin source files to report symbol counts and structural metrics.
 * Can be invoked programmatically from the app or via unit tests.
 */
object ASTIntrospection {

    /**
     * File-level metrics from introspection.
     */
    data class FileMetrics(
        val filename: String,
        val lines: Int,
        val bytes: Int,
        val functions: Int,
        val classes: Int,
        val objects: Int,
        val interfaces: Int
    )

    /**
     * Analyze a Kotlin source string and return metrics.
     */
    fun analyze(source: String, filename: String): FileMetrics {
        val lines = source.lines().size
        val bytes = source.toByteArray(Charsets.UTF_8).size

        val funCount = Regex("""\bfun\s+""").findAll(source).count()
        val classCount = Regex("""\bclass\s+\w+""").findAll(source).count()
        val objectCount = Regex("""\bobject\s+\w+""").findAll(source).count()
        val ifaceCount = Regex("""\binterface\s+\w+""").findAll(source).count()

        return FileMetrics(
            filename = filename,
            lines = lines,
            bytes = bytes,
            functions = funCount,
            classes = classCount,
            objects = objectCount,
            interfaces = ifaceCount
        )
    }

    /**
     * Generate a formatted introspection report string.
     */
    fun report(metrics: List<FileMetrics>): String {
        val sb = StringBuilder()
        sb.appendLine("=== AST Self-Introspection: Kotlin Android App ===")
        sb.appendLine()
        sb.appendLine(
            "  %-28s %6s %8s %6s %6s %6s %6s".format(
                "File", "Lines", "Bytes", "Funcs", "Class", "Obj", "Iface"
            )
        )
        sb.appendLine("  " + "─".repeat(70))

        var tLines = 0; var tBytes = 0; var tFun = 0
        var tCls = 0; var tObj = 0; var tIface = 0

        for (m in metrics) {
            sb.appendLine(
                "  %-28s %6d %8d %6d %6d %6d %6d".format(
                    m.filename, m.lines, m.bytes, m.functions,
                    m.classes, m.objects, m.interfaces
                )
            )
            tLines += m.lines; tBytes += m.bytes; tFun += m.functions
            tCls += m.classes; tObj += m.objects; tIface += m.interfaces
        }

        sb.appendLine("  " + "─".repeat(70))
        sb.appendLine(
            "  %-28s %6d %8d %6d %6d %6d %6d".format(
                "TOTAL", tLines, tBytes, tFun, tCls, tObj, tIface
            )
        )
        return sb.toString()
    }
}
