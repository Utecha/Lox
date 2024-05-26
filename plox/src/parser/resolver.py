# Python Imports
from enum import Enum

# Project Imports
from src.ast.expr import (
    Expr,
    ExprVisitor,
    Assign,
    Binary,
    Call,
    Conditional,
    Get,
    Grouping,
    Literal,
    Logical,
    Self,
    Set,
    Super,
    Unary,
    Variable
)
from src.ast.stmt import (
    Stmt,
    StmtVisitor,
    Block,
    Break,
    Class,
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


class ClassType(Enum):
    NONE = 0
    CLASS = 1
    SUBCLASS = 2


class FunctionType(Enum):
    NONE = 0
    FUNCTION = 1
    INITIALIZER = 2
    METHOD = 3


class Resolver(ExprVisitor, StmtVisitor):
    def __init__(self, interpreter, err_manager):
        self.interpreter = interpreter
        self.err_manager = err_manager
        self.current_class = ClassType.NONE
        self.current_func = FunctionType.NONE
        self.scopes = []

    def resolve_stmts(self, stmts: list[Stmt]):
        for stmt in stmts:
            self.resolve_stmt(stmt)

    def resolve_stmt(self, stmt: Stmt):
        stmt.accept(self)

    def resolve_expr(self, expr: Expr):
        expr.accept(self)

    def begin_scope(self):
        self.scopes.append({})

    def end_scope(self):
        self.scopes.pop()

    def declare(self, name):
        if not self.scopes:
            return

        scope = self.scopes[-1]
        if name.lexeme in scope.keys():
            self.err_manager.parse_error(
                name,
                "Already a variable with this name in this scope."
            )

        scope[name.lexeme] = False

    def define(self, name):
        if not self.scopes:
            return

        self.scopes[-1][name.lexeme] = True

    def resolve_local(self, expr, name):
        for i in range(len(self.scopes) - 1, -1, -1):
            if name.lexeme in self.scopes[i]:
                self.interpreter.resolve(expr, len(self.scopes) - 1 - i)
                return

    def resolve_function(self, function, function_type):
        enclosing_func = self.current_func
        self.current_func = function_type

        self.begin_scope()
        for param in function.params:
            self.declare(param)
            self.define(param)

        self.resolve_stmts(function.body)
        self.end_scope()
        self.current_func = enclosing_func

    def visit_block_stmt(self, stmt: Block):
        self.begin_scope()
        self.resolve_stmts(stmt.statements)
        self.end_scope()

    def visit_break_stmt(self, stmt: Break):
        pass

    def visit_class_stmt(self, stmt: Class):
        enclosing_class = self.current_class
        self.current_class = ClassType.CLASS

        self.declare(stmt.name)
        self.define(stmt.name)

        if stmt.superclass != None:
            if stmt.name.lexeme == stmt.superclass.name.lexeme:
                self.err_manager.parse_error(
                    stmt.superclass.name,
                    "A class cannot inherit from itself."
                )

            self.resolve_stmt(stmt.superclass)

            self.begin_scope()
            self.scopes[-1] |= {"super": True}

        self.begin_scope()
        self.scopes[-1] |= {"this": True}
        self.scopes[-1] |= {"self": True}

        for method in stmt.methods:
            declaration = FunctionType.METHOD

            if method.name.lexeme == "init" or  \
                method.name.lexeme == stmt.name:

                declaration = FunctionType.INITIALIZER

            self.resolve_function(method, declaration)

        self.end_scope()

        if stmt.superclass != None:
            self.end_scope()

        self.current_class = enclosing_class

    def visit_const_stmt(self, stmt: Const):
        self.declare(stmt.name)
        self.resolve_expr(stmt.initializer)
        self.define(stmt.name)

    def visit_continue_stmt(self, stmt: Continue):
        pass

    def visit_echo_stmt(self, stmt: Echo):
        self.resolve_expr(stmt.expression)

    def visit_expression_stmt(self, stmt: Expression):
        self.resolve_expr(stmt.expression)

    def visit_for_stmt(self, stmt: For):
        if stmt.initializer != None:
            self.resolve_expr(stmt.initializer)

        self.resolve_expr(stmt.condition)

        if stmt.increment != None:
            self.resolve_expr(stmt.increment)

        self.resolve_stmt(stmt.body)

    def visit_function_stmt(self, stmt: Function):
        self.declare(stmt.name)
        self.define(stmt.name)

        self.resolve_function(stmt, FunctionType.FUNCTION)

    def visit_if_stmt(self, stmt: If):
        self.resolve_expr(stmt.condition)
        self.resolve_stmt(stmt.then_branch)

        if stmt.else_branch != None:
            self.resolve_stmt(stmt.else_branch)

    def visit_return_stmt(self, stmt: Return):
        if self.current_func == FunctionType.NONE:
            self.err_manager.parse_error(
                stmt.keyword,
                "Cannot return from top-level code."
            )

        if stmt.value != None:
            if self.current_func == FunctionType.INITIALIZER:
                self.err_manager.parse_error(
                    stmt.keyword,
                    "Cannot return a value from an initializer."
                )

            self.resolve_expr(stmt.value)

    def visit_var_stmt(self, stmt: Var):
        self.declare(stmt.name)
        if stmt.initializer != None:
            self.resolve_expr(stmt.initializer)
        self.define(stmt.name)

    def visit_while_stmt(Self, stmt: While):
        self.resolve_expr(stmt.condition)
        self.resolve_stmt(stmt.body)

    def visit_assign_expr(self, expr: Assign):
        self.resolve_expr(expr.value)
        self.resolve_local(expr, expr.name)

    def visit_binary_expr(self, expr: Binary):
        self.resolve_expr(expr.left)
        self.resolve_expr(expr.right)

    def visit_call_expr(self, expr: Call):
        self.resolve_expr(expr.callee)

        for argument in expr.arguments:
            self.resolve_expr(argument)

    def visit_conditional_expr(self, expr: Conditional):
        self.resolve_expr(stmt.condition)
        self.resolve_expr(stmt.then_branch)
        self.resolve_expr(stmt.else_branch)

    def visit_get_expr(self, expr: Get):
        self.resolve_expr(expr.obj)

    def visit_grouping_expr(self, expr: Grouping):
        self.resolve_expr(expr.expression)

    def visit_literal_expr(self, expr: Literal):
        pass

    def visit_logical_expr(self, expr: Logical):
        self.resolve_expr(expr.left)
        self.resolve_expr(expr.right)

    def visit_self_expr(self, expr: Self):
        if self.current_class == ClassType.NONE:
            self.err_manager.parse_error(
                expr.keyword,
                "Cannot use 'self' (or 'this') outside of a class."
            )

        self.resolve_local(expr, expr.keyword)

    def visit_set_expr(self, expr: Set):
        self.resolve_expr(expr.value)
        self.resolve_expr(expr.obj)

    def visit_super_expr(self, expr: Super):
        if self.current_class == ClassType.NONE:
            self.err_manager.parse_error(
                expr.keyword,
                "Cannot use 'super' outside of a class."
            )
        elif self.current_class != ClassType.SUBCLASS:
            self.err_manager.parse_error(
                expr.keyword,
                "Cannot use 'super' in a class with no superclass."
            )

        self.resolve_local(expr, expr.keyword)

    def visit_unary_expr(self, expr: Unary):
        self.resolve_expr(expr.right)

    def visit_variable_expr(self, expr: Variable):
        if self.scopes and self.scopes[-1].get(expr.name.lexeme) == False:
            self.err_manager.parse_error(
                expr.name,
                "Cannot read a local variable within its own initializer."
            )

        self.resolve_local(expr, expr.name)

