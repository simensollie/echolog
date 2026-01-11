# PRD: Terminal User Interface (TUI)

## 1. Problem Statement

Users currently interact with echolog exclusively through CLI commands (`start`, `stop`, `status`, `devices`, `files`). While functional, this requires memorizing commands and lacks real-time feedback during recording sessions. Users cannot easily monitor recording progress, view live audio levels, or manage sessions without running multiple commands.

## 2. Goals and Non-Goals

### Goals
- Provide a rich, interactive terminal interface for managing recording sessions
- Display real-time recording status, elapsed time, and chunk progress
- Show live audio level visualization (VU meter)
- Enable quick device selection and configuration
- Display session logs and chunk history in real-time
- Support keyboard shortcuts for common actions

### Non-Goals
- GUI/graphical desktop application
- Web-based interface
- Remote/networked control
- Audio waveform visualization
- Editing or playback of recordings

## 3. User Stories

- As a user, I want to see a dashboard with recording status so I can monitor progress without running commands
- As a user, I want to see elapsed time and chunk count in real-time so I know how much I've recorded
- As a user, I want to see audio levels so I can verify audio is being captured
- As a user, I want to select an audio device from a list so I don't have to look up device names
- As a user, I want to start/stop recording with a keypress so I can quickly control sessions
- As a user, I want to see recent log entries so I can spot issues immediately
- As a user, I want to see disk space remaining so I don't run out mid-session

## 4. Functional Requirements

### 4.1 Main Dashboard View
- **Status Panel**: Current state (Idle/Recording/Paused), session ID
- **Timer Display**: Elapsed recording time (HH:MM:SS)
- **Progress Bar**: Visual segment progress (time until next chunk)
- **Chunk Counter**: Current chunk number and list of created chunks
- **Audio Level Meter**: Real-time VU meter showing input levels
- **Disk Space**: Available space in output directory
- **Time Limit Indicator**: If configured, show remaining time

### 4.2 Device Selection View
- List all available audio sources
- Highlight currently selected device
- Allow navigation and selection via keyboard
- Show device details (name, type)

### 4.3 Configuration View
- Display current settings (segment duration, format, sample rate, etc.)
- Allow editing common settings
- Show config file path
- Save changes to config

### 4.4 Log View
- Display recent session log entries
- Auto-scroll with new entries
- Filter by log level (debug/info/warning/error)
- Highlight errors and warnings

### 4.5 Files/History View
- List recording sessions with dates
- Show chunks per session with sizes
- Display total size per session

### 4.6 Keyboard Shortcuts
| Key | Action |
|-----|--------|
| `r` | Start recording |
| `s` | Stop recording |
| `d` | Open device selection |
| `c` | Open configuration |
| `l` | Open log view |
| `f` | Open files view |
| `q` | Quit application |
| `?` | Show help |
| `Tab` | Switch between panels |
| `Esc` | Return to dashboard |

## 5. Technical Requirements

