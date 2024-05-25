package lox;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.Charset;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.List;

public class Lox {
    private static final Interpreter interpreter = new Interpreter();
    private static boolean hadError = false;
    private static boolean hadRuntimeError = false;
    private static boolean debug = false;

    public static void main(String[] args) throws IOException {
        switch (args.length) {
            case 0 -> {
                debug = false;
                runPrompt();
            }

            case 1 -> {
                if (args[0].equals("-d")) {
                    debug = true;
                    runPrompt();
                } else {
                    debug = false;
                    runFile(args[0]);
                }
            }

            case 2 -> {
                if (args[0].equals("-d")) {
                    debug = true;
                    runFile(args[1]);
                } else {
                    usage();
                }
            }

            default -> usage();
        }
    }

    private static void runFile(String path) throws IOException {
        byte[] bytes = Files.readAllBytes(Paths.get(path));
        run(new String(bytes, Charset.defaultCharset()));

        if (hadError)
            System.exit(65);
        if (hadRuntimeError)
            System.exit(70);
    }

    private static void runPrompt() throws IOException {
        InputStreamReader input = new InputStreamReader(System.in);
        BufferedReader reader = new BufferedReader(input);

        for (;;) {
            System.out.print(">>> ");
            String line = reader.readLine();

            if (line == null) {
                System.out.println();
                break;
            }

            run(line);

            hadError = false;
            hadRuntimeError = false;
        }
    }

    private static void run(String source) {
        Scanner scanner = new Scanner(source);
        List<Token> tokens = scanner.scanTokens();

        Parser parser = new Parser(tokens);
        List<Stmt> statements = parser.parse();

        if (hadError)
            return;

        if (debug) {
            // Tokenization
            for (Token token : tokens) {
                System.out.println(token);
            }

            // Ast Representation
            for (Stmt statement : statements) {
                System.out.println(new AstPrinter().print(statement));
            }
        } else {
            Resolver resolver = new Resolver(interpreter);
            resolver.resolve(statements);

            if (hadError)
                return;

            interpreter.interpret(statements);
        }
    }

    static void usage() {
        System.err.println("Usage: jlox *-d <script>");
        System.err.println("* '-d' is an optional flag for enabling debug info.");
        System.err.println("  This will suppress interpretation, dumping a print-out of");
        System.err.println("  the lexical token generation and the AST-representation generated");
        System.err.println("  by the Parser.");
        System.exit(64);
    }

    static void error(int line, String message) {
        report(line, "", message);
    }

    private static void report(int line, String where, String message) {
        System.err.println("[line " + line + "] Error" + where + ": " + message);
        hadError = true;
    }

    static void error(Token token, String message) {
        if (token.type == TokenType.EOF) {
            report(token.line, " at end", message);
        } else {
            report(token.line, " at '" + token.lexeme + "'", message);
        }
    }

    static void runtimeError(RuntimeError error) {
        System.err.println(error.getMessage() +
                "\n[line " + error.token.line + "]");
        hadRuntimeError = true;
    }
}
