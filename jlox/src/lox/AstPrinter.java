package lox;

class AstPrinter implements Expr.Visitor<String>, Stmt.Visitor<String> {
    /* Begin Statements */
    @Override
    public String visitBlockStmt(Stmt.Block stmt) {
        return buildStmtTree(stmt);
    }

    @Override
    public String visitClassStmt(Stmt.Class stmt) {
        return buildStmtTree(stmt);
    }

    @Override
    public String visitExpressionStmt(Stmt.Expression stmt) {
        return buildStmtTree(stmt);
    }

    @Override
    public String visitFunctionStmt(Stmt.Function stmt) {
        return buildStmtTree(stmt);
    }

    @Override
    public String visitIfStmt(Stmt.If stmt) {
        return buildStmtTree(stmt);
    }

    @Override
    public String visitPrintStmt(Stmt.Print stmt) {
        return buildStmtTree(stmt);
    }

    @Override
    public String visitReturnStmt(Stmt.Return stmt) {
        return buildStmtTree(stmt);
    }

    @Override
    public String visitVarStmt(Stmt.Var stmt) {
        return buildStmtTree(stmt);
    }

    @Override
    public String visitWhileStmt(Stmt.While stmt) {
        return buildStmtTree(stmt);
    }
    /* End Statements */

    /* Begin Expression */
    @Override
    public String visitAssignExpr(Expr.Assign expr) {
        return buildExprTree(expr);
    }

    @Override
    public String visitBinaryExpr(Expr.Binary expr) {
        return buildExprTree(expr);
    }

    @Override
    public String visitCallExpr(Expr.Call expr) {
        return buildExprTree(expr);
    }

    @Override
    public String visitGetExpr(Expr.Get expr) {
        return buildExprTree(expr);
    }

    @Override
    public String visitGroupingExpr(Expr.Grouping expr) {
        return buildExprTree(expr);
    }

    @Override
    public String visitLiteralExpr(Expr.Literal expr) {
        return buildExprTree(expr);
    }

    @Override
    public String visitLogicalExpr(Expr.Logical expr) {
        return buildExprTree(expr);
    }

    @Override
    public String visitSetExpr(Expr.Set expr) {
        return buildExprTree(expr);
    }

    @Override
    public String visitSuperExpr(Expr.Super expr) {
        return buildExprTree(expr);
    }

    @Override
    public String visitThisExpr(Expr.This expr) {
        return buildExprTree(expr);
    }

    @Override
    public String visitUnaryExpr(Expr.Unary expr) {
        return buildExprTree(expr);
    }

    @Override
    public String visitVariableExpr(Expr.Variable expr) {
        return buildExprTree(expr);
    }
    /* End Expressions */

    private String buildBlock(Stmt.Block stmt) {
        String result = "{\n";

        for (Stmt statement : stmt.statements) {
            result += "\t" + statement.accept(this) + "\n";
        }

        result += "}";
        return result;
    }

