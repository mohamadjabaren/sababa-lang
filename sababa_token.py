# =============================================================================
# token.py — SababaLang Token Definitions
# =============================================================================
# This module defines every kind of "word" (token) that the SababaLang lexer
# can produce.  Think of tokens like the atoms of the language — the smallest
# meaningful units before grammar kicks in.
#
# Two things live here:
#   1. TokenType  — an enum listing every possible token category
#   2. Token      — a tiny data-class that pairs a TokenType with its raw text
#                   and the source-line it came from (for error messages).
# =============================================================================

from enum import Enum, auto


# ---------------------------------------------------------------------------
# TokenType — every category of symbol the lexer can emit
# ---------------------------------------------------------------------------
class TokenType(Enum):
    # ── Program structure ───────────────────────────────────────────────────
    YALLA       = auto()   # יאללה  → marks the start of the program (main)
    SIYAMNU     = auto()   # סיימנו → marks the end of the program

    # ── Variable types ───────────────────────────────────────────────────────
    MISPAR      = auto()   # מספר   → int
    TEKST       = auto()   # טקסט   → string (char* in C)

    # ── Assignment ───────────────────────────────────────────────────────────
    SIM         = auto()   # שים    → assignment operator  (like =)

    # ── Control flow ─────────────────────────────────────────────────────────
    IM          = auto()   # אם     → if
    AZ          = auto()   # אז     → then (marks start of an if-body)
    ACHERET     = auto()   # אחרת   → else

    # ── Boolean literals ─────────────────────────────────────────────────────
    SABABA      = auto()   # סבבה   → true  (1 in C)
    BASA        = auto()   # באסה   → false (0 in C)

    # ── Loop ─────────────────────────────────────────────────────────────────
    KHALOD      = auto()   # כלעוד  → while

    # ── Output ───────────────────────────────────────────────────────────────
    TADPIS      = auto()   # תדפיס  → print

    # ── Logical operators ─────────────────────────────────────────────────────
    VEGAM       = auto()   # וגם    → &&  (logical AND)
    O           = auto()   # או     → ||  (logical OR)
    LO          = auto()   # לא     → !   (logical NOT)

    # ── Functions ────────────────────────────────────────────────────────────
    FUNCTION    = auto()   # פונקציה → function declaration
    TACHZIR     = auto()   # תחזיר  → return

    # ── Comparison & arithmetic operators (plain ASCII) ─────────────────────
    PLUS        = auto()   # +
    MINUS       = auto()   # -
    STAR        = auto()   # *
    SLASH       = auto()   # /
    EQ_EQ       = auto()   # ==
    BANG_EQ     = auto()   # !=
    GT          = auto()   # >
    LT          = auto()   # <
    GT_EQ       = auto()   # >=
    LT_EQ       = auto()   # <=

    # ── Delimiters ───────────────────────────────────────────────────────────
    LBRACE      = auto()   # {
    RBRACE      = auto()   # }
    LPAREN      = auto()   # (
    RPAREN      = auto()   # )

    # ── Literals ─────────────────────────────────────────────────────────────
    NUMBER      = auto()   # integer literal, e.g. 42
    STRING      = auto()   # string literal, e.g. "שלום עולם"
    IDENTIFIER  = auto()   # variable / function name, e.g. counter

    # ── Housekeeping ──────────────────────────────────────────────────────────
    EOF         = auto()   # signals the end of the source file

    COMMA       = auto()   # ,
    LBRACK      = auto()   # [
    RBRACK      = auto()   # ]
    LEKOL       = auto()   # לכל (For)
    RESHIMA     = auto()   # רשימה (Array/List)
    ORECH       = auto()   # אורך (Length)
    
    YAVE        = auto()   # ייבא  → Import
# ---------------------------------------------------------------------------
# Keyword table — maps every Hebrew keyword to its TokenType.
# The lexer checks this table after reading a word to decide whether it is a
# reserved keyword or just a user-chosen identifier.
# ---------------------------------------------------------------------------
KEYWORDS: dict[str, TokenType] = {
    "יאללה":    TokenType.YALLA,
    "סיימנו":   TokenType.SIYAMNU,
    "מספר":     TokenType.MISPAR,
    "טקסט":     TokenType.TEKST,
    "שים":      TokenType.SIM,
    "אם":       TokenType.IM,
    "אז":       TokenType.AZ,
    "אחרת":     TokenType.ACHERET,
    "סבבה":     TokenType.SABABA,
    "באסה":     TokenType.BASA,
    "כלעוד":    TokenType.KHALOD,
    "תדפיס":    TokenType.TADPIS,
    "וגם":      TokenType.VEGAM,
    "או":       TokenType.O,
    "לא":       TokenType.LO,
    "פונקציה":  TokenType.FUNCTION,
    "תחזיר":    TokenType.TACHZIR,
    "לכל":      TokenType.LEKOL,
    "רשימה":    TokenType.RESHIMA,
    "אורך":     TokenType.ORECH,
    "ייבא":     TokenType.YAVE,
}


# ---------------------------------------------------------------------------
# Token — the data-class that the lexer produces and the parser consumes
# ---------------------------------------------------------------------------
class Token:
    """
    Represents a single token emitted by the lexer.

    Attributes
    ----------
    type    : TokenType   — what kind of token this is
    value   : str         — the exact text from the source file
    line    : int         — 1-based source line (used in error messages)
    """

    def __init__(self, type: TokenType, value: str, line: int) -> None:
        self.type  = type
        self.value = value
        self.line  = line

    # ── Pretty-print for debugging / verbose mode ─────────────────────────
    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, line={self.line})"