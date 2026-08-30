# SababaLang

A small programming language with Hebrew keywords, together with the compiler
front end, a C code generator, a tree-walking interpreter, and a simple IDE.

Written in Python. The compiler and interpreter use only the standard library;
the IDE uses PyQt5.

---

## Overview

SababaLang replaces the usual English keywords with Hebrew words drawn from
everyday speech. `יאללה` opens a program, `שים` assigns, `תדפיס` prints,
`סבבה` and `באסה` are the boolean literals.

The point of the project was to build the compiler pipeline end to end rather
than to produce a language anyone should use in production. Source text goes
through a lexer, a recursive-descent parser and a semantic analyzer, and the
resulting AST is then consumed by one of two back ends: a C code generator, or
an interpreter that executes the tree directly.

```
                                     ┌──> CodeGenerator ──> C source ──> gcc
source ──> Lexer ──> Parser ──> AST ─┤
              (tokens)   │           └──> Evaluator ──> executed in Python
                         └──> SemanticAnalyzer (type & scope checks)
```

---

## Language

| Concept | Common syntax | SababaLang | Literal meaning |
|---|---|---|---|
| Program start | `main` | `יאללה` | "let's go" |
| Program end | `exit` | `סיימנו` | "we're done" |
| Assignment | `=` | `שים` | "put" |
| Integer type | `int` | `מספר` | "number" |
| String type | `string` | `טקסט` | "text" |
| Print | `print` | `תדפיס` | "print" |
| If / then / else | `if` / `else` | `אם` / `אז` / `אחרת` | |
| True / false | `true` / `false` | `סבבה` / `באסה` | "cool" / "bummer" |
| While | `while` | `כלעוד` | "as long as" |
| For | `for` | `לכל` | "for each" |
| Function | `def` | `פונקציה` | |
| Return | `return` | `תחזיר` | "give back" |
| Array | `array` | `רשימה` | "list" |
| Import | `import` | `ייבא` | |

Error messages are also written in Hebrew and carry the source line number.

---

## Two back ends, different coverage

This is the most important thing to know before running anything. Both back
ends walk the same AST, but they do not support the same subset of the
language.

| Feature | Interpreter (IDE) | C back end (`compiler.py`) |
|---|---|---|
| Variables, types, assignment | yes | yes |
| Arithmetic, comparison, logic, unary | yes | yes |
| `אם` / `אחרת` | yes | yes |
| `כלעוד` (while) | yes | yes |
| `תדפיס` (print) | yes | yes |
| Functions and calls | yes | **no** |
| `לכל` (for) | yes | **no** |
| Arrays and indexing | yes | **no** |
| `ייבא` (import) | yes | **no** |

The interpreter implements visitors for all 18 AST node types; the C generator
implements 11. Passing a program that uses functions, for-loops, arrays or
imports to `compiler.py` produces a "no idea how to translate this node" error.
Everything in `stdlib/` is written with functions, so the standard library is
currently interpreter-only.

Example files in `examples/` are named to make this explicit.

---

## Installation

Python 3.10 or newer.

```bash
git clone https://github.com/<your-username>/sababa-lang.git
cd sababa-lang
```

The compiler and interpreter need no third-party packages. Only the IDE does:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

To run the tests as well:

```bash
pip install -r requirements-dev.txt
```

---

## Usage

**Compile to C:**

```bash
python compiler.py examples/02_conditionals.sababa
```

This writes `examples/02_conditionals.c` next to the source.

**Compile, build with gcc and run:**

```bash
python compiler.py examples/02_conditionals.sababa --run
```

**Inspect the tokens and the AST:**

```bash
python compiler.py examples/02_conditionals.sababa --verbose
```

**Launch the IDE (interpreter, supports the whole language):**

```bash
python sababa.py
```

---

## Example

```
יאללה

מספר גיל שים 22

אם גיל > 18 אז {
    תדפיס "אתה יכול לתכנת בסבבה!"
} אחרת {
    תדפיס "איזה באסה, תחזור כשתגדל."
}

סיימנו
```

The C back end emits:

```c
// --- תורגם אוטומטית מ-SababaLang ---
#include <stdio.h>
#include <stdbool.h>

int main() {
    int גיל = 22;
    if ((גיל > 18)) {
        printf("%s\n", "אתה יכול לתכנת בסבבה!");
    } else {
        printf("%s\n", "איזה באסה, תחזור כשתגדל.");
    }
    return 0;
}
```

The Hebrew identifiers survive into the C source. GCC accepts them as extended
identifiers, so the file compiles and runs unchanged.

---

## Testing

```bash
python -m pytest tests -v
```

16 tests cover the lexer's keyword recognition and line tracking, the parser's
AST construction and operator precedence, the semantic analyzer's type and
scope errors, the interpreter's loops, recursion and array indexing, and the
shape of the generated C. Two tests deliberately pin known gaps so that they
fail once those gaps are closed.

---

## Project structure

```
sababa-lang/
├── compiler.py           CLI driver: source -> C, optionally gcc + run
├── sababa.py             SababaCharm IDE (PyQt5), runs the interpreter
├── lexer.py              text -> tokens
├── sababa_token.py       TokenType enum, Token, KEYWORDS table
├── parser.py             recursive-descent parser -> AST
├── ast_nodes.py          18 AST node classes
├── semantic.py           scoped symbol table, type checks
├── codegen.py            AST -> C source (visitor pattern)
├── evaluator.py          AST -> executed directly (visitor pattern)
├── stdlib/               libraries written in SababaLang (interpreter only)
├── examples/             sample programs
└── tests/                pytest suite
```

The parser expresses precedence through its call chain:
`expression → logical_or → logical_and → equality → comparison → term →
factor → unary → primary`. Each level consumes tighter-binding operators than
the one above it.

`sababa_token.py` is named that way on purpose, to avoid shadowing the standard
library's `token` module.

---

## Limitations

These are real and known, not oversights discovered by users:

- **The C back end covers 11 of 18 node types.** See the coverage table above.
  Functions, for-loops, arrays and imports run only under the interpreter.
- **The semantic analyzer only checks top-level statements.** It has no
  visitors for `IfStmt`, `WhileStmt`, `ForStmt`, `PrintStmt`, `ReturnStmt`,
  `UnaryOp`, `ArrayLiteral`, `ArrayAccess` or `ImportStmt`, and `generic_visit`
  does nothing. Because nothing recurses into a control-flow body, a type error
  inside an `אם` block is not reported. Two tests document this.
- **No function return-type inference.** Calls are typed `לא_ידוע` ("unknown")
  and skipped by the type checker, so a function's return value can be assigned
  to a variable of any type.
- **Integers only.** There is no floating-point type.
- **No line number on semantic errors.** They are all raised with line 0;
  only lexer and parser errors carry a real position.
- **The IDE has no file open/save.** Code is typed into the editor and run.

## Possible next steps

- Implement `FunctionDef`, `FunctionCall`, `ForStmt`, `ArrayLiteral`,
  `ArrayAccess` and `ImportStmt` in the C back end so both back ends agree.
- Add the missing semantic visitors so checking descends into block bodies.
- Carry token line numbers into the AST so semantic errors can report position.
- Open/save files in the IDE.
