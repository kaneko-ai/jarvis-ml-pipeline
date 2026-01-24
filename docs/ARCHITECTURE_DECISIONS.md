# Architecture Decisions

> Authority: REFERENCE (Level 2, Non-binding)


## Runtime and deployment boundaries

- Serverless (Pages) should only reference the manifest and static artifacts.
- The local API is a supporting tool and should not be a recommended dependency for Pages.

## Bundle assembly

- The canonical bundle implementation is consolidated in `jarvis_core/bundle/assembler.py`.
