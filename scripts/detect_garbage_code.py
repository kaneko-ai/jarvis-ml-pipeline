"""ゴミコード自動検出スクリプト"""
import ast
import sys
from pathlib import Path

class GarbageDetector(ast.NodeVisitor):
    def __init__(self):
        self.issues = []
    
    def visit_FunctionDef(self, node):
        # ダミー実装検出: bodyが1行で pass or return リテラルのみ
        if len(node.body) == 1:
            stmt = node.body[0]
            # ホワイトリスト: __exit__ での return False/True は正当
            if node.name == "__exit__" and isinstance(stmt, ast.Return):
                if isinstance(stmt.value, ast.Constant) and stmt.value.value in (True, False):
                    self.generic_visit(node)
                    return

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
                    # return True, return False, return 0 等を検出
                    self.issues.append(
                        f"{node.lineno}:{node.name}: ダミー実装（return {stmt.value.value}のみ）"
                    )
        self.generic_visit(node)
    
    def visit_ExceptHandler(self, node):
        # 握りつぶしexcept検出
        # try: ... except: pass のようなケース
        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            # ホワイトリスト: 特定の例外はpassを許可
            if isinstance(node.type, ast.Name) and node.type.id in ("ImportError", "AttributeError"):
                self.generic_visit(node)
                return
            
            # 型指定なしの bare except も検出対象
            self.issues.append(
                f"{node.lineno}: 握りつぶしexcept（except: pass）"
            )
        self.generic_visit(node)

def scan_file(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return [f"{path}: SyntaxError"]
    except UnicodeDecodeError:
        # バイナリファイルやエンコーディングが異なる場合はスキップ
        return []
    
    detector = GarbageDetector()
    detector.visit(tree)
    return [f"{path}:{issue}" for issue in detector.issues]

def main():
    issues = []
    # jarvis_core 配下の全 .py ファイルを再帰的にスキャン
    # scripts や tests も含めるか検討したが、指示書では jarvis_core/ が対象
    target_dir = Path("jarvis_core")
    if not target_dir.exists():
        print(f"Error: {target_dir} not found.")
        sys.exit(1)

    for py_file in target_dir.rglob("*.py"):
        issues.extend(scan_file(py_file))
    
    if issues:
        print("=== ゴミコード検出 ===")
        for issue in issues:
            print(issue)
        print(f"\n合計 {len(issues)} 件の問題が見つかりました。")
        sys.exit(1)
    else:
        print("ゴミコードなし")
        sys.exit(0)

if __name__ == "__main__":
    main()
