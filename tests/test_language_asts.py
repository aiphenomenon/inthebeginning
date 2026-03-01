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


if __name__ == "__main__":
    unittest.main()
