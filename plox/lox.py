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
    def __init__(self):
        self.file_name = "STDIN"
        self.debug = False
        self.err_manager = LoxError()
        self.mode = RunMode.FILE
        self.interpreter = Interpreter(self.err_manager, self.mode)

    def main(self):
        exec, *argv = sys.argv

        match len(argv):
            case 0:
                self.mode = RunMode.REPL
                self.run_prompt()
            case 1:
                arg, *argv = argv

                if arg == "-d":
                    self.debug = True
                    self.mode = RunMode.REPL

                    self.run_prompt()
                else:
                    self.debug = False
                    self.run_file(arg)
            case 2:
                cmd, *argv = argv
                fp, *argv = argv

                if cmd == "-d":
                    self.debug = True
                    self.run_file(fp)
                else:
                    self.err_manager.error(
                        ErrType.ARG_ERROR,
                        f"Invalid command provided: {cmd}"
                    )
                    self.usage()
                    sys.exit(64)
            case _:
                self.err_manager.error(
                    ErrType.ARG_ERROR,
                    "Too many arguments provided."
                )
                self.usage()
                sys.exit(64)

    def run_file(self, file_path):
        try:
            with open(file_path, "r") as f:
                source = f.read()

            self.run(source)

            if self.err_manager.had_error:
                sys.exit(65)
            if self.err_manager.had_runtime_error:
                sys.exit(70)

        except FileNotFoundError as e:
            print(e)
            self.err_manager.error(ErrType.IO_ERROR, f" {e}"[10:])

    def run_prompt(self):
        if self.debug:
            print("Lox REPL Version 0.0.1 [DEBUG MODE]")
            print("Lang Version 0.0.5")
        else:
            print("Lox REPL Version 0.0.1")
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

    def usage(self):
        print("Usage: ./plox.py *-d <script>")
        print("* Optional command for enabling debugging info for your script.")
        print("  This suppresses the interpreter and prints out the lexical breakdown")
        print("  as well as the AST representation generated by the parser.")


if __name__ == "__main__":
    lox = Lox()
    lox.main()
