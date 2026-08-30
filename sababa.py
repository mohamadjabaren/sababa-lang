#!/usr/bin/env python3
# =============================================================================
# sababa.py — SababaCharm IDE (Ultimate Edition - True RTL)
# =============================================================================

import sys
import io
from contextlib import redirect_stdout
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTextEdit, QVBoxLayout, 
                             QPushButton, QWidget, QLabel, QHBoxLayout, QSplitter, QPlainTextEdit)
from PyQt5.QtGui import QFont, QSyntaxHighlighter, QTextCharFormat, QColor, QPainter, QTextFormat, QTextOption
from PyQt5.QtCore import Qt, QRegExp, QRect, QSize

from lexer import Lexer, SababaError
from parser import Parser
from evaluator import Evaluator
from semantic import SemanticAnalyzer

# =============================================================================
# 1. محرك تلوين الكود
# =============================================================================
class SababaHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlightingRules = []

        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor("#cc7832"))
        keywords = ["יאללה", "סיימנו", "מספר", "טקסט", "שים", "אם", "אז", "אחרת", 
                    "סבבה", "באסה", "כלעוד", "תדפיס", "וגם", "או", "לא", "פונקציה", "תחזיר", "ייבא", "לכל", "רשימה", "כמות", "גודל"]
        for word in keywords:
            pattern = QRegExp(r'\b' + word + r'\b')
            self.highlightingRules.append((pattern, keywordFormat))

        stringFormat = QTextCharFormat()
        stringFormat.setForeground(QColor("#6a8759"))
        self.highlightingRules.append((QRegExp('"[^"]*"'), stringFormat))

        numberFormat = QTextCharFormat()
        numberFormat.setForeground(QColor("#6897bb"))
        self.highlightingRules.append((QRegExp(r'\b\d+\b'), numberFormat))

        commentFormat = QTextCharFormat()
        commentFormat.setForeground(QColor("#629755"))
        self.highlightingRules.append((QRegExp(r'#.*'), commentFormat))

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

# =============================================================================
# 2. منطقة أرقام الأسطر والمحرر
# =============================================================================
class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.codeEditor = editor

    def sizeHint(self):
        return QSize(self.codeEditor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)

class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.lineNumberArea = LineNumberArea(self)
        
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        
        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()
        
        self.setLineWrapMode(QPlainTextEdit.NoWrap)

        # ── السر هنا: إجبار محرك النص على دعم اللغات السامية (من اليمين لليسار) ──
        text_option = self.document().defaultTextOption()
        text_option.setTextDirection(Qt.RightToLeft)
        text_option.setAlignment(Qt.AlignRight)
        self.document().setDefaultTextOption(text_option)

    def lineNumberAreaWidth(self):
        digits = 1
        max_value = max(1, self.blockCount())
        while max_value >= 10:
            max_value /= 10
            digits += 1
        space = 10 + self.fontMetrics().width('9') * digits
        return space

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), QColor("#313335"))
        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(QColor("#606366"))
                painter.drawText(0, int(top), self.lineNumberArea.width() - 5, self.fontMetrics().height(),
                                 Qt.AlignRight | Qt.AlignVCenter, number)
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1

    def highlightCurrentLine(self):
        extraSelections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            lineColor = QColor("#323232")
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)


# =============================================================================
# 3. الواجهة الرئيسية
# =============================================================================
class SababaCharm(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SababaCharm IDE 🇮🇱 - סבבה צ'ארם (Ultimate)")
        self.resize(1000, 800)
        self.setStyleSheet("background-color: #2b2b2b; color: #a9b7c6;")

        self.evaluator = Evaluator()
        self.semantic = SemanticAnalyzer()

        # إرجاع الواجهة لتدعم اللغات السامية بشكل عام
        self.setLayoutDirection(Qt.RightToLeft)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # ── منطقة الأزرار العلوية ──
        btn_layout = QHBoxLayout()
        self.run_btn = QPushButton("▶ הריצו קוד (Run Sababa)")
        self.run_btn.setStyleSheet("background-color: #499c54; color: white; font-weight: bold; font-size: 16px; padding: 10px; border-radius: 5px;")
        self.run_btn.setCursor(Qt.PointingHandCursor)
        self.run_btn.clicked.connect(self.run_code)
        btn_layout.addWidget(self.run_btn)
        btn_layout.addStretch() 
        main_layout.addLayout(btn_layout)

        # ── أداة تقسيم الشاشة (QSplitter) ──
        splitter = QSplitter(Qt.Vertical)
        
        # 1. المحرر (Editor)
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        
        editor_label = QLabel("קוד SababaLang (Editor):")
        editor_label.setFont(QFont("Arial", 12, QFont.Bold))
        editor_layout.addWidget(editor_label)

        self.editor = CodeEditor()
        self.editor.setFont(QFont("Courier New", 16, QFont.Bold))
        self.editor.setStyleSheet("background-color: #1e1e1e; color: #a9b7c6; border: 1px solid #555;")
        editor_layout.addWidget(self.editor)
        
        self.highlighter = SababaHighlighter(self.editor.document())

        default_code = 'יאללה\n# ברוכים הבאים ל-SababaLang\n\nתדפיס "סבבה אחי!"\n\nסיימנו'
        self.editor.setPlainText(default_code)

        # 2. המخرجات (Console)
        console_widget = QWidget()
        console_layout = QVBoxLayout(console_widget)
        console_layout.setContentsMargins(0, 10, 0, 0)

        console_label = QLabel("תוצאה (Output Console):")
        console_label.setFont(QFont("Arial", 12, QFont.Bold))
        console_layout.addWidget(console_label)

        self.console = QTextEdit()
        self.console.setFont(QFont("Courier New", 14))
        self.console.setStyleSheet("background-color: #2b2b2b; color: #a9b7c6; border: 1px solid #555; padding: 5px;")
        self.console.setReadOnly(True)
        
        # ─── الحل النهائي: الكونسول من اليمين لليسار (RTL) كطبيعة اللغات السامية ───
        self.console.setLayoutDirection(Qt.RightToLeft)
        console_option = self.console.document().defaultTextOption()
        console_option.setTextDirection(Qt.RightToLeft)
        console_option.setAlignment(Qt.AlignRight)
        self.console.document().setDefaultTextOption(console_option)

        console_layout.addWidget(self.console)

        splitter.addWidget(editor_widget)
        splitter.addWidget(console_widget)
        splitter.setSizes([600, 200])

        main_layout.addWidget(splitter)

    def print_console(self, text, is_error=False):
        if is_error:
            self.console.setTextColor(QColor("#ff6b68"))
        else:
            self.console.setTextColor(QColor("#a9b7c6"))
        self.console.setPlainText(text)

    def run_code(self):
        source_code = self.editor.toPlainText().strip()
        if not source_code:
            self.print_console("אחי, הקוד ריק! אין מה להריץ.", True)
            return

        f = io.StringIO()
        with redirect_stdout(f):
            try:
                lexer = Lexer(source_code)
                tokens = lexer.tokenize()
                parser = Parser(tokens)
                ast = parser.parse()
                
                self.semantic.analyze(ast)
                self.evaluator.evaluate(ast)

                output = f.getvalue()
                if not output:
                    output = "[הקוד רץ בהצלחה, אבל לא הודפס כלום]"
                self.print_console(output)
            except SababaError as e:
                self.print_console(str(e), True)
            except Exception as e:
                self.print_console(f"שגיאת מערכת: {str(e)}", True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SababaCharm()
    window.show()
    sys.exit(app.exec_())