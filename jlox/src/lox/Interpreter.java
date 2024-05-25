package lox;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

class Interpreter implements Expr.Visitor<Object>, Stmt.Visitor<Void> {
    final Environment globals = new Environment();
    private Environment environment = globals;
    private final Map<Expr, Integer> locals = new HashMap<>();

    Interpreter() {
        globals.define("clock", new LoxCallable() {
            @Override
            public int
            arity() { return 0; }

            @Override
            public Object
            call(Interpreter interpreter, List<Object> arguments)
            {
                return (double)System.currentTimeMillis() / 1000.0;
            }

            @Override
            public String
            toString() { return "<Native Fn - clock>"; }
        });
    }

    void
    interpret(List<Stmt> statements)
    {
        try {
            for (Stmt statement : statements) {
                execute(statement);
            }
        } catch (RuntimeError error) {
            Lox.runtimeError(error);
        }
    }

    void
    resolve(Expr expr, int depth)
    {
        locals.put(expr, depth);
    }

    private void
    execute(Stmt stmt)
    {
        stmt.accept(this);
    }

    void
    executeBlock(List<Stmt> statements, Environment environment)
    {
        Environment previous = this.environment;

        try {
            this.environment = environment;

            for (Stmt statement : statements) {
                execute(statement);
            }
        } finally {
            this.environment = previous;
        }
    }

    private Object
    evaluate(Expr expr)
    {
        return expr.accept(this);
    }

    @Override
    public Void
    visitBlockStmt(Stmt.Block stmt)
    {
        executeBlock(stmt.statements, new Environment(environment));
        return null;
    }

    @Override
    public Void
    visitClassStmt(Stmt.Class stmt)
    {
        Object superclass = null;
        if (stmt.superclass != null) {
            superclass = evaluate(stmt.superclass);
            if (!(superclass instanceof LoxClass)) {
                throw new RuntimeError(stmt.superclass.name, "Superclass must be a class.");
            }
        }

        environment.define(stmt.name.lexeme, null);

        if (stmt.superclass != null) {
            environment = new Environment(environment);
            environment.define("super", superclass);
        }

        Map<String, LoxFunction> methods = new HashMap<>();
        for (Stmt.Function method : stmt.methods) {
            LoxFunction function = new LoxFunction(
                    method,
                    environment,
                    method.name.lexeme.equals("init")
            );

            methods.put(method.name.lexeme, function);
        }

        LoxClass klass = new LoxClass(stmt.name.lexeme, (LoxClass)superclass, methods);

        if (superclass != null) {
            environment = environment.enclosing;
        }

        environment.assign(stmt.name, klass);
        return null;
    }

    @Override
    public Void
    visitExpressionStmt(Stmt.Expression stmt)
    {
        evaluate(stmt.expression);
        return null;
    }

    @Override
    public Void
    visitFunctionStmt(Stmt.Function stmt)
    {
        LoxFunction function = new LoxFunction(stmt, environment, false);
        environment.define(stmt.name.lexeme, function);
        return null;
    }

    @Override
    public Void
    visitIfStmt(Stmt.If stmt)
    {
        if (isTruthy(evaluate(stmt.condition))) {
            execute(stmt.thenBranch);
        } else if (stmt.elseBranch != null) {
            execute(stmt.elseBranch);
        }

        return null;
    }

    @Override
    public Void
    visitPrintStmt(Stmt.Print stmt)
    {
        Object value = evaluate(stmt.expression);
        System.out.println(stringify(value));
        return null;
    }

    @Override
    public Void
    visitReturnStmt(Stmt.Return stmt)
    {
        Object value = null;
        if (stmt.value != null) value = evaluate(stmt.value);

        throw new Return(value);
    }

    @Override
    public Void visitVarStmt(Stmt.Var stmt) {
        Object value = null;
        if (stmt.initializer != null) {
            value = evaluate(stmt.initializer);
        }

        environment.define(stmt.name.lexeme, value);
        return null;
    }

    @Override
    public Void
    visitWhileStmt(Stmt.While stmt)
    {
        while (isTruthy(evaluate(stmt.condition))) {
            execute(stmt.body);
        }

        return null;
    }

    @Override
    public Object
    visitAssignExpr(Expr.Assign expr)
    {
        Object value = evaluate(expr.value);

        Integer distance = locals.get(expr);
        if (distance != null) {
            environment.assignAt(distance, expr.name, value);
        } else {
            environment.assign(expr.name, value);
        }

        return value;
    }

