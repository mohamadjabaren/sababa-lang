"""
Tests for the SababaLang compiler pipeline.

Each stage is tested in isolation where possible: lexer, parser, semantic
analyzer, interpreter, and C code generator.

Run with:  python -m pytest tests -v
"""
import pytest

from lexer import Lexer, SababaError
from parser import Parser
from semantic import SemanticAnalyzer
from evaluator import Evaluator
from codegen import CodeGenerator
from ast_nodes import Program, VarDecl, IfStmt, FunctionDef


def parse(source: str) -> Program:
    """Run the front end: source text -> AST."""
    return Parser(Lexer(source).tokenize()).parse()


def run(source: str, capsys) -> str:
    """Interpret a program and return everything it printed."""
    ast = parse(source)
    SemanticAnalyzer().analyze(ast)
    ev = Evaluator()
    for stmt in ast.statements:
        ev.evaluate(stmt)
    return capsys.readouterr().out


# ── Lexer ────────────────────────────────────────────────────────────────────
def test_lexer_recognises_hebrew_keywords():
    tokens = Lexer("יאללה\nסיימנו").tokenize()
    assert [t.value for t in tokens][:2] == ["יאללה", "סיימנו"]


def test_lexer_tracks_line_numbers_for_error_messages():
    tokens = Lexer("יאללה\n\nתדפיס 1\nסיימנו").tokenize()
    print_token = next(t for t in tokens if t.value == "תדפיס")
    assert print_token.line == 3


# ── Parser ───────────────────────────────────────────────────────────────────
def test_parser_builds_a_variable_declaration():
    ast = parse("יאללה\nמספר גיל שים 22\nסיימנו")
    decl = next(s for s in ast.statements if isinstance(s, VarDecl))
    assert decl.name == "גיל" and decl.var_type == "מספר"


def test_parser_builds_an_if_else():
    ast = parse('יאללה\nמספר x שים 5\nאם x > 1 אז {\nתדפיס "כן"\n} אחרת {\nתדפיס "לא"\n}\nסיימנו')
    stmt = next(s for s in ast.statements if isinstance(s, IfStmt))
    assert stmt.else_branch is not None


def test_operator_precedence_multiplication_binds_tighter_than_addition(capsys):
    """2 + 3 * 4 must be 14, not 20 — precedence lives in the parser's chain."""
    assert run("יאללה\nתדפיס 2 + 3 * 4\nסיימנו", capsys).strip() == "14"


# ── Semantic analyzer ────────────────────────────────────────────────────────
def test_semantic_rejects_type_mismatch():
    ast = parse('יאללה\nמספר גיל שים "טקסט"\nסיימנו')
    with pytest.raises(SababaError):
        SemanticAnalyzer().analyze(ast)


def test_semantic_rejects_undeclared_variable():
    ast = parse("יאללה\nx שים 5\nסיימנו")
    with pytest.raises(SababaError):
        SemanticAnalyzer().analyze(ast)


def test_semantic_rejects_arithmetic_on_text():
    ast = parse('יאללה\nטקסט a שים "שלום"\nמספר b שים a - 1\nסיימנו')
    with pytest.raises(SababaError):
        SemanticAnalyzer().analyze(ast)


# ── Documented limitation of the semantic analyzer ───────────────────────────
# The analyzer has visitors for Program, Block, VarDecl, Assign, BinaryOp,
# Literal, VarAccess, FunctionDef and FunctionCall. It has none for IfStmt,
# WhileStmt, ForStmt, PrintStmt, ReturnStmt, UnaryOp, ArrayLiteral,
# ArrayAccess or ImportStmt, and generic_visit is a no-op. Nothing therefore
# recurses into a control-flow body, so checking stops at the top level.
# The tests below pin that boundary so it fails loudly once it is fixed.

def test_known_gap_errors_inside_control_flow_bodies_are_not_checked():
    inside_if = 'יאללה\nאם 1 < 2 אז {\nמספר x שים "טקסט"\n}\nסיימנו'
    SemanticAnalyzer().analyze(parse(inside_if))  # currently passes; should not


def test_known_gap_expressions_inside_print_are_not_checked():
    ast = parse("יאללה\nפונקציה f(x) {\nתחזיר x\n}\nתדפיס f(1, 2)\nסיימנו")
    SemanticAnalyzer().analyze(ast)  # wrong arity, currently not reported


# ── Interpreter ──────────────────────────────────────────────────────────────
def test_interpreter_runs_a_while_loop(capsys):
    src = "יאללה\nמספר i שים 0\nכלעוד i < 3 {\nתדפיס i\ni שים i + 1\n}\nסיימנו"
    assert run(src, capsys).split() == ["0", "1", "2"]


def test_interpreter_supports_recursion(capsys):
    src = ("יאללה\nפונקציה עצרת(n) {\n"
           "אם n <= 1 אז {\nתחזיר 1\n} אחרת {\nתחזיר n * עצרת(n - 1)\n}\n}\n"
           "תדפיס עצרת(5)\nסיימנו")
    assert run(src, capsys).strip() == "120"


def test_interpreter_indexes_arrays(capsys):
    src = "יאללה\nרשימה a שים [10, 20, 30]\nתדפיס a[1]\nסיימנו"
    assert run(src, capsys).strip() == "20"


# ── C code generator ─────────────────────────────────────────────────────────
def test_codegen_emits_a_compilable_main():
    c = CodeGenerator(parse("יאללה\nמספר x שים 7\nתדפיס x\nסיימנו")).generate()
    assert "#include <stdio.h>" in c
    assert "int main() {" in c and "return 0;" in c
    assert "printf" in c


def test_codegen_preserves_control_flow():
    c = CodeGenerator(parse('יאללה\nמספר x שים 5\nאם x > 1 אז {\nתדפיס "hi"\n}\nסיימנו')).generate()
    assert "if (" in c


def test_c_backend_does_not_yet_support_functions():
    """
    Documented limitation, not a bug to be surprised by: the interpreter
    handles all 18 AST node types, the C backend handles 11. Functions,
    for-loops, arrays and imports are interpreter-only. This test pins that
    boundary so it fails loudly the day someone implements it.
    """
    ast = parse("יאללה\nפונקציה f(x) {\nתחזיר x\n}\nסיימנו")
    assert any(isinstance(s, FunctionDef) for s in ast.statements)
    with pytest.raises(Exception):
        CodeGenerator(ast).generate()
