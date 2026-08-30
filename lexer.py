# =============================================================================
# lexer.py — SababaLang Lexer (Tokenizer)
# =============================================================================
# The lexer is Stage 1 of the compiler pipeline.
# Its job: take a raw UTF-8 string of SababaLang source code and break it
# into a flat list of Token objects that the parser can digest.
#
# How it works (high-level):
#   • We walk through the source character-by-character using a cursor (pos).
#   • At each position we look at the current character and decide what kind
#     of token starts here.
#   • We consume as many characters as belong to that token, build a Token,
#     add it to the list, and repeat until we hit the end of the file.
#
# Hebrew note:
#   Hebrew is written right-to-left visually, but stored left-to-right in
#   memory (logical order).  Python strings handle this transparently, so we
#   can index them with plain integer offsets just like ASCII text.
# =============================================================================

from sababa_token import Token, TokenType, KEYWORDS

# ---------------------------------------------------------------------------
# SababaError — our custom compiler error (with Hebrew flair)
# ---------------------------------------------------------------------------
class SababaError(Exception):
    """
    Raised whenever the lexer (or later stages) encounter invalid input.
    Always includes the source line number so the user knows where to look.
    """
    def __init__(self, message: str, line: int) -> None:
        # Prefix with the Hebrew word for "Error" so the output looks cool
        super().__init__(f"[שגיאה בשורה {line}] {message}")
        self.line = line


