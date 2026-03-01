/**
 * Node.js AST introspection module using Acorn parser.
 *
 * Provides JavaScript/TypeScript AST parsing and analysis,
 * outputting universal AST format compatible with the DSL engine.
 */
const acorn = require("acorn");
const fs = require("fs");
const path = require("path");

function parseToUniversalAST(source, filename = "<string>") {
  const tree = acorn.parse(source, {
    ecmaVersion: "latest",
    sourceType: "module",
    locations: true,
  });
  return convertNode(tree, source);
}

function convertNode(node, source) {
  if (!node || typeof node !== "object") return null;

  const result = {
    type: node.type || "Unknown",
    name: extractName(node),
    line: node.loc ? node.loc.start.line : 0,
    col: node.loc ? node.loc.start.column : 0,
    end_line: node.loc ? node.loc.end.line : 0,
    end_col: node.loc ? node.loc.end.column : 0,
    attrs: extractAttrs(node),
    children: [],
  };

  // Extract source text
  if (node.start !== undefined && node.end !== undefined) {
    let src = source.substring(node.start, node.end);
    if (src.length > 200) src = src.substring(0, 200) + "...";
    result.src = src;
  }

  // Recurse into children
  for (const key of Object.keys(node)) {
    if (["type", "start", "end", "loc", "raw"].includes(key)) continue;
    const val = node[key];
    if (Array.isArray(val)) {
      for (const item of val) {
        const child = convertNode(item, source);
        if (child) result.children.push(child);
      }
    } else if (val && typeof val === "object" && val.type) {
      const child = convertNode(val, source);
      if (child) result.children.push(child);
    }
  }

  return result;
}

function extractName(node) {
  if (node.id && node.id.name) return node.id.name;
  if (node.name) return node.name;
  if (node.key && node.key.name) return node.key.name;
  if (node.type === "Identifier") return node.name || "";
  if (node.type === "ImportDeclaration" && node.source)
    return node.source.value || "";
  return "";
}

function extractAttrs(node) {
  const attrs = {};
  if (node.kind) attrs.kind = node.kind;
  if (node.async) attrs.async = true;
  if (node.generator) attrs.generator = true;
  if (node.params) attrs.param_count = node.params.length;
  if (node.superClass) {
    attrs.extends = node.superClass.name || "unknown";
  }
  return Object.keys(attrs).length > 0 ? attrs : {};
}

function findSymbols(source) {
  const ast = parseToUniversalAST(source);
  const symbols = [];

  function walk(node) {
    if (!node) return;
    if (
      [
        "FunctionDeclaration",
        "ClassDeclaration",
        "VariableDeclaration",
        "MethodDefinition",
      ].includes(node.type)
    ) {
      symbols.push({
        type: node.type,
        name: node.name,
        line: node.line,
        attrs: node.attrs,
      });
    }
    if (node.children) {
      for (const child of node.children) walk(child);
    }
  }

  walk(ast);
  return symbols;
}

function findDependencies(source) {
  const ast = parseToUniversalAST(source);
  const deps = [];

  function walk(node) {
    if (!node) return;
    if (node.type === "ImportDeclaration") {
      deps.push({ type: "import", module: node.name, line: node.line });
    }
    if (
      node.type === "CallExpression" &&
      node.children[0] &&
      node.children[0].name === "require"
    ) {
      const arg = node.children[1];
      if (arg && arg.src) {
        deps.push({
          type: "require",
          module: arg.src.replace(/['"]/g, ""),
          line: node.line,
        });
      }
    }
    if (node.children) {
      for (const child of node.children) walk(child);
    }
  }

  walk(ast);
  return deps;
}

function toCompact(node, depth = 0) {
  if (!node) return "";
  let parts = [node.type];
  if (node.name) parts[0] += ":" + node.name;
  if (node.line) parts[0] += "@" + node.line;
  if (node.attrs && Object.keys(node.attrs).length > 0) {
    const a = Object.entries(node.attrs)
      .map(([k, v]) => k + "=" + v)
      .join(",");
    parts.push("[" + a + "]");
  }
  if (node.children && node.children.length > 0) {
    const kids = node.children.map((c) => toCompact(c, depth + 1)).join(";");
    parts.push("{" + kids + "}");
  }
  return parts.join("");
}

// CLI interface for integration with Python driver
if (require.main === module) {
  const args = process.argv.slice(2);
  const action = args[0] || "parse";
  const target = args[1] || "";

  let source;
  if (target && fs.existsSync(target)) {
    source = fs.readFileSync(target, "utf8");
  } else {
    source = target;
  }

  const start = process.hrtime.bigint();
  const memBefore = process.memoryUsage();

  let result;
  switch (action) {
    case "parse":
      result = parseToUniversalAST(source, target);
      break;
    case "symbols":
      result = findSymbols(source);
      break;
    case "dependencies":
      result = findDependencies(source);
      break;
    case "compact":
      result = toCompact(parseToUniversalAST(source, target));
      break;
    default:
      result = { error: "Unknown action: " + action };
  }

  const elapsed = Number(process.hrtime.bigint() - start) / 1e6;
  const memAfter = process.memoryUsage();

  const output = {
    success: true,
    data: result,
    metrics: {
      wall_time_ms: elapsed.toFixed(2),
      heap_used_kb: Math.round(
        (memAfter.heapUsed - memBefore.heapUsed) / 1024
      ),
      rss_kb: Math.round(memAfter.rss / 1024),
    },
  };

  console.log(JSON.stringify(output));
}

module.exports = {
  parseToUniversalAST,
  findSymbols,
  findDependencies,
  toCompact,
};
