#!/usr/bin/env python3

import sys
sys.path.append("..")

from plox.src.util.writer import Writer


class AstGenerator:
    def defineAst(self, output_dir, basename, types):
        path = f"{output_dir}/{basename.lower()}.py"
        writer = Writer(path)
        print(f"Generating {basename} AST -> {path}")

        self.define_imports(writer, basename)
        self.define_base_class(writer, basename)
        self.define_visitor(writer, path, basename, types)

        for type_ in types:
            classname = type_.split("|")[0].strip()
            fields = type_.split("|")[1].strip()
            self.define_type(writer, basename, classname, fields)

        writer.write()
        print(f"{basename} AST Generation complete.")

    def define_imports(self, writer, basename):
        writer.addln("# Python Imports")
        writer.addln("from abc import ABC, abstractmethod")
        writer.addln()

        writer.addln("# Project Imports")
        if basename == "Stmt":
            writer.addln("from src.ast.expr import Expr")

        writer.addln("from src.scanner.token import Token")
        writer.addln()

    def define_base_class(self, writer, basename):
        writer.addln()
        writer.addln(f"class {basename}(ABC):")
        writer.addln("    @abstractmethod")
        writer.addln("    def accept(self, visitor):")
        writer.addln("        ...")
        writer.addln()

    def define_type(self, writer, basename, classname, field_list):
        writer.addln()
        writer.addln(f"class {classname}({basename}):")
        writer.add("    def __init__(self")

        if not field_list:
            writer.addln("):")
            writer.addln("        pass")
        else:
            writer.addln(f", {field_list}):")

            fields = field_list.split(", ")

            for field in fields:
                name = field.split(":")[0].strip()
                writer.addln(f"        self.{name} = {name}")

        writer.addln()
        if basename == "Stmt":
            writer.addln("    def accept(self, visitor: StmtVisitor):")
        else:
            writer.addln("    def accept(self, visitor: ExprVisitor):")

        writer.add(f"        return visitor.visit_{classname.lower()}_")
        writer.addln(f"{basename.lower()}(self)")
        writer.addln()

    def define_visitor(self, writer, path, basename, types):
        print(f"Generating {basename} Visitor Patterns -> {path}")
        writer.addln()
        writer.addln(f"class {basename}Visitor(ABC):")

        for type_ in types:
            typename = type_.split("|")[0].strip()
            writer.addln("    @abstractmethod")
            writer.add(f"    def visit_{typename.lower()}_{basename.lower()}")
            writer.add(f"(self, {basename.lower()}: {basename})")
            if basename == "Stmt":
                writer.addln(f" -> None:")
            else:
                writer.addln(f" -> object | None:")

            writer.addln("        ...")
            writer.addln()

        print(f"{basename} Visitor Pattern generation complete.")


if __name__ == "__main__":
    exec, *argv = sys.argv
    generator = AstGenerator()

    if len(argv) != 1:
        print(f"Usage: {exec} <output directory>")
        sys.exit(64)

    output_dir = argv[0]

    generator.defineAst(
        output_dir,
        "Expr",
        [
            "Assign         | name: Token, operator: Token, value: Expr",
            "Binary         | left: Expr, operator: Token, right: Expr",
            "Call           | callee: Expr, paren: Token, arguments: list[Expr]",
            "Conditional    | condition: Expr, then_branch: Expr, else_branch: Expr",
            "Get            | obj: Expr, name: Token",
            "Grouping       | expression: Expr",
            "Literal        | value: object",
            "Logical        | left: Expr, operator: Token, right: Token",
            "Self           | keyword: Token",
            "Set            | obj: Expr, name: Token, value: Expr",
            "Super          | keyword: Token, method: Token",
            "Unary          | operator: Token, right: Expr",
            "Variable       | name: Token"
        ]
    )

    generator.defineAst(
        output_dir,
        "Stmt",
        [
            "Block          | statements: list[Stmt]",
            "Break          | keyword: Token",
            "Class          | name: Token, superclass: Expr, methods: list[Stmt]",
            "Const          | name: Token, initializer: Expr",
            "Continue       | keyword: Token",
            "Echo           | expression: Expr",
            "Expression     | expression: Expr",
            "For            | initializer: Stmt, condition: Expr, increment: Expr, body: Stmt",
            "Function       | name: Token, params: list[Token], body: list[Stmt]",
            "If             | condition: Expr, then_branch: Stmt, else_branch: Stmt",
            "Return         | keyword: Token, value: Expr",
            "Var            | name: Token, keyword: Token, initializer: Expr",
            "While          | condition: Expr, body: Stmt",
        ]
    )
