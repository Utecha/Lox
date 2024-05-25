# Python Imports
import sys

# Project Imports
from src.ast.expr import (
    Assign,
    Binary,
    Call,
    Conditional,
    Grouping,
    Literal,
    Logical,
    Unary,
    Variable
)
from src.ast.stmt import (
    Block,
    Break,
    Const,
    Continue,
    Echo,
    Expression,
    For,
    Function,
    If,
    Return,
    Var,
    While
)
from src.scanner.scanner import TokenType
from src.util.errors import ParseError


class Parser:
    def __init__(self, tokens, err_manager):
        self.tokens = tokens
        self.debug = False
        self.err_manager = err_manager
        self.current = 0
        self.loop_depth = 0

    def parse(self):
        if self.debug:
            print("=== Begin Parser ===", file=sys.stderr)

        statements = []
        while not self.is_at_end():
            statements.append(self.declaration())

        if self.debug:
            print("=== End Parser ===", file=sys.stderr)

        return statements

    def declaration(self):
        if self.debug:
            print("DECLARATION", file=sys.stderr)

        try:
            if self.match(TokenType.CONST):
                return self.const_declaration()

            if self.match(TokenType.FUN, TokenType.FN):
                return self.function("function")

            if self.match(TokenType.LET, TokenType.VAR):
                return self.var_declaration()

            return self.statement()
        except ParseError as e:
            self.synchronize()
            return

    def statement(self):
        if self.debug:
            print("STATEMENT", file=sys.stderr)

        if self.match(TokenType.BREAK):
            return self.break_()

        if self.match(TokenType.CONTINUE):
            return self.continue_()

        if self.match(TokenType.ECHO, TokenType.PRINT):
            return self.echo_statement()

        if self.match(TokenType.FOR):
            return self.for_statement()

        if self.match(TokenType.IF):
            return self.if_statement()

        if self.match(TokenType.LBRACE):
            return Block(self.block())

        if self.match(TokenType.RETURN):
            return self.return_()

        if self.match(TokenType.WHILE):
            return self.while_statement()

        return self.expr_statement()

    def block(self):
        if self.debug:
            print("STMT: BLOCK", file=sys.stderr)

        statements = []

        while not self.check(TokenType.RBRACE) and not self.is_at_end():
            statements.append(self.declaration())

        self.consume(TokenType.RBRACE, "Expected '}' after block.")
        return statements

    def break_(self):
        if self.debug:
            print("EXCEPTION STMT: BREAK", file=sys.stderr)

        keyword = self.previous()

        if self.loop_depth == 0:
            self.error(keyword, "Cannot use 'break' outside of a loop.")

        self.consume(TokenType.SEMICOLON, "Expected ';' after 'break'.")
        return Break(keyword)

    def continue_(self):
        if self.debug:
            print("EXCEPTION STMT: CONTINUE", file=sys.stderr)

        keyword = self.previous()

        if self.loop_depth == 0:
            self.error(keyword, "Cannot use 'continue' outside of a loop.")

        self.consume(TokenType.SEMICOLON, "Expected ';' after 'continue'.")
        return Continue(keyword)

    def const_declaration(self):
        if self.debug:
            print("STMT: CONST DECLARATION", file=sys.stderr)

        keyword = self.previous()
        name = self.consume(TokenType.IDENTIFIER, "Expected constant name.")

        initializer = None
        if self.match(TokenType.EQ):
            initializer = self.expression()

        if initializer == None:
            self.error(self.previous(), "Cannot define a constant uninitialized.")

        self.consume(TokenType.SEMICOLON, "Expected ';' after constant declaration.")
        return Const(name, initializer)

    def echo_statement(self):
        if self.debug:
            print("STMT: ECHO", file=sys.stderr)

        value = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after 'echo' value.")
        return Echo(value)

    def expr_statement(self):
        if self.debug:
            print("STMT: EXPRESSION", file=sys.stderr)

        expr = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after expression.")
        return Expression(expr)

    def for_statement(self):
        if self.debug:
            print("STMT: FOR LOOP", file=sys.stderr)

        self.consume(TokenType.LPAREN, "Expected '(' after 'for'.")

        initializer = None
        if self.match(TokenType.SEMICOLON):
            pass
        elif self.match(TokenType.LET, TokenType.VAR):
            initializer = self.var_declaration()
        else:
            initializer = self.expr_statement()

        condition = None
        if not self.check(TokenType.SEMICOLON):
            condition = self.expression()
        self.consume(TokenType.SEMICOLON, "Expected ';' after 'for' condition.")

        increment = None
        if not self.check(TokenType.RPAREN):
            increment = self.expression()
        self.consume(TokenType.RPAREN, "Expected ')' after 'for' clauses.")

        try:
            self.loop_depth += 1
            body = self.statement()

            if increment != None and isinstance(body, Block):
                body.statements.append(Expression(increment))
            elif increment != None:
                body = Block([body, Expression(increment)])

            if condition == None:
                condition = Literal(True)

            return For(initializer, condition, increment, body)
        finally:
            self.loop_depth -= 1

    def function(self, kind):
        if self.debug:
            print("DECL: FUNCTION", file=sys.stderr)

        name = self.consume(TokenType.IDENTIFIER, f"Expected {kind} name.")
        self.consume(TokenType.LPAREN, f"Expected '(' after {kind} name.")

        parameters = []
        if not self.check(TokenType.RPAREN):
            while True:
                if len(parameters) >= 255:
                    self.error(
                        self.peek(),
                        f"{kind}s can only have up to 255 arguments."
                    )

                parameters.append(
                    self.consume(TokenType.IDENTIFIER, "Expected parameter name.")
                )

                if not self.match(TokenType.COMMA):
                    break

        self.consume(TokenType.RPAREN, f"Expected ')' after {kind} parameters.")
        self.consume(TokenType.LBRACE, "Expected '{' before " + kind + " body.")

        body = self.block()
        return Function(name, parameters, body)

    def if_statement(self):
        if self.debug:
            print("STMT: IF", file=sys.stderr)

        self.consume(TokenType.LPAREN, "Expected '(' after 'if'.")
        condition = self.expression()
        self.consume(TokenType.RPAREN, "Expected ')' after 'if' condition.")

        then_branch = self.statement()
        else_branch = None

        if self.match(TokenType.ELSE):
            else_branch = self.statement()

        return If(condition, then_branch, else_branch)

    def return_(self):
        if self.debug:
            print("STMT: RETURN", file=sys.stderr)

        keyword = self.previous()
        value = None

        if not self.check(TokenType.SEMICOLON):
            value = self.expression()

        self.consume(TokenType.SEMICOLON, "Expected ';' after return value.")
        return Return(keyword, value)

    def var_declaration(self):
        if self.debug:
            print("DECL: VAR", file=sys.stderr)

        keyword = self.previous()
        name = self.consume(TokenType.IDENTIFIER, "Expected variable name.")

        initializer = None
        if self.match(TokenType.EQ):
            initializer = self.expression()

        if keyword.type == TokenType.LET and initializer == None:
            self.error(
                self.previous(),
                "Variables defined with 'let' cannot be declared, they must be initialized."
            )

        self.consume(TokenType.SEMICOLON, "Expected ';' after variable declaration.")
        return Var(name, keyword, initializer)

    def while_statement(self):
        if self.debug:
            print("STMT: WHILE LOOP", file=sys.stderr)

        self.consume(TokenType.LPAREN, "Expected '(' after 'while'.")
        condition = self.expression()
        self.consume(TokenType.RPAREN, "Expected ')' after 'while' condition.")

        try:
            self.loop_depth += 1

            body = self.statement()
            return While(condition, body)
        finally:
            self.loop_depth -= 1

    def expression(self):
        if self.debug:
            print("EXPRESSION", file=sys.stderr)

        return self.assignment()

    def assignment(self):
        if self.debug:
            print("EXPR: ASSIGNMENT", file=sys.stderr)

        expr = self.conditional()

        if self.match(
            TokenType.EQ,
            TokenType.MINUSEQ,
            TokenType.MODEQ,
            TokenType.PLUSEQ,
            TokenType.SLASHEQ,
            TokenType.STAREQ
        ):
            operator = self.previous()
            value = self.assignment()

            if isinstance(expr, Variable):
                name = expr.name
                return Assign(name, operator, value)

            self.error(operator, "Invalid assignment target.")

        return expr

    def conditional(self):
        if self.debug:
            print("EXPR: CONDITIONAL", file=sys.stderr)

        expr = self.or_()

        while self.match(TokenType.QUESTION):
            then_branch = self.assignment()
            self.consume(TokenType.COLON, "Expected ':' after conditional 'true' expression.")
            else_branch = self.assignment()
            expr = Conditional(expr, then_branch, else_branch)

        return expr

    def or_(self):
        if self.debug:
            print("EXPR: LOGICAL OR", file=sys.stderr)

        expr = self.and_()

        while self.match(TokenType.OR):
            operator = self.previous()
            right = self.and_()
            expr = Logical(expr, operator, right)

        return expr

    def and_(self):
        if self.debug:
            print("EXPR: LOGICAL AND", file=sys.stderr)

        expr = self.equality()

        while self.match(TokenType.AND):
            operator = self.previous()
            right = self.equality()
            expr = Logical(expr, operator, right)

        return expr

    def equality(self):
        if self.debug:
            print("EXPR: EQUALITY", file=sys.stderr)

        expr = self.comparison()

        while self.match(TokenType.BANGEQ, TokenType.EQEQ):
            operator = self.previous()
            right = self.comparison()
            expr = Binary(expr, operator, right)

        return expr

    def comparison(self):
        if self.debug:
            print("EXPR: COMPARISON", file=sys.stderr)

        expr = self.term()

        while self.match(
            TokenType.GT,
            TokenType.GTEQ,
            TokenType.LT,
            TokenType.LTEQ
        ):
            operator = self.previous()
            right = self.term()
            expr = Binary(expr, operator, right)

        return expr

    def term(self):
        if self.debug:
            print("EXPR: TERM", file=sys.stderr)

        expr = self.factor()

        while self.match(TokenType.MINUS, TokenType.PLUS):
            operator = self.previous()
            right = self.factor()
            expr = Binary(expr, operator, right)

        return expr

    def factor(self):
        if self.debug:
            print("EXPR: FACTOR", file=sys.stderr)

        expr = self.power()

        while self.match(TokenType.MODULUS, TokenType.SLASH, TokenType.STAR):
            operator = self.previous()
            right = self.power()
            expr = Binary(expr, operator, right)

        return expr

    def power(self):
        if self.debug:
            print("EXPR: POWER", file=sys.stderr)

        expr = self.unary()

        while self.match(TokenType.POWER):
            operator = self.previous()
            right = self.power()
            expr = Binary(expr, operator, right)

        return expr

    def unary(self):
        if self.debug:
            print("EXPR: UNARY", file=sys.stderr)

        if self.match(TokenType.BANG, TokenType.MINUS):
            operator = self.previous()
            right = self.unary()
            return Unary(operator, right)

        return self.call()

    def finish_call(self, callee):
        arguments = []
        if not self.check(TokenType.RPAREN):
            while True:
                if len(arguments) >= 255:
                    self.error(
                        self.peek(),
                        "Classes, functions, and methods cannot have more than 255 arguments."
                    )

                arguments.append(self.expression())

                if not self.match(TokenType.COMMA):
                    break

        paren = self.consume(TokenType.RPAREN, "Expected ')' after arguments.")
        return Call(callee, paren, arguments)

    def call(self):
        expr = self.primary()

        while True:
            if self.match(TokenType.LPAREN):
                expr = self.finish_call(expr)
            else:
                break

        return expr

    def primary(self):
        if self.debug:
            print("EXPR: PRIMARY", file=sys.stderr)

        if self.match(TokenType.FALSE):
            return Literal(False)

        if self.match(TokenType.TRUE):
            return Literal(True)

        if self.match(TokenType.NULL):
            return Literal(None)

        if self.match(TokenType.NUMBER, TokenType.STRING):
            return Literal(self.previous().literal)

        if self.match(TokenType.IDENTIFIER):
            return Variable(self.previous())

        if self.match(TokenType.LPAREN):
            expr = self.expression()
            self.consume(TokenType.RPAREN, "Expected ')' after expression.")
            return Grouping(expr)

        if self.match(
            TokenType.MINUS,
            TokenType.MODULUS,
            TokenType.PLUS,
            TokenType.POWER,
            TokenType.SLASH,
            TokenType.STAR,
            TokenType.GT,
            TokenType.GTEQ,
            TokenType.LT,
            TokenType.LTEQ,
            TokenType.BANGEQ,
            TokenType.EQEQ,
            TokenType.QUESTION,
            TokenType.COLON,
        ):
            raise self.error(self.previous(), "Binary/ternary operator found in a unary context.")

        raise self.error(self.previous(), "Expected expression.")

    def match(self, *types):
        for type_ in types:
            if self.check(type_):
                self.advance()
                return True

        return False

    def consume(self, type_, message):
        if self.check(type_):
            return self.advance()

        raise self.error(self.peek(), message)

    def check(self, type_):
        if self.is_at_end():
            return False

        return self.peek().type == type_

    def advance(self):
        if not self.is_at_end():
            self.current += 1

        return self.previous()

    def is_at_end(self):
        return self.peek().type == TokenType.EOF

    def peek(self):
        return self.tokens[self.current]

    def previous(self):
        return self.tokens[self.current - 1]

    def error(self, token, message):
        self.err_manager.parse_error(token, message)
        return ParseError()

    def synchronize(self):
        self.advance()

        while not self.is_at_end():
            if self.previous().type == TokenType.SEMICOLON:
                return

            match self.peek().type:
                case TokenType.BREAK:
                    return
                case TokenType.CLASS:
                    return
                case TokenType.CONTINUE:
                    return
                case TokenType.CONST:
                    return
                case TokenType.ECHO:
                    return
                case TokenType.FUN, TokenType.FN:
                    return
                case TokenType.IF:
                    return
                case TokenType.LET:
                    return
                case TokenType.RETURN:
                    return
                case TokenType.VAR:
                    return
                case TokenType.WHILE:
                    return

            self.advance()
