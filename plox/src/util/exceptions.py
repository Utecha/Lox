from src.util.errors import LoxRuntimeError

class BreakException(RuntimeError):
    def __init__(self, keyword):
        self.keyword = keyword
        super().__init__()

    def __str__(self):
        return f"{self.keyword.lexeme}"


class ContinueException(RuntimeError):
    def __init__(self, keyword):
        self.keyword = keyword
        super().__init__()

    def __str__(self):
        return f"{self.keyword.lexeme}"


class ReturnException(RuntimeError):
    def __init__(self, keyword, value):
        self.keyword = keyword
        self.value = value
        super().__init__()

    def __str__(self):
        return f"{self.keyword.lexeme} {self.value}"
