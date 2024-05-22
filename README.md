# Lox

Lox is a dynamically-typed, garbage collected scripting language developed for the book Crafting Interpreters by Robert Nystrom.

This repo will contain the following:

1. My implementations of the original language in every form I've done it in. Following the book, there are two implementations: A tree-walk interpreted version written in Java, and a bytecode compiled VM version written in C. On top of that, I've experimented with writing it in Python, as well as Kotlin.

2. Links to another repo where I will keep my own complete language implementation roughly based on what I've learned thus far. I am constantly inspired by various features of other languages and have many features I would like to add. One of the many goals with this is to write a combination of a VM-interpreted language with an optional native compiler. Look forward to that!


## Table of Contents

- [Features](#features)
- [Usage](#usage)
- [MANUAL](#manual)
- [LICENSE](https://github.com/Utecha/Lax/blob/main/LICENSE)

## Features

- Arithmetic Operators ( + || - || * || / )
- Comparison Operators ( > || >= || < || <= )
- Equality Operators ( == || != )
- Unary Operators ( ! || - )
- Variables Declaration & Definition (like C -- Declared variables left undefined are initialized to 'nil');
- 'nil', 'true', and 'false' as functional keywords. Nil is a rough equivalent to NULL from C and other languages.
- Functions
- Classes, Methods, and Inheritance
- Pretty fast -- Bytecode compiled with a VM to interpret, and a built in garbage collector.
- Garbage-Collected

## Usage

To install, first clone the repo:

```console
git clone https://github.com/Utecha/lox.git
cd lox
```

At the current moment, this repo currently only has clox, so all you need to do is run ```make```. If for any reason you need to rebuild it or want to clean out the binaries, run ```make clean```.

Afterwards, all you need to do is run...

```console
./clox <path_to_your_script>
```

Or...

```console
./clox
```

The binary alone runs the REPL. Including an argument will attempt to run a file, so make sure it is a proper Lox script! Technically the file extension does not matter, but the convention would be ```.lox``` :)


## MANUAL

The manual is surprisingly extensive for such as language. This will be implemented soon!
