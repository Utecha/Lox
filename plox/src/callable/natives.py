# Python Imports
import time

# Project Imports
from src.callable.lox_callable import LoxCallable


class Clock(LoxCallable):
    def arity(self):
        return 0

    def call(self, interpreter, arguments):
        return time.time()

    def __str__(self):
        return "<Native Fn - clock>"


def define_natives(interpreter):
    interpreter.globals.define_const("clock", Clock())
