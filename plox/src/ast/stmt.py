# Python Imports
from abc import ABC, abstractmethod

# Project Imports
from src.ast.expr import Expr
from src.scanner.token import Token


class Stmt(ABC):
    @abstractmethod
    def accept(self, visitor):
        ...


class StmtVisitor(ABC):
    @abstractmethod
    def visit_block_stmt(self, stmt: Stmt) -> None:
        ...

    @abstractmethod
    def visit_break_stmt(self, stmt: Stmt) -> None:
        ...

    @abstractmethod
    def visit_class_stmt(self, stmt: Stmt) -> None:
        ...

    @abstractmethod
    def visit_const_stmt(self, stmt: Stmt) -> None:
        ...

    @abstractmethod
    def visit_continue_stmt(self, stmt: Stmt) -> None:
        ...

    @abstractmethod
    def visit_echo_stmt(self, stmt: Stmt) -> None:
        ...

    @abstractmethod
    def visit_expression_stmt(self, stmt: Stmt) -> None:
        ...

    @abstractmethod
    def visit_for_stmt(self, stmt: Stmt) -> None:
        ...

    @abstractmethod
    def visit_function_stmt(self, stmt: Stmt) -> None:
        ...

    @abstractmethod
    def visit_if_stmt(self, stmt: Stmt) -> None:
        ...

    @abstractmethod
    def visit_return_stmt(self, stmt: Stmt) -> None:
        ...

    @abstractmethod
    def visit_var_stmt(self, stmt: Stmt) -> None:
        ...

    @abstractmethod
    def visit_while_stmt(self, stmt: Stmt) -> None:
        ...


class Block(Stmt):
    def __init__(self, statements: list[Stmt]):
        self.statements = statements

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_block_stmt(self)


class Break(Stmt):
    def __init__(self, keyword: Token):
        self.keyword = keyword

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_break_stmt(self)


class Class(Stmt):
    def __init__(self, name: Token, superclass: Expr, methods: list[Stmt]):
        self.name = name
        self.superclass = superclass
        self.methods = methods

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_class_stmt(self)


class Const(Stmt):
    def __init__(self, name: Token, initializer: Expr):
        self.name = name
        self.initializer = initializer

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_const_stmt(self)


class Continue(Stmt):
    def __init__(self, keyword: Token):
        self.keyword = keyword

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_continue_stmt(self)


class Echo(Stmt):
    def __init__(self, expression: Expr):
        self.expression = expression

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_echo_stmt(self)


class Expression(Stmt):
    def __init__(self, expression: Expr):
        self.expression = expression

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_expression_stmt(self)


class For(Stmt):
    def __init__(self, initializer: Stmt, condition: Expr, increment: Expr, body: Stmt):
        self.initializer = initializer
        self.condition = condition
        self.increment = increment
        self.body = body

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_for_stmt(self)


class Function(Stmt):
    def __init__(self, name: Token, params: list[Token], body: list[Stmt]):
        self.name = name
        self.params = params
        self.body = body

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_function_stmt(self)


class If(Stmt):
    def __init__(self, condition: Expr, then_branch: Stmt, else_branch: Stmt):
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_if_stmt(self)


class Return(Stmt):
    def __init__(self, keyword: Token, value: Expr):
        self.keyword = keyword
        self.value = value

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_return_stmt(self)


class Var(Stmt):
    def __init__(self, name: Token, keyword: Token, initializer: Expr):
        self.name = name
        self.keyword = keyword
        self.initializer = initializer

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_var_stmt(self)


class While(Stmt):
    def __init__(self, condition: Expr, body: Stmt):
        self.condition = condition
        self.body = body

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_while_stmt(self)

