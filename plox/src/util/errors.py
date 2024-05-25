from enum import Enum
import sys


class ErrType(Enum):
    ERROR = "ERROR"
    IO_ERROR = "I/O ERROR"
    ARG_ERROR = "ARG ERROR"


class LoxError(BaseException):
    def __init__(self, message = None):
        self.message = message
        self.had_error = False
        self.had_runtime_error = False

    def error(self, type_, message):
        print(f"[{type_.value}] {message}", file=sys.stderr)

    def scan_error(self, line, where, message):
        self.report("scan", line, where, message)

    def parse_error(self, token, message):
        self.report("parse", token.line, f"{token.lexeme}", message)

    def runtime_error(self, error):
        result = f"\n[RUNTIME ERROR]\n{error.message}\n"
        result += f"at [ '{error.token.lexeme}' ]\n"
        result += f"on [ Ln : {error.token.line} ]\n"

        self.had_runtime_error = True
        print(result, file=sys.stderr)

    def report(self, type_, line, where, message):
        result = f"\n[{type_.upper()} ERROR]\n{message}\n"
        result += f"at [ '{where}' ]\n"
        result += f"on [ Ln : {line} ]\n"

        self.had_error = True
        print(result, file=sys.stderr)


class ParseError(LoxError, RuntimeError):
    def __init__(self):
        super().__init__()


class LoxRuntimeError(LoxError, RuntimeError):
    def __init__(self, token, message):
        self.token = token
        self.message = message
        super().__init__(self.message)
