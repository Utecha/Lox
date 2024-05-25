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

        for type_ in types:
            classname = type_.split("|")[0].strip()
            fields = type_.split("|")[1].strip()
            self.define_type(writer, basename, classname, fields)

        self.define_visitor(writer, path, basename, types)

        writer.write()
        print(f"{basename} AST Generation complete.")

    def define_imports(self, writer, basename):
        writer.addln("from abc import ABC, abstractmethod")
        writer.addln()

    def define_base_class(self, writer, basename):
        writer.addln()
        writer.addln(f"class {basename}(ABC):")
        writer.addln("    @abstractmethod")
        writer.addln("    def accept(self, visitor):")
        writer.addln("        pass")
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
                # name = field.split(":")[0].strip()
                writer.addln(f"        self.{field} = {field}")

        writer.addln()
        writer.addln("    def accept(self, visitor):")
        writer.addln(
            f"        return visitor.visit_{classname.lower()}_" +
            f"{basename.lower()}(self)"
        )
        writer.addln()

    def define_visitor(self, writer, path, basename, types):
        print(f"Generating {basename} Visitor Patterns -> {path}")
        writer.addln()
        writer.addln(f"class {basename}Visitor(ABC):")

        for type_ in types:
            typename = type_.split("|")[0].strip()
            writer.addln("    @abstractmethod")
            writer.addln(
                f"    def visit_{typename.lower()}_{basename.lower()}" +
                f"(self, {basename.lower()}: {typename}):"
            )
            writer.addln("        pass")
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
            "Assign         | name, operator, value",
            "Binary         | left, operator, right",
            "Call           | callee, paren, arguments",
            "Conditional    | condition, then_branch, else_branch",
            "Grouping       | expression",
            "Literal        | value",
            "Logical        | left, operator, right",
            "Unary          | operator, right",
            "Variable       | name"
        ]
    )

    generator.defineAst(
        output_dir,
        "Stmt",
        [
            "Block          | statements",
            "Break          | keyword",
            "Const          | name, initializer",
            "Continue       | keyword",
            "Echo           | expression",
            "Expression     | expression",
            "For            | initializer, condition, increment, body",
            "Function       | name, params, body",
            "If             | condition, then_branch, else_branch",
            "Return         | keyword, value",
            "Var            | name, keyword, initializer",
            "While          | condition, body",
        ]
    )
