from src.callable.lox_callable import LoxCallable
from src.callable.lox_instance import LoxInstance


class LoxClass(LoxCallable):
    def __init__(self, name, superclass, methods):
        self.superclass = superclass
        self.name = name
        self.methods = methods

    def find_method(self, name):
        if name in self.methods.keys():
            return self.methods.get(name)

        if self.superclass != None:
            return self.superclass.find_method(name)

    def arity(self):
        initializer = self.find_method("init")
        if initializer == None:
            initializer = self.find_method(self.name)

        if initializer == None:
            return 0

        return initializer.arity()

    def call(self, interpreter, arguments):
        instance = LoxInstance(self)

        initializer = self.find_method("init")
        if initializer == None:
            initializer = self.find_method(self.name)

        if initializer != None:
            initializer.bind(instance).call(interpreter, arguments)

        return instance

    def __str__(self):
        return f"<Class : {self.name}>"
