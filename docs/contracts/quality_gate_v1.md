# Quality Gate v1

## 目的
"空っぽの成功"を禁止し、CIの成果物が最低品質を満たしているかを機械的に判定する。

## 入力
次の成果物から評価する。

- `summary.json`
- `stats.json`
- `report.md`
- `warnings.jsonl` (任意)

## 判定基準 (v1)

| 項目 | 判定 | 備考 |
| --- | --- | --- |
| papers_found | `>= 1` | `stats.json` の `meta` を優先し、なければ `summary.json` の `papers` を使用 |
| report.md | 存在する | `report.md` が生成されていること |
| citations_attached | `true` | `report.md` 内に引用の痕跡 (例: `[1]` または `http`) があること |

## 出力

Quality Gate v1 は以下を返す。

- `gate_passed` (boolean)
- `gate_reason` (string)
- `papers_found` (integer)
- `papers_processed` (integer)
- `citations_attached` (boolean)

## 運用ルール

- `gate_passed` が `false` の場合、CIの `status` は必ず `failed` に落とす。
- `gate_passed` が `true` であっても、`status` が `failed` の場合は成功とは見なさない。
