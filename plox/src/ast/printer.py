# Python Imports
import sys

# Project Imports
from src.ast.expr import (
    Expr,
    ExprVisitor,
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
    Stmt,
    StmtVisitor,
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

class AstPrinter(ExprVisitor, StmtVisitor):
    def visit_block_stmt(self, stmt: Block):
        return self.build_stmt_tree(stmt)

    def visit_break_stmt(self, stmt: Break):
        return self.build_stmt_tree(stmt)

    def visit_const_stmt(self, stmt: Const):
        return self.build_stmt_tree(stmt)

    def visit_continue_stmt(self, stmt: Continue):
        return self.build_stmt_tree(stmt)

    def visit_echo_stmt(self, stmt: Echo):
        return self.build_stmt_tree(stmt)

    def visit_expression_stmt(self, stmt: Expression):
        return self.build_stmt_tree(stmt)

    def visit_for_stmt(self, stmt: For):
        return self.build_stmt_tree(stmt)

    def visit_function_stmt(self, stmt: Function):
        return self.build_stmt_tree(stmt)

    def visit_if_stmt(self, stmt: If):
        return self.build_stmt_tree(stmt)

    def visit_return_stmt(self, stmt: Return):
        return self.build_stmt_tree(stmt)

    def visit_var_stmt(self, stmt: Var):
        return self.build_stmt_tree(stmt)

    def visit_while_stmt(self, stmt: While):
        return self.build_stmt_tree(stmt)

    def visit_assign_expr(self, expr: Assign):
        return self.build_expr_tree(expr)

    def visit_binary_expr(self, expr: Binary):
        return self.build_expr_tree(expr)

    def visit_call_expr(self, expr: Call):
        return self.build_expr_tree(expr)

    def visit_conditional_expr(self, expr: Conditional):
        return self.build_expr_tree(expr)

    def visit_grouping_expr(self, expr: Grouping):
        return self.build_expr_tree(expr)

    def visit_literal_expr(self, expr: Literal):
        return self.build_expr_tree(expr)

    def visit_logical_expr(self, expr: Logical):
        return self.build_expr_tree(expr)

    def visit_unary_expr(self, expr: Unary):
        return self.build_expr_tree(expr)

    def visit_variable_expr(self, expr: Variable):
        return self.build_expr_tree(expr)

    def build_block(self, statements: list[Stmt]):
        result = "{"

        for statement in statements:
            result += f"\n\t{statement.accept(self)}"

        result += "\n}"
        return result

    def build_stmt_tree(self, stmt: Stmt):
        result = "["

        if isinstance(stmt, Block):
            return self.build_block(stmt.statements)

        elif isinstance(stmt, Const):
            result += f" = const define {stmt.name.lexeme}"
            result += f" {stmt.initializer.accept(self)} "

        elif isinstance(stmt, Echo):
            result += f" echo {stmt.expression.accept(self)} "

        elif isinstance(stmt, Expression):
            result += f" {stmt.expression.accept(self)} "

        elif isinstance(stmt, For):
            result += " for"
            if stmt.initializer != None:
                result += f" : {stmt.initializer.accept(self)} :"

            result += f" if {stmt.condition.accept(self)} is True :"
            if stmt.increment != None:
                result += f" increment {stmt.increment.accept(self)}"

            if isinstance(stmt.body, Block):
                result += f" {self.build_block(stmt.body.statements)} "
            else:
                result += f" {stmt.body.accept(self)} "

        elif isinstance(stmt, Function):
            pass

        elif isinstance(stmt, If):
            result += f" if {stmt.condition.accept(self)} is True,"

            if stmt.else_branch != None:
                result += f" then do {stmt.then_branch.accept(self)}"
                result += f" else do {stmt.else_branch.accept(self)} "
            else:
                result += f" then do {stmt.then_branch.accept(self)} "

        elif isinstance(stmt, Return):
            result += f" return {stmt.value.accept(self)} "

        elif isinstance(stmt, Var):
            if stmt.initializer == None:
                result += f" var declare {stmt.name.lexeme} "
            else:
                result += f" = {stmt.keyword.lexeme} define {stmt.name.lexeme}"
                result += f" {stmt.initializer.accept(self)} "

        elif isinstance(stmt, While):
            pass

        result += "]"
        return result

    def build_expr_tree(self, expr: Expr):
        result = "("

        if isinstance(expr, Assign):
            result += f" {expr.operator.lexeme}"
            result += f" var {expr.name.lexeme} {expr.value.accept(self)} "

        elif isinstance(expr, Binary):
            result += f" {expr.operator.lexeme}"
            result += f" {expr.left.accept(self)}"
            result += f" {expr.right.accept(self)} "

        elif isinstance(expr, Call):
            result += f" call {expr.callee.name.lexeme}"

            if len(expr.arguments) > 0:
                result += " with arguments ("

                for arg in expr.arguments:
                    if arg == expr.arguments[len(expr.arguments) - 1]:
                        result += f" {arg.accept(self)} "
                    else:
                        result += f" {arg.accept(self)},"

                result += ") "
            else:
                result += " with no arguments "


        elif isinstance(expr, Conditional):
            result += f" {expr.condition.accept(self)}"
            result += f" ? {expr.then_branch.accept(self)}"
            result += f" : {expr.else_branch.accept(self)} "

        elif isinstance(expr, Grouping):
            return f" Group ( {expr.expression.accept(self)} ) "

        elif isinstance(expr, Literal):
            if expr.value == None:
                return "null"

            return str(expr.value)

        elif isinstance(expr, Logical):
            result += f" {expr.operator.lexeme}"
            result += f" {expr.left.accept(self)}"
            result += f" {expr.right.accept(self)} "

        elif isinstance(expr, Unary):
            result += f" {expr.operator.lexeme}"
            result += f" {expr.right.accept(self)} "

        elif isinstance(expr, Variable):
            result += expr.name.lexeme

        result += ")"
        return result

    def print_stmt(self, stmt: Stmt):
        print(stmt.accept(self), file=sys.stderr)

    def print_expr(self, expr: Expr):
        print(expr.accept(self), file=sys.stderr)

