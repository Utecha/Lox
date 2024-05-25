package lox;

enum TokenType {
    // Symbol Tokens
    LPAREN,
    RPAREN,
    LBRACE,
    RBRACE,
    COMMA,
    DOT,
    SEMICOLON,

    // Arithmetic Tokens
    MINUS,
    PLUS,
    SLASH,
    STAR,

    // Equality Tokens
    BANGEQ,
    EQEQ,

    // Comparison Tokens
    GT,
    GTEQ,
    LT,
    LTEQ,

    // Logical Tokens
    BANG,

    // Assignment Tokens
    EQ,

    // Primitive Types
    IDENTIFIER,
    NUMBER,
    STRING,

    AND,
    CLASS,
    ELSE,
    FALSE,
    FOR,
    FUN,
    IF,
    NIL,
    OR,
    PRINT,
    RETURN,
    SUPER,
    THIS,
    TRUE,
    VAR,
    WHILE,

    EOF
}
