# PRD: Terminal User Interface (TUI)

## Introduction

Add an interactive terminal user interface for echolog that provides real-time feedback during recording sessions. Users can monitor recording progress, view audio levels, manage sessions, and control recordings with keyboard shortcuts—all without memorizing CLI commands.

## Goals

- Provide a rich, interactive terminal interface for managing recording sessions
- Display real-time recording status, elapsed time, and chunk progress
- Show live audio level visualization (VU meter)
- Enable quick device selection and configuration
- Display session logs and chunk history in real-time
- Support keyboard shortcuts for common actions

## User Stories

### US-001: Launch TUI application ✅
**Description:** As a user, I want to launch the TUI with a simple command so I can access all features from one interface.

**Acceptance Criteria:**
- [x] `echolog tui` command launches the TUI application
- [x] TUI displays main dashboard on startup
- [x] Application exits cleanly with `q` key
- [x] Typecheck passes

### US-002: Display recording status ✅
**Description:** As a user, I want to see the current recording status so I know whether a session is active.

**Acceptance Criteria:**
- [x] Status panel shows "Idle" when not recording
- [x] Status panel shows "Recording" with indicator when active
- [x] Session ID displayed when recording
- [x] Status updates immediately when state changes
- [x] Typecheck passes

### US-003: Display elapsed time ✅
**Description:** As a user, I want to see elapsed recording time so I know how long I've been recording.

**Acceptance Criteria:**
- [x] Timer displays HH:MM:SS format
- [x] Timer updates every second during recording
- [x] Timer shows 00:00:00 when idle
- [x] Typecheck passes

### US-004: Display segment progress ✅
**Description:** As a user, I want to see progress toward the next chunk so I know when segments are created.

**Acceptance Criteria:**
- [x] Progress bar shows time elapsed in current segment
- [x] Displays current chunk number
- [x] Shows time remaining until next chunk
- [x] Progress resets when new chunk starts
- [x] Typecheck passes

### US-005: Display chunk list ✅
**Description:** As a user, I want to see a list of created chunks so I can track recording output.

**Acceptance Criteria:**
- [x] List shows all chunks created in current session
- [x] Each chunk shows filename and size
- [x] Completed chunks marked with checkmark
- [x] Current/in-progress chunk indicated
- [x] List scrolls if more chunks than visible space
- [x] Typecheck passes

### US-006: Start recording via keyboard ✅
**Description:** As a user, I want to start recording with a keypress so I can quickly begin sessions.

**Acceptance Criteria:**
- [x] Pressing `r` opens session name prompt
- [x] After entering name, recording starts
- [x] Status updates to "Recording"
- [x] Error shown if recording fails to start
- [x] Typecheck passes

### US-007: Stop recording via keyboard ✅
**Description:** As a user, I want to stop recording with a keypress so I can end sessions quickly.

**Acceptance Criteria:**
- [x] Pressing `s` stops active recording
- [x] Confirmation message shown
- [x] Status updates to "Idle"
- [x] Final chunk is properly finalized
- [x] Typecheck passes

### US-008: Display device info ✅
**Description:** As a user, I want to see the current audio device so I know what's being recorded.

**Acceptance Criteria:**
- [x] Info panel shows current device name
- [x] Shows format (OGG/Opus, FLAC, etc.)
- [x] Shows sample rate
- [x] Shows segment duration setting
- [x] Typecheck passes

### US-009: Display disk space ✅
**Description:** As a user, I want to see available disk space so I don't run out mid-session.

**Acceptance Criteria:**
- [x] Info panel shows free space in output directory
- [x] Updates periodically during recording
- [x] Warning color when space is low (<1GB)
- [x] Typecheck passes

### US-010: Display session log
**Description:** As a user, I want to see recent log entries so I can spot issues immediately.

**Acceptance Criteria:**
- [ ] Log panel shows last 5 log entries (configurable)
- [ ] New entries appear in real-time
- [ ] Errors highlighted in red
- [ ] Warnings highlighted in yellow
- [ ] Typecheck passes

### US-011: Device selection view
**Description:** As a user, I want to select an audio device from a list so I don't have to look up device names.

