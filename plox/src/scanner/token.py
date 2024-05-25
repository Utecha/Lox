from enum import Enum, auto


class TokenType(Enum):
    # Symbol Tokens
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    COMMA = auto()
    DOT = auto()
    QUESTION = auto()
    COLON = auto()
    SEMICOLON = auto()

    # Arithmetic Tokens
    MINUS = auto()
    MODULUS = auto()
    PLUS = auto()
    POWER = auto()
    SLASH = auto()
    STAR = auto()

    # Equality Tokens
    BANGEQ = auto()
    EQEQ = auto()

    # Comparison Tokens
    GT = auto()
    GTEQ = auto()
    LT = auto()
    LTEQ = auto()

    # Logical Tokens
    BANG = auto()

    # Assignment Tokens
    EQ = auto()
    MINUSEQ = auto()
    MODEQ = auto()
    PLUSEQ = auto()
    SLASHEQ = auto()
    STAREQ = auto()

    # Primitive Types
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()

    # Language Built-In Keywords
    AND = auto()
    BREAK = auto()
    CLASS = auto()
    CONTINUE = auto()
    CONST = auto()
    ECHO = auto()
    ELSE = auto()
    FALSE = auto()
    FN = auto()
    FUN = auto()
    FOR = auto()
    IF = auto()
    LET = auto()
    NULL = auto()
    OR = auto()
    PRINT = auto()
    RETURN = auto()
    SELF = auto()
    SUPER = auto()
    THIS = auto()
    TRUE = auto()
    VAR = auto()
    WHILE = auto()

    # Special Tokens
    EOF = auto()


class Token:
    def __init__(self, type_, lexeme, literal, line):
        self.type = type_
        self.lexeme = lexeme
        self.literal = literal
        self.line = line

    def __str__(self):
        result = ""

        if self.type == TokenType.EOF:
            result = f"[ {self.type.name} ]\n"
        else:
            result = f"[ {self.type.name} ]\n"

            if self.type == TokenType.STRING:
                result += f"[ Lexeme : {self.lexeme} ]\n"
            else:
                result += f"[ Lexeme : '{self.lexeme}' ]\n"

            result += f"[ Literal : {self.literal} ]\n"
            result += f"[ Line : {self.line} ]\n"

        return result
