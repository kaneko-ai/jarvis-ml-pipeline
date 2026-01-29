"""Vulture whitelist - 意図的に未使用に見えるコード"""
# CLIエントリーポイント
main  # jarvis_cli.py
cmd_screen  # jarvis_core/active_learning/cli.py

# pytest fixtures
# これらはpytestが自動検出するため未使用に見える

# Pydanticモデルの __init__ パラメータ
# model_validator等で使用