    @Override
    public Object
    visitBinaryExpr(Expr.Binary expr)
    {
        Object left = evaluate(expr.left);
        Object right = evaluate(expr.right);

        switch (expr.operator.type) {
            case MINUS -> {
                checkOperands(expr.operator, left, right);
                return (double) left - (double) right;
            }
            case SLASH -> {
                checkOperands(expr.operator, left, right);

                if ((double)right == 0) {
                    throw new RuntimeError(expr.operator, "Cannot divide by Zero.");
                }

                return (double) left / (double) right;
            }
            case STAR -> {
                checkOperands(expr.operator, left, right);
                return (double) left * (double) right;
            }
            case PLUS -> {
                if (left instanceof Double && right instanceof Double) {
                    return (double)left + (double)right;
                }

                if (left instanceof String && right instanceof String) {
                    return left + (String)right;
                }

                if (left instanceof Double && right instanceof String) {
                    return stringify(left) + right;
                }

                if (left instanceof String && right instanceof Double) {
                    return left + stringify(right);
                }

                throw new RuntimeError(expr.operator, "Operands must be numbers or strings, not mixed.");
            }
            case GT -> {
                checkOperands(expr.operator, left, right);
                return (double) left > (double) right;
            }
            case GTEQ -> {
                checkOperands(expr.operator, left, right);
                return (double) left >= (double) right;
            }
            case LT -> {
                checkOperands(expr.operator, left, right);
                return (double) left < (double) right;
            }
            case LTEQ -> {
                checkOperands(expr.operator, left, right);
                return (double) left <= (double) right;
            }
            case BANGEQ -> {
                return !isEqual(left, right);
            }
            case EQEQ -> {
                return isEqual(left, right);
            }
        }

        return null;
    }

    @Override
    public Object
    visitCallExpr(Expr.Call expr)
    {
        Object callee = evaluate(expr.callee);

        List<Object> arguments = new ArrayList<>();
        for (Expr argument : expr.arguments) {
            arguments.add(evaluate(argument));
        }

        if (!(callee instanceof LoxCallable function)) {
            throw new RuntimeError(expr.paren, "Can only call classes, functions or methods.");
        }

        if (arguments.size() != function.arity()) {
            throw new RuntimeError(expr.paren,
                    "Expected " + function.arity() + " arguments" +
                    " but got " + arguments.size() + " instead.");
        }

        return function.call(this, arguments);
    }

    @Override
    public Object
    visitGetExpr(Expr.Get expr)
    {
        Object object = evaluate(expr.object);
        if (object instanceof LoxInstance) {
            return ((LoxInstance)object).get(expr.name);
        }

        throw new RuntimeError(expr.name, "Only instances of an object have properties.");
    }

    @Override
    public Object
    visitGroupingExpr(Expr.Grouping expr)
    {
        return evaluate(expr.expression);
    }

    @Override
    public Object
    visitLiteralExpr(Expr.Literal expr)
    {
        return expr.value;
    }

    @Override
    public Object
    visitLogicalExpr(Expr.Logical expr)
    {
        Object left = evaluate(expr.left);

        if (expr.operator.type == TokenType.OR) {
            if (isTruthy(left)) return left;
        } else {
            if (!isTruthy(left)) return left;
        }

        return evaluate(expr.right);
    }

    @Override
    public Object
    visitSetExpr(Expr.Set expr)
    {
        Object object = evaluate(expr.object);

        if (!(object instanceof LoxInstance)) {
            throw new RuntimeError(expr.name, "only instances have fields.");
        }

        Object value = evaluate(expr.value);
        ((LoxInstance)object).set(expr.name, value);

        return value;
    }

    @Override
    public Object
    visitSuperExpr(Expr.Super expr)
    {
        int distance = locals.get(expr);

        LoxClass superclass = (LoxClass)environment.getAt(distance, "super");
        LoxInstance object = (LoxInstance)environment.getAt(distance - 1, "this");
        LoxFunction method = superclass.findMethod(expr.method.lexeme);

        if (method == null) {
            throw new RuntimeError(expr.method, "Undefined property '" + expr.method.lexeme + "'.");
        }

        return method.bind(object);
    }

    @Override
    public Object
    visitThisExpr(Expr.This expr)
    {
        return lookUpVariable(expr.keyword, expr);
    }

    @Override
    public Object
    visitUnaryExpr(Expr.Unary expr)
    {
        Object right = evaluate(expr.right);

        return switch (expr.operator.type) {
            case BANG -> !isTruthy(right);
            case MINUS -> {
                checkOperand(expr.operator, right);
                yield -(double) right;
            }
            default -> null;
        };
    }

    @Override
    public Object
    visitVariableExpr(Expr.Variable expr)
    {
        return lookUpVariable(expr.name, expr);
    }

    private Object
    lookUpVariable(Token name, Expr expr)
    {
        Integer distance = locals.get(expr);

        if (distance != null) {
            return environment.getAt(distance, name.lexeme);
        } else {
            return globals.get(name);
        }
    }

    private boolean
    isTruthy(Object object)
    {
        if (object == null) return false;
        if (object instanceof Boolean) return (boolean)object;
        return true;
    }

    private boolean
    isEqual(Object a, Object b)
    {
        if (a == null && b == null) return true;
        if (a == null) return false;

        return a.equals(b);
    }

    private void
    checkOperand(Token operator, Object operand)
    {
        if (operand instanceof Double) return;
        throw new RuntimeError(operator, "Operand must be a number.");
    }

    private void
    checkOperands(Token operator, Object left, Object right)
    {
        if (left instanceof Double && right instanceof Double) return;
        throw new RuntimeError(operator, "Operands must be numbers.");
    }

    private String
    stringify(Object object)
    {
        if (object == null) return "nil";

        if (object instanceof Double) {
            String text = object.toString();
            if (text.endsWith(".0")) {
                text = text.substring(0, text.length() - 2);
            }

            return text;
        }

        return object.toString();
    }
}
