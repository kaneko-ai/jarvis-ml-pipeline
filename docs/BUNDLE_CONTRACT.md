> Authority: GATE (Level 3, Binding)

# JARVIS Run Bundle Contract

Run成果物（Bundle）の契約。すべてのrunはこの契約に従う。

---

## 出力ディレクトリ

```
logs/runs/{run_id}/
```

run_id: UUID形式（例: 20241227_192700_abc123）

---

## 必須ファイル（欠けたらrun FAIL）

| ファイル | 用途 | 必須キー |
|---------|------|---------|
| `input.json` | 実行条件 | goal, query, constraints |
| `run_config.json` | 実行設定 | run_id, pipeline, timestamp |
| `papers.jsonl` | 論文メタ | paper_id, title, year |
| `claims.jsonl` | 主張 | claim_id, paper_id, claim_text |
| `evidence.jsonl` | 根拠 | claim_id, paper_id, evidence_text, locator |
| `scores.json` | スコア | features, rankings |
| `result.json` | 実行結果 | run_id, status, answer, citations |
| `eval_summary.json` | 評価結果 | gate_passed, fail_reasons, metrics |
| `warnings.jsonl` | 警告 | code, message, severity |
| `report.md` | 人間向け | - |

---

## result.json スキーマ

```json
{
  "run_id": "string",
  "task_id": "string",
  "status": "success|failed|needs_retry",
  "answer": "string",
  "citations": [
    {
      "paper_id": "string",
      "claim_id": "string",
      "evidence_text": "string",
      "locator": { "section": "string", "paragraph": 0 }
    }
  ],
  "warnings": [],
  "timestamp": "ISO8601"
}
```

---

## eval_summary.json スキーマ

```json
{
  "run_id": "string",
  "status": "pass|fail",
  "gate_passed": true,
  "fail_reasons": [
    { "code": "CITATION_MISSING", "msg": "..." }
  ],
  "metrics": {
    "citation_count": 0,
    "evidence_coverage": 0.0,
    "warning_count": 0
  },
  "timestamp": "ISO8601"
}
```

---

## fail_reasons コード一覧

| Code | 説明 |
|------|------|
| CITATION_MISSING | 引用がゼロ |
| EVIDENCE_WEAK | 根拠が薄い |
| LOCATOR_MISSING | 根拠位置情報がない |
| ASSERTION_DANGER | 断定の危険 |
| PII_DETECTED | PII検出 |
| FETCH_FAIL | 取得失敗 |
| INDEX_MISSING | 索引なし |
| BUDGET_EXCEEDED | 予算超過 |

---

## DoD

- [ ] runが完了したら必須10ファイルが揃う
- [ ] 失敗時でもresult.jsonとeval_summary.jsonが残る
- [ ] gate_passed=false のとき status=failed
- [ ] show-runがfail理由を表示できる
