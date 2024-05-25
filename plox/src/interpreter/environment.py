# Project Imports
from src.scanner.token import Token
from src.util.errors import LoxRuntimeError


# Environment
class Environment:
    def __init__(self, enclosing = None):
        self.enclosing = enclosing
        self.values = {}
        self.constants = {}

    def get(self, name: Token):
        if name.lexeme in self.values.keys():
            return self.values[name.lexeme]

        if name.lexeme in self.constants.keys():
            return self.constants[name.lexeme]

        if self.enclosing != None:
            return self.enclosing.get(name)

        raise LoxRuntimeError(name, f"Undefined Variable '{name.lexeme}'.")

    def get_at(self, distance: int, name: str):
        return self.ancestor(distance).values[name]

    def assign(self, name: Token, value: object):
        if name.lexeme in self.values.keys():
            self.values[name.lexeme] = value
            return

        if name.lexeme in self.constants.keys():
            raise LoxRuntimeError(name, "Cannot reassign a constant.")

        if self.enclosing != None:
            self.enclosing.assign(name, value)
            return

        raise LoxRuntimeError(name, f"Undefined Variable '{name.lexeme}'.")

    def assign_at(self, distance: int, name: Token, value: object):
        self.ancestor(distance).values[name.lexeme] = value

    def define(self, name: str, value: object):
        self.values[name] = value

    def define_const(self, name: str, value: object):
        self.constants[name] = value

    def ancestor(self, distance):
        environment = self
        for i in range(distance):
            environment = environment.enclosing

        return environment