**Acceptance Criteria:**
- [ ] Pressing `d` opens device selection view
- [ ] Lists all available audio sources
- [ ] Current device highlighted
- [ ] Arrow keys navigate, Enter selects
- [ ] Esc returns to dashboard
- [ ] Selected device used for next recording
- [ ] Typecheck passes

### US-012: Display time limit indicator
**Description:** As a user, I want to see remaining time when a limit is set so I know when recording will stop.

**Acceptance Criteria:**
- [ ] If time limit configured, show remaining time
- [ ] Indicator hidden when no limit set
- [ ] Warning color when <5 minutes remaining
- [ ] Typecheck passes

### US-013: Audio level meter
**Description:** As a user, I want to see audio levels so I can verify audio is being captured.

**Acceptance Criteria:**
- [ ] VU meter shows current audio level
- [ ] Updates at ~10 Hz for smooth visualization
- [ ] Shows level in dB
- [ ] Meter disabled when not recording
- [ ] Configurable via `--no-meter` flag
- [ ] Typecheck passes

### US-014: Help overlay
**Description:** As a user, I want to see available keyboard shortcuts so I can learn the interface.

**Acceptance Criteria:**
- [ ] Pressing `?` shows help overlay
- [ ] Lists all keyboard shortcuts
- [ ] Any key dismisses overlay
- [ ] Typecheck passes

## Functional Requirements

- FR-1: Add `tui` action to CLI that launches the TUI application
- FR-2: Display main dashboard with status, timer, progress, chunks, info, and log panels
- FR-3: Update timer display every second during active recording
- FR-4: Update chunk list when new chunks are created
- FR-5: Bind `r` key to start recording (prompt for session name)
- FR-6: Bind `s` key to stop recording
- FR-7: Bind `d` key to open device selection view
- FR-8: Bind `q` key to quit application (stop recording first if active)
- FR-9: Bind `?` key to show help overlay
- FR-10: Display available disk space in output directory
- FR-11: Stream session log entries to log panel in real-time
- FR-12: Show time limit remaining when configured
- FR-13: Display audio level meter during recording (optional, can disable)
- FR-14: Handle terminal resize gracefully

## Non-Goals

- GUI/graphical desktop application
- Web-based interface
- Remote/networked control
- Audio waveform visualization
- Editing or playback of recordings
- Mouse-based interactions (Phase 5 future enhancement)
- Multiple simultaneous recordings
- Recording scheduling

## Design Considerations

- Use box-drawing characters for panel borders
- Status indicator: green dot for recording, gray for idle
- Color scheme: support dark terminal backgrounds
- Layout should work in 80x24 minimum terminal size
- Graceful degradation: hide optional panels on small terminals

**Reference Layout:**
```
┌─────────────────────────────────────────────────────────────────┐
│  ECHOLOG                                          [?] Help      │
├─────────────────────────────────────────────────────────────────┤
│   Status: ● RECORDING          Session: meeting_20260111       │
│   ┌─ Time ─────────┐  ┌─ Segment ──────────────────────────┐   │
│   │   01:23:45     │  │ Chunk 6/∞   [████████░░░░] 3:42    │   │
│   └────────────────┘  └────────────────────────────────────┘   │
│   ┌─ Audio Level ──────────────────────────────────────────┐   │
│   │ L [████████████████░░░░░░░░] -12 dB                    │   │
│   └────────────────────────────────────────────────────────┘   │
│   ┌─ Chunks ───────────────────┐  ┌─ Info ─────────────────┐   │
│   │ ✓ chunk_001.ogg  15.2 MB   │  │ Device: pulse:monitor  │   │
│   │ ✓ chunk_002.ogg  15.1 MB   │  │ Format: OGG/Opus       │   │
│   │ ◐ chunk_003.ogg  (rec...)  │  │ Disk: 45.2 GB free     │   │
│   └────────────────────────────┘  └────────────────────────┘   │
│   ┌─ Log ──────────────────────────────────────────────────┐   │
│   │ 10:15:03 INFO  session start id=meeting_20260111       │   │
│   │ 10:20:03 INFO  chunk created chunk_001.ogg             │   │
│   └────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│ [R]ecord  [S]top  [D]evices  [C]onfig  [L]ogs  [F]iles  [Q]uit │
└─────────────────────────────────────────────────────────────────┘
```

