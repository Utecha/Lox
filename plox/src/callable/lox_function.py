from src.callable.lox_callable import LoxCallable
from src.interpreter.environment import Environment
from src.util.exceptions import ReturnException


class LoxFunction(LoxCallable):
    def __init__(self, declaration, closure):
        self.closure = closure
        self.declaration = declaration

    def arity(self):
        return len(self.declaration.params)

    def call(self, interpreter, arguments):
        environment = Environment(self.closure)

        for i in range(len(self.declaration.params)):
            environment.define(
                self.declaration.params[i].lexeme,
                arguments[i]
            )

        try:
            interpreter.execute_block(self.declaration.body, environment)
        except ReturnException as returnValue:
            return returnValue.value

    def __str__(self):
        return f"<User Fn - {self.declaration.callee.name.lexeme}>"