    private String buildStmtTree(Stmt stmt) {
        String result = "[";

        if (stmt instanceof Stmt.Block) {
            return buildBlock((Stmt.Block) stmt);

        } else if (stmt instanceof Stmt.Class) {
            result += " class " + ((Stmt.Class) stmt).name.lexeme + " ";

            if (((Stmt.Class) stmt).superclass != null) {
                result += " inherits from " + ((Stmt.Class) stmt).superclass.name.lexeme;
            }

            for (Stmt method : ((Stmt.Class) stmt).methods) {
                result += "\n" + method.accept(this);
            }

        } else if (stmt instanceof Stmt.Expression) {
            result += " " + ((Stmt.Expression) stmt).expression.accept(this) + " ";

        } else if (stmt instanceof Stmt.Function) {
            result += " fun " + ((Stmt.Function) stmt).name.lexeme;

            result += " ( ";
            for (Token param : ((Stmt.Function) stmt).params) {
                if (param == ((Stmt.Function) stmt).params.get(((Stmt.Function) stmt).params.size() - 1)) {
                    result += param.lexeme;
                } else {
                    result += param.lexeme + ", ";
                }
            }
            result += " )\n";

            for (Stmt statement : ((Stmt.Function) stmt).body) {
                result += "\t" + statement.accept(this) + "\n";
            }
        } else if (stmt instanceof Stmt.If) {
            result += " if " + ((Stmt.If) stmt).condition.accept(this);
            if (((Stmt.If) stmt).elseBranch != null) {
                result += " then " + ((Stmt.If) stmt).thenBranch.accept(this);
                result += " else " + ((Stmt.If) stmt).elseBranch.accept(this) + " ";
            } else {
                result += " then " + ((Stmt.If) stmt).thenBranch.accept(this) + " ";
            }

        } else if (stmt instanceof Stmt.Print) {
            result += " print " + ((Stmt.Print) stmt).expression.accept(this) + " ";

        } else if (stmt instanceof Stmt.Var) {
            result += " = var " + ((Stmt.Var) stmt).name.lexeme;
            result += " " + ((Stmt.Var) stmt).initializer.accept(this) + " ";

        } else if (stmt instanceof Stmt.While) {
            result += " do " + ((Stmt.While) stmt).body.accept(this);
            result += " while " + ((Stmt.While) stmt).condition.accept(this) + " == true ";
        }

        result += "]";
        return result;
    }

    private String buildExprTree(Expr expr) {
        String result = "(";

        if (expr instanceof Expr.Assign) {
            result += " var " + ((Expr.Assign) expr).name.lexeme;
            result += " = " + ((Expr.Assign) expr).value.accept(this) + " ";

        } else if (expr instanceof Expr.Binary) {
            result += " " + ((Expr.Binary) expr).operator.lexeme;
            result += " " + ((Expr.Binary) expr).left.accept(this);
            result += " " + ((Expr.Binary) expr).right.accept(this) + " ";

        } else if (expr instanceof Expr.Call) {
            result += " call " + ((Expr.Call) expr).callee.accept(this);

            result += " ( ";
            for (Expr argument : ((Expr.Call) expr).arguments) {
                if (argument == ((Expr.Call) expr).arguments.get(((Expr.Call) expr).arguments.size() - 1)) {
                    result += argument.accept(this);
                } else {
                    result += argument.accept(this) + ", ";
                }
            }
            result += " ) ";

        } else if (expr instanceof Expr.Get) {
            result += " Get Property of " + ((Expr.Get) expr).object.accept(this) + " : "
                    + ((Expr.Get) expr).name.lexeme + " ";

        } else if (expr instanceof Expr.Grouping) {
            return "Group " + ((Expr.Grouping) expr).expression.accept(this);

        } else if (expr instanceof Expr.Literal) {
            if (((Expr.Literal) expr).value == null) {
                return "nil";
            } else {
                return ((Expr.Literal) expr).value.toString();
            }

        } else if (expr instanceof Expr.Logical) {
            result += " " + ((Expr.Logical) expr).operator.lexeme;
            result += " " + ((Expr.Logical) expr).left.accept(this);
            result += " " + ((Expr.Logical) expr).right.accept(this) + " ";

        } else if (expr instanceof Expr.Set) {
            result += " Set Property of " + ((Expr.Set) expr).object.accept(this) + " : "
                    + ((Expr.Set) expr).name.lexeme + " = " + ((Expr.Set) expr).value.accept(this) + " ";

        } else if (expr instanceof Expr.This) {
            result += " this ";

        } else if (expr instanceof Expr.Unary) {
            result += " " + ((Expr.Unary) expr).operator.lexeme;
            result += " " + ((Expr.Unary) expr).right.accept(this) + " ";

        } else if (expr instanceof Expr.Variable) {
            result += " " + ((Expr.Variable) expr).name.lexeme + " ";
        }

        result += ")";
        return result;
    }

    String print(Expr expr) {
        return expr.accept(this);
    }

    String print(Stmt stmt) {
        return stmt.accept(this);
    }
}
