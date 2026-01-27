# Terminal Security

## 概要とセキュリティモデル

Terminal Security はターミナルコマンドの実行を制御するためのポリシー層です。
`ExecutionPolicy` と Allow/Deny List を組み合わせ、危険なコマンドの実行を防止します。

## ExecutionPolicy の説明

- **OFF**: コマンド実行を完全に無効化します。
- **AUTO**: 既定の安全パターンに一致するコマンドのみ実行します。
- **TURBO**: 高速実行モード。Allow/Deny List をベースに実行します。

## Allow List / Deny List の設定方法

`configs/terminal_security.yaml` でポリシーを指定します。

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

`allow_list` と `deny_list` は以下の形式です。

```yaml
- pattern: "ls"
  is_regex: false
  reason: "Directory listing"
```

`is_regex: true` の場合は正規表現として評価されます。

## デフォルトパターン一覧

既定では以下のコマンドが許可されます。

- `ls`, `pwd`, `cat`
- `git status`, `git diff`
- `rg`, `sed`, `awk`

## Sudo 承認フローの説明

`require_confirmation_for_sudo: true` の場合、`sudo` を含むコマンドは承認フローを経由します。

1. 実行前に承認要求が発行される
2. 承認されると一度だけ実行される
3. 承認されない場合は実行されない
