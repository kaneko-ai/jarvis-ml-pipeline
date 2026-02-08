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

### Blocker #SEC-001 - 2026-02-08

**Task**: SEC-001 (.env history purge)
**Category**: Security / Repository history rewrite
**Priority**: P0

**Status**: PENDING HUMAN APPROVAL

**Detail**:
- Removed `.env` from git tracking and added `.env` to `.gitignore`.
- Full history purge requires force-push and coordination for all collaborators.
- Deferred for manual execution after explicit approval.

### Blocker #TD-010 - 2026-02-08

**Task**: TD-010 (10 consecutive green CI runs on `main`)
**Category**: CI verification window / requires remote history
**Priority**: P1

**Status**: PENDING REMOTE VERIFICATION

**Detail**:
- Local quality gates are currently passing.
- Completion criterion requires observing 10 consecutive successful CI executions on `main`.
- This cannot be finalized from local-only execution; needs GitHub Actions history confirmation after merges.

### Blocker #TD-020 - 2026-02-08

**Task**: TD-020 (Docker full validation)
**Category**: Environment dependency
**Priority**: P1

**Status**: PENDING ENVIRONMENT SETUP

**Detail**:
- `docker --version` returned command-not-found on this machine.
- `docker build -t jarvis-test .` and containerized validation are currently not executable.
- Continue with non-Docker tasks first; complete TD-020 after Docker installation.
