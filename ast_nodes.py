# =============================================================================
# ast_nodes.py — SababaLang Abstract Syntax Tree (AST) Nodes
# =============================================================================
# This file contains the classes that represent the parsed structure of our
# code. The Parser will create instances of these classes to build a tree
# that the Code Generator will later traverse to output C code.
# =============================================================================

class ASTNode:
    """Base class for all AST nodes."""
    def dump(self, indent=0) -> str:
        """Helper to recursively print the AST in a readable format for verbose mode."""
        lines = []
        indent_str = "  " * indent
        node_name = self.__class__.__name__
        lines.append(f"{indent_str}└── {node_name}")
        
        for key, value in self.__dict__.items():
            if isinstance(value, ASTNode):
                lines.append(f"{indent_str}    {key}:")
                lines.append(value.dump(indent + 2))
            elif isinstance(value, list):
                lines.append(f"{indent_str}    {key}: [")
                for item in value:
                    if isinstance(item, ASTNode):
                        lines.append(item.dump(indent + 3))
                    else:
                        lines.append(f"{indent_str}      {item}")
                lines.append(f"{indent_str}    ]")
            else:
                lines.append(f"{indent_str}    {key}: {value}")
        return "\n".join(lines)

# ─── Program Structure ────────────────────────────────────────────────────────

class Program(ASTNode):
    def __init__(self, statements):
        self.statements = statements  # List of statement nodes

class Block(ASTNode):
    def __init__(self, statements):
        self.statements = statements

# ─── Statements ───────────────────────────────────────────────────────────────

class VarDecl(ASTNode):
    def __init__(self, var_type: str, name: str, value: ASTNode):
        self.var_type = var_type  # "מספר" or "טקסט"
        self.name = name          # Variable identifier
        self.value = value        # Expression node

class Assign(ASTNode):
    def __init__(self, name: str, value: ASTNode):
        self.name = name
        self.value = value

class IfStmt(ASTNode):
    def __init__(self, condition: ASTNode, then_branch: Block, else_branch: Block = None):
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch

class WhileStmt(ASTNode):
    def __init__(self, condition: ASTNode, body: Block):
        self.condition = condition
        self.body = body

class PrintStmt(ASTNode):
    def __init__(self, expression: ASTNode):
        self.expression = expression

class ReturnStmt(ASTNode):
    def __init__(self, expression: ASTNode):
        self.expression = expression

# ─── Expressions ──────────────────────────────────────────────────────────────

class BinaryOp(ASTNode):
    def __init__(self, left: ASTNode, op: str, right: ASTNode):
        self.left = left
        self.op = op              # e.g., "+", "-", "==", "וגם"
        self.right = right

class UnaryOp(ASTNode):
    def __init__(self, op: str, right: ASTNode):
        self.op = op              # e.g., "-", "לא"
        self.right = right

class Literal(ASTNode):
    def __init__(self, value, c_type: str):
        self.value = value
        self.c_type = c_type      # Used later for code generation

class VarAccess(ASTNode):
    def __init__(self, name: str):
        self.name = name
        
# ─── Functions (הוספת פונקציות) ──────────────────────────────────────────────

class FunctionDef(ASTNode):
    """تعريف دالة جديدة"""
    def __init__(self, name: str, params: list, body: Block):
        self.name = name
        self.params = params  # قائمة بأسماء المعاملات
        self.body = body

class FunctionCall(ASTNode):
    """استدعاء الدالة"""
    def __init__(self, name: str, arguments: list):
        self.name = name
        self.arguments = arguments  # قائمة بالقيم المُمررة
        
# ─── Arrays & Loops ──────────────────────────────────────────────

class ForStmt(ASTNode):
    """לכל משתנה שים התחלה; תנאי; צעד { ... }"""
    def __init__(self, init, condition, step, body):
        self.init = init
        self.condition = condition
        self.step = step
        self.body = body

class ArrayLiteral(ASTNode):
    """[1, 2, 3]"""
    def __init__(self, elements: list):
        self.elements = elements

class ArrayAccess(ASTNode):
    """nums[0]"""
    def __init__(self, name: str, index: ASTNode):
        self.name = name
        self.index = index

class ImportStmt(ASTNode):
    """ייבא "filename.sababa" """
    def __init__(self, module_name: str):
        self.module_name = module_name