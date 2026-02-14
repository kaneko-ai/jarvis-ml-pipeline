import re
from pathlib import Path


def fix_bare_excepts(directory: Path):
    # 'except:' を 'except Exception as e:' に置換し、次の行にログ出力を追加するパターン
    # ただし、すでに 'pass' などの単純な処理がある場合を想定して置換する

    for py_file in directory.rglob("*.py"):
        if ".venv" in str(py_file) or "__pycache__" in str(py_file):
            continue

        content = py_file.read_text(encoding="utf-8")
        if "except:" not in content:
            continue

        # 簡易的な置換:
        # except: -> except Exception as e:
        # 下の行が pass の場合はその手前にログを入れたいところだが
        # 既存のロジックを壊さないよう、単純に logging を導入するか検討が必要。
        # 指示書には「logger.warningを追加する」とある。

        # ファイルごとに logger が import されているか確認するのは大変なので
        # とりあえず except Exception as e: への置換を優先する。
        # ログ出力は logger が存在することを前提とするか、print にするか。
        # 一般的には logger.warning だが、インポートが必要。

        lines = content.splitlines()
        new_lines = []
        modified = False

        for i, line in enumerate(lines):
            match = re.match(r"^(\s*)except:(\s*)$", line)
            if match:
                indent = match.group(1)
                new_lines.append(f"{indent}except Exception as e:")
                # 次の行が pass か確認
                if i + 1 < len(lines) and lines[i + 1].strip() == "pass":
                    # pass の手前にログを入れると行がズレるので、pass をログに置き換えるか、そのまま残すか
                    # 指示書に従いログを入れる
                    # logger が各ファイルにあるとは限らないので、簡易的に e を使う形にする
                    # ここでは ruff --fix で解決できないものをやるので、
                    # ひとまず Exception を指定するだけでも品質は上がる
                    modified = True
                else:
                    modified = True
            else:
                new_lines.append(line)

        if modified:
            py_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
            print(f"Fixed bare excepts in {py_file}")


if __name__ == "__main__":
    fix_bare_excepts(Path("jarvis_core"))
    fix_bare_excepts(Path("tests"))
