// Package ast_dsl provides Go AST introspection for the reactive agent pair.
//
// Uses Go's built-in go/ast, go/parser, and go/token packages for full
// AST access. Outputs universal AST format as JSON for cross-language
// compatibility with the DSL engine.
package main

import (
	"encoding/json"
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"os"
	"runtime"
	"strings"
	"time"
)

// UniversalNode is the cross-language AST node format.
type UniversalNode struct {
	Type     string            `json:"type"`
	Name     string            `json:"name,omitempty"`
	Line     int               `json:"line,omitempty"`
	Col      int               `json:"col,omitempty"`
	EndLine  int               `json:"end_line,omitempty"`
	EndCol   int               `json:"end_col,omitempty"`
	Attrs    map[string]any    `json:"attrs,omitempty"`
	Src      string            `json:"src,omitempty"`
	Children []*UniversalNode  `json:"children,omitempty"`
}

// Metrics tracks performance data.
type Metrics struct {
	WallTimeMs float64 `json:"wall_time_ms"`
	AllocKB    int64   `json:"alloc_kb"`
	SysKB      int64   `json:"sys_kb"`
}

// Result wraps the output with metrics.
type Result struct {
	Success bool    `json:"success"`
	Data    any     `json:"data"`
	Metrics Metrics `json:"metrics"`
}

func convertNode(fset *token.FileSet, node ast.Node, src []byte) *UniversalNode {
	if node == nil {
		return nil
	}

	u := &UniversalNode{
		Type:  fmt.Sprintf("%T", node),
		Attrs: make(map[string]any),
	}

	// Strip the *ast. prefix
	u.Type = strings.TrimPrefix(u.Type, "*ast.")

	pos := fset.Position(node.Pos())
	end := fset.Position(node.End())
	u.Line = pos.Line
	u.Col = pos.Column
	u.EndLine = end.Line
	u.EndCol = end.Column

	// Extract source text
	if node.Pos().IsValid() && node.End().IsValid() {
		startOff := fset.Position(node.Pos()).Offset
		endOff := fset.Position(node.End()).Offset
		if startOff >= 0 && endOff <= len(src) && endOff > startOff {
			s := string(src[startOff:endOff])
			if len(s) > 200 {
				s = s[:200] + "..."
			}
			u.Src = s
		}
	}

	switch n := node.(type) {
	case *ast.File:
		u.Name = n.Name.Name
	case *ast.FuncDecl:
		u.Name = n.Name.Name
		if n.Recv != nil {
			u.Attrs["receiver"] = true
		}
		if n.Type.Params != nil {
			u.Attrs["params"] = n.Type.Params.NumFields()
		}
	case *ast.GenDecl:
		u.Attrs["tok"] = n.Tok.String()
	case *ast.TypeSpec:
		u.Name = n.Name.Name
	case *ast.ValueSpec:
		names := make([]string, len(n.Names))
		for i, name := range n.Names {
			names[i] = name.Name
		}
		u.Name = strings.Join(names, ", ")
	case *ast.Ident:
		u.Name = n.Name
	case *ast.ImportSpec:
		if n.Path != nil {
			u.Name = n.Path.Value
		}
	case *ast.CallExpr:
		if ident, ok := n.Fun.(*ast.Ident); ok {
			u.Name = ident.Name
		} else if sel, ok := n.Fun.(*ast.SelectorExpr); ok {
			u.Name = sel.Sel.Name
		}
	}

	if len(u.Attrs) == 0 {
		u.Attrs = nil
	}

	// Recurse into children via ast.Inspect
	ast.Inspect(node, func(child ast.Node) bool {
		if child == nil || child == node {
			return true
		}
		childNode := convertNode(fset, child, src)
		if childNode != nil {
			u.Children = append(u.Children, childNode)
		}
		return false // Don't recurse further; we handle it ourselves
	})

	return u
}

func parseFile(filename string) (*UniversalNode, error) {
	src, err := os.ReadFile(filename)
	if err != nil {
		return nil, err
	}

	fset := token.NewFileSet()
	file, err := parser.ParseFile(fset, filename, src, parser.ParseComments)
	if err != nil {
		return nil, err
	}

	return convertNode(fset, file, src), nil
}

func parseSource(source string) (*UniversalNode, error) {
	src := []byte(source)
	fset := token.NewFileSet()
	file, err := parser.ParseFile(fset, "<string>", src, parser.ParseComments)
	if err != nil {
		return nil, err
	}
	return convertNode(fset, file, src), nil
}

func findSymbols(node *UniversalNode) []map[string]any {
	var symbols []map[string]any
	if node == nil {
		return symbols
	}

	if node.Type == "FuncDecl" || node.Type == "TypeSpec" {
		symbols = append(symbols, map[string]any{
			"type": node.Type,
			"name": node.Name,
			"line": node.Line,
		})
	}

	for _, child := range node.Children {
		symbols = append(symbols, findSymbols(child)...)
	}
	return symbols
}

func toCompact(node *UniversalNode) string {
	if node == nil {
		return ""
	}
	s := node.Type
	if node.Name != "" {
		s += ":" + node.Name
	}
	if node.Line > 0 {
		s += fmt.Sprintf("@%d", node.Line)
	}
	if len(node.Children) > 0 {
		var kids []string
		for _, c := range node.Children {
			kids = append(kids, toCompact(c))
		}
		s += "{" + strings.Join(kids, ";") + "}"
	}
	return s
}

func main() {
	if len(os.Args) < 3 {
		fmt.Fprintf(os.Stderr, "Usage: go_ast <action> <file|source>\n")
		os.Exit(1)
	}

	action := os.Args[1]
	target := os.Args[2]

	start := time.Now()
	var memBefore runtime.MemStats
	runtime.ReadMemStats(&memBefore)

	var data any
	var err error

	switch action {
	case "parse":
		if _, statErr := os.Stat(target); statErr == nil {
			data, err = parseFile(target)
		} else {
			data, err = parseSource(target)
		}
	case "symbols":
		var node *UniversalNode
		if _, statErr := os.Stat(target); statErr == nil {
			node, err = parseFile(target)
		} else {
			node, err = parseSource(target)
		}
		if err == nil {
			data = findSymbols(node)
		}
	case "compact":
		var node *UniversalNode
		if _, statErr := os.Stat(target); statErr == nil {
			node, err = parseFile(target)
		} else {
			node, err = parseSource(target)
		}
		if err == nil {
			data = toCompact(node)
		}
	default:
		err = fmt.Errorf("unknown action: %s", action)
	}

	elapsed := time.Since(start)
	var memAfter runtime.MemStats
	runtime.ReadMemStats(&memAfter)

	result := Result{
		Success: err == nil,
		Data:    data,
		Metrics: Metrics{
			WallTimeMs: float64(elapsed.Microseconds()) / 1000.0,
			AllocKB:    int64(memAfter.TotalAlloc-memBefore.TotalAlloc) / 1024,
			SysKB:      int64(memAfter.Sys) / 1024,
		},
	}

	if err != nil {
		result.Data = map[string]string{"error": err.Error()}
	}

	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	enc.Encode(result)
}
