# Tasks: Recording Session Logs

PRD QA: Pass
- High-risk gaps: None blocking; watch I/O overhead and ffmpeg stderr noise.
- Suggested edits: Default map ffmpeg stderr to DEBUG unless severity detected; enforce UTC timestamps explicitly in config doc.

## Milestones
- M1: Logger foundation and config/CLI (Owner: maintainer) — 2025-09-24
- M2: ffmpeg integration + chunk events (Owner: maintainer) — 2025-09-25
- M3: UX/status, docs, performance guardrails (Owner: maintainer) — 2025-09-26

## Backlog
- [x] Implement session logger with rotation (P0, feat)
- [x] Parse logging config from `echolog.conf` (P1, feat)
- [x] Add CLI flags for logging (P1, feat)
- [x] Log session start metadata (P0, feat)
- [x] Log ffmpeg command (P0, feat)
- [x] Capture ffmpeg stderr lines (P0, feat)
- [x] Log chunk creation events (P0, feat)
- [x] Log session stop summary (P0, feat)
- [x] Flush logs on shutdown and fatal (P1, chore)
- [x] Expose log path in `status` (P1, feat)
- [x] Add performance guardrails (P2, chore/test)
- [x] Update README docs (P1, docs)

---

### Task: Implement session logger with rotation
- Label: P0, feat
- Summary: Create session-scoped logger writing `session.log` with size-based rotation.
- Steps:
  - Instantiate Python `logging.Logger` per session with `RotatingFileHandler`.
  - Configure format `%(asctime)s %(levelname)s %(name)s: %(message)s`, UTC.
  - Place file at `~/recordings/{session_id}/session.log`.
- DoD:
  - Log file appears on session start; rollover at ~5MB with 3 backups.
- Tests:
  - Unit: handler configured with expected params.
  - Integration: start short session; assert file created and writable.
- Affected files/modules:
  - `echolog.py` (session lifecycle), logging utility module if extracted.

### Task: Parse logging config from echolog.conf
- Label: P1, feat
- Summary: Add config keys for level, rotation, size, backups, utc/time_when.
- Steps:
  - Extend config parser to read `logging.*` keys with defaults.
  - Validate values; clamp/normalize.
- DoD:
  - Configured values reflected in logger initialization.
- Tests:
  - Unit: parse valid/invalid configs; ensure defaults applied.
- Affected files/modules:
  - `echolog.conf`, config parsing in `echolog.py`.

### Task: Add CLI flags for logging
- Label: P1, feat
- Summary: Add `--log-level`, `--log-rotation`, `--log-max-bytes`, `--log-backup-count`.
- Steps:
  - Extend `argparse` with flags; merge with config precedence.
  - Print startup line: log path + level.
- DoD:
  - Flags override config; help text present.
- Tests:
  - Unit: argparse parsing; precedence tests.
- Affected files/modules:
  - `echolog.py` (CLI setup).

### Task: Log session start metadata
- Label: P0, feat
- Summary: Emit metadata fields and resolved ffmpeg settings at start.
- Steps:
  - Gather device, sample rate, channels, codec/format, segment time, output dir, overrides.
  - Log as a single structured line.
- DoD:
  - Line contains all required keys; timestamps UTC ISO8601.
- Tests:
  - Integration: start session; validate presence/format with regex.
- Affected files/modules:
  - `echolog.py` (start flow).

### Task: Log ffmpeg command
- Label: P0, feat
- Summary: Log the exact command array/string before launching ffmpeg.
- Steps:
  - Before subprocess spawn, log the command at INFO/DEBUG.
- DoD:
  - Command captured exactly as executed.
- Tests:
  - Unit: command builder returns string; compare against log line.
- Affected files/modules:
  - `echolog.py` (ffmpeg invocation).

### Task: Capture ffmpeg stderr lines
- Label: P0, feat
- Summary: Stream stderr line-by-line into session logger.
- Steps:
  - Read from process stderr asynchronously; write to logger respecting level.
- DoD:
  - Stderr present in log during recording; performance unaffected.
- Tests:
  - Integration: simulate ffmpeg; assert lines appear.
- Affected files/modules:
  - `echolog.py` (process I/O loop).

### Task: Log chunk creation events
- Label: P0, feat
- Summary: On each segment finalize, log file name, index, start/end, size.
- Steps:
  - Hook into segmentation completion; stat file size on close.
- DoD:
  - One log line per chunk with all fields populated.
- Tests:
  - Integration: record short session with 2 segments; verify two lines.
- Affected files/modules:
  - `echolog.py` (segmentation handling).

### Task: Log session stop summary
- Label: P0, feat
- Summary: On stop, log reason, total chunks, total duration.
- Steps:
  - Capture stop cause (user/device/error); compute duration.
- DoD:
  - Final line present with summary fields.
- Tests:
  - Integration: stop via user request; assert summary line.
- Affected files/modules:
  - `echolog.py` (shutdown flow).

### Task: Flush logs on shutdown and fatal
- Label: P1, chore
- Summary: Ensure handlers flush/close on normal and error paths.
- Steps:
  - Register atexit/signal handlers to flush; try/finally around main loop.
- DoD:
  - No missing tail lines in abrupt stop simulations.
- Tests:
  - Integration: send SIGINT/SIGTERM; check last lines present.
- Affected files/modules:
  - `echolog.py` (signal handling), logging setup.

### Task: Expose log path in status
- Label: P1, feat
- Summary: Include `log: <path>` in `status` command output.
- Steps:
  - Add field to status construction; print human-friendly path.
- DoD:
  - `status` shows path when session active.
- Tests:
  - Unit: status formatter outputs field.
- Affected files/modules:
  - `echolog.py` (status command).

### Task: Add performance guardrails
- Label: P2, chore/test
- Summary: Verify logging overhead and provide guidance for tuning.
- Steps:
  - Run 30–60 min session; measure CPU and log size/hour.
  - Document findings and recommended levels.
- DoD:
  - Overhead <1% CPU on ref machine; metrics recorded.
- Tests:
  - Manual benchmark; attach results to PR.
- Affected files/modules:
  - N/A (docs/bench notes), `README.md` update.

### Task: Update README with usage and config
- Label: P1, docs
- Summary: Document log file location, flags, config, examples.
- Steps:
  - Add section to README; include sample log lines.
- DoD:
  - README section complete with examples and defaults.
- Tests:
  - Docs lint/build if applicable; peer review.
- Affected files/modules:
  - `README.md`


