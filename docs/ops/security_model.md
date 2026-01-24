# Security Model

> Authority: POLICY (Level 1, Binding)

## Goals

- Prevent powerful tokens from being exposed to browsers.
- Ensure write endpoints require explicit authorization.
- Restrict CORS so read-only APIs are accessible only from approved origins.

## Trust Boundary

- **Browser**: Untrusted. Only read-only endpoints are accessible via CORS.
- **Worker**: Enforces authentication for write operations.
- **GitHub Actions**: Uses a dedicated token for status updates and workflow dispatch.

## Authentication

All write endpoints **must** include `Authorization: Bearer <token>`.

| Endpoint | Method | Required Token | Purpose |
| --- | --- | --- | --- |
| `/dispatch` or `/` | POST | `DISPATCH_TOKEN` | Trigger GitHub Actions workflow dispatch. |
| `/schedule/create` | POST | `SCHEDULE_TOKEN` | Create scheduled runs. |
| `/schedule/toggle` | POST | `SCHEDULE_TOKEN` | Enable/disable schedules. |
| `/status/update` | POST | `STATUS_TOKEN` | Update run status from GitHub Actions. |

Tokens are stored as Worker secrets and must never be embedded in browser code.

## CORS Policy

Read-only endpoints are public **but** CORS is restricted:

- **Allowed methods**: `GET` only.
- **Allowed origins**: GitHub Pages origin only by default (e.g. `https://kaneko-ai.github.io`).
- **Local development**: Add local origins via `ALLOWED_ORIGINS` (comma-separated) if needed.

Endpoints with CORS enabled:

| Endpoint | Method | Notes |
| --- | --- | --- |
| `/status` | GET | Polling run status. |
| `/schedule/list` | GET | List schedules for UI. |

Write endpoints do not send CORS headers, so browsers cannot call them directly.

## Configuration

Worker environment variables:

- `ALLOWED_ORIGINS`: Comma-separated list of approved origins.
- `DISPATCH_TOKEN`: Bearer token for dispatch.
- `SCHEDULE_TOKEN`: Bearer token for schedule writes.
- `STATUS_TOKEN`: Bearer token for status updates.

## Validation Checklist

- Anonymous POST requests are rejected.
- CORS is not `*` and only allows `GET` from approved origins.
