from src.util.errors import LoxRuntimeError


class LoxInstance:
    def __init__(self, klass):
        self.klass = klass
        self.fields = {}

    def get(self, name):
        if name.lexeme in self.fields.keys():
            return self.fields.get(name.lexeme)

        method = self.klass.find_method(name.lexeme)
        if method != None:
            return method.bind(self)

        raise LoxRuntimeError(name, f"Undefined Property '{name.lexeme}'.")

    def set_(self, name, value):
        self.fields[name.lexeme] = value

    def __str__(self):
        return f"<Instance of : {self.klass.name}>"
