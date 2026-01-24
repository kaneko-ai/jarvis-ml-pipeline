import ast
import sys
import os
from pathlib import Path

# 禁止されているAPIリスト
BANNED_FUNCTIONS = {"eval", "exec", "__import__"}

def check_file(path: Path) -> list[str]:
    errors = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(path))
            
        for node in ast.walk(tree):
            # 関数呼び出しのチェック
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in BANNED_FUNCTIONS:
                        errors.append(f"{path}:{node.lineno}: Use of banned function '{node.func.id}'")
                elif isinstance(node.func, ast.Attribute):
                    # obj.eval() 等の形式（あまり一般的ではないがチェック）
                    if node.func.attr in BANNED_FUNCTIONS:
                        errors.append(f"{path}:{node.lineno}: Use of banned attribute/method '{node.func.attr}'")
    except SyntaxError:
        # 構文エラーのファイルはスキップ（別のリンターが拾うはず）
        pass
    except Exception as e:
        print(f"Error processing {path}: {e}")
        
    return errors

def main():
    target_dirs = ["jarvis_core", "jarvis_web", "api"]
    all_errors = []
    
    for d in target_dirs:
        if not os.path.exists(d):
            continue
        for root, _, files in os.walk(d):
            for file in files:
                if file.endswith(".py"):
                    all_errors.extend(check_file(Path(root) / file))
                    
    if all_errors:
        print("\n❌ Banned API usage found:")
        for err in all_errors:
            print(f"  {err}")
        sys.exit(1)
    else:
        print("✅ No banned API usage found.")

if __name__ == "__main__":
    main()
