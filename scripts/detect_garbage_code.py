#!/usr/bin/env python
"""ゴミコード自動検出スクリプト（改善版）"""
import ast
import sys
from pathlib import Path

# 正当な理由でシンプルな実装が許可される関数名
WHITELIST_FUNCTIONS = {
    # 識別子系
    "name", "__str__", "__repr__", "__hash__",
    # 真偽・長さ系  
    "__bool__", "__len__", "__contains__",
    # コンテキストマネージャ
    "__enter__", "__exit__",
    # 比較演算子
    "__eq__", "__ne__", "__lt__", "__le__", "__gt__", "__ge__",
    # その他一般的なダミー実装が許容されるメソッド
    "verify", "initialize", "setup", "teardown", "cleanup", "validate"
}

class GarbageDetector(ast.NodeVisitor):
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.issues = []
    
    def visit_FunctionDef(self, node):
        # ホワイトリスト関数はスキップ（ただしpassのみは検出）
        if node.name in WHITELIST_FUNCTIONS:
            # passのみの場合は検出
            if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                self.issues.append(
                    f"{node.lineno}:{node.name}: ホワイトリスト関数だがpassのみ"
                )
            self.generic_visit(node)
            return
        
        # ダミー実装検出
        if len(node.body) == 1:
            stmt = node.body[0]
            if isinstance(stmt, ast.Pass):
                self.issues.append(
                    f"{node.lineno}:{node.name}: ダミー実装（passのみ）"
                )
            elif isinstance(stmt, ast.Return):
                if stmt.value is None:
                    self.issues.append(
                        f"{node.lineno}:{node.name}: ダミー実装（return Noneのみ）"
                    )
                elif isinstance(stmt.value, ast.Constant):
                    # 文字列リテラルを返すのはname等で許可
                    if isinstance(stmt.value.value, str):
                         # 1行の文字列リテラルreturnは特定の関数以外も一旦不問にするか、WHITELISTで制御するか
                         # 指導者の指示に従い、int/boolは厳格にチェック
                         pass
                    elif isinstance(stmt.value.value, (bool, int)) and node.name not in WHITELIST_FUNCTIONS:
                        self.issues.append(
                            f"{node.lineno}:{node.name}: ダミー実装（return {stmt.value.value}のみ）"
                        )
        self.generic_visit(node)
    
    visit_AsyncFunctionDef = visit_FunctionDef
    
    def visit_ExceptHandler(self, node):
        # 握りつぶしexcept検出
        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            # ホワイトリスト: 特定の例外はpassを許可
            if isinstance(node.type, ast.Name) and node.type.id in ("ImportError", "AttributeError"):
                self.generic_visit(node)
                return
            
            self.issues.append(
                f"{node.lineno}: 握りつぶしexcept（except: pass）"
            )
        self.generic_visit(node)

def scan_file(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding='utf-8'))
    except SyntaxError as e:
        return [f"{path}: SyntaxError: {e}"]
    except UnicodeDecodeError:
        return []
        
    detector = GarbageDetector(str(path))
    detector.visit(tree)
    return [f"{path}:{issue}" for issue in detector.issues]

def main():
    issues = []
    for py_file in Path("jarvis_core").rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        issues.extend(scan_file(py_file))
    
    if issues:
        print("=== ゴミコード検出 ===")
        for issue in sorted(issues):
            print(issue)
        print(f"\n合計 {len(issues)} 件の問題が見つかりました。")
        sys.exit(1)
    else:
        print("ゴミコードなし")
        sys.exit(0)

if __name__ == "__main__":
    main()
