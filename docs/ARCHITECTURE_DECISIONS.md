# Architecture Decisions

## Runtime and deployment boundaries

- Serverless (Pages) must only reference the manifest and static artifacts.
- The local API is a supporting tool and must not be a required dependency for Pages.

## Bundle assembly

- The canonical bundle implementation is consolidated in `jarvis_core/bundle/assembler.py`.
