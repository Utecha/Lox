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
from src.callable.lox_callable import LoxCallable
from src.callable.lox_class import LoxClass
from src.callable.lox_function import LoxFunction
from src.callable.lox_instance import LoxInstance
from src.interpreter.environment import Environment
from src.callable.natives import define_natives
from src.scanner.token import TokenType
from src.util.errors import LoxRuntimeError
from src.util.exceptions import (
    BreakException,
    ContinueException,
    ReturnException
)
from src.util.mode import RunMode


# Interpreter Class
class Interpreter(ExprVisitor, StmtVisitor):
    def __init__(self, err_manager, mode):
        self.err_manager = err_manager
        self.mode = mode
        self.globals = Environment()
        self.environment = self.globals
        self.locals = {}
        self.loop_depth = 0

        # Native Functions
        define_natives(self)

    def interpret(self, statements: list[Stmt]):
        try:
            for statement in statements:
                if self.mode == RunMode.REPL:
                    self.execute_repl_friendly(statement)
                elif self.mode == RunMode.FILE:
                    self.execute(statement)
        except LoxRuntimeError as e:
            self.err_manager.runtime_error(e)

    def execute_repl_friendly(self, stmt: Stmt):
        if isinstance(stmt, Expression):
            if not isinstance(stmt.expression, Assign):
                value = self.evaluate(stmt.expression)
                print(self.stringify(value))
            else:
                self.evaluate(stmt.expression)
        else:
            self.execute(stmt)

    def resolve(self, expr, depth):
        self.locals[expr] = depth

    def execute(self, stmt: Stmt):
        stmt.accept(self)

    def execute_block(self, statements: list[Stmt], environment):
        previous = self.environment

        try:
            self.environment = environment

            for statement in statements:
                self.execute(statement)
        finally:
            self.environment = previous

    def evaluate(self, expr: Expr):
        return expr.accept(self)

    def visit_block_stmt(self, stmt: Block):
        self.execute_block(stmt.statements, Environment(self.environment))

    def visit_break_stmt(self, stmt: Break):
        raise BreakException(stmt.keyword)

    def visit_class_stmt(self, stmt: Class):
        superclass = None
        if stmt.superclass != None:
            superclass = self.evaluate(stmt.superclass)

            if not isinstance(superclass, LoxClass):
                raise LoxRuntimeError(
                    stmt.superclass.name,
                    "Superclass must be a class."
                )

        self.environment.define(stmt.name.lexeme, None)

        if stmt.superclass != None:
            self.environment = Environment(self.environment)
            self.environment.define("super", superclass)

        methods = {}
        for method in stmt.methods:
            function = LoxFunction(
                method,
                self.environment,
                (method.name.lexeme == "init" or
                    method.name.lexeme == stmt.name.lexeme)
            )
            methods[method.name.lexeme] = function

        klass = LoxClass(stmt.name.lexeme, superclass, methods)

        if superclass != None:
            self.environment = self.environment.enclosing

        self.environment.assign(stmt.name, klass)

    def visit_const_stmt(self, stmt: Const):
        value = self.evaluate(stmt.initializer)
        self.environment.define_const(stmt.name.lexeme, value)

    def visit_continue_stmt(self, stmt: Continue):
        raise ContinueException(stmt.keyword)

    def visit_echo_stmt(self, stmt: Echo):
        value = self.evaluate(stmt.expression)
        print(self.stringify(value))

    def visit_expression_stmt(self, stmt: Expression):
        self.evaluate(stmt.expression)

    def visit_for_stmt(self, stmt: For):
        if stmt.initializer != None:
            self.evaluate(stmt.initializer)

        try:
            self.loop_depth += 1
            while self.is_truthy(self.evaluate(stmt.condition)):
                try:
                    self.evaluate(stmt.body)
                except BreakException:
                    return
                except ContinueException:
                    if isinstance(stmt.body, Block):
                        self.execute_block(
                            [stmt.body.statements[-1]],
                            Environment(self.environment)
                        )
        finally:
            self.loop_depth -= 1

    def visit_function_stmt(self, stmt: Function):
        function = LoxFunction(stmt, self.environment, False)
        self.environment.define(stmt.name.lexeme, function)

    def visit_if_stmt(self, stmt: If):
        if self.is_truthy(self.evaluate(stmt.condition)):
            self.execute(stmt.then_branch)

        elif stmt.else_branch != None:
            self.execute(stmt.else_branch)

    def visit_return_stmt(self, stmt: Return):
        value = None
        if stmt.value != None:
            value = self.evaluate(stmt.value)

        raise ReturnException(stmt.keyword.lexeme, value)

    def visit_var_stmt(self, stmt: Var):
        value = None
        if stmt.initializer != None:
            value = self.evaluate(stmt.initializer)

        self.environment.define(stmt.name.lexeme, value)

    def visit_while_stmt(self, stmt: While):
        while self.is_truthy(self.evaluate(stmt.condition)):
            self.execute(stmt.body)

    def visit_assign_expr(self, expr: Assign):
        value = self.evaluate(expr.value)

        match expr.operator.type:
            case TokenType.EQ:
                distance = self.locals.get(expr)
                if distance != None:
                    self.environment.assign_at(distance, expr.name, value)
                else:
                    self.environment.assign(expr.name, value)

                return value

            case TokenType.MINUSEQ:
                if not isinstance(value, float):
                    raise LoxRuntimeError(expr.operator, "Cannot use augmented assignment on non-number values.")

                initial = self.environment.get(expr.name)
                initial -= value

                distance = self.locals.get(expr)
                if distance != None:
                    self.environment.assign_at(distance, expr.name, initial)
                else:
                    self.environment.assign(expr.name, initial)

                return value

            case TokenType.MODEQ:
                if not isinstance(value, float):
                    raise LoxRuntimeError(expr.operator, "Cannot use augmented assignment on non-number values.")

                if value == 0:
                    raise LoxRuntimeError(expr.operator, "Cannot divide by Zero.")

                initial = self.environment.get(expr.name)
                initial %= value

                distance = self.locals.get(expr)
                if distance != None:
                    self.environment.assign_at(distance, expr.name, initial)
                else:
                    self.environment.assign(expr.name, initial)

                return value

            case TokenType.PLUSEQ:
                if not isinstance(value, float):
                    raise LoxRuntimeError(expr.operator, "Cannot use augmented assignment on non-number values.")

                initial = self.environment.get(expr.name)
                initial += value

                distance = self.locals.get(expr)
                if distance != None:
                    self.environment.assign_at(distance, expr.name, initial)
                else:
                    self.environment.assign(expr.name, initial)

                return value

            case TokenType.SLASHEQ:
                if not isinstance(value, float):
                    raise LoxRuntimeError(expr.operator, "Cannot use augmented assignment on non-number values.")

                if value == 0:
                    raise LoxRuntimeError(expr.operator, "Cannot divide by Zero.")

                initial = self.environment.get(expr.name)
                initial /= value

                distance = self.locals.get(expr)
                if distance != None:
                    self.environment.assign_at(distance, expr.name, initial)
                else:
                    self.environment.assign(expr.name, initial)

                return value

            case TokenType.STAREQ:
                if not isinstance(value, float):
                    raise LoxRuntimeError(expr.operator, "Cannot use augmented assignment on non-number values.")

                initial = self.environment.get(expr.name)
                initial *= value

                distance = self.locals.get(expr)
                if distance != None:
                    self.environment.assign_at(distance, expr.name, initial)
                else:
                    self.environment.assign(expr.name, initial)

                return value

    def visit_binary_expr(self, expr: Binary):
        left = self.evaluate(expr.left)
        right = self.evaluate(expr.right)

        match expr.operator.type:
            case TokenType.MINUS:
                if self.check_operands(expr.operator, left, right) == True:
                    return left - right

            case TokenType.MODULUS:
                if self.check_operands(expr.operator, left, right) == True:
                    if right == 0:
                        raise LoxRuntimeError(expr.operator, "Cannot divide by Zero.")

                    return left % right

            case TokenType.PLUS:
                if isinstance(left, float) and isinstance(right, float):
                    return left + right

                elif isinstance(left, str) and isinstance(right, str):
                    return left + right

                elif isinstance(left, float) and isinstance(right, str):
                    return self.stringify(left) + right

                elif isinstance(left, str) and isinstance(right, float):
                    return left + self.stringify(right)

                raise LoxRuntimeError(expr.operator, "Operands must be numbers or strings. Combining the two is allowed.")
            case TokenType.POWER:
                if self.check_operands(expr.operator, left, right) == True:
                    return left ** right

            case TokenType.SLASH:
                if self.check_operands(expr.operator, left, right) == True:
                    if right == 0:
                        raise LoxRuntimeError(expr.operator, "Cannot divide by Zero.")

                    return left / right

            case TokenType.STAR:
                if self.check_operands(expr.operator, left, right) == True:
                    return left * right

            case TokenType.GT:
                if self.check_operands(expr.operator, left, right) == True:
                    return left > right

            case TokenType.GTEQ:
                if self.check_operands(expr.operator, left, right) == True:
                    return left >= right

            case TokenType.LT:
                if self.check_operands(expr.operator, left, right) == True:
                    return left < right

            case TokenType.LTEQ:
                if self.check_operands(expr.operator, left, right) == True:
                    return left <= right

            case TokenType.BANGEQ:
                return not self.is_equal(left, right)

            case TokenType.EQEQ:
                return self.is_equal(left, right)

    def visit_call_expr(self, expr: Call):
        callee = self.evaluate(expr.callee)

        arguments = []
        for argument in expr.arguments:
            arguments.append(self.evaluate(argument))

        if not isinstance(callee, LoxCallable):
            raise LoxRuntimeError(
                expr.paren,
                "Only classes, functions or methods can be called."
            )

        function = callee
        if len(arguments) != function.arity():
            raise LoxRuntimeError(
                expr.paren,
                f"Expected {function.arity()} arguments " +
                f"but got {len(arguments)} instead."
            )
        return function.call(self, arguments)

    def visit_conditional_expr(self, expr: Conditional):
        if self.is_truthy(self.evaluate(expr.condition)):
            return self.evaluate(expr.then_branch)

        return self.evaluate(expr.else_branch)

    def visit_get_expr(self, expr: Get):
        obj = self.evaluate(expr.obj)
        if isinstance(obj, LoxInstance):
            return obj.get(expr.name)

        raise LoxRuntimeError(
            expr.name,
            "Only instances of an object have properties."
        )

    def visit_grouping_expr(self, expr: Grouping):
        return self.evaluate(expr.expression)

    def visit_literal_expr(self, expr: Literal):
        return expr.value

    def visit_logical_expr(self, expr: Logical):
        left = self.evaluate(expr.left)

        if expr.operator.type == TokenType.OR:
            if self.is_truthy(left):
                return left
        else:
            if not self.is_truthy(left):
                return left

        return self.evaluate(expr.right)

    def visit_self_expr(self, expr: Self):
        return self.look_up_variable(expr.keyword, expr)

    def visit_set_expr(self, expr: Set):
        obj = self.evaluate(expr.obj)

        if not isinstance(obj, LoxInstance):
            raise LoxRuntimeError(
                expr.name,
                "Only instances of an object have fields."
            )

        value = self.evaluate(expr.value)
        obj.set_(expr.name, value)
        return value

    def visit_super_expr(self, expr: Super):
        distance = self.locals.get(expr)
        superclass = self.environment.get_at(distance, "super")

        obj = self.environment.get_at(distance - 1, "self")
        if obj == None:
            obj = self.environment.get_at(distance - 1, "this")

        method = superclass.find_method(expr.method.lexeme)

        if method == None:
            raise LoxRuntimeError(
                expr.method,
                f"Undefined Property '{expr.method.lexeme}'."
            )

        return method.bind(obj)

    def visit_unary_expr(self, expr: Unary):
        right = self.evaluate(expr.right)

        match expr.operator.type:
            case TokenType.BANG:
                return not self.is_truthy(right)

            case TokenType.MINUS:
                if self.check_operand(expr.operator, right) == True:
                    return -right

    def visit_variable_expr(self, expr: Variable):
        # return self.environment.get(expr.name)
        return self.look_up_variable(expr.name, expr)

    def look_up_variable(self, name, expr):
        distance = self.locals.get(expr)
        if distance != None:
            return self.environment.get_at(distance, name.lexeme)
        else:
            return self.globals.get(name)

    def is_truthy(self, obj):
        if obj == None:
            return False

        if isinstance(obj, bool):
            return obj

        return True

    def is_equal(self, a, b):
        if (a == None) and (b == None):
            return True

        if a == None:
            return False

        return a == b

    def check_operand(self, operator, operand):
        if isinstance(operand, float):
            return True

        raise LoxRuntimeError(operator, "Operand must be a number.")

    def check_operands(self, operator, left, right):
        if isinstance(left, float) and isinstance(right, float):
            return True

        raise LoxRuntimeError(operator, "Operands must be numbers.")

    def stringify(self, obj):
        if obj == None:
            return "null"

        if isinstance(obj, float):
            text = str(obj)
            if text.endswith(".0"):
                text = text[0 : len(text) - 2]

            return text

        return str(obj)
