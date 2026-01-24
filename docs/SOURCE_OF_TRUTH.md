# JARVIS Single Source of Truth (SSoT)

このドキュメントは、JARVIS Research OS プロジェクトにおける「唯一の正解」となる設計原則、品質基準、規約を定義します。他のドキュメントがこれと矛盾する場合、本ドキュメントを優先します。

---

## 1. アーキテクチャ原則 (Architecture Principles)

### 1.1 モジュール管理の定義
- **`jarvis_core/`**: 安定したコアロジック。高いカバレッジ（原則 85% 以上）と厳格なインターフェースが求められる。
- **`jarvis_core/experimental/`**: 試作・研究段階のモジュール。カバレッジ要件は緩和されるが、コアロジックから完全に隔離（Import 分離）されなければならない。
- **`jarvis_web/`**: フロントエンド・API 層。

### 1.2 データフローの規約
- すべてのパイプライン実行結果は `docs/BUNDLE_CONTRACT.md` に従った構造で出力されなければならない。
- 実行中のログと成果物は `logs/runs/{run_id}/` に集約される。

---

## 2. 品質基準 (Quality Guardrails)

### 2.1 テストカバレッジ
- **Phase 1 (ブロッキング)**: Statement/Line カバレッジ **85%**。
- **Phase 2 (最終目標)**: Branch カバレッジを含む **95%**。
- ポリシー詳細は `docs/COVERAGE_POLICY.md` を参照。

### 2.2 契約テスト (Contract Testing)
- `BundleV2` 形式の出力は、必須 10 ファイルおよびスキーマ検証をパスしなければならない。
- PR ごとに `scripts/check_project_contract.py` によるリポジトリ整合性チェックが必須。

---

## 3. セキュリティポリシー (Security Policy)

### 3.1 ファイル操作の安全
- `jarvis_core.security.fs_safety` を通さないファイル入出力・サニタイズを禁止する。
- 外部からの ZIP ファイルはパス・トラバーサル対策済みの `safe_extract_zip` を用いること。

### 3.2 危険な関数の制限
- `eval()`, `exec()` の使用は原則禁止。数式評価などは `ast.parse` を用いた安全な評価器を自実装する。
- OS コマンドの発行はサニタイズされた引数のみを許可する。

---

## 4. ドキュメントの正当性 (Documentation Hierarchy)

1. **`docs/SOURCE_OF_TRUTH.md`** (本ファイル): 戦略的・原則的合意。
2. **`docs/contracts/`**: 形式的・技術的なインターフェース定義。
3. **`docs/PLANS/`**: 特定フェーズの実行計画（完了したものは本ファイルへ反映）。

---

## 5. DoD (Definition of Done)

機能開発 PR は以下の項目をすべて満たして完了とする。
- [ ] 既存の 6000+ 件のテストをパスしている。
- [ ] 対象モジュールの Line カバレッジが 85% を超えている。
- [ ] `check_project_contract.py` が成功している。
- [ ] `SOURCE_OF_TRUTH.md` の原則に反していない。
