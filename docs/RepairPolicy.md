# JARVIS Repair Policy

> Authority: REFERENCE (Level 2, Non-binding)


## 失敗タイプと対応

### 1. 取得失敗（FETCH_FAIL）
| 条件 | アクション |
|------|-----------|
| 一時的ネットワーク | 3回リトライ後スキップ |
| API制限 | warnings.jsonlに記録、次回実行 |
| 論文削除 | paper status=unavailable |

**非推奨**: 取得失敗を無視して空bundleを出す

### 2. 根拠抽出失敗（EVIDENCE_FAIL）
| 条件 | アクション |
|------|-----------|
| fulltext取得不可 | abstract fallback |
| パース失敗 | confidence=low + warnings |
| locator特定不可 | claim残す、evidence無しで明示 |

**非推奨**: claimを削除する

### 3. 品質回帰（REGRESSION）
| 条件 | アクション |
|------|-----------|
| evidence_coverage低下 | 直近変更をrevert |
| 構造破損 | 即時hotfix |
| goldset failが増加 | PRマージ非推奨 |

### 4. CI失敗（CI_FAIL）
| タイプ | アクション |
|--------|-----------|
| core fail | マージ非推奨、即修正 |
| legacy fail | artifact確認、計画的修正 |
| install fail | requirements.lock確認 |

## エスカレーション

1. 自動修復不可 → Runbook手順実行
2. Runbook手順で解決不可 → DecisionLog.mdに記録
3. 重大回帰 → revert + postmortem
