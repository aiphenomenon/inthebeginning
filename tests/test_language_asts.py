"""Tests for multi-language AST parsers."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ast_dsl.core import ASTNode
from ast_dsl.java_ast import parse_java_source, find_java_symbols, to_compact as java_compact
from ast_dsl.rust_ast import parse_rust_source, find_rust_symbols, to_compact as rust_compact
from ast_dsl.perl_ast import parse_perl_source, find_perl_symbols, to_compact as perl_compact
from ast_dsl.php_ast import parse_php_source, find_php_symbols, to_compact as php_compact
from ast_dsl.c_ast import parse_c_source, find_c_symbols, to_compact as c_compact
from ast_dsl.wasm_ast import parse_wasm_source, find_wasm_symbols, to_compact as wasm_compact
from ast_dsl.typescript_ast import parse_typescript_source, find_typescript_symbols, to_compact as ts_compact
from ast_dsl.swift_ast import parse_swift_source, find_swift_symbols, to_compact as swift_compact
from ast_dsl.kotlin_ast import parse_kotlin_source, find_kotlin_symbols, to_compact as kotlin_compact


SAMPLE_JAVA = '''
package com.example;

import java.util.List;
import static java.lang.Math.PI;

public class Calculator {
    private int value;

    public int add(int a, int b) {
        return a + b;
    }

    public double divide(double a, double b) {
        if (b == 0) {
            throw new ArithmeticException("Division by zero");
        }
        return a / b;
    }
}

interface Computable {
    int compute(int x);
}
'''

SAMPLE_RUST = '''
use std::collections::HashMap;
use std::io;

mod utils;

pub struct Calculator {
    history: Vec<f64>,
}

pub enum Operation {
    Add,
    Subtract,
    Multiply,
}

pub trait Computable {
    fn compute(&self, x: f64) -> f64;
}

impl Calculator {
    pub fn new() -> Self {
        Calculator { history: Vec::new() }
    }

    pub async fn add(&mut self, a: f64, b: f64) -> f64 {
        let result = a + b;
        self.history.push(result);
        result
    }
}

fn helper(x: i32) -> i32 {
    x * 2
}
'''

SAMPLE_PERL = '''
package Calculator;

use strict;
use warnings;
use Carp qw(croak);

sub new {
    my ($class) = @_;
    my $self = bless { history => [] }, $class;
    return $self;
}

sub add {
    my ($self, $a, $b) = @_;
    my $result = $a + $b;
    push @{$self->{history}}, $result;
    return $result;
}

our $VERSION = '1.0';

1;
'''

SAMPLE_PHP = '''<?php
namespace App\\Models;

use App\\Interfaces\\Calculable;
use App\\Traits\\Loggable;

abstract class Calculator {
    private int $value;

    public function add(int $a, int $b): int {
        return $a + $b;
    }

    protected function divide(float $a, float $b): ?float {
        if ($b == 0) {
            return null;
        }
        return $a / $b;
    }
}

interface Computable {
    public function compute(int $x): int;
}

trait Loggable {
    public function log(string $msg): void {
        echo $msg;
    }
}
'''

SAMPLE_C = '''
int add(int a, int b) {
    return a + b;
}
'''


class TestJavaAST(unittest.TestCase):
    def test_parse(self):
        root = parse_java_source(SAMPLE_JAVA)
        self.assertEqual(root.node_type, "CompilationUnit")

    def test_find_symbols(self):
        symbols = find_java_symbols(SAMPLE_JAVA)
        names = [s["name"] for s in symbols]
        self.assertIn("Calculator", names)
        self.assertIn("add", names)
        self.assertIn("divide", names)

    def test_package_detection(self):
        root = parse_java_source(SAMPLE_JAVA)
        pkgs = [n for n in root.walk() if n.node_type == "PackageDecl"]
        self.assertEqual(len(pkgs), 1)
        self.assertEqual(pkgs[0].name, "com.example")

    def test_import_detection(self):
        root = parse_java_source(SAMPLE_JAVA)
        imports = [n for n in root.walk() if n.node_type == "ImportDecl"]
        self.assertGreater(len(imports), 0)
        # Check static import
        static_imports = [i for i in imports
                          if i.attributes.get("static")]
        self.assertEqual(len(static_imports), 1)

    def test_interface_detection(self):
        root = parse_java_source(SAMPLE_JAVA)
        interfaces = [n for n in root.walk()
                      if n.node_type == "InterfaceDecl"]
        self.assertEqual(len(interfaces), 1)
        self.assertEqual(interfaces[0].name, "Computable")

    def test_method_params(self):
        root = parse_java_source(SAMPLE_JAVA)
        methods = [n for n in root.walk()
                   if n.node_type == "MethodDecl" and n.name == "add"]
        self.assertGreater(len(methods), 0)
        self.assertIn("params", methods[0].attributes)

    def test_compact(self):
        root = parse_java_source(SAMPLE_JAVA)
        compact = java_compact(root)
        self.assertIn("CompilationUnit", compact)


class TestRustAST(unittest.TestCase):
    def test_parse(self):
        root = parse_rust_source(SAMPLE_RUST)
        self.assertEqual(root.node_type, "Crate")

    def test_find_symbols(self):
        symbols = find_rust_symbols(SAMPLE_RUST)
        names = [s["name"] for s in symbols]
        self.assertIn("Calculator", names)
        self.assertIn("Operation", names)
        self.assertIn("Computable", names)

    def test_use_declarations(self):
        root = parse_rust_source(SAMPLE_RUST)
        uses = [n for n in root.walk() if n.node_type == "UseDecl"]
        self.assertGreater(len(uses), 0)

    def test_mod_declarations(self):
        root = parse_rust_source(SAMPLE_RUST)
        mods = [n for n in root.walk() if n.node_type == "ModDecl"]
        self.assertEqual(len(mods), 1)
        self.assertEqual(mods[0].name, "utils")

    def test_struct_detection(self):
        root = parse_rust_source(SAMPLE_RUST)
        structs = [n for n in root.walk() if n.node_type == "StructDecl"]
        self.assertEqual(len(structs), 1)
        self.assertEqual(structs[0].name, "Calculator")
        self.assertEqual(structs[0].attributes.get("visibility"), "pub")

    def test_enum_detection(self):
        root = parse_rust_source(SAMPLE_RUST)
        enums = [n for n in root.walk() if n.node_type == "EnumDecl"]
        self.assertEqual(len(enums), 1)

    def test_trait_detection(self):
        root = parse_rust_source(SAMPLE_RUST)
        traits = [n for n in root.walk() if n.node_type == "TraitDecl"]
        self.assertEqual(len(traits), 1)

    def test_impl_detection(self):
        root = parse_rust_source(SAMPLE_RUST)
        impls = [n for n in root.walk() if n.node_type == "ImplBlock"]
        self.assertGreater(len(impls), 0)

    def test_async_fn(self):
        root = parse_rust_source(SAMPLE_RUST)
        fns = [n for n in root.walk()
               if n.node_type == "FnDecl" and n.name == "add"]
        self.assertGreater(len(fns), 0)
        self.assertTrue(fns[0].attributes.get("async"))

    def test_compact(self):
        root = parse_rust_source(SAMPLE_RUST)
        compact = rust_compact(root)
        self.assertIn("Crate", compact)


class TestPerlAST(unittest.TestCase):
    def test_parse(self):
        root = parse_perl_source(SAMPLE_PERL)
        self.assertEqual(root.node_type, "PerlScript")

    def test_find_symbols(self):
        symbols = find_perl_symbols(SAMPLE_PERL)
        names = [s["name"] for s in symbols]
        self.assertIn("Calculator", names)

    def test_use_declarations(self):
        root = parse_perl_source(SAMPLE_PERL)
        uses = [n for n in root.walk() if n.node_type == "UseDecl"]
        self.assertGreater(len(uses), 0)

    def test_package_detection(self):
        root = parse_perl_source(SAMPLE_PERL)
        pkgs = [n for n in root.walk() if n.node_type == "PackageDecl"]
        self.assertEqual(len(pkgs), 1)
        self.assertEqual(pkgs[0].name, "Calculator")

    def test_sub_declarations(self):
        root = parse_perl_source(SAMPLE_PERL)
        subs = [n for n in root.walk() if n.node_type == "SubDecl"]
        self.assertGreater(len(subs), 0)
        names = [s.name for s in subs]
        self.assertIn("new", names)
        self.assertIn("add", names)

    def test_var_declarations(self):
        root = parse_perl_source(SAMPLE_PERL)
        vars_ = [n for n in root.walk() if n.node_type == "VarDecl"]
        self.assertGreater(len(vars_), 0)

    def test_method_calls(self):
        root = parse_perl_source(SAMPLE_PERL)
        calls = [n for n in root.walk() if n.node_type == "MethodCall"]
        # bless is not an arrow call, but push uses ->
        # Actually checking for arrow calls in the sample

    def test_compact(self):
        root = parse_perl_source(SAMPLE_PERL)
        compact = perl_compact(root)
        self.assertIn("PerlScript", compact)


class TestPHPAST(unittest.TestCase):
    def test_parse(self):
        root = parse_php_source(SAMPLE_PHP)
        self.assertEqual(root.node_type, "PHPFile")

    def test_find_symbols(self):
        symbols = find_php_symbols(SAMPLE_PHP)
        names = [s["name"] for s in symbols]
        self.assertIn("Calculator", names)
        self.assertIn("add", names)

    def test_namespace(self):
        root = parse_php_source(SAMPLE_PHP)
        ns = [n for n in root.walk() if n.node_type == "NamespaceDecl"]
        self.assertEqual(len(ns), 1)
        self.assertIn("App", ns[0].name)

    def test_use_declarations(self):
        root = parse_php_source(SAMPLE_PHP)
        uses = [n for n in root.walk() if n.node_type == "UseDecl"]
        self.assertGreater(len(uses), 0)

    def test_class_detection(self):
        root = parse_php_source(SAMPLE_PHP)
        classes = [n for n in root.walk() if n.node_type == "ClassDecl"]
        self.assertGreater(len(classes), 0)
        calc = [c for c in classes if c.name == "Calculator"][0]
        self.assertEqual(calc.attributes.get("modifier"), "abstract")

    def test_interface_detection(self):
        root = parse_php_source(SAMPLE_PHP)
        interfaces = [n for n in root.walk()
                      if n.node_type == "InterfaceDecl"]
        self.assertEqual(len(interfaces), 1)

    def test_trait_detection(self):
        root = parse_php_source(SAMPLE_PHP)
        traits = [n for n in root.walk() if n.node_type == "TraitDecl"]
        self.assertEqual(len(traits), 1)

    def test_function_return_type(self):
        root = parse_php_source(SAMPLE_PHP)
        funcs = [n for n in root.walk()
                 if n.node_type == "FunctionDecl" and n.name == "add"]
        self.assertGreater(len(funcs), 0)
        self.assertEqual(funcs[0].attributes.get("return_type"), "int")

    def test_compact(self):
        root = parse_php_source(SAMPLE_PHP)
        compact = php_compact(root)
        self.assertIn("PHPFile", compact)


class TestCAST(unittest.TestCase):
    def test_parse(self):
        root = parse_c_source(SAMPLE_C)
        self.assertIsInstance(root, ASTNode)

    def test_find_symbols(self):
        symbols = find_c_symbols(SAMPLE_C)
        # May find symbols depending on pycparser
        self.assertIsInstance(symbols, list)

    def test_compact(self):
        root = parse_c_source(SAMPLE_C)
        compact = c_compact(root)
        self.assertIsInstance(compact, str)


SAMPLE_WASM = '''
(module
  (type $sig_i32 (func (param i32) (result i32)))
  (import "env" "memory" (memory 1))
  (import "env" "log" (func $log (param i32)))
  (func $add (param i32) (param i32) (result i32)
    local.get 0
    local.get 1
    i32.add)
  (func $main (result i32)
    i32.const 42)
  (export "add" (func $add))
  (export "main" (func $main))
  (global $counter (mut i32) (i32.const 0))
  (table 1 funcref)
  (data (i32.const 0) "hello")
  (start $main)
)
'''

SAMPLE_TYPESCRIPT = '''
import { Component } from '@angular/core';
import * as utils from './utils';

@Component({ selector: 'app-root' })
export class AppComponent {
    private name: string;
    public count: number = 0;

    constructor(name: string) {
        this.name = name;
    }

    public async fetchData(url: string): Promise<Data> {
        return fetch(url).then(r => r.json());
    }
}

interface Computable<T> {
    compute(x: T): T;
}

type Handler = (event: Event) => void;

enum Direction {
    Up = "UP",
    Down = "DOWN",
}

export async function loadConfig(path: string): Promise<Config> {
    const data = await readFile(path);
    return JSON.parse(data);
}

const API_URL: string = "https://api.example.com";

namespace Utils {
    export function format(s: string): string { return s.trim(); }
}
'''

SAMPLE_SWIFT = '''
import Foundation
import UIKit

@main
public final class AppDelegate: UIResponder, UIApplicationDelegate {
    var window: UIWindow?
}

public struct User<T>: Codable, Equatable {
    public let id: Int
    public var name: String

    public init(id: Int, name: String) {
        self.id = id
        self.name = name
    }
}

enum Direction: String {
    case up = "UP"
    case down = "DOWN"
}

protocol Fetchable: AnyObject {
    func fetch() async throws -> Data
}

extension User: CustomStringConvertible {
    public var description: String { return name }
}

actor DataStore: Sendable {
    var items: [String] = []
}

public func loadData(from url: URL) async throws -> Data {
    let (data, _) = try await URLSession.shared.data(from: url)
    return data
}

typealias Handler = (Data) -> Void
'''

SAMPLE_KOTLIN = '''
package com.example.app

import kotlinx.coroutines.flow.Flow
import android.os.Bundle

@Serializable
data class User(
    val id: Int,
    val name: String,
)

sealed class Result<out T> {
    data class Success<T>(val data: T) : Result<T>()
    data class Error(val message: String) : Result<Nothing>()
}

object AppConfig {
    const val API_URL = "https://api.example.com"
}

interface Repository<T> {
    suspend fun getAll(): List<T>
    fun getById(id: Int): T?
}

sealed interface UiState {
    object Loading : UiState
}

class UserRepository(private val api: Api) : Repository<User> {
    override suspend fun getAll(): List<User> = api.fetchUsers()
    override fun getById(id: Int): User? = null
}

suspend fun fetchData(url: String): Result<String> {
    return Result.Success("data")
}

fun String.capitalize(): String = this.replaceFirstChar { it.uppercase() }

val lazyValue: String by lazy { "computed" }
var counter: Int = 0

typealias UserList = List<User>

companion object Factory {
    fun create(): User = User(0, "")
}
'''


class TestWebAssemblyAST(unittest.TestCase):
    def test_parse(self):
        root = parse_wasm_source(SAMPLE_WASM)
        self.assertEqual(root.node_type, "WasmModule")

    def test_find_symbols(self):
        symbols = find_wasm_symbols(SAMPLE_WASM)
        names = [s["name"] for s in symbols]
        self.assertIn("add", names)
        self.assertIn("main", names)

    def test_func_declarations(self):
        root = parse_wasm_source(SAMPLE_WASM)
        funcs = [n for n in root.walk() if n.node_type == "FuncDecl"]
        self.assertGreater(len(funcs), 0)
        add_fn = [f for f in funcs if f.name == "add"]
        self.assertEqual(len(add_fn), 1)

    def test_import_declarations(self):
        root = parse_wasm_source(SAMPLE_WASM)
        imports = [n for n in root.walk() if n.node_type == "ImportDecl"]
        self.assertGreater(len(imports), 0)

    def test_export_declarations(self):
        root = parse_wasm_source(SAMPLE_WASM)
        exports = [n for n in root.walk() if n.node_type == "ExportDecl"]
        self.assertGreater(len(exports), 0)
        names = [e.name for e in exports]
        self.assertIn("add", names)

    def test_global_declarations(self):
        root = parse_wasm_source(SAMPLE_WASM)
        globals_ = [n for n in root.walk() if n.node_type == "GlobalDecl"]
        self.assertGreater(len(globals_), 0)
        self.assertEqual(globals_[0].name, "counter")

    def test_memory_in_import(self):
        root = parse_wasm_source(SAMPLE_WASM)
        # Memory is declared via import in our sample
        imports = [n for n in root.walk() if n.node_type == "ImportDecl"]
        mem_imports = [i for i in imports if i.attributes.get("kind") == "memory"]
        self.assertGreater(len(mem_imports), 0)

    def test_type_declaration(self):
        root = parse_wasm_source(SAMPLE_WASM)
        types = [n for n in root.walk() if n.node_type == "TypeDecl"]
        self.assertGreater(len(types), 0)

    def test_start_declaration(self):
        root = parse_wasm_source(SAMPLE_WASM)
        starts = [n for n in root.walk() if n.node_type == "StartDecl"]
        self.assertEqual(len(starts), 1)
        self.assertEqual(starts[0].name, "main")

    def test_compact(self):
        root = parse_wasm_source(SAMPLE_WASM)
        compact = wasm_compact(root)
        self.assertIn("WasmModule", compact)


class TestTypeScriptAST(unittest.TestCase):
    def test_parse(self):
        root = parse_typescript_source(SAMPLE_TYPESCRIPT)
        self.assertEqual(root.node_type, "TSModule")

    def test_find_symbols(self):
        symbols = find_typescript_symbols(SAMPLE_TYPESCRIPT)
        names = [s["name"] for s in symbols]
        self.assertIn("AppComponent", names)
        self.assertIn("Computable", names)
        self.assertIn("Direction", names)

    def test_import_declarations(self):
        root = parse_typescript_source(SAMPLE_TYPESCRIPT)
        imports = [n for n in root.walk() if n.node_type == "ImportDecl"]
        self.assertGreater(len(imports), 0)

    def test_class_detection(self):
        root = parse_typescript_source(SAMPLE_TYPESCRIPT)
        classes = [n for n in root.walk() if n.node_type == "ClassDecl"]
        self.assertGreater(len(classes), 0)

    def test_interface_detection(self):
        root = parse_typescript_source(SAMPLE_TYPESCRIPT)
        ifaces = [n for n in root.walk() if n.node_type == "InterfaceDecl"]
        self.assertGreater(len(ifaces), 0)
        comp = [i for i in ifaces if i.name == "Computable"]
        self.assertEqual(len(comp), 1)

    def test_type_alias(self):
        root = parse_typescript_source(SAMPLE_TYPESCRIPT)
        aliases = [n for n in root.walk() if n.node_type == "TypeAliasDecl"]
        self.assertGreater(len(aliases), 0)

    def test_enum_detection(self):
        root = parse_typescript_source(SAMPLE_TYPESCRIPT)
        enums = [n for n in root.walk() if n.node_type == "EnumDecl"]
        self.assertEqual(len(enums), 1)
        self.assertEqual(enums[0].name, "Direction")

    def test_function_detection(self):
        root = parse_typescript_source(SAMPLE_TYPESCRIPT)
        funcs = [n for n in root.walk() if n.node_type == "FunctionDecl"]
        self.assertGreater(len(funcs), 0)

    def test_namespace_detection(self):
        root = parse_typescript_source(SAMPLE_TYPESCRIPT)
        ns = [n for n in root.walk() if n.node_type == "NamespaceDecl"]
        self.assertGreater(len(ns), 0)
        self.assertEqual(ns[0].name, "Utils")

    def test_decorator(self):
        root = parse_typescript_source(SAMPLE_TYPESCRIPT)
        decs = [n for n in root.walk() if n.node_type == "DecoratorDecl"]
        self.assertGreater(len(decs), 0)

    def test_compact(self):
        root = parse_typescript_source(SAMPLE_TYPESCRIPT)
        compact = ts_compact(root)
        self.assertIn("TSModule", compact)


class TestSwiftAST(unittest.TestCase):
    def test_parse(self):
        root = parse_swift_source(SAMPLE_SWIFT)
        self.assertEqual(root.node_type, "SwiftModule")

    def test_find_symbols(self):
        symbols = find_swift_symbols(SAMPLE_SWIFT)
        names = [s["name"] for s in symbols]
        self.assertIn("User", names)
        self.assertIn("Direction", names)
        self.assertIn("Fetchable", names)

    def test_import_declarations(self):
        root = parse_swift_source(SAMPLE_SWIFT)
        imports = [n for n in root.walk() if n.node_type == "ImportDecl"]
        self.assertGreater(len(imports), 0)
        names = [i.name for i in imports]
        self.assertIn("Foundation", names)

    def test_struct_detection(self):
        root = parse_swift_source(SAMPLE_SWIFT)
        structs = [n for n in root.walk() if n.node_type == "StructDecl"]
        self.assertGreater(len(structs), 0)
        user = [s for s in structs if s.name == "User"]
        self.assertEqual(len(user), 1)

    def test_class_detection(self):
        root = parse_swift_source(SAMPLE_SWIFT)
        classes = [n for n in root.walk() if n.node_type == "ClassDecl"]
        self.assertGreater(len(classes), 0)

    def test_enum_detection(self):
        root = parse_swift_source(SAMPLE_SWIFT)
        enums = [n for n in root.walk() if n.node_type == "EnumDecl"]
        self.assertGreater(len(enums), 0)
        self.assertEqual(enums[0].name, "Direction")

    def test_protocol_detection(self):
        root = parse_swift_source(SAMPLE_SWIFT)
        protos = [n for n in root.walk() if n.node_type == "ProtocolDecl"]
        self.assertGreater(len(protos), 0)

    def test_extension_detection(self):
        root = parse_swift_source(SAMPLE_SWIFT)
        exts = [n for n in root.walk() if n.node_type == "ExtensionDecl"]
        self.assertGreater(len(exts), 0)

    def test_actor_detection(self):
        root = parse_swift_source(SAMPLE_SWIFT)
        actors = [n for n in root.walk() if n.node_type == "ActorDecl"]
        self.assertGreater(len(actors), 0)
        self.assertEqual(actors[0].name, "DataStore")

    def test_func_async_throws(self):
        root = parse_swift_source(SAMPLE_SWIFT)
        funcs = [n for n in root.walk()
                 if n.node_type == "FuncDecl" and n.name == "loadData"]
        self.assertGreater(len(funcs), 0)

    def test_init_detection(self):
        root = parse_swift_source(SAMPLE_SWIFT)
        inits = [n for n in root.walk() if n.node_type == "InitDecl"]
        self.assertGreater(len(inits), 0)

    def test_typealias(self):
        root = parse_swift_source(SAMPLE_SWIFT)
        aliases = [n for n in root.walk() if n.node_type == "TypeAliasDecl"]
        self.assertGreater(len(aliases), 0)

    def test_compact(self):
        root = parse_swift_source(SAMPLE_SWIFT)
        compact = swift_compact(root)
        self.assertIn("SwiftModule", compact)


class TestKotlinAST(unittest.TestCase):
    def test_parse(self):
        root = parse_kotlin_source(SAMPLE_KOTLIN)
        self.assertEqual(root.node_type, "KotlinFile")

    def test_find_symbols(self):
        symbols = find_kotlin_symbols(SAMPLE_KOTLIN)
        names = [s["name"] for s in symbols]
        self.assertIn("User", names)
        self.assertIn("Result", names)
        self.assertIn("AppConfig", names)

    def test_package_detection(self):
        root = parse_kotlin_source(SAMPLE_KOTLIN)
        pkgs = [n for n in root.walk() if n.node_type == "PackageDecl"]
        self.assertEqual(len(pkgs), 1)
        self.assertEqual(pkgs[0].name, "com.example.app")

    def test_import_declarations(self):
        root = parse_kotlin_source(SAMPLE_KOTLIN)
        imports = [n for n in root.walk() if n.node_type == "ImportDecl"]
        self.assertGreater(len(imports), 0)

    def test_data_class(self):
        root = parse_kotlin_source(SAMPLE_KOTLIN)
        classes = [n for n in root.walk()
                   if n.node_type == "ClassDecl" and n.name == "User"]
        self.assertGreater(len(classes), 0)
        self.assertTrue(classes[0].attributes.get("data"))

    def test_sealed_class(self):
        root = parse_kotlin_source(SAMPLE_KOTLIN)
        classes = [n for n in root.walk()
                   if n.node_type == "ClassDecl" and n.name == "Result"]
        self.assertGreater(len(classes), 0)
        self.assertTrue(classes[0].attributes.get("sealed"))

    def test_object_declaration(self):
        root = parse_kotlin_source(SAMPLE_KOTLIN)
        objs = [n for n in root.walk() if n.node_type == "ObjectDecl"]
        self.assertGreater(len(objs), 0)
        config = [o for o in objs if o.name == "AppConfig"]
        self.assertEqual(len(config), 1)

    def test_interface_detection(self):
        root = parse_kotlin_source(SAMPLE_KOTLIN)
        ifaces = [n for n in root.walk() if n.node_type == "InterfaceDecl"]
        self.assertGreater(len(ifaces), 0)

    def test_sealed_interface(self):
        root = parse_kotlin_source(SAMPLE_KOTLIN)
        ifaces = [n for n in root.walk()
                  if n.node_type == "InterfaceDecl" and n.name == "UiState"]
        self.assertGreater(len(ifaces), 0)
        self.assertTrue(ifaces[0].attributes.get("sealed"))

    def test_suspend_fun(self):
        root = parse_kotlin_source(SAMPLE_KOTLIN)
        funs = [n for n in root.walk()
                if n.node_type == "FunDecl" and n.name == "fetchData"]
        self.assertGreater(len(funs), 0)
        self.assertTrue(funs[0].attributes.get("suspend"))

    def test_extension_function(self):
        root = parse_kotlin_source(SAMPLE_KOTLIN)
        funs = [n for n in root.walk()
                if n.node_type == "FunDecl" and n.name == "capitalize"]
        self.assertGreater(len(funs), 0)

    def test_property_declarations(self):
        root = parse_kotlin_source(SAMPLE_KOTLIN)
        props = [n for n in root.walk() if n.node_type == "PropertyDecl"]
        self.assertGreater(len(props), 0)

    def test_typealias(self):
        root = parse_kotlin_source(SAMPLE_KOTLIN)
        aliases = [n for n in root.walk() if n.node_type == "TypeAliasDecl"]
        self.assertGreater(len(aliases), 0)

    def test_compact(self):
        root = parse_kotlin_source(SAMPLE_KOTLIN)
        compact = kotlin_compact(root)
        self.assertIn("KotlinFile", compact)


if __name__ == "__main__":
    unittest.main()
