#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "common.h"
#include "compiler.h"
#include "scanner.h"

#ifdef DEBUG_PRINT_CODE
#include "debug.h"
#endif // DEBUG_PRINT_CODE

Parser parser;
Compiler *current = NULL;

static Chunk *
currentChunk()
{
    return &current->function->chunk;
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
emitLoop(int loopStart)
{
    emitByte(OP_LOOP);

    int offset = currentChunk()->count - loopStart + 2;
    if (offset > UINT16_MAX) error("Loop body too large.");

    emitByte((offset >> 8) & 0xff);
    emitByte(offset & 0xff);
}

static int
emitJump(uint8_t instruction)
{
    emitByte(instruction);
    emitByte(0xff);
    emitByte(0xff);
    return currentChunk()->count - 2;
}

static void
emitReturn()
{
    emitByte(OP_NIL);
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
patchJump(int offset)
{
    // -2 to adjust the bytecode for the jump offset
    int jump = currentChunk()->count - offset - 2;

    if (jump > UINT16_MAX) {
        error("Too much code to jump over.");
    }

    currentChunk()->code[offset] = (jump >> 8) & 0xff;
    currentChunk()->code[offset + 1] = jump & 0xff;
}

static void
initCompiler(Compiler *compiler, FunctionType type)
{
    compiler->enclosing = current;
    compiler->function = NULL;
    compiler->type = type;
    compiler->localCount = 0;
    compiler->scopeDepth = 0;
    compiler->function = newFunction();
    current = compiler;

    if (type != TYPE_SCRIPT) {
        current->function->name = copyString(parser.previous.start,
                                             parser.previous.length);
    }

    Local *local = &current->locals[current->localCount++];
    local->depth = 0;
    local->isCaptured = false;
    local->name.start = "";
    local->name.length = 0;
}

static ObjFunction *
endCompiler()
{
    emitReturn();
    ObjFunction *function = current->function;

#ifdef DEBUG_PRINT_CODE
    if (!parser.hadError) {
        disassembleChunk(currentChunk(), function->name != NULL ?
                         function->name->chars : "<Script>");
    }
#endif // DEBUG_PRINT_CODE

    current = current->enclosing;
    return function;
}

static void
beginScope()
{
    current->scopeDepth++;
}

static void
endScope()
{
    current->scopeDepth--;

    while (current->localCount > 0 &&
           current->locals[current->localCount - 1].depth >
           current->scopeDepth) {

        if (current->locals[current->localCount - 1].isCaptured) {
            emitByte(OP_CLOSE_UPVALUE);
        } else {
            emitByte(OP_POP);
        }
        current->localCount--;
    }
}

/* BEGIN FWD DECLARATIONS */
static void
parsePrecedence(Precedence precedence);

static uint8_t
identifierConstant(Token *name);

static int
resolveUpvalue(Compiler *compiler, Token *name);

static int
resolveLocal(Compiler *compiler, Token *name);

static uint8_t
argumentList();

static ParseRule *
getRule(TokenType type);

static void
expression();

static void
varDeclaration();

static void
declaration();

static void
statement();
/* END FWD DECLARATIONS */

static void
and_(bool canAssign)
{
    int endJump = emitJump(OP_JUMP_IF_FALSE);

    emitByte(OP_POP);
    parsePrecedence(PREC_AND);

    patchJump(endJump);
}

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
call(bool canAssign)
{
    uint8_t argCount = argumentList();
    emitBytes(OP_CALL, argCount);
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
or_(bool canAssign)
{
    int elseJump = emitJump(OP_JUMP_IF_FALSE);
    int endJump = emitJump(OP_JUMP);

    patchJump(elseJump);
    emitByte(OP_POP);

    parsePrecedence(PREC_OR);
    patchJump(endJump);
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
    uint8_t getOp, setOp;
    int arg = resolveLocal(current, &name);

    if (arg != -1) {
        getOp = OP_GET_LOCAL;
        setOp = OP_SET_LOCAL;
    } else if ((arg = resolveUpvalue(current, &name)) != -1) {
        getOp = OP_GET_UPVALUE;
        setOp = OP_SET_UPVALUE;
    } else {
        arg = identifierConstant(&name);
        getOp = OP_GET_GLOBAL;
        setOp = OP_SET_GLOBAL;
    }

    if (canAssign && match(EQ_TK)) {
        expression();
        emitBytes(setOp, (uint8_t)arg);
    } else {
        emitBytes(getOp, (uint8_t)arg);
    }
}

static void
variable(bool canAssign)
{
    namedVariable(parser.previous, canAssign);
}

ParseRule rules[] = {
    [LPAREN_TK]     = { grouping,   call,   PREC_CALL },
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
    [AND_TK]        = { NULL,       and_,   PREC_AND },
    [CLASS_TK]      = { NULL,       NULL,   PREC_NONE },
    [ELSE_TK]       = { NULL,       NULL,   PREC_NONE },
    [FALSE_TK]      = { literal,    NULL,   PREC_NONE },
    [FOR_TK]        = { NULL,       NULL,   PREC_NONE },
    [FUN_TK]        = { NULL,       NULL,   PREC_NONE },
    [IF_TK]         = { NULL,       NULL,   PREC_NONE },
    [NIL_TK]        = { literal,    NULL,   PREC_NONE },
    [OR_TK]         = { NULL,       or_,    PREC_OR },
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

static bool
identifiersEqual(Token *a, Token *b)
{
    if (a->length != b->length) return false;
    return memcmp(a->start, b->start, a->length) == 0;
}

static int
resolveLocal(Compiler *compiler, Token *name)
{
    for (int i = compiler->localCount - 1; i >= 0; i--) {
        Local *local = &compiler->locals[i];

        if (identifiersEqual(name, &local->name)) {
            if (local->depth == -1) {
                error("Cannot read a variable within its own initializer.");
            }

            return i;
        }
    }

    return -1;
}

static int
addUpvalue(Compiler *compiler, uint8_t index, bool isLocal)
{
    int upvalueCount = compiler->function->upvalueCount;

    for (int i = 0; i < upvalueCount; i++) {
        Upvalue *upvalue = &compiler->upvalues[i];

        if (upvalue->index == index && upvalue->isLocal == isLocal) {
            return i;
        }
    }

    if (upvalueCount == UINT8_COUNT) {
        error("Too many closure variables within a function.");
        return 0;
    }

    compiler->upvalues[upvalueCount].isLocal = isLocal;
    compiler->upvalues[upvalueCount].index = index;
    return compiler->function->upvalueCount++;
}

static int
resolveUpvalue(Compiler *compiler, Token *name)
{
    if (compiler->enclosing == NULL) return -1;

    int local = resolveLocal(compiler->enclosing, name);
    if (local != -1) {
        compiler->enclosing->locals[local].isCaptured = true;
        return addUpvalue(compiler, (uint8_t)local, true);
    }

    int upvalue = resolveUpvalue(compiler->enclosing, name);
    if (upvalue != -1) {
        return addUpvalue(compiler, (uint8_t)upvalue, false);
    }

    return -1;
}

static void
addLocal(Token name)
{
    if (current->localCount == UINT8_COUNT) {
        error("Too many local variables in function.");
        return;
    }

    Local *local = &current->locals[current->localCount++];
    local->name = name;
    local->depth = -1;
    local->isCaptured = false;
}

static void
declareVariable()
{
    if (current->scopeDepth == 0) return;

    Token *name = &parser.previous;

    for (int i = current->localCount - 1; i >= 0; i--) {
        Local *local = &current->locals[i];

        if (local->depth != -1 && local->depth < current->scopeDepth) {
            break;
        }

        if (identifiersEqual(name, &local->name)) {
            error("Already a variable with this name in this scope.");
        }
    }

    addLocal(*name);
}

static uint8_t
parseVariable(const char *errorMessage)
{
    consume(IDENTIFIER_TK, errorMessage);

    declareVariable();
    if (current->scopeDepth > 0) return 0;

    return identifierConstant(&parser.previous);
}

static void
markInitialized()
{
    if (current->scopeDepth == 0) return;
    current->locals[current->localCount - 1].depth = current->scopeDepth;
}

static void
defineVariable(uint8_t global)
{
    if (current->scopeDepth > 0) {
        markInitialized();
        return;
    }

    emitBytes(OP_DEFINE_GLOBAL, global);
}

static uint8_t
argumentList()
{
    uint8_t argCount = 0;

    if (!check(RPAREN_TK)) {
        do {
            expression();

            if (argCount == 255) {
                error("Cannot have more than 255 arguments.");
            }

            argCount++;
        } while (match(COMMA_TK));
    }
    consume(RPAREN_TK, "Expected ')' after arguments.");

    return argCount;
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
block()
{
    while (!check(RBRACE_TK) && !check(EOF_TK)) {
        declaration();
    }

    consume(RBRACE_TK, "Expected '}' after block.");
}

static void
expressionStatement()
{
    expression();
    consume(SEMICOLON_TK, "Expected ';' after expression.");
    emitByte(OP_POP);
}

static void
forStatement()
{
    beginScope();
    consume(LPAREN_TK, "Expected '(' after 'for'.");

    if (match(SEMICOLON_TK)) {
        // Do nothing
    } else if (match(VAR_TK)) {
        varDeclaration();
    } else {
        expressionStatement();
    }

    consume(SEMICOLON_TK, "Expected ';' alone or after loop init expression.");

    int loopStart = currentChunk()->count;

    int exitJump = -1;
    if (!match(SEMICOLON_TK)) {
        expression();
        consume(SEMICOLON_TK, "Expected ';' after loop condition.");

        // Jump out of the loop if the condition is false
        exitJump = emitJump(OP_JUMP_IF_FALSE);
        emitByte(OP_POP); // Condition
    }


    if (!match(RPAREN_TK)) {
        int bodyJump = emitJump(OP_JUMP);
        int incrementStart = currentChunk()->count;

        expression();
        emitByte(OP_POP);
        consume(RPAREN_TK, "Expected ')' after for clauses.");

        emitLoop(loopStart);
        loopStart = incrementStart;
        patchJump(bodyJump);
    }

    statement();
    emitLoop(loopStart);

    if (exitJump != -1) {
        patchJump(exitJump);
        emitByte(OP_POP); // Condition
    }

    endScope();
}

static void
function(FunctionType type)
{
    Compiler compiler;
    initCompiler(&compiler, type);
    beginScope();

    consume(LPAREN_TK, "Expected '(' after function name.");
    if (!check(RPAREN_TK)) {
        do {
            current->function->arity++;

            if (current->function->arity > 255) {
                errorAtCurrent("Cannot have more than 255 parameters.");
            }

            uint8_t constant = parseVariable("Expected parameter name.");
            defineVariable(constant);
        } while (match(COMMA_TK));
    }

    consume(RPAREN_TK, "Expected ')' after parameters.");
    consume(LBRACE_TK, "Expected '{' before function body.");
    block();

    ObjFunction *function = endCompiler();
    emitBytes(OP_CLOSURE, makeConstant(OBJ_VAL(function)));

    for (int i = 0; i < function->upvalueCount; i++) {
        emitByte(compiler.upvalues[i].isLocal ? 1 : 0);
        emitByte(compiler.upvalues[i].index);
    }
}

static void
funDeclaration()
{
    uint8_t global = parseVariable("Expected function name.");
    markInitialized();
    function(TYPE_FUNCTION);
    defineVariable(global);
}

static void
ifStatement()
{
    consume(LPAREN_TK, "Expected '(' after 'if'.");
    expression();
    consume(RPAREN_TK, "Expected ')' after condition.");

    int thenJump = emitJump(OP_JUMP_IF_FALSE);
    emitByte(OP_POP);
    statement();

    int elseJump = emitJump(OP_JUMP);
    patchJump(thenJump);
    emitByte(OP_POP);

    if (match(ELSE_TK)) statement();
    patchJump(elseJump);

}

static void
printStatement()
{
    expression();
    consume(SEMICOLON_TK, "Expected ';' after print value.");
    emitByte(OP_PRINT);
}

static void
returnStatement()
{
    if (current->type == TYPE_SCRIPT) {
        error("Cannot return from top-level code.");
    }

    if (match(SEMICOLON_TK)) {
        emitReturn();
    } else {
        expression();
        consume(SEMICOLON_TK, "Expected ';' after return value.");
        emitByte(OP_RETURN);
    }
}

static void
whileStatement()
{
    int loopStart = currentChunk()->count;

    consume(LPAREN_TK, "Expected '(' after 'while'.");
    expression();
    consume(RPAREN_TK, "Expected ')' after condition.");

    int exitJump = emitJump(OP_JUMP_IF_FALSE);
    emitByte(OP_POP);
    statement();

    emitLoop(loopStart);

    patchJump(exitJump);
    emitByte(OP_POP);
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
    if (match(FUN_TK)) funDeclaration();
    else if (match(VAR_TK)) varDeclaration();
    else statement();

    if (parser.panicMode) synchronize();
}

static void
statement()
{
    if (match(PRINT_TK)) {
        printStatement();
    } else if (match(LBRACE_TK)) {
        beginScope();
        block();
        endScope();
    } else if (match(FOR_TK)) {
        forStatement();
    } else if (match(IF_TK)) {
        ifStatement();
    } else if (match(RETURN_TK)) {
        returnStatement();
    } else if (match(WHILE_TK)) {
        whileStatement();
    } else {
        expressionStatement();
    }
}

ObjFunction *
compile(const char *source)
{
    initScanner(source);

    Compiler compiler;
    initCompiler(&compiler, TYPE_SCRIPT);

    parser.hadError = false;
    parser.panicMode = false;

    advance();

    while (!match(EOF_TK)) {
        declaration();
    }

    ObjFunction *function = endCompiler();
    return parser.hadError ? NULL : function;
}
