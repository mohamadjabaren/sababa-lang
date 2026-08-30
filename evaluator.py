# =============================================================================
# evaluator.py — SababaLang Interpreter (REPL Engine)
# =============================================================================
# يقوم هذا الملف بتنفيذ الأوامر مباشرة (Interpreting) بدلاً من تحويلها إلى C.
# يحتفظ بالمتغيرات في الذاكرة ويتيح للمستخدم تشغيل الكود فوراً.
# =============================================================================
import os
from lexer import Lexer
from parser import Parser
from ast_nodes import *
from lexer import SababaError

class ReturnValue(Exception):
    def __init__(self, value):
        self.value = value
        
class Evaluator:
    def __init__(self):
        # هنا نحفظ المتغيرات في الذاكرة لكي يتذكرها البرنامج في الأسطر القادمة
        self.environment = {}

    def evaluate(self, node: ASTNode):
        """توجيه كل عقدة (Node) إلى الدالة المسؤولة عن تنفيذها"""
        if node is None: return None
        method_name = f'eval_{type(node).__name__}'
        evaluator_func = getattr(self, method_name, self.generic_eval)
        return evaluator_func(node)

    def generic_eval(self, node: ASTNode):
        raise Exception(f"אחי, אני לא יודע איך להריץ את זה: {type(node).__name__}")
    def eval_FunctionDef(self, node: FunctionDef):
        # حفظ الدالة في الذاكرة (Environment)
        self.environment[node.name] = node

    def eval_FunctionCall(self, node: FunctionCall):
        if node.name not in self.environment:
            raise SababaError(f"פונקציה '{node.name}' לא קיימת אחי!", 0)
        
        func_def = self.environment[node.name]
        
        # إنشاء ذاكرة جديدة (Scope) خاصة بالدالة لكي لا تتداخل المتغيرات
        previous_env = self.environment.copy()
        
        # ربط القيم الممررة بأسماء المتغيرات
        for param, arg_expr in zip(func_def.params, node.arguments):
            self.environment[param] = self.evaluate(arg_expr)
            
        try:
            self.evaluate(func_def.body)
        except ReturnValue as ret:
            # استعادة الذاكرة الأصلية بعد انتهاء الدالة
            self.environment = previous_env
            return ret.value
            
        self.environment = previous_env
        return None # إذا لم تُرجع الدالة شيئاً

    def eval_ReturnStmt(self, node: ReturnStmt):
        value = self.evaluate(node.expression)
        raise ReturnValue(value)
    def eval_ForStmt(self, node: ForStmt):
        self.evaluate(node.init)
        while self.evaluate(node.condition):
            self.evaluate(node.body)
            self.evaluate(node.step)

    def eval_ArrayLiteral(self, node: ArrayLiteral):
        return [self.evaluate(el) for el in node.elements]

    def eval_ArrayAccess(self, node: ArrayAccess):
        if node.name not in self.environment:
            raise SababaError(f"אחי, המערך '{node.name}' לא קיים", 0)
        
        arr = self.environment[node.name]
        idx = self.evaluate(node.index)
        
        try:
            return arr[idx]
        except IndexError:
            raise SababaError(f"חריגה מגבולות המערך! ניסית לגשת לאינדקס {idx} אבל הגודל הוא {len(arr)}", 0)
    # ─── تنفيذ الهيكل الأساسي ────────────────────────────────────────────────

    def eval_Program(self, node: Program):
        result = None
        for stmt in node.statements:
            result = self.evaluate(stmt)
        return result

    def eval_Block(self, node: Block):
        for stmt in node.statements:
            self.evaluate(stmt)

    # ─── تنفيذ الأوامر (Statements) ──────────────────────────────────────────

    def eval_VarDecl(self, node: VarDecl):
        value = self.evaluate(node.value)
        self.environment[node.name] = value

    def eval_Assign(self, node: Assign):
        if node.name not in self.environment:
            raise SababaError(f"מה נסגר? המשתנה '{node.name}' לא מוגדר!", 0)
        value = self.evaluate(node.value)
        self.environment[node.name] = value

    def eval_IfStmt(self, node: IfStmt):
        condition = self.evaluate(node.condition)
        if condition:
            self.evaluate(node.then_branch)
        elif node.else_branch:
            self.evaluate(node.else_branch)

    def eval_WhileStmt(self, node: WhileStmt):
        while self.evaluate(node.condition):
            self.evaluate(node.body)

    def eval_PrintStmt(self, node: PrintStmt):
        val = self.evaluate(node.expression)
        # طباعة القيم المنطقية بأسلوب سبابا
        if isinstance(val, bool):
            print("סבבה" if val else "באסה")
        else:
            print(val)

    # ─── تنفيذ العمليات الحسابية والمنطقية (Expressions) ─────────────────────

    def eval_BinaryOp(self, node: BinaryOp):
        left = self.evaluate(node.left)
        right = self.evaluate(node.right)
        op = node.op

        if op == '+': return left + right
        if op == '-': return left - right
        if op == '*': return left * right
        if op == '/': return left / right
        if op == '==': return left == right
        if op == '!=': return left != right
        if op == '>': return left > right
        if op == '<': return left < right
        if op == '>=': return left >= right
        if op == '<=': return left <= right
        if op == 'וגם': return left and right
        if op == 'או': return left or right

    def eval_UnaryOp(self, node: UnaryOp):
        right = self.evaluate(node.right)
        if node.op == '-': return -right
        if node.op == 'לא': return not right

    def eval_Literal(self, node: Literal):
        return node.value

    def eval_VarAccess(self, node: VarAccess):
        if node.name not in self.environment:
            raise SababaError(f"אחי איפה זה? המשתנה '{node.name}' לא קיים", 0)
        return self.environment[node.name]
        
    def eval_ImportStmt(self, node: ImportStmt):
        file_path = node.module_name
        
        if not os.path.exists(file_path):
            # محاولة البحث في مجلد stdlib إذا لم يكن في المجلد الحالي
            stdlib_path = os.path.join("stdlib", file_path)
            if os.path.exists(stdlib_path):
                file_path = stdlib_path
            else:
                raise SababaError(f"אחי איפה זה? לא מצאתי את הקובץ '{node.module_name}' לייבוא!", 0)

        # قراءة الملف المستورد
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()

        # لكي نمرر الكود من الملف بدون أن نزعجه بطلب "יאללה" و "סיימנו" في المكتبات
        if "יאללה" not in source_code:
            source_code = "יאללה\n" + source_code + "\nסיימנו"

        # ترجمة الملف
        lexer = Lexer(source_code)
        parser = Parser(lexer.tokenize())
        ast = parser.parse()

        # تنفيذ الملف داخل نفس الذاكرة الحالية (self) لكي نرث دواله
        for stmt in ast.statements:
            self.evaluate(stmt)