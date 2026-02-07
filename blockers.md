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