# ---------------------------------------------------------------------------
# Lexer — the main class
# ---------------------------------------------------------------------------
class Lexer:
    """
    Converts a SababaLang source string into a list of Token objects.

    Usage
    -----
        lexer  = Lexer(source_code)
        tokens = lexer.tokenize()

    Parameters
    ----------
    source  : str   — full source code as a Python string (already decoded)
    verbose : bool  — if True, print every token as it is produced
    """

    def __init__(self, source: str, verbose: bool = False) -> None:
        self.source  = source        # The complete source text
        self.verbose = verbose       # Verbose/debug mode flag
        self.pos     = 0             # Current character index into source
        self.line    = 1             # Current line number (1-based)
        self.tokens: list[Token] = []  # Accumulated output

    # ================================================================
    # Public API
    # ================================================================

    def tokenize(self) -> list[Token]:
        """
        Entry point — scan the entire source and return the token list.
        An EOF token is always appended at the end so the parser has a
        clean sentinel to check against.
        """
        while not self._at_end():
            self._scan_next_token()

        # Always finish with an EOF sentinel
        self._emit(TokenType.EOF, "<EOF>")
        return self.tokens

    # ================================================================
    # Core scanning loop
    # ================================================================

    def _scan_next_token(self) -> None:
        """
        Inspect the character at the current position and dispatch to the
        appropriate helper method.  This is the heart of the lexer.
        """
        ch = self._peek()   # look without consuming

        # ── Whitespace & newlines ─────────────────────────────────────────
        if ch == "\n":
            self.line += 1   # track line numbers for error messages
            self._advance()
            return

        if ch in " \t\r":
            self._advance()
            return

        # ── Single-line comments  (#  until end of line) ──────────────────
        if ch == "#":
            self._skip_comment()
            return

        # ── String literals  ("...") ──────────────────────────────────────
        if ch == '"':
            self._read_string()
            return

        # ── Number literals  (digits) ─────────────────────────────────────
        if ch.isdigit():
            self._read_number()
            return

        # ── Two-character operators  (==, !=, >=, <=) ─────────────────────
        if ch in "=!><":
            self._read_comparison_op()
            return

        # ── Single-character ASCII operators & delimiters ─────────────────
        single = self._try_single_char_token(ch)
        if single is not None:
            self._advance()
            self._emit(single, ch)
            return

        # ── Hebrew keywords & identifiers ─────────────────────────────────
        # Hebrew Unicode block: U+0590–U+05FF
        # We also allow ASCII letters/digits/underscore in identifiers so
        # that variable names like "counter1" work fine.
        if self._is_word_start(ch):
            self._read_word()
            return

        # ── Anything else is an error ─────────────────────────────────────
        raise SababaError(
            f"אחי מה זה?! תו לא מוכר: '{ch}'",
            self.line
        )

    # ================================================================
    # Token-reading helpers
    # ================================================================

    def _read_string(self) -> None:
        """
        Consume a double-quoted string literal.
        The opening and closing quotes are stripped; the Token value contains
        only the inner text.

        Supports:
          • \" inside a string (escaped quote)
          • Multi-line strings are NOT supported — an unterminated string
            that crosses a newline triggers an error.
        """
        start_line = self.line
        self._advance()          # consume the opening "
        chars: list[str] = []

        while not self._at_end():
            ch = self._peek()

            if ch == "\n":
                raise SababaError(
                    "אחי שכחת לסגור מרכאות! המחרוזת לא נסגרת בשורה הזו",
                    start_line
                )

            if ch == '"':
                self._advance()  # consume the closing "
                self._emit(TokenType.STRING, "".join(chars))
                return

            if ch == "\\" and self._peek_next() == '"':
                # escaped quote inside the string
                self._advance()  # skip backslash
                chars.append('"')
                self._advance()  # skip the quote
            else:
                chars.append(ch)
                self._advance()

        raise SababaError(
            "אחי, שכחת לסגור מרכאות — המחרוזת לא נסגרת עד סוף הקובץ!",
            start_line
        )

    def _read_number(self) -> None:
        """
        Consume a sequence of digits and emit a NUMBER token.
        Only integers are supported for now (no floats).
        """
        start = self.pos
        while not self._at_end() and self._peek().isdigit():
            self._advance()
        self._emit(TokenType.NUMBER, self.source[start:self.pos])

    def _read_comparison_op(self) -> None:
        """
        Handle the operators that can be one OR two characters:
          =   →  (single = is not valid — we use שים for assignment)
          ==  →  EQ_EQ
          !=  →  BANG_EQ
          >   →  GT
          >=  →  GT_EQ
          <   →  LT
          <=  →  LT_EQ
        """
        ch   = self._advance()   # consume first character
        next = self._peek()      # look at second without consuming

        if ch == "=" and next == "=":
            self._advance()
            self._emit(TokenType.EQ_EQ, "==")
        elif ch == "!" and next == "=":
            self._advance()
            self._emit(TokenType.BANG_EQ, "!=")
        elif ch == ">" and next == "=":
            self._advance()
            self._emit(TokenType.GT_EQ, ">=")
        elif ch == "<" and next == "=":
            self._advance()
            self._emit(TokenType.LT_EQ, "<=")
        elif ch == ">":
            self._emit(TokenType.GT, ">")
        elif ch == "<":
            self._emit(TokenType.LT, "<")
        else:
            # Bare '=' or bare '!' that isn't followed by '='
            raise SababaError(
                f"אחי מה זה '{ch}'? אולי התכוונת ל-'{ch}='?",
                self.line
            )

    def _read_word(self) -> None:
        """
        Consume a contiguous run of word characters (Hebrew letters, ASCII
        letters, digits, underscores) and decide whether it is:
          • A reserved keyword (look up in KEYWORDS table)  →  keyword token
          • Anything else                                   →  IDENTIFIER
        """
        start = self.pos
        while not self._at_end() and self._is_word_char(self._peek()):
            self._advance()

        text = self.source[start:self.pos]

        # Check against the keyword table first
        token_type = KEYWORDS.get(text, TokenType.IDENTIFIER)
        self._emit(token_type, text)

    def _skip_comment(self) -> None:
        """
        Consume everything from '#' to the end of the current line.
        Comments are silently discarded (no token emitted).
        """
        while not self._at_end() and self._peek() != "\n":
            self._advance()

    # ================================================================
    # Single-character token dispatch table
    # ================================================================

    # Maps a single character to its corresponding TokenType.
    # Characters NOT in this dict are handled elsewhere (digits, letters,
    # quotes, comparison starters, whitespace, comments).
    _SINGLE_CHAR: dict[str, TokenType] = {
        "+": TokenType.PLUS,
        "-": TokenType.MINUS,
        "*": TokenType.STAR,
        "/": TokenType.SLASH,
        "{": TokenType.LBRACE,
        "}": TokenType.RBRACE,
        "(": TokenType.LPAREN,
        ")": TokenType.RPAREN,
        # ── أضف هذه الأسطر ──
        ",": TokenType.COMMA,
        "[": TokenType.LBRACK,
        "]": TokenType.RBRACK,
    }

    def _try_single_char_token(self, ch: str) -> TokenType | None:
        """Return the TokenType for a single-char token, or None."""
        return self._SINGLE_CHAR.get(ch)

    # ================================================================
    # Character classification helpers
    # ================================================================

    def _is_word_start(self, ch: str) -> bool:
        """
        True if this character can BEGIN a keyword or identifier.
        Allowed: Hebrew letters (U+05D0–U+05EA and nearby), ASCII letters,
        or an underscore.
        """
        return ch.isalpha() or ch == "_"

    def _is_word_char(self, ch: str) -> bool:
        """
        True if this character can CONTINUE a keyword or identifier.
        Same as start, but also allows digits (e.g. variable 'x1').
        """
        return ch.isalnum() or ch == "_"

    # ================================================================
    # Cursor / source navigation helpers
    # ================================================================

    def _peek(self) -> str:
        """Return the character at the current position without consuming it."""
        if self._at_end():
            return "\0"    # null sentinel — signals end of input
        return self.source[self.pos]

    def _peek_next(self) -> str:
        """Return the character ONE ahead of the current position (look-ahead 2)."""
        if self.pos + 1 >= len(self.source):
            return "\0"
        return self.source[self.pos + 1]

    def _advance(self) -> str:
        """Consume and return the current character, then move the cursor forward."""
        ch = self.source[self.pos]
        self.pos += 1
        return ch

    def _at_end(self) -> bool:
        """True when we have consumed every character in the source."""
        return self.pos >= len(self.source)

    # ================================================================
    # Token emission
    # ================================================================

    def _emit(self, token_type: TokenType, value: str) -> None:
        """
        Create a Token and append it to self.tokens.
        If verbose mode is on, also print the token — useful for debugging.
        """
        tok = Token(token_type, value, self.line)
        self.tokens.append(tok)

        if self.verbose:
            print(f"  🔤  {tok}")