# Recording Session Logs

- Owner: Echolog Maintainers
- Status: Draft
- Last Updated: 2025-09-22

## Summary
Add a session-scoped logging capability that writes a readable, rotating log file into each recording session directory. The log captures session metadata, lifecycle events (start/stop, chunk creation), ffmpeg command and stderr, and application warnings/errors with configurable verbosity. This enables users to troubleshoot recording issues, audit behavior, and correlate artifacts with timestamps without leaving the session folder.

Press release: “Echolog now generates per-session logs with rich metadata and events, making troubleshooting simple and transparent.”

## Goals
- G1 (P0): Create a `session.log` file in each session folder containing metadata and lifecycle events by default before first chunk is recorded. Measurable: file exists with ≥5 required metadata fields.
- G2 (P0): Capture chunk creation events with filename, sequence, timestamps, and final file size. Measurable: one log line per chunk with all fields.
- G3 (P0): Record the exact ffmpeg command and stream stderr lines with level‑appropriate verbosity. Measurable: command present; stderr captured when level ≥ info.
- G4 (P1): Allow configuring log level and rotation via config and CLI. Measurable: settings persist and are reflected in runtime behavior.
- G5 (P2): Ensure logging overhead is negligible (<1% CPU baseline, imperceptible I/O impact). Measurable: internal benchmark on 2h session.

### Non-goals
- Centralized/remote log aggregation, analytics, or cloud export.
- Retrofitting old sessions with logs.

## Users & Use cases (JTBD)
- When my recording has artifacts, I want a timeline of chunk creation and errors so I can pinpoint issues.
- When ffmpeg fails to start, I want the full command and stderr so I can diagnose quickly.
- When supporting other users, I want a single `session.log` file to request for triage.

## Requirements

### Functional (numbered, testable)
1. [P0] On session start, create `~/recordings/{session_id}/session.log` before audio capture begins. Rationale: ensures early failure visibility.
2. [P0] Log metadata: `session_id`, ISO8601 UTC start time, device identifier, sample rate, channels, codec/format, segment duration, output dir, CLI/config overrides. Rationale: complete reproducibility.
3. [P0] Log lifecycle events: session start/stop (with reason), chunk creation (filename, sequence, start/end timestamps, size), recoveries/retries. Rationale: investigate artifacts.
4. [P0] Log ffmpeg: exact command; stream stderr lines. Rationale: primary dependency visibility.
5. [P1] Configurable level: `debug|info|warning|error` via config and CLI, default `info`. Rationale: noise control.
6. [P1] Rotation: size‑based by default (`5 MB`, keep 3); support disabling or time‑based rotation. Rationale: prevent disk bloat during long sessions.
7. [P1] Status command surfaces active session log path. Rationale: discoverability.
8. [P2] Flush logs on graceful shutdown and on fatal error handler. Rationale: durability.

### Non-functional
- Performance (P0): Logging adds <1% CPU on reference machine; async/buffered writes.
- Reliability (P0): Log is written even if recording ends unexpectedly; final line indicates stop reason.
- Security/Privacy (P1): No user PII beyond device/system identifiers used for audio capture.
- Operability (P1): Log format is human‑readable and grep‑friendly; timestamps in UTC.

## UX
- CLI prints a single informational line on start: `Logging to <path> (level=<level>)`.
- `status` displays: `log: <path>`.

## Data (schema / events)
- File: `session.log` (rotated as `session.log.[N]`).
- Line format: `YYYY-MM-DDTHH:MM:SSZ LEVEL logger: message key=value ...`.
- Events: `session_start`, `chunk_created`, `warning`, `error`, `session_stop`.

## API changes
- CLI flags:
  - `--log-level {debug,info,warning,error}`
  - `--log-rotation {size,time,off}`
  - `--log-max-bytes BYTES` (default 5242880)
  - `--log-backup-count N` (default 3)
- Config (`echolog.conf`):
  - `logging.level`, `logging.rotation`, `logging.max_bytes`, `logging.backup_count`, `logging.time_when`, `logging.utc`.

## Dependencies & migration
- Uses Python `logging` with `RotatingFileHandler` and optionally `TimedRotatingFileHandler`.
- No data migration. Backwards compatible with existing sessions; new sessions gain logs.

## Rollout & guardrails
- Default enabled at `info` level with size rotation.
- Feature flags: CLI/config can effectively disable rotation or lower verbosity.
- Fallback: If file handler fails, print path+error to stderr and continue recording.

## Success metrics & telemetry
- Leading: % sessions where `session.log` exists and contains required metadata.
- Leading: Average log file size per hour of recording (target <1 MB/h at `info`).
- Lagging: Reduction in unresolved support issues related to “unknown ffmpeg error.”

## Risks & open questions
- Risk: Excessive stderr volume from ffmpeg at `info`. Mitigation: default mapper to `DEBUG` unless error patterns detected.
- Risk: I/O contention on slow disks. Mitigation: buffered writes; reduce frequency at `info`.
- Open: Should we redact device names if they contain user identifiers?
- Open: Do we need JSON logs for future machine parsing?


