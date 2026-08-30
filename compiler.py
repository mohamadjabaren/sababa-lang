#!/usr/bin/env python3
# =============================================================================
# compiler.py — SababaLang Compiler Driver
# =============================================================================
# The main entry point. Orchestrates the compiler pipeline.
# =============================================================================

import argparse
import sys
import subprocess
import os

from lexer import Lexer, SababaError
from parser import Parser
from codegen import CodeGenerator

def main():
    arg_parser = argparse.ArgumentParser(description="SababaLang to C Compiler")
    arg_parser.add_argument("file", help="The .sababa source file to compile")
    arg_parser.add_argument("--verbose", action="store_true", help="Print Tokens and AST")
    arg_parser.add_argument("--run", action="store_true", help="Compile with GCC and run automatically")
    
    args = arg_parser.parse_args()

    if not args.file.endswith(".sababa"):
        print("שגיאה אחי: הקובץ חייב להסתיים ב-.sababa")
        sys.exit(1)

    # 1. Read Source
    try:
        with open(args.file, "r", encoding="utf-8") as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"אחי איפה הקובץ? לא מצאתי את: {args.file}")
        sys.exit(1)

    try:
        # 2. Lexical Analysis (Stage 1)
        if args.verbose: print("\n--- [1] Tokenizing (Lexer) ---")
        
        # تم التحديث هنا: استخدام دالة tokenize() بدلاً من get_next_token()
        lexer = Lexer(source_code, verbose=args.verbose)
        tokens = lexer.tokenize()

        # 3. Parsing (Stage 2)
        if args.verbose: print("\n--- [2] Parsing (AST) ---")
        parser = Parser(tokens, verbose=args.verbose)
        ast = parser.parse()

        # 4. Code Generation (Stage 3)
        if args.verbose: print("\n--- [3] Generating C Code ---")
        codegen = CodeGenerator(ast)
        c_code = codegen.generate()

        # 5. Output
        output_file = args.file.replace(".sababa", ".c")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(c_code)
            
        print(f"סבבה! הקוד קומפל בהצלחה ל- {output_file}")

        # 6. GCC Compilation & Run (Optional)
        if args.run:
            binary_name = args.file.replace(".sababa", "")
            if os.name == 'nt': # Windows
                binary_name += ".exe"
                
            print("\n--- [4] Running GCC ---")
            gcc_command = ["gcc", output_file, "-o", binary_name]
            result = subprocess.run(gcc_command, capture_output=True, text=True)
            
            if result.returncode != 0:
                print("באסה. שגיאה בקומפילציה של ה-C:")
                print(result.stderr)
                sys.exit(1)
                
            print(f"נוצר קובץ הרצה: {binary_name}")
            print("--- [5] Running Binary ---\n")
            run_command = f"./{binary_name}" if os.name != 'nt' else f"{binary_name}"
            subprocess.run(run_command, shell=True)

    except SababaError as e:
        # Hebrew error handling
        print("\n" + str(e))
        sys.exit(1)
    except Exception as e:
        print(f"\nשגיאת קומפיילר לא צפויה: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()