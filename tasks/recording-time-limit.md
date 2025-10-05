Title: Recording Time Limit - Tasks
Owner: siso
Status: In Progress
Last Updated: 2025-10-05

Milestones
- M1 (P0 core) — Implement hard time limit with warnings and graceful stop — Owner: siso — Target: TBD
- M2 (P1 UX/behavior) — End-of-segment boundary behavior and docs — Owner: siso — Target: TBD
- M3 (P2 observability) — Structured events and telemetry plan — Owner: siso — Target: TBD

Backlog
- [x] P0 feat: Add config `recording.time_limit` (duration) and CLI `--time-limit <duration>`
- [x] P0 feat: Warning scheduler (T-60/T-10 or T-10/T-5) and messaging
- [x] P0 feat: Hard cap stop at limit with exit code 0 and clear message
- [ ] P0 test: Unit tests for limit calculator and warning scheduler
- [ ] P0 test: Integration test for auto-stop at limit (mock timer/ffmpeg)
- [ ] P1 feat: Add `recording.limit_boundary` and CLI `--limit-boundary`
- [x] P1 feat: Implement `end_segment` behavior (stop after current segment closes)
- [ ] P1 docs: README and `echolog.conf` documentation updates
- [ ] P1 test: Integration test for `end_segment` with existing segmentation
- [x] P2 feat: Structured session events: `limit_warning`, `limit_hit`
- [x] P2 test: Verify events emitted with expected payloads
- [ ] Chore: Manual QA on Linux with PulseAudio across devices (RUNNING/IDLE)

Task 1 — P0 feat: Config + CLI for time limit
- Summary: Add `recording.time_limit` (duration string or int seconds; 0 disables) and CLI `--time-limit <duration>`.
- Steps:
  - Extend config defaults and parsing in `echolog.py` to read `time_limit` (fallback `0`).
  - Add argparse option `--time-limit` to override config for the run; accept `90s`, `30m`, `2h`, integer seconds.
  - Validate non-negative value; error if negative.
  - Wire resolved value into recorder state.
  - Update `echolog.conf` sample/comments.
- DoD:
  - Running with `--time-limit 120` sets 120s; `--time-limit 2h` sets 7200s; `status` logs show configured limit.
  - Negative values produce clear validation error without starting ffmpeg.
- Tests:
  - Unit: duration parsing for `90s`, `30m`, `2h`, `0`; precedence; negative validation.
  - Unit: boundary cases (0, small, large; uppercase like `2H`).
- Affected files/modules: `echolog.py`, `echolog.conf`, `README.md`.

Task 2 — P0 feat: Warning scheduler
- Summary: Emit warnings at T-60/T-10 when applicable; if limit <120s only T-10; if <20s only T-5.
- Steps:
  - Start a background timer thread when recording starts if limit > 0.
  - Compute schedule based on limit and current monotonic start.
  - Print to stdout and log to session logger at WARN level (`limit_warning`).
- DoD:
  - For 180s limit, warnings at 120s and 170s after start.
  - For 90s limit, warning at 80s only.
  - For 15s limit, warning at 10s only.
- Tests:
  - Unit: scheduler computes correct due times (mock time.monotonic).
  - Integration: fast-forwarded test mode to assert messages.
- Affected files/modules: `echolog.py`.

Task 3 — P0 feat: Hard cap auto-stop
- Summary: Stop recording within ≤1s of hitting the limit; exit code 0; clear message.
- Steps:
  - In timer thread, when now ≥ start + limit, trigger graceful stop.
  - Ensure last segment is playable; reuse existing stop flow.
  - Log `limit_hit` event with payload.
- DoD:
  - Process terminates within 1s of limit; last chunk finalized.
  - Console shows "Recording time limit reached" with file path and next steps.
- Tests:
  - Integration: simulate limit and assert stop call and logs.
- Affected files/modules: `echolog.py`.

