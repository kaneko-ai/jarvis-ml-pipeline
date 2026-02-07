# Blockers & Manual Review Required

**Purpose**: Document issues that require human intervention

---

## Active Blockers (0)

(Empty - will be populated when blockers are encountered)

---

## Template for New Blocker

```markdown
### Blocker #N - [DATE]

**Test**: tests/test_file.py::test_name
**Category**: [Import Error / Assertion Failure / Architecture Issue / etc.]
**Priority**: [P0 / P1 / P2 / P3]

**Error Message**:
(Paste full error)

**Attempted Solutions**:
1. [Description of attempt 1] - Result: Failed because X
2. [Description of attempt 2] - Result: Failed because Y
3. [Description of attempt 3] - Result: Failed because Z

**Hypothesis**:
[Why this is failing - root cause theory]

**Recommendation**:
[What needs to be done to fix - may require human decision]

**Status**: 🔴 BLOCKED
```

---

## Resolved Blockers (0)

(Will be moved here when resolved)

---

### Blocker #1 - 2026-02-07

**Task**: TD-027 PRコメント投稿
**Category**: Tooling / Environment
**Priority**: P1

**Error Message**:
gh : The term 'gh' is not recognized

**Hypothesis**:
GitHub CLI が実行環境に未インストールのため、PR #85/#90/#96 へのコメント投稿を自動実行できない。

**Recommendation**:
gh を導入して gh auth login 後にコメント投稿を再実行する。

**Status**: BLOCKED

### Blocker #2 - 2026-02-07

**Task**: TD-029 mypy core modules
**Category**: Type Checking
**Priority**: P1

**Error Message**:
uv run mypy --explicit-package-bases --follow-imports=skip ... -> Found 48 errors in 20 files

**Hypothesis**:
コア4モジュールに未注釈関数・Optional未処理・型不整合が広く残っている。

**Recommendation**:
モジュール単位（evidence/contradiction/citation/sources）で段階修正し、最後に || true を除去する。

**Status**: BLOCKED

### Blocker #3 - 2026-02-07

**Task**: TD-026 bandit gate
**Category**: Security
**Priority**: P1

**Error Message**:
uv run bandit -r jarvis_core -ll -> Medium 33件

**Hypothesis**:
既存コードに urllib.request.urlopen / pickle.load / timeout未指定 requests が多く残存。

**Recommendation**:
高頻出パターンから順次修正し、必要箇所のみ # nosec に理由を添えて限定適用する。

**Status**: BLOCKED
