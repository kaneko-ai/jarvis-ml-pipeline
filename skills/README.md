# Lean-24 Core Skills

> 最小・明確・再利用可能な20の開発スキル

## 概要

Lean-24 Coreは、AI駆動開発における**構想→実装→検証→統合**の全サイクルを、20個の疎結合スキルで実現するフレームワークです。各スキルは単一責務を持ち、相互参照により組み合わせて使用します。

## スキル一覧

### 計画・設計フェーズ
| スキル | 説明 | トリガ |
|--------|------|--------|
| [BRAIN](BRAIN.md) | アイデア→要件化（1問1答/選択肢） | 新機能/変更開始時 |
| [SPEC](SPEC.md) | 2–5分粒度の実装計画作成 | BRAIN合意後 |
| [VIBE-UI](VIBE-UI.md) | 美学駆動のUI設計 | UI/UX設計時 |

### 実装フェーズ
| スキル | 説明 | トリガ |
|--------|------|--------|
| [ORCH](ORCH.md) | タスク別サブエージェント実行 | SPEC実行時 |
| [PARA](PARA.md) | 独立課題の並列実行 | 複数独立タスク |
| [TDD](TDD.md) | テスト駆動開発（Red→Green→Refactor） | 全実装 |
| [WORKTREE](WORKTREE.md) | 隔離ワークスペース作成 | 並行作業 |

### 検証・デバッグフェーズ
| スキル | 説明 | トリガ |
|--------|------|--------|
| [VERIFY](VERIFY.md) | 証拠付き成功主張 | 完了主張前 |
| [DBG](DBG.md) | 体系的デバッグ（再現→差分→仮説→検証） | バグ発生時 |
| [WEBTEST](WEBTEST.md) | Playwrightによる動的Web検証 | Web機能テスト |

### 統合・品質管理フェーズ
| スキル | 説明 | トリガ |
|--------|------|--------|
| [REVIEW](REVIEW.md) | 仕様適合+コード品質レビュー | タスク完了後 |
| [FINISH](FINISH.md) | テスト→統合方針→実行→清掃 | ブランチ統合前 |

### インフラ・環境管理
| スキル | 説明 | トリガ |
|--------|------|--------|
| [ENV](ENV.md) | 環境差異吸収と設定分岐 | 環境依存処理 |
| [SAFE-IO](SAFE-IO.md) | 冪等・安全なファイル操作 | ファイル書込 |
| [RECOVER](RECOVER.md) | リトライ+エスカレーション | 一時的失敗 |

### ドキュメント・統合ツール
| スキル | 説明 | トリガ |
|--------|------|--------|
| [TOKEN](TOKEN.md) | トークン消費最適化 | 全フェーズ |
| [JOURNAL](JOURNAL.md) | 作業ログと再開ポイント記録 | セッション開始/終了 |
| [MCP](MCP.md) | MCPサーバ設計 | MCP開発時 |
| [OFFICE](OFFICE.md) | Office文書統合処理 | 文書生成/編集 |
| [SKILL-CREATOR](SKILL-CREATOR.md) | 新スキル作成ガイド | スキル追加時 |

## 使い方

### 基本フロー
```
1. BRAIN → 要件定義（選択肢で意図固め）
2. SPEC → 実装計画（2–5分タスク分解）
3. ORCH → 実装（サブエージェント + TDD）
4. VERIFY → 検証（証拠取得）
5. REVIEW → レビュー（仕様+品質）
6. FINISH → 統合（Merge/PR/保持/破棄）
```

### 典型的な組み合わせ

#### 新機能開発
```
BRAIN → SPEC → WORKTREE → ORCH(TDD + VERIFY) → REVIEW → FINISH
```

#### バグ修正
```
DBG → TDD → VERIFY → REVIEW → FINISH
```

#### 並行作業
```
SPEC → PARA(独立タスク群) → REVIEW → FINISH
```

#### UI開発
```
VIBE-UI → SPEC → WORKTREE → ORCH(WEBTEST) → REVIEW → FINISH
```

## 設計原則

### 1. 単一責務
各スキルは1つの明確な目的のみを持つ

### 2. 外部参照優先
重複を避け、`see [SKILL_NAME]`で他スキルを参照

### 3. 最小本文
frontmatter + 短手順のみ、詳細は外部ドキュメントへ

### 4. トリガ明示
いつ使うべきかを`description`に明記

### 5. 証拠ベース
主張には常に証拠（コマンド実行結果）を添付

## 拡張方法

新しいスキルを追加する場合は、[SKILL-CREATOR](SKILL-CREATOR.md)に従って作成してください。

```bash
# 新スキル作成例
1. skills/NEW-SKILL.md を作成
2. frontmatter (name/description) を記述
3. 既存スキルとの重複を確認
4. 参照リンクで既存スキルを活用
5. 100語以内で本文をまとめる
```

## メンテナンス

- **更新**: 実運用で改善点を発見したら即座に反映
- **削除**: 6ヶ月使われないスキルは非推奨化
- **統合**: 類似スキルは統合を検討
- **分割**: 1スキルが複数責務を持つ場合は分割

## ライセンス

MIT License - プロジェクトライセンスに準拠

## 参照

- [JARVIS Research OS](../README.md) - メインプロジェクト
- [SPEC_AUTHORITY](../docs/SPEC_AUTHORITY.md) - 仕様権威レベル
- [DoD](../docs/DoD.md) - Definition of Done
