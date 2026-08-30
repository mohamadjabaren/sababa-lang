# =============================================================================
# codegen.py — SababaLang Code Generator
# =============================================================================
# This is Stage 3 of the compiler.
# It takes the AST produced by the parser and translates it into valid C code.
# We use the "Visitor Pattern" to walk the tree node by node.
# =============================================================================

from ast_nodes import *
from lexer import SababaError

class CodeGenerator:
    def __init__(self, ast: Program):
        self.ast = ast
        self.c_code = []
        self.indent_level = 0
        self.symbol_table = {}  # Tracks variable types for printf formatting

    def _emit(self, code: str):
        """Appends a line of C code with proper indentation."""
        indent = "    " * self.indent_level
        self.c_code.append(f"{indent}{code}")

    def generate(self) -> str:
        """Main entry point to generate C code from the AST."""
        self.c_code.append("// --- תורגם אוטומטית מ-SababaLang ---")
        self.c_code.append("#include <stdio.h>")
        self.c_code.append("#include <stdbool.h>")
        self.c_code.append("")
        self.c_code.append("int main() {")
        
        self.indent_level += 1
        
        for stmt in self.ast.statements:
            self.visit(stmt)
            
        self._emit("return 0;")
        self.indent_level -= 1
        self.c_code.append("}")
        
        return "\n".join(self.c_code)

    def visit(self, node: ASTNode) -> str:
        """Dispatches to the correct visit method based on node type."""
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ASTNode):
        raise Exception(f"אחי, אין לי מושג איך לתרגם את הצומת הזה: {type(node).__name__}")

    # ─── Statement Visitors ────────────────────────────────────────────────

    def visit_VarDecl(self, node: VarDecl):
        # Map Sababa types to C types
        c_type = "int" if node.var_type == "מספר" else "char*"
        self.symbol_table[node.name] = node.var_type  # Save for printf
        
        expr_c = self.visit(node.value)
        self._emit(f"{c_type} {node.name} = {expr_c};")

    def visit_Assign(self, node: Assign):
        if node.name not in self.symbol_table:
            raise Exception(f"מה נסגר? המשתנה '{node.name}' לא מוגדר!")
            
        expr_c = self.visit(node.value)
        self._emit(f"{node.name} = {expr_c};")

    def visit_IfStmt(self, node: IfStmt):
        cond_c = self.visit(node.condition)
        self._emit(f"if ({cond_c}) {{")
        
        self.visit_Block(node.then_branch)
        
        if node.else_branch:
            self._emit("} else {")
            self.visit_Block(node.else_branch)
            
        self._emit("}")

    def visit_WhileStmt(self, node: WhileStmt):
        cond_c = self.visit(node.condition)
        self._emit(f"while ({cond_c}) {{")
        self.visit_Block(node.body)
        self._emit("}")

    def visit_PrintStmt(self, node: PrintStmt):
        expr_c = self.visit(node.expression)
        expr_type = self._infer_type(node.expression)
        
        # C printf needs formatting based on type
        format_specifier = "%s" if expr_type == "טקסט" else "%d"
        self._emit(f'printf("{format_specifier}\\n", {expr_c});')

    def visit_ReturnStmt(self, node: ReturnStmt):
        expr_c = self.visit(node.expression)
        self._emit(f"return {expr_c};")

    def visit_Block(self, node: Block):
        self.indent_level += 1
        for stmt in node.statements:
            self.visit(stmt)
        self.indent_level -= 1

    # ─── Expression Visitors ───────────────────────────────────────────────

    def visit_BinaryOp(self, node: BinaryOp) -> str:
        left = self.visit(node.left)
        right = self.visit(node.right)
        
        # Translate Hebrew logical operators to C
        op = node.op
        if op == "וגם": op = "&&"
        elif op == "או": op = "||"
        
        return f"({left} {op} {right})"

    def visit_UnaryOp(self, node: UnaryOp) -> str:
        right = self.visit(node.right)
        op = "!" if node.op == "לא" else node.op
        return f"({op}{right})"

    def visit_Literal(self, node: Literal) -> str:
        if isinstance(node.value, bool):
            return "1" if node.value else "0"
        if isinstance(node.value, str):
            return f'"{node.value}"'
        return str(node.value)

    def visit_VarAccess(self, node: VarAccess) -> str:
        if node.name not in self.symbol_table:
            raise Exception(f"מה נסגר? משתנה לא מוגדר: '{node.name}'")
        return node.name

    # ─── Helpers ───────────────────────────────────────────────────────────

    def _infer_type(self, node: ASTNode) -> str:
        """Simple type inference to figure out printf formatting."""
        if isinstance(node, Literal):
            return node.c_type
        if isinstance(node, VarAccess):
            return self.symbol_table.get(node.name, "מספר")
        return "מספר" # Default to int for binary operations