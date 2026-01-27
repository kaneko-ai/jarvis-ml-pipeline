# Skills System Guide

## 概要とディレクトリ構造

Skills System は `skills/` 配下の `SKILL.md` と補助ファイルを読み込み、特定の作業フローを自動化します。

```
skills/
  README.md
  SKILL-CREATOR.md
  MCP.md
  WEBTEST.md
  ...
```

## SKILL.md の書き方

`SKILL.md` は以下の要素を含みます。

- 目的（いつ使うか）
- 必要な手順（順序付き）
- 参照ファイルやスクリプトの場所

```markdown
# Skill: Example

## Trigger
- Use when user requests X.

## Steps
1. Load configs.
2. Run scripts.
```

## リソースとスクリプトの使用方法

- `references/` は補足資料として読み込む
- `scripts/` は自動化スクリプトとして優先実行
- `assets/` はテンプレートや画像などの再利用素材

## 組み込みスキル一覧

- `SKILL-CREATOR`: スキル作成のガイド
- `MCP`: MCP Hub 連携の標準フロー
- `WEBTEST`: ブラウザテストの手順
- `SPEC`: 仕様確認フロー
- `TDD`: テスト駆動の手順

## カスタムスキルの作成方法

1. `skills/` に新しいフォルダを作成
2. `SKILL.md` を追加してトリガー条件と手順を記載
3. 必要に応じて `scripts/` や `references/` を追加

## CLI コマンドリファレンス

- `jarvis skills list`: 利用可能なスキル一覧
- `jarvis skills show <skill>`: スキル詳細
- `jarvis skills run <skill>`: スキル実行
