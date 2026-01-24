# Antigravity Auto-Approval Protocol (Phase 12)

## 概要
Antigravity AI（または他の自動化ツール）によるコード修正やアップデートを、安全に自動承認するための基準を定義します。

## 承認条件
以下のすべてのチェックが Github Actions において **PASS** している場合、PR は自動承認の対象となります。

1.  **Quality Gate (`quality-gates.yml`)**
    - ユニットテスト (`pytest`) が 100% 合格していること。
    - 回帰テストがパスしていること。
2.  **Security Audit Gate (`security_gate.yml`)**
    - `Bandit` による重大な脆弱性が検出されていないこと。
    - `Pip-audit` による依存関係の脆弱性がゼロであること。
    - `Secret Scan` により秘密情報の混入が疑われないこと。
3.  **Architecture Gate (`code-quality.yml` 内 / scripts/arch_gate.py)**
    - パッケージ境界違反がないこと。
4.  **Path Traversal Prevention (`security-cri-003.yml`)**
    - 外部入力に対するパスバリデーションが構成されていること。

## 適用外のケース
以下の変更を含む場合は、自動承認を行わず、人間によるレビューを必須とします。
- `jarvis_core/settings.py` の必須項目の変更。
- セキュリティポリシー (`policies/SECRETS_POLICY.md`) 自体の変更。
- 認証・認可ロジック (`jarvis_web/auth.py` 等) の大幅な改変。

## 運用
基準を満たした PR には `auto-approve` ラベルを付与し、ボットが承認コメントを投稿します。
