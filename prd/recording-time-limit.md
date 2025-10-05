Title: Recording Time Limit
Owner: siso
Status: Draft
Last Updated: 2025-10-05

Summary
The Recording Time Limit feature introduces configurable maximum durations for audio recording sessions in Echolog. It prevents runaway recordings, protects disk space, and enforces policy-driven capture windows. Users can set global and per-mode limits (e.g., quick note vs. long session), receive proactive countdown notifications, and choose what happens on limit reach (auto stop, segment and continue, or prompt). The feature integrates guardrails for disk space and service health, logs events for observability, and is backward compatible (disabled by default).

Goals
- P0: Enable a configurable global recording time limit (e.g., 30 min default off) applied to all sessions.
- P0: Provide clear user notifications before and at limit, with graceful stop by default.
- P1: Support per-profile/per-mode overrides via config.
- P1: Support limit boundary behavior: either stop immediately at limit or finish the current segment, then stop.
- P2: Emit structured telemetry and session logs for limit warnings, limit hits, and outcomes.

Non-goals
- Implementing a new UI; initial release uses CLI/log notifications.
- Cloud upload or archival automation.
- Enforcing quotas across multiple hosts/users.

Users & Use Cases (JTBD)
- As a researcher, I want long recordings capped to avoid accidental all-day capture.
- As a podcaster, I want automatic file segmentation every N minutes to ease editing.
- As an engineer on shared workstations, I want policy-compliant max durations.
- As a student, I want to record lectures and make sure it stops after lecture ends.

Requirements
Functional (numbered, testable)
1. P0: Config supports `recording.time_limit` (duration string or seconds; 0 disables). Accepts `90s`, `30m`, `2h`, or integer seconds. Rationale: Human-friendly and scriptable.
2. P0: When active, recorder stops within ≤1s after limit is reached and writes a complete playable file. Rationale: Data integrity.
3. P0: Emit warnings at T-60s and T-10s when applicable; if limit < 120s, emit only T-10s; if limit < 20s, emit only T-5s. Rationale: User preparedness.
4. P0: On limit hit, default behavior is graceful stop with exit code 0 and clear message. Rationale: Predictability.
5. P1: Config supports `recording.limit_boundary` in {"immediate","end_segment"}; default "immediate". Rationale: Predictable cutoff.
6. P1: When `recording.limit_boundary=end_segment`, the recorder stops after the current ffmpeg segment finalizes; no new segments are started at/after the limit. Rationale: Avoid truncation artifacts.
7. P1: Config supports `recording.profile_overrides` to set `time_limit_seconds` and `on_limit` per named profile. Rationale: Per-mode needs.
8. P2: Emit structured events to session logs: `limit_warning`, `limit_hit`, `segment_started`, with timestamps and configuration snapshot. Rationale: Observability.
9. P0: Logs contain actionable remediation if the limit stops a recording. Rationale: UX clarity.
10. P0: Feature must not start if `ffmpeg` is unavailable; error must be clear and actionable. Rationale: Robustness.

Non-functional
- Performance: Timer overhead ≤ 1% CPU; no measurable impact on audio encoding throughput.
- Reliability: No corrupted output files at limit boundaries; segmentation gap ≤ 2s total.
- Security/Compliance: No change to data access controls; respects existing file permissions.
- Compatibility: Backward compatible; default behavior disabled.

UX
- CLI notifications via stdout/stderr with timestamps and levels (INFO/WARN).
- Countdown warnings at T-60 and T-10 seconds where applicable.
- Final message on stop or segment boundary shows file path(s) and next steps.
- Future work (not in scope): GUI/system notifications.

Data
- No schema changes. File naming when segmenting follows current pattern: `{session_id_timestamp}_chunk_%03d.{ext}` (default ext `ogg`), under `~/recordings/{session_id}/`.
- Metrics/events (to logs): `limit_warning`, `limit_hit`, `segment_started` with fields {session_id, profile, configured_limit_s, remaining_s, file_path}.

API Changes
- Config (`echolog.conf`):
  - `recording.time_limit: string|int` (default `0` = disabled). Examples: `0`, `90s`, `30m`, `2h`.
  - `recording.limit_boundary: "immediate" | "end_segment"` (default "immediate")
  - `recording.profile_overrides: map<string, {time_limit_seconds:int, on_limit:string}>` (optional)
- CLI (if applicable):
  - `--time-limit <duration>` overrides config for this run (optional). Examples: `90s`, `30m`, `2h`, `1800`.
  - `--limit-boundary <immediate|end-segment>` overrides behavior
- Exit codes:
  - 0 on normal stop (including limit stop)
  - Non-zero only for errors (e.g., ffmpeg missing, permission denied)

Errors
- Validation error: negative time limit → exit with clear message.
- ffmpeg not available → provide installation instructions.
- Permission denied on device/file → surface guidance for audio group membership.
- PulseAudio not running → guidance to restart or switch device.
- Disk space low/full during segmentation → stop gracefully and notify, preserving prior segments.

Dependencies & Migration
- Depends on `ffmpeg` availability and existing recording pipeline in `echolog.py`.
- Backward-compatible defaults; migration notes limited to new config keys with defaults.

Rollout & Guardrails
- Feature flag: treated as off when `time_limit_seconds=0`.
- Phased: enable in dev → staging → prod.
- Guardrails: refuse to enable segmentation if disk free < configured threshold (future P2).
- Fallback: if segmentation fails, stop and finalize current file with clear message.

Success Metrics & Telemetry Plan
- Leading: % sessions with warnings emitted; % sessions hitting limit unintentionally (user feedback).
- Lagging: Incidents of runaway recordings → target 0; corrupted files at boundary → target 0.
- Capture structured events in session logs; optional integration to external telemetry later.

Risks & Open Questions
- Risk: Segment boundary audio gaps; Mitigation: pre-roll buffer and flush policy.
- Risk: Prompt mode in headless contexts; Mitigation: disable prompt if non-interactive.
- Open: For `end_segment`, confirm we keep existing codec/container settings driven by config/profile.
- Open: What is the desired default global limit, if any? (proposed 0 = disabled)

Press Release (one sentence)
Echolog now offers configurable recording time limits with optional seamless segmentation to protect your storage and keep sessions tidy.