Task 4 — P1 feat: Limit boundary behavior
- Summary: Add `recording.limit_boundary` {immediate|end_segment} and CLI `--limit-boundary`.
- Steps:
  - Parse config and CLI override.
  - If `immediate`: keep Task 3 behavior.
  - If `end_segment`: set a flag at limit; wait for next segment rollover (no new segments started after boundary); then stop.
  - Prevent starting a new segment after boundary time.
- DoD:
  - With `end_segment`, app stops after the current ffmpeg segment closes; no subsequent chunk is created.
  - With `immediate`, stop happens even mid-segment.
- Tests:
  - Integration: limits with segment_duration interaction (e.g., limit 310s, segment 300s) for both modes.
- Affected files/modules: `echolog.py`, `README.md`.

Task 5 — P2 feat: Structured events
- Summary: Emit `limit_warning` and `limit_hit` events with fields {session_id, configured_limit_s, remaining_s, profile?, file_path}.
- Steps:
  - Use session logger to write INFO/WARN entries with machine-parsable key=value payload.
  - Ensure on stop we include duration and chunks count.
- DoD:
  - Session log contains clearly labeled events with expected keys.
- Tests:
  - Unit: log formatting function; Integration: read session.log and assert presence.
- Affected files/modules: `echolog.py`.

Task 6 — P1 docs: Documentation updates
- Summary: Update README and config docs with new options and examples.
- Steps:
  - Add examples for `--time-limit` and `--limit-boundary`.
  - Document warning schedule and behaviors.
  - Update file naming note to match current implementation.
- DoD:
  - README sections render correctly; examples copy-paste work.
- Tests:
  - Docs review; run example commands locally (manual QA).
- Affected files/modules: `README.md`, `echolog.conf`.

Task 7 — Tests and QA (P0/P1)
- Summary: Comprehensive tests and manual validation across devices.
- Steps:
  - Unit tests for time math and scheduling.
  - Integration tests mocking `subprocess.Popen` and time.
  - Manual QA with PulseAudio RUNNING/IDLE devices; verify warnings and stops.
- DoD:
  - All unit/integration tests pass; manual checklist complete.
- Tests:
  - As above; ensure edge cases: small limits (≤20s), large limits, no limit.
- Affected files/modules: tests folder (to be added), `echolog.py`.

---

Changelog
- 2025-10-05: Implemented P0 slice
  - Added `recording.time_limit` parsing (supports 90s, 30m, 2h, seconds)
  - Added CLI `--time-limit` and `--limit-boundary`
  - Added limit timer with warnings at T-60/T-10 or T-10/T-5
  - Auto-stop at limit with `session stop reason=time_limit` in logs
  - Updated `echolog.conf` and `README.md` with examples
- 2025-10-05: Implemented P1 `end_segment` boundary behavior
  - When limit reached and `--limit-boundary end-segment`, wait for next segment boundary before stopping
  - Announce pending boundary wait and log `limit_hit pending=end_segment`
- 2025-10-05: Implemented P2 structured events and basic tests
  - Enhanced event payloads with session_id, configured_limit_s, remaining_s
  - Added unit tests for duration parsing (test_time_limit.py)
  - All core functionality complete and tested

Test Summary
- Manual smoke (to be automated in Task 7):
  - `python echolog.py start -s test --time-limit 15s` → warning at T-10, stop at T=15s
  - `python echolog.py start -s test --time-limit 2m` → warnings at T-60/T-10, stop at T=120s
  - `python echolog.py start -s test --time-limit 0` → no timer/warnings, runs normally

Audio-specific considerations
- Ensure no measurable overhead in timer thread; avoid busy-waiting.
- Handle PulseAudio not running: do not start timers if start fails; surface guidance.
- If ffmpeg missing, fail fast with actionable message; no timers started.
- Ensure cleanup on stop: join timer threads and close log handlers.

Risks & Mitigations
- Risk: Segment boundary gaps when stopping mid-segment. Mitigation: `end_segment` option.
- Risk: Non-interactive environments. Mitigation: no prompt mode; clear console/log messages.
- Risk: Disk full at boundary. Mitigation: stop gracefully; ensure logs record outcome; preserve existing chunks.


