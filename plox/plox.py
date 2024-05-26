#!/usr/bin/env python3

# Python Imports
import sys

# Project Imports
from src.ast.printer import AstPrinter
from src.interpreter.interpreter import Interpreter
from src.parser.parser import Parser
from src.parser.resolver import Resolver
from src.scanner.scanner import Scanner
from src.util.errors import ErrType, LoxError
from src.util.mode import RunMode


class Lox:
    def __init__(self, file_name="STDIN"):
        self.fn = file_name
        self.debug = False
        self.err_manager = LoxError()
        self.mode = RunMode.FILE
        self.interpreter = Interpreter(self.err_manager, self.mode)

    def run_file(self, file_path):
        try:
            with open(file_path, "rt") as f:
                source = f.read()

            self.run(source)

            if self.err_manager.had_error:
                sys.exit(65)
            if self.err_manager.had_runtime_error:
                sys.exit(70)

        except FileNotFoundError as e:
            print(e)
            self.err_manager.error(ErrType.IO_ERROR, f" {e}"[10:])

    def repl(self):
        if self.debug:
            print("plox REPL Version 0.0.1 [DEBUG MODE]")
            print("Lang Version 0.0.5")
        else:
            print("plox REPL Version 0.0.1")
            print("Lang Version 0.0.5")
        print("Press Ctrl-D to quit.")

        try:
            while True:
                line = input(">>> ")

                if line == "exit":
                    break

                self.run(line)

                self.err_manager.had_error = False
                self.err_manager.had_runtime_error = False

        except EOFError:
            print()
            sys.exit(0)

        except KeyboardInterrupt:
            print()
            sys.exit(0)

    def run(self, source):
        # Lexer
        scanner = Scanner(source, self.err_manager)
        tokens = scanner.scan_tokens()

        if self.err_manager.had_error:
            return

        # Parser
        parser = Parser(tokens, self.err_manager)
        statements = parser.parse()

        if self.err_manager.had_error:
            if self.debug:
                for token in tokens:
                    print(token, file=sys.stderr)
            return

        if self.debug:
            printer = AstPrinter()
            for token in tokens:
                print(token, file=sys.stderr)

            for statement in statements:
                printer.print_stmt(statement)
        else:
            resolver = Resolver(self.interpreter, self.err_manager)
            resolver.resolve_stmts(statements)

            if self.err_manager.had_error:
                return

            self.interpreter.mode = self.mode
            self.interpreter.interpret(statements)


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser(prog="plox.py")
    lox = Lox()

    parser.add_argument(
        "script",
        nargs="?",
        default=None,
        help="Source file ending in .lox"
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Run in Debug Mode. Spits out results of " + \
             "lexer and parser, suppressing interpretation."
    )

    args = parser.parse_args()

    if args.debug:
        lox.debug = True
    else:
        lox.debug = False

    if args.script is not None:
        lox.run_file(args.script)
    else:
        lox.mode = RunMode.REPL
        lox.repl()
