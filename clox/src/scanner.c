#include <stdio.h>
#include <string.h>

#include "common.h"
#include "scanner.h"

Scanner scanner;

static bool
isAtEnd()
{
    return *scanner.start == '\0';
}

static char
advance()
{
    scanner.current++;
    return scanner.current[-1];
}

static char
peek()
{
    return *scanner.current;
}

static char
peekNext()
{
    if (isAtEnd()) return '\0';
    return scanner.current[1];
}

static bool
match(char expected)
{
    if (isAtEnd()) return false;
    if (*scanner.current != expected) return false;

    scanner.current++;
    return true;
}

static Token
makeToken(TokenType type)
{
    Token token;

    token.type = type;
    token.start = scanner.start;
    token.length = (int)(scanner.current - scanner.start);
    token.line = scanner.line;

    return token;
}

static Token
errorToken(const char *message)
{
    Token token;

    token.type = ERROR_TK;
    token.start = message;
    token.length = (int)strlen(message);
    token.line = scanner.line;

    return token;
}

static void
skipWhitespace()
{
    for (;;) {
        char c = peek();
        switch (c) {
            case ' ':
            case '\r':
            case '\t': {
                advance();
            } break;

            case '\n': {
                scanner.line++;
                advance();
            } break;

            case '/': {
                if (peekNext() == '/') {
                    while (peek() != '\n' && !isAtEnd()) advance();
                } else {
                    return;
                }
            } break;

            default:
                return;
        }
    }
}

static bool
isAlpha(char c)
{
    return (c >= 'a' && c <= 'z') ||
           (c >= 'A' && c <= 'Z') ||
            c == '_';
}

static bool
isDigit(char c)
{
    return c >= '0' && c <= '9';
}

static bool
isAlphaNumeric(char c)
{
    return isAlpha(c) || isDigit(c);
}

static TokenType
checkKeyword(int start, int length, const char *rest, TokenType type)
{
    if (scanner.current - scanner.start == start + length &&
        memcmp(scanner.start + start, rest, length) == 0) {

        return type;
    }

    return IDENTIFIER_TK;
}

static TokenType
identifierType()
{
    switch (scanner.start[0]) {
        case 'a':   return checkKeyword(1, 2, "nd", AND_TK);
        case 'c':   return checkKeyword(1, 4, "lass", CLASS_TK);
        case 'e':   return checkKeyword(1, 3, "lse", ELSE_TK);
        case 'f': {
            if (scanner.current - scanner.start > 1) {
                switch (scanner.start[1]) {
                    case 'a':   return checkKeyword(2, 3, "lse", FALSE_TK);
                    case 'o':   return checkKeyword(2, 1, "r", FOR_TK);
                    case 'u':   return checkKeyword(2, 1, "n", FUN_TK);
                }
            }
        } break;
        case 'i':   return checkKeyword(1, 1, "f", IF_TK);
        case 'n':   return checkKeyword(1, 2, "il", NIL_TK);
        case 'o':   return checkKeyword(1, 1, "r", OR_TK);
        case 'p':   return checkKeyword(1, 4, "rint", PRINT_TK);
        case 'r':   return checkKeyword(1, 5, "eturn", RETURN_TK);
        case 's':   return checkKeyword(1, 4, "uper", SUPER_TK);
        case 't': {
            if (scanner.current - scanner.start > 1) {
                switch (scanner.start[1]) {
                    case 'h':   return checkKeyword(2, 2, "is", THIS_TK);
                    case 'r':   return checkKeyword(2, 2, "ue", TRUE_TK);
                }
            }
        } break;
        case 'v':   return checkKeyword(1, 2, "ar", VAR_TK);
        case 'w':   return checkKeyword(1, 4, "hile", WHILE_TK);
    }

    return IDENTIFIER_TK;
}

static Token
identifier()
{
    while (isAlphaNumeric(peek())) advance();

    return makeToken(identifierType());
}

static Token
number()
{
    while (isDigit(peek())) advance();

    if (peek() == '.' && isDigit(peekNext())) {
        advance();

        while (isDigit(peek())) advance();
    }

    return makeToken(NUMBER_TK);
}

static Token
string()
{
    while (peek() != '"' && !isAtEnd()) {
        if (peek() == '\n') scanner.line++;
        advance();
    }

    if (isAtEnd()) return errorToken("Unterminated String.");

    advance();
    return makeToken(STRING_TK);
}

void
initScanner(const char *source)
{
    scanner.start = source;
    scanner.current = source;
    scanner.line = 1;
}

Token
scanToken()
{
    skipWhitespace();
    scanner.start = scanner.current;

    if (isAtEnd()) return makeToken(EOF_TK);

    char c = advance();
    if (isAlpha(c)) return identifier();
    if (isDigit(c)) return number();

    switch (c) {
        case '(':   return makeToken(LPAREN_TK);
        case ')':   return makeToken(RPAREN_TK);
        case '{':   return makeToken(LBRACE_TK);
        case '}':   return makeToken(RBRACE_TK);
        case ',':   return makeToken(COMMA_TK);
        case '.':   return makeToken(DOT_TK);
        case ';':   return makeToken(SEMICOLON_TK);
        case '-':   return makeToken(MINUS_TK);
        case '+':   return makeToken(PLUS_TK);
        case '/':   return makeToken(SLASH_TK);
        case '*':   return makeToken(STAR_TK);
        case '!':   return makeToken(match('=') ? BANGEQ_TK : BANG_TK);
        case '=':   return makeToken(match('=') ? EQEQ_TK : EQ_TK);
        case '>':   return makeToken(match('=') ? GTEQ_TK : GT_TK);
        case '<':   return makeToken(match('=') ? LTEQ_TK : LT_TK);
        case '"':   return string();
    }

    return errorToken("Unexpected Character.");
}
