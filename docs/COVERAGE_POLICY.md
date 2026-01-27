> Authority: SPEC (Level 1, Binding)

# Coverage Policy - カバレッジポリシー

このドキュメントはJARVIS Research OSのテストカバレッジに関する公式ポリシーを定義します。

---

## 2段階ゲート方式

### Phase 1（当面のブロッキング）

| 項目 | 値 |
|------|-----|
| 評価対象 | Statement/Line のみ |
| Branch評価 | **無効** |
| しきい値 | **85%** |
| 設定ファイル | `.coveragerc.phase1` |

**目的**: CIを現実に合わせて"回る状態"に戻し、カバレッジ改善を継続可能にする

### Phase 2（最終ゲート）

| 項目 | 値 |
|------|-----|
| 評価対象 | Statement/Line + Branch |
| Branch評価 | **有効** |
| しきい値 | **95%** |
| 設定ファイル | `.coveragerc.phase2` |

**目的**: 分岐品質まで含めた最終ゲート

---

## 計測方法

### 計測コマンド

```bash
# Phase 1（デフォルト）
COVERAGE_PHASE=1 bash scripts/ci_coverage.sh

# Phase 2
COVERAGE_PHASE=2 bash scripts/ci_coverage.sh
```

### 設定ファイル

カバレッジ設定は以下のファイルで管理:
- `.coveragerc.phase1` - Phase 1用（branch無効、85%）
- `.coveragerc.phase2` - Phase 2用（branch有効、95%）
- `scripts/ci_coverage.sh` - CI用カバレッジ実行スクリプト

> [!IMPORTANT]
> **`ci.yml`にカバレッジ設定を直接書かない**
> カバレッジ条件の変更は必ず`scripts/ci_coverage.sh`または`.coveragerc.*`で行う。

---

## 除外ルール

### 許可されない除外方法

以下の方法でカバレッジ数値を作ることは**行わない**:
- `# pragma: no cover`の乱用
- `.coveragerc`での広範な除外パターン追加
- テストが通らないファイルを除外で数字を誤魔化す

### 許可される除外

- `if __name__ == "__main__":` ブロック
- デバッグ用コード（`if DEBUG:`等）
- 型チェック用のプロトコルクラス

---

## Phase 2 切替条件

### 必要条件

Phase 2に切り替えるには、以下の**すべて**を満たす必要がある:

1. Phase 1（85%）が**mainで連続10回**CI成功
2. 直近5PRで**カバレッジ低下が0回**
3. flake（再実行で通る系）が**0件**

### 切替手順

1. CIの`COVERAGE_PHASE`を2に変更するPRを**単独**で出す
2. そのPRでは"カバレッジを上げる変更は行わない"（原因切り分け）
3. PRタイトルに`[COVERAGE-GATE]`を含める

---

## 改善履歴の記録

PR毎に`docs/coverage_improvement_history.md`に以下を記録:

```markdown
## PR #xxx: [タイトル]
- 日付: YYYY-MM-DD
- 変更前カバレッジ: xx.xx%
- 変更後カバレッジ: xx.xx%
- 改善幅: +x.xx%
- 主な追加テスト:
  - `tests/xxx.py` - 対象モジュール説明
- CI時間: x分xx秒
```

---

## 関連ドキュメント

- [DECISIONS.md](./DECISIONS.md) - DEC-007: 2段階カバレッジゲート
- [coverage_improvement_history.md](./coverage_improvement_history.md) - 改善履歴

---

## Daily Coverage Snapshotとの役割分担

### 目的の違い

| 観点 | CIゲート（本ポリシー） | Daily Snapshot |
|------|------------------------|----------------|
| 目的 | PRの品質担保 | 継続的な観測・トレンド把握 |
| 実行タイミング | PR/push時 | 毎日00:10 JST |
| fail_under | 有効（85%/95%） | 無効 |
| 失敗時 | CIブロック | ログ記録のみ |

### 参照ドキュメント

- 詳細仕様: `docs/JAVIS_STATE_AND_ROADMAP.md` セクション8
- 実装: `scripts/daily_coverage_snapshot.sh`, `scripts/append_coverage_daily_md.py`
- 履歴: `docs/coverage_daily.md`

### 避けるべき行為（共通）

Daily Snapshotの数値が低い場合でも、以下は行わない:

1. `# pragma: no cover`を追加してカバレッジを上げる
2. `.coveragerc`の除外パターンを拡大する
3. テストをスキップする

これらはCIゲートのポリシー違反として扱われる。