### 5.1 Framework
- **Library**: [Textual](https://textual.textualize.io/) - Modern Python TUI framework
- **Rationale**: Rich widget library, async support, CSS-like styling, active development

### 5.2 Architecture
- Separate TUI layer from core `EchologRecorder` class
- Event-driven updates from recorder to TUI
- Non-blocking UI with async I/O
- Graceful handling of terminal resize

### 5.3 Audio Level Monitoring
- Parse ffmpeg stderr for audio level data (`-af showinfo` or similar)
- Alternatively, use `pavucontrol`-style PulseAudio level queries
- Update meter at ~10 Hz for smooth visualization

### 5.4 Performance
- TUI must not impact recording performance
- Use efficient terminal updates (differential rendering)
- Limit log buffer size to prevent memory growth

### 5.5 Dependencies
- `textual>=0.50.0` - TUI framework
- `rich>=13.0.0` - Terminal formatting (Textual dependency)

## 6. UI Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  ECHOLOG                                          [?] Help      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Status: ● RECORDING          Session: meeting_20260111       │
│                                                                 │
│   ┌─ Time ─────────┐  ┌─ Segment ──────────────────────────┐   │
│   │   01:23:45     │  │ Chunk 6/∞   [████████░░░░] 3:42    │   │
│   └────────────────┘  └────────────────────────────────────┘   │
│                                                                 │
│   ┌─ Audio Level ──────────────────────────────────────────┐   │
│   │ L [████████████████░░░░░░░░] -12 dB                    │   │
│   │ R [███████████████░░░░░░░░░] -14 dB                    │   │
│   └────────────────────────────────────────────────────────┘   │
│                                                                 │
│   ┌─ Chunks ───────────────────┐  ┌─ Info ─────────────────┐   │
│   │ ✓ chunk_001.ogg  15.2 MB   │  │ Device: pulse:monitor  │   │
│   │ ✓ chunk_002.ogg  15.1 MB   │  │ Format: OGG/Opus       │   │
│   │ ✓ chunk_003.ogg  15.3 MB   │  │ Rate: 16000 Hz         │   │
│   │ ✓ chunk_004.ogg  15.0 MB   │  │ Segment: 5 min         │   │
│   │ ✓ chunk_005.ogg  15.2 MB   │  │ Disk: 45.2 GB free     │   │
│   │ ◐ chunk_006.ogg  (rec...)  │  │ Limit: 2h (36m left)   │   │
│   └────────────────────────────┘  └────────────────────────┘   │
│                                                                 │
│   ┌─ Log ──────────────────────────────────────────────────┐   │
│   │ 10:15:03 INFO  session start id=meeting_20260111       │   │
│   │ 10:20:03 INFO  chunk created chunk_001.ogg             │   │
│   │ 10:25:04 INFO  chunk created chunk_002.ogg             │   │
│   └────────────────────────────────────────────────────────┘   │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ [R]ecord  [S]top  [D]evices  [C]onfig  [L]ogs  [F]iles  [Q]uit │
└─────────────────────────────────────────────────────────────────┘
```

## 7. Configuration

### 7.1 Config File (`echolog.conf`)
```ini
[tui]
theme = dark          # dark | light
refresh_rate = 10     # UI updates per second
show_audio_meter = true
log_lines = 5         # visible log lines in dashboard
```

### 7.2 CLI
```bash
echolog tui                    # Launch TUI
echolog tui --theme light      # Override theme
echolog tui --no-meter         # Disable audio meter
```

## 8. Implementation Phases

### Phase 1: Core Dashboard (MVP)
- Basic layout with status, timer, chunk list
- Start/stop recording via keyboard
- Session log display
- Device info display

### Phase 2: Device Selection
- Interactive device picker
- Device refresh capability
- Remember last used device

### Phase 3: Audio Meter
- Real-time level visualization
- Peak hold indicator
- Configurable meter style

### Phase 4: Configuration Editor
- In-TUI settings editing
- Config validation
- Live preview of changes

### Phase 5: Polish
- Theming support
- Responsive layout
- Mouse support
- Help system

## 9. Acceptance Criteria

- [ ] TUI launches with `echolog tui` command
- [ ] Dashboard displays recording status in real-time
- [ ] Timer updates every second during recording
- [ ] Chunk list updates as new chunks are created
- [ ] Start/stop works via keyboard shortcuts
- [ ] Device selection allows choosing audio source
- [ ] Log entries appear in real-time
- [ ] Application exits cleanly and stops any active recording
- [ ] Works in common terminal emulators (Alacritty, Kitty, Ghostty, GNOME Terminal)
- [ ] Graceful degradation on small terminals

## 10. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Audio level monitoring impacts performance | Recording quality | Use separate thread, rate-limit updates |
| Terminal compatibility issues | Broken UI | Test on major terminals, provide fallback mode |
| Textual library breaking changes | Maintenance burden | Pin version, follow semver |
| Complex async state management | Bugs | Clear separation between recorder and TUI layers |

## 11. Future Enhancements (Out of Scope)

- Mouse-based interactions
- Multiple simultaneous recordings
- Recording scheduling
- Hotkey daemon (global shortcuts)
- Audio waveform preview
- Session notes/annotations
