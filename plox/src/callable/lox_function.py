from src.callable.lox_callable import LoxCallable
from src.interpreter.environment import Environment
from src.util.exceptions import ReturnException


class LoxFunction(LoxCallable):
    def __init__(self, declaration, closure, is_init):
        self.is_init = is_init
        self.closure = closure
        self.declaration = declaration

    def bind(self, instance):
        environment = Environment(self.closure)
        environment.define("this", instance)
        environment.define("self", instance)
        return LoxFunction(self.declaration, environment, self.is_init)

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
            if self.is_init:
                return self.closure.get_at(0, "self")

            return returnValue.value

        if self.is_init:
            return self.closure.get_at(0, "self")

    def __str__(self):
        return f"<User Fn - {self.declaration.name.lexeme}>"
