# Terminal Security

このドキュメントは、ターミナルコマンドの実行を制御する設定ファイルのフォーマットを説明します。

## 設定ファイル

`configs/terminal_security.yaml` を編集してポリシーを指定します。

### 主要フィールド

- `execution_policy`: `off` / `auto` / `turbo` のいずれか
- `allow_list`: 実行を許可するコマンドパターン
- `deny_list`: 実行を拒否するコマンドパターン
- `max_execution_time_seconds`: 実行タイムアウト（秒）
- `require_confirmation_for_sudo`: sudo 実行時の承認フラグ

### パターン形式

`allow_list` と `deny_list` は以下の形式で定義します。

```yaml
- pattern: "ls"
  is_regex: false
  reason: "Directory listing"
```

`is_regex: true` の場合は正規表現として評価されます。

## 例

```yaml
execution_policy: auto
allow_list:
  - pattern: "git status"
    is_regex: false
    reason: "Git status"

deny_list:
  - pattern: "rm -rf /"
    is_regex: false
    reason: "Dangerous delete"
```