## Technical Considerations

- **Framework:** Textual (https://textual.textualize.io/) - Modern Python TUI framework with async support
- **Dependencies:** `textual>=0.50.0`, `rich>=13.0.0`
- **Architecture:** Separate TUI layer from core `EchologRecorder` class
- **Event-driven:** Use callbacks/events from recorder to update TUI
- **Audio levels:** Parse ffmpeg stderr for level data or query PulseAudio
- **Performance:** TUI must not impact recording; use efficient differential rendering
- **Log buffer:** Limit to prevent memory growth during long sessions

## Success Metrics

- TUI launches in under 1 second
- Timer and status updates visible within 100ms of state change
- Audio meter updates smoothly (~10 Hz) without impacting recording
- Works in Alacritty, Kitty, Ghostty, GNOME Terminal
- No increase in CPU usage during recording compared to CLI mode

## Open Questions

- Should we persist last-used device between sessions? yes
- Should configuration editing be in-TUI or just display current config? edit in tui
- What audio level parsing method works best (ffmpeg stderr vs PulseAudio)?
- Should we add mouse support in Phase 5? not yet

---

## Bugs and Missing Functionality (Discovered During Implementation/Review)

### Bugs (Current Behavior vs Expected)

- **BUG-001: Most keyboard commands appear “non-functional”**
  - **Observed:** Only `?` (help), `q` (quit), and the Textual command palette work reliably; `r` (record), `s` (stop), `d` (devices) may not trigger.
  - **Likely cause:** Key binding mismatch when users press **uppercase** shortcuts shown in UI labels (e.g., `Shift+R`) vs bindings only defined for lowercase (`r`), plus focus/event routing differences.
  - **Impact:** Blocks validation of recording flow (status, timer, chunk list, device selector).
  - **Fix target:** Bind both lowercase and uppercase keys for main actions; ensure actions are reachable via command palette and keypress.

- **BUG-002: Session names with underscores break chunk discovery/finalization**
  - **Observed (code-level):** Several recorder methods derive the session folder/pattern using `self.session_id.split('_')[0]`, which truncates session names that contain `_`.
  - **Impact:** Chunk list may stay empty or incomplete; stop summary may compute wrong directory; “no chunks yet” even when files exist.
  - **Fix target:** Store a dedicated `session_name` (base) and `session_id` (unique) and use `self._session_dir` + `self.session_id` for globbing instead of string splitting.

### Missing / Not Yet Verified Functionality

- **GAP-001: Log panel user story not complete**
  - **US-010** remains unchecked; log streaming/highlighting needs verification and may still be incomplete.

- **GAP-002: Device selector not tested end-to-end**
  - **Observed:** Device modal exists, but selection flow hasn’t been validated due to command issues and dependency on `pactl` output.
  - **Fix target:** Add unit tests around “press devices key → modal opens → selection updates config”.

- **GAP-003: Recording start/stop not testable (blocked by command issue)**
  - **Observed:** Without working `r/s`, status/timer/progress and chunk list behavior can’t be validated.
  - **Fix target:** Restore command handling, then validate status + timer updates via unit tests and a manual smoke test.

- **GAP-004: Default recording name + edit-while-recording**
  - **Requested:** Start recording with a sensible **default session name**, and allow editing the “name” while recording.
  - **Constraints:** Renaming on-disk folders/files mid-recording is risky; safest approach is treating this as a **display/session label** that does not change file paths.

### Design Discrepancies (See Attached Images)

- **UI-001: Color/border styling differs from reference**
  - **Observed:** Panels use bright green borders; reference layout uses subdued/neutral borders suitable for dark terminals.
  - **Fix target:** Align border color and emphasis with Textual theme variables (e.g., `$primary`, `$surface`) and match the reference’s visual hierarchy.

- **UI-002: Status line/session naming differs from reference**
  - **Observed:** Status line may show a full internal `session_id` (including timestamp) instead of the clean “Session: meeting_20260111” shown in the mock.
  - **Fix target:** Show a stable `session_name`/label in the UI; keep unique ID internal.
