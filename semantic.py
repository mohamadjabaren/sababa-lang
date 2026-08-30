# =============================================================================
# semantic.py — SababaLang Semantic Analyzer (Type & Logic Checking)
# =============================================================================

from ast_nodes import *
from lexer import SababaError

class SemanticAnalyzer:
    def __init__(self):
        # جدول الرموز (Symbol Table): يتذكر المتغيرات وأنواعها والدوال
        self.scopes = [{}]
        self.functions = {} 

    def analyze(self, node: ASTNode):
        if node is None: return None
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ASTNode):
        pass

    # ─── إدارة الذاكرة الوهمية (לניהול זיכרון וירטואלי) ───
    def define_var(self, name: str, var_type: str):
        self.scopes[-1][name] = var_type

    def lookup_var(self, name: str):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    # ─── فحص العقد (Node Visitors) ───
    def visit_Program(self, node: Program):
        for stmt in node.statements:
            self.analyze(stmt)

    def visit_Block(self, node: Block):
        self.scopes.append({}) # فتح نطاق جديد (Scope)
        for stmt in node.statements:
            self.analyze(stmt)
        self.scopes.pop() # إغلاق النطاق

    def visit_VarDecl(self, node: VarDecl):
        expr_type = self.analyze(node.value)
        # فحص تطابق الأنواع (مع السماح بمرور 'לא_ידוע' القادم من الدوال)
        if expr_type and node.var_type in ["מספר", "טקסט"]:
            if expr_type != node.var_type and expr_type != "לא_ידוע":
                raise SababaError(
                    f"שגיאת סמנטיקה: המשתנה '{node.name}' הוא מטיפוס '{node.var_type}', "
                    f"אבל ניסית להכניס לו '{expr_type}'!", 0
                )
        self.define_var(node.name, node.var_type)

    def visit_Assign(self, node: Assign):
        var_type = self.lookup_var(node.name)
        if not var_type:
            raise SababaError(f"שגיאת סמנטיקה: אי אפשר לשים ערך ב-'{node.name}' לפני שמגדירים אותו!", 0)
            
        expr_type = self.analyze(node.value)
        # السماح بمرور 'לא_ידוע' القادم من الدوال
        if expr_type and expr_type != var_type and var_type != "רשימה" and expr_type != "לא_ידוע":
            raise SababaError(
                f"שגיאת סמנטיקה: המשתנה '{node.name}' הוא מטיפוס '{var_type}', "
                f"אי אפשר להכניס לו '{expr_type}'!", 0
            )

    def visit_BinaryOp(self, node: BinaryOp):
        left_type = self.analyze(node.left)
        right_type = self.analyze(node.right)

        # منع العمليات الحسابية على النصوص
        if node.op in ['-', '*', '/', '>', '<', '>=', '<=']:
            if left_type == "טקסט" or right_type == "טקסט":
                raise SababaError(
                    f"שגיאת סמנטיקה: אי אפשר לעשות פעולת '{node.op}' על טקסט אחי, רק על מספרים!", 0
                )
        return left_type 

    def visit_Literal(self, node: Literal):
        if isinstance(node.value, str): return "טקסט"
        return "מספר"

    def visit_VarAccess(self, node: VarAccess):
        var_type = self.lookup_var(node.name)
        if not var_type:
            raise SababaError(f"שגיאת סמנטיקה: המשתנה '{node.name}' לא הוגדר מעולם!", 0)
        return var_type

    def visit_FunctionDef(self, node: FunctionDef):
        # حفظ عدد المتغيرات المطلوبة للدالة
        self.functions[node.name] = len(node.params)
        
        self.scopes.append({})
        for param in node.params:
            self.define_var(param, "לא_ידוע")
        self.analyze(node.body)
        self.scopes.pop()

    def visit_FunctionCall(self, node: FunctionCall):
        if node.name in self.functions:
            expected_args = self.functions[node.name]
            # فحص عدد المعاملات الممررة
            if len(node.arguments) != expected_args:
                raise SababaError(
                    f"שגיאת סמנטיקה: הפונקציה '{node.name}' מצפה ל-{expected_args} משתנים, "
                    f"אבל שלחת לה {len(node.arguments)}!", 0
                )
        for arg in node.arguments:
            self.analyze(arg)
        return "לא_ידוע"