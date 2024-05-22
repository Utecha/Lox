#include <stdio.h>
#include <stdlib.h>

#include "common.h"
#include "compiler.h"
#include "scanner.h"

#ifdef DEBUG_PRINT_CODE
#include "debug.h"
#endif // DEBUG_PRINT_CODE

Parser parser;
Chunk *compilingChunk;

static Chunk *
currentChunk()
{
    return compilingChunk;
}

static void
errorAt(Token *token, const char *message)
{
    if (parser.panicMode) return;
    parser.panicMode = true;

    fprintf(stderr, "[line %d] Error", token->line);

    if (token->type == EOF_TK) {
        fprintf(stderr, " at end");
    } else if (token->type == ERROR_TK) {
        // Nothing
    } else {
        fprintf(stderr, " at '%.*s'", token->length, token->start);
    }

    fprintf(stderr, ": %s\n", message);
    parser.hadError = true;
}

static void
error(const char *message)
{
    errorAt(&parser.previous, message);
}

static void
errorAtCurrent(const char *message)
{
    errorAt(&parser.current, message);
}

static void
advance()
{
    parser.previous = parser.current;

    for (;;) {
        parser.current = scanToken();
        if (parser.current.type != ERROR_TK) break;

        errorAtCurrent(parser.current.start);
    }
}

static void
consume(TokenType type, const char *message)
{
    if (parser.current.type == type) {
        advance();
        return;
    }

    errorAtCurrent(message);
}

static bool
check(TokenType type)
{
    return parser.current.type == type;
}

static bool
match(TokenType type)
{
    if (!check(type)) return false;
    advance();
    return true;
}

static void
emitByte(uint8_t byte)
{
    writeChunk(currentChunk(), byte, parser.previous.line);
}

static void
emitBytes(uint8_t byte1, uint8_t byte2)
{
    emitByte(byte1);
    emitByte(byte2);
}

static void
emitReturn()
{
    emitByte(OP_RETURN);
}

static uint8_t
makeConstant(Value value)
{
    int constant = addConstant(currentChunk(), value);
    if (constant > UINT8_MAX) {
        error("Too many constants in one chunk.");
        return 0;
    }

    return (uint8_t)constant;
}

static void
emitConstant(Value value)
{
    emitBytes(OP_CONSTANT, makeConstant(value));
}

static void
endCompiler()
{
    emitReturn();

#ifdef DEBUG_PRINT_CODE
    if (!parser.hadError) {
        disassembleChunk(currentChunk(), "Code");
    }
#endif // DEBUG_PRINT_CODE
}

/* BEGIN FWD DECLARATIONS */
static void
parsePrecedence(Precedence precedence);

static uint8_t
identifierConstant(Token *name);

static ParseRule *
getRule(TokenType type);

static void
expression();

static void
declaration();

static void
statement();
/* END FWD DECLARATIONS */

static void
binary(bool canAssign)
{
    TokenType opType = parser.previous.type;

    ParseRule *rule = getRule(opType);
    parsePrecedence((Precedence)(rule->precedence + 1));

    switch (opType) {
        case BANGEQ_TK:     emitBytes(OP_EQUAL, OP_NOT);    break;
        case EQEQ_TK:       emitByte(OP_EQUAL);             break;
        case GT_TK:         emitByte(OP_GREATER);           break;
        case GTEQ_TK:       emitBytes(OP_LESS, OP_NOT);     break;
        case LT_TK:         emitByte(OP_LESS);              break;
        case LTEQ_TK:       emitBytes(OP_GREATER, OP_NOT);  break;
        case MINUS_TK:      emitByte(OP_SUBTRACT);          break;
        case PLUS_TK:       emitByte(OP_ADD);               break;
        case SLASH_TK:      emitByte(OP_DIVIDE);            break;
        case STAR_TK:       emitByte(OP_MULTIPLY);          break;
        default:            return; // Unreachable
    }
}

static void
literal(bool canAssign)
{
    switch (parser.previous.type) {
        case FALSE_TK:      emitByte(OP_FALSE); break;
        case NIL_TK:        emitByte(OP_NIL);   break;
        case TRUE_TK:       emitByte(OP_TRUE);  break;
        default:            return; // Unreachable
    }
}

static void
grouping(bool canAssign)
{
    expression();
    consume(RPAREN_TK, "Expected ')' after expression.");
}

static void
unary(bool canAssign)
{
    TokenType opType = parser.previous.type;

    parsePrecedence(PREC_UNARY);

    switch (opType) {
        case BANG_TK:   emitByte(OP_NOT);       break;
        case MINUS_TK:  emitByte(OP_NEGATE);    break;
        default:        return; // Unreachable
    }
}

static void
number(bool canAssign)
{
    double value = strtod(parser.previous.start, NULL);
    emitConstant(NUMBER_VAL(value));
}

static void
string(bool canAssign)
{
    emitConstant(
        OBJ_VAL(
            copyString(parser.previous.start + 1, parser.previous.length -2)
        )
    );
}

static void
namedVariable(Token name, bool canAssign)
{
    uint8_t arg = identifierConstant(&name);

    if (canAssign && match(EQ_TK)) {
        expression();
        emitBytes(OP_SET_GLOBAL, arg);
    } else {
        emitBytes(OP_GET_GLOBAL, arg);
    }
}

static void
variable(bool canAssign)
{
    namedVariable(parser.previous, canAssign);
}

