#ifndef CLOX_SCANNER_H
#define CLOX_SCANNER_H

typedef enum {
    // Symbol Tokens
    LPAREN_TK,
    RPAREN_TK,
    LBRACE_TK,
    RBRACE_TK,
    COMMA_TK,
    DOT_TK,
    SEMICOLON_TK,

    // Arithmetic Tokens
    MINUS_TK,
    PLUS_TK,
    SLASH_TK,
    STAR_TK,

    // Equality Tokens
    BANGEQ_TK,
    EQEQ_TK,

    // Comparison Tokens
    GT_TK,
    GTEQ_TK,
    LT_TK,
    LTEQ_TK,

    // Logical Tokens
    BANG_TK,

    // Assignment Tokens
    EQ_TK,

    // Primitive Types
    IDENTIFIER_TK,
    NUMBER_TK,
    STRING_TK,

    // Language Built-In Keywords
    AND_TK,
    CLASS_TK,
    ELSE_TK,
    FALSE_TK,
    FOR_TK,
    FUN_TK,
    IF_TK,
    NIL_TK,
    OR_TK,
    PRINT_TK,
    RETURN_TK,
    SUPER_TK,
    THIS_TK,
    TRUE_TK,
    VAR_TK,
    WHILE_TK,

    // Special Tokens
    ERROR_TK,
    EOF_TK
} TokenType;

typedef struct {
    TokenType type;
    const char *start;
    int length;
    int line;
} Token;

typedef struct {
    const char *start;
    const char *current;
    int line;
} Scanner;

void
initScanner(const char *source);

Token
scanToken();

#endif // CLOX_SCANNER_H
