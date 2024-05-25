from src.scanner.token import Token, TokenType


class Scanner:
    def __init__(self, source, err_manager):
        self.source = source
        self.err_manager = err_manager
        self.tokens = []

        self.start = 0
        self.current = 0
        self.line = 1

        self.keywords = {
            "and": TokenType.AND,
            "break": TokenType.BREAK,
            "class": TokenType.CLASS,
            "continue": TokenType.CONTINUE,
            "const": TokenType.CONST,
            "echo": TokenType.ECHO,
            "else": TokenType.ELSE,
            "false": TokenType.FALSE,
            "for": TokenType.FOR,
            "fun": TokenType.FUN,
            "fn": TokenType.FN,
            "if": TokenType.IF,
            "let": TokenType.LET,
            "null": TokenType.NULL,
            "or": TokenType.OR,
            "print" : TokenType.PRINT,
            "return": TokenType.RETURN,
            "self": TokenType.SELF,
            "super": TokenType.SUPER,
            "this": TokenType.THIS,
            "true": TokenType.TRUE,
            "var": TokenType.VAR,
            "while": TokenType.WHILE,
        }

    def scan_tokens(self):
        while not self.is_at_end():
            self.start = self.current
            self.scan_token()

        self.tokens.append(Token(TokenType.EOF, "", None, self.line))
        return self.tokens

    def scan_token(self):
        c = self.advance()

        match c:
            # Whitespace
            case ' ': return
            case '\r': return
            case '\t': return
            case '\n':
                self.line += 1
                return

            # Symbol Tokens
            case '(':
                self.add_token(TokenType.LPAREN)
                return
            case ')':
                self.add_token(TokenType.RPAREN)
                return
            case '{':
                self.add_token(TokenType.LBRACE)
                return
            case '}':
                self.add_token(TokenType.RBRACE)
                return
            case ',':
                self.add_token(TokenType.COMMA)
                return
            case '.':
                self.add_token(TokenType.DOT)
                return
            case '?':
                self.add_token(TokenType.QUESTION)
                return
            case ':':
                self.add_token(TokenType.COLON)
                return
            case ';':
                self.add_token(TokenType.SEMICOLON)
                return

            # Arithmetic Tokens
            case '-':
                self.add_token(
                    TokenType.MINUSEQ if self.match('=') else TokenType.MINUS
                )
                return
            case '%':
                self.add_token(
                    TokenType.MODEQ if self.match('=') else TokenType.MODULUS
                )
                return
            case '+':
                self.add_token(
                    TokenType.PLUSEQ if self.match('=') else TokenType.PLUS
                )
                return
            case '*':
                if self.match('*'):
                    self.add_token(TokenType.POWER)

                elif self.match('='):
                    self.add_token(TokenType.STAREQ)

                else:
                    self.add_token(TokenType.STAR)
                return
            case '/':
                if self.match('/'):
                    while self.peek() != '\n' and not self.is_at_end():
                        self.advance()

                elif self.match('*'):
                    while True:
                        if self.is_at_end():
                            self.err_manager.scan_error(
                                self.line, c, "Unterminated comment block.")
                            break

                        if self.peek() == '\n':
                            self.line += 1

                        if self.peek() == '*' and self.peek_next() == '/':
                            self.advance()
                            self.advance()
                            break

                        self.advance()

                elif self.match('='):
                    self.add_token(TokenType.SLASHEQ)

                else:
                    self.add_token(TokenType.SLASH)
                return

            # Logical Tokens
            case '&':
                if self.match('&'):
                    self.add_token(TokenType.AND)
                else:
                    self.err_manager.scan_error(self.line, c, "Unexpected Character")
                return
            case '|':
                if self.match('|'):
                    self.add_token(TokenType.OR)
                else:
                    self.err_manager.scan_error(self.line, c, "Unexpected Character")
                return

            # Equality Tokens
            case '!':
                self.add_token(
                    TokenType.BANGEQ if self.match('=') else TokenType.BANG
                )
                return
            case '=':
                self.add_token(
                    TokenType.EQEQ if self.match('=') else TokenType.EQ
                )
                return

            # Comparison Tokens
            case '>':
                self.add_token(
                    TokenType.GTEQ if self.match('=') else TokenType.GT
                )
                return
            case '<':
                self.add_token(
                    TokenType.LTEQ if self.match('=') else TokenType.LT
                )
                return

            # Other
            case '"':
                self.string()
                return
            case _:
                if c.isdigit():
                    self.number()
                elif c.isalpha():
                    self.identifier()
                else:
                    self.err_manager.scan_error(
                        self.line,
                        c,
                        "Unexpected Character"
                    )
                return

    def identifier(self):
        while self.peek().isalnum():
            self.advance()

        text = self.source[self.start: self.current]
        type_ = None

        if text in self.keywords.keys():
            type_ = self.keywords[text]
        else:
            type_ = TokenType.IDENTIFIER

        self.add_token(type_)

    def number(self):
        while self.peek().isdigit():
            self.advance()

        if self.peek() == '.' and self.peek_next().isdigit():
            self.advance()

            while self.peek().isdigit():
                self.advance()

        self.add_token(
            TokenType.NUMBER,
            float(self.source[self.start: self.current])
        )

    def string(self):
        while self.peek() != '"' and not self.is_at_end():
            if self.peek() == '\n':
                self.line += 1

            self.advance()

        if self.is_at_end():
            self.err_manager.scan_error(
                self.line,
                self.peek(),
                "Unterminated String."
            )
            return

        self.advance()

        value = self.source[self.start + 1: self.current - 1]
        self.add_token(TokenType.STRING, value)

    def add_token(self, type_, literal=None):
        lexeme = self.source[self.start: self.current]
        self.tokens.append(Token(type_, lexeme, literal, self.line))

    def is_at_end(self):
        return self.current >= len(self.source)

    def advance(self):
        if self.is_at_end():
            return '\0'

        char = self.source[self.current]

        self.current += 1
        return char

    def peek(self):
        if self.is_at_end():
            return '\0'

        return self.source[self.current]

    def peek_next(self):
        if self.current + 1 >= len(self.source):
            return '\0'

        return self.source[self.current + 1]

    def match(self, char):
        if self.is_at_end():
            return False

        if self.source[self.current] != char:
            return False

        self.current += 1
        return True