ParseRule rules[] = {
    [LPAREN_TK]     = { grouping,   NULL,   PREC_NONE },
    [RPAREN_TK]     = { NULL,       NULL,   PREC_NONE },
    [LBRACE_TK]     = { NULL,       NULL,   PREC_NONE },
    [RBRACE_TK]     = { NULL,       NULL,   PREC_NONE },
    [COMMA_TK]      = { NULL,       NULL,   PREC_NONE },
    [DOT_TK]        = { NULL,       NULL,   PREC_NONE },
    [SEMICOLON_TK]  = { NULL,       NULL,   PREC_NONE },
    [MINUS_TK]      = { unary,      binary, PREC_TERM },
    [PLUS_TK]       = { NULL,       binary, PREC_TERM },
    [SLASH_TK]      = { NULL,       binary, PREC_FACTOR },
    [STAR_TK]       = { NULL,       binary, PREC_FACTOR },
    [BANGEQ_TK]     = { NULL,       binary, PREC_EQUALITY },
    [EQEQ_TK]       = { NULL,       binary, PREC_EQUALITY },
    [GT_TK]         = { NULL,       binary, PREC_COMPARE },
    [GTEQ_TK]       = { NULL,       binary, PREC_COMPARE },
    [LT_TK]         = { NULL,       binary, PREC_COMPARE },
    [LTEQ_TK]       = { NULL,       binary, PREC_COMPARE },
    [BANG_TK]       = { unary,      NULL,   PREC_NONE },
    [EQ_TK]         = { NULL,       NULL,   PREC_NONE },
    [IDENTIFIER_TK] = { variable,   NULL,   PREC_NONE },
    [NUMBER_TK]     = { number,     NULL,   PREC_NONE },
    [STRING_TK]     = { string,     NULL,   PREC_NONE },
    [AND_TK]        = { NULL,       NULL,   PREC_NONE },
    [CLASS_TK]      = { NULL,       NULL,   PREC_NONE },
    [ELSE_TK]       = { NULL,       NULL,   PREC_NONE },
    [FALSE_TK]      = { literal,    NULL,   PREC_NONE },
    [FOR_TK]        = { NULL,       NULL,   PREC_NONE },
    [FUN_TK]        = { NULL,       NULL,   PREC_NONE },
    [IF_TK]         = { NULL,       NULL,   PREC_NONE },
    [NIL_TK]        = { literal,    NULL,   PREC_NONE },
    [OR_TK]         = { NULL,       NULL,   PREC_NONE },
    [PRINT_TK]      = { NULL,       NULL,   PREC_NONE },
    [RETURN_TK]     = { NULL,       NULL,   PREC_NONE },
    [SUPER_TK]      = { NULL,       NULL,   PREC_NONE },
    [THIS_TK]       = { NULL,       NULL,   PREC_NONE },
    [TRUE_TK]       = { literal,    NULL,   PREC_NONE },
    [VAR_TK]        = { NULL,       NULL,   PREC_NONE },
    [WHILE_TK]      = { NULL,       NULL,   PREC_NONE },
    [ERROR_TK]      = { NULL,       NULL,   PREC_NONE },
    [EOF_TK]        = { NULL,       NULL,   PREC_NONE },
};

static void
parsePrecedence(Precedence precedence)
{
    advance();

    ParseFn prefixRule = getRule(parser.previous.type)->prefix;
    if (prefixRule == NULL) {
        error("Expected expression.");
        return;
    }

    bool canAssign = precedence <= PREC_ASSIGN;
    prefixRule(canAssign);

    while (precedence <= getRule(parser.current.type)->precedence) {
        advance();

        ParseFn infixRule = getRule(parser.previous.type)->infix;
        infixRule(canAssign);
    }

    if (canAssign && match(EQ_TK)) error("Invalid assignment target.");
}

static uint8_t
identifierConstant(Token *name)
{
    return makeConstant(OBJ_VAL(copyString(name->start, name->length)));
}

static uint8_t
parseVariable(const char *errorMessage)
{
    consume(IDENTIFIER_TK, errorMessage);
    return identifierConstant(&parser.previous);
}

static void
defineVariable(uint8_t global)
{
    emitBytes(OP_DEFINE_GLOBAL, global);
}

static ParseRule *
getRule(TokenType type)
{
    return &rules[type];
}

static void
expression()
{
    parsePrecedence(PREC_ASSIGN);
}

static void
expressionStatement()
{
    expression();
    consume(SEMICOLON_TK, "Expected ';' after expression.");
    emitByte(OP_POP);
}

static void
printStatement()
{
    expression();
    consume(SEMICOLON_TK, "Expected ';' after print value.");
    emitByte(OP_PRINT);
}

static void
varDeclaration()
{
    uint8_t global = parseVariable("Expected variable name.");

    if (match(EQ_TK)) expression();
    else emitByte(OP_NIL);

    consume(SEMICOLON_TK, "Expected ';' after variable declaration.");
    defineVariable(global);
}

static void
synchronize()
{
    parser.panicMode = false;

    while (parser.current.type != EOF_TK) {
        if (parser.previous.type == SEMICOLON_TK) return;

        switch (parser.current.type) {
            case CLASS_TK:
            case FUN_TK:
            case VAR_TK:
            case FOR_TK:
            case IF_TK:
            case WHILE_TK:
            case PRINT_TK:
            case RETURN_TK:
                return;
            default:
                ; // Do nothing
        }

        advance();
    }
}

static void
declaration()
{
    if (match(VAR_TK)) varDeclaration();
    else statement();

    if (parser.panicMode) synchronize();
}

static void
statement()
{
    if (match(PRINT_TK)) printStatement();
    else expressionStatement();
}

bool
compile(const char *source, Chunk *chunk)
{
    initScanner(source);
    compilingChunk = chunk;

    parser.hadError = false;
    parser.panicMode = false;

    advance();

    while (!match(EOF_TK)) {
        declaration();
    }

    endCompiler();

    return !parser.hadError;
}
