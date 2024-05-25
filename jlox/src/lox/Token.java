package lox;

class Token {
    final TokenType type;
    final String lexeme;
    final Object literal;
    final int line;

    Token(TokenType type, String lexeme, Object literal, int line)
    {
        this.type = type;
        this.lexeme = lexeme;
        this.literal = literal;
        this.line = line;
    }

    public String
    toString()
    {
        String result = "[ " + type + " ]\n";
        result += "Lexeme : ( " + lexeme + " )\n";
        result += "Literal : ( " + literal + " )\n";
        result += "Line : " + line + "\n";

        return result;
    }
}
