# Echolog - Product Requirements Document

## 1. Overview

### 1.1 Purpose
A minimal Python wrapper around ffmpeg designed to record audio and automatically segment the recordings into manageable chunks.

### 1.2 Target Users
- Anyone needing to record system audio with automatic segmentation

## 2. Functional Requirements

### 2.1 Core Features
- **Audio Capture**: Record audio from system audio output using ffmpeg
- **Automatic Segmentation**: Split recordings into configurable time segments (default: 15 minutes)
- **Format Support**: Support FLAC format (high quality, compressed)
- **Simple Interface**: Command-line interface to start and stop recording sessions
- **Device Detection**: Automatically detect available audio sources

### 2.2 Audio Quality
- **Sample Rate**: 44.1 kHz (CD quality)
- **Channels**: Stereo
- **Codec**: FLAC (lossless compression)

### 2.3 File Management
- **Naming Convention**: `{session_id}_{timestamp}_chunk_{chunk_num}.flac`
- **Directory Structure**: Organized in `~/recordings/{session_id}/` folders
- **Metadata**: Include timestamp in filenames

## 3. Technical Requirements

### 3.1 Platform Support
- **Primary**: Linux (Arch Linux)
- **Audio System**: PulseAudio support
- **Python Version**: 3.8+

### 3.2 Dependencies
- **ffmpeg**: For audio capture and segmentation (external dependency)
- **psutil**: For process management
- **configparser**: For configuration management
- **argparse**: For command-line interface (built-in)

### 3.3 Performance
- **Resource Usage**: Minimal Python overhead, ffmpeg handles heavy lifting
- **Reliability**: Graceful handling of interruptions and device changes

## 4. User Interface

### 4.1 Command Line Interface
- Simple commands: `start`, `stop`, `status`, `devices`
- Configuration via config file
- Basic status output

## 5. Configuration Options

### 5.1 Recording Settings
- Segment duration (default: 15 minutes)
- Output directory (default: `~/recordings/`)
- Audio device (auto-detect)

## 6. Success Criteria

### 6.1 Functional Success
- Successfully records system audio
- Creates properly segmented FLAC files
- Handles recording sessions of 2+ hours without issues

### 6.2 User Experience Success
- Easy to set up and use
- Reliable operation without crashes
- Clear feedback on recording status

## 7. Future Enhancements (Out of Scope for MVP)

### 7.1 Potential Features
- Custom output directory selection
- Multiple audio format support
- GUI interface
- Windows/macOS support
- Audio level monitoring

## 8. Constraints and Assumptions

### 8.1 Technical Constraints
- Must work with PulseAudio on Linux
- Requires ffmpeg installation
- Limited to system audio output capture

### 8.2 User Assumptions
- Users have basic command-line knowledge
- Audio output is available through system audio
- Sufficient disk space for recordings

## 9. Risk Assessment

### 9.1 Technical Risks
- **ffmpeg Availability**: ffmpeg must be installed
- **Audio Device Access**: Potential permission issues

### 9.2 Mitigation Strategies
- Provide clear installation instructions
- Add ffmpeg availability checking
- Implement graceful error handling

## 10. Feature PRD: Recording Session Logs

### 10.1 Problem Statement
Users need a reliable way to diagnose issues and audit what happened during a recording session. Today, there is no session-scoped log that captures metadata, lifecycle events, or ffmpeg output, making troubleshooting and support difficult.

### 10.2 Goals and Non‑Goals
- Goals:
  - Create a session-scoped log file per recording session placed in the session directory.
  - Capture key metadata (start/stop time, device, settings), lifecycle events (chunk creation), and errors/warnings.
  - Persist ffmpeg command and relevant output for debugging.
  - Provide configurable log levels and basic log rotation for long sessions.
- Non‑Goals:
  - Centralized log aggregation or remote log shipping.
  - Post‑processing/analytics of logs.

### 10.3 User Stories
- As a user, I want a log file in the session folder so I can inspect what happened during that session without hunting elsewhere.
- As a user, I want to see when each chunk file was created so I can correlate with audio artifacts.
- As a user, I want errors and warnings recorded so I can troubleshoot device or ffmpeg problems after the fact.
- As a power user, I want to adjust verbosity (debug/info/warning/error) to control log detail.

### 10.4 Functional Requirements
- Log file is created in the session directory at session start, e.g. `~/recordings/{session_id}/session.log`.
- Metadata logged at start: session_id, start timestamp (ISO 8601), device info, sample rate, channels, codec/format, segment duration, output directory, CLI/config overrides, generated ffmpeg command.
- Lifecycle events logged:
  - Session start and stop (with timestamps and exit reason/status)
  - Each chunk creation with filename, sequential number, start/end timestamps, file size on close
  - Any device change or recovery attempts
- Error handling:
  - Log all errors and warnings from the application layer
  - Capture and append ffmpeg stderr lines (honoring log level filtering when safe)
- Configurable log level: `debug`, `info`, `warning`, `error` (default: `info`).
- Log rotation for long sessions:
  - Options: size‑based (default) and/or time‑based
  - Default size limit: 5 MB per file, keep last 3 rotations (configurable)
  - Filenames: `session.log`, `session.log.1`, `session.log.2`, ...
- Performance: logging must not significantly impact recording; use buffered, line‑oriented I/O.
- Robustness: ensure logs are flushed on graceful shutdown and on fatal errors.

### 10.5 Technical Design
- Use Python `logging` module with a session‑scoped logger and handlers:
  - `RotatingFileHandler` (size‑based) with configurable `maxBytes` and `backupCount`.
  - Optional `TimedRotatingFileHandler` if time‑based rotation enabled.
  - Structured, readable format: `%(asctime)s %(levelname)s %(name)s: %(message)s` (UTC ISO 8601 preferred).
- ffmpeg integration:
  - Log the exact command invoked.
  - Stream ffmpeg stderr line‑by‑line and write to the session logger at `INFO` or `DEBUG` depending on verbosity.
- Event hooks:
  - Emit log entries from existing segmentation/chunk finalization points.
  - Emit start/stop events from session lifecycle controller.
- Time and IDs:
  - Use monotonic time for durations; use timezone‑aware UTC timestamps for logs.

### 10.6 Configuration
- Config file (`echolog.conf`):
  - `logging.level = info | debug | warning | error` (default: `info`)
  - `logging.rotation = size | time | off` (default: `size`)
  - `logging.max_bytes = 5242880` (default 5 MB)
  - `logging.backup_count = 3`
  - `logging.time_when = midnight` (if time‑based; uses `TimedRotatingFileHandler` semantics)
  - `logging.utc = true` (default true)
- CLI overrides:
  - `--log-level {debug,info,warning,error}`
  - `--log-rotation {size,time,off}`
  - `--log-max-bytes BYTES`
  - `--log-backup-count N`

### 10.7 CLI and UX
- `status` should indicate the log file path for the active session.
- On startup, print a single line indicating where logs are written: e.g., `Logging to ~/recordings/{session_id}/session.log (level=info)`.

### 10.8 File Layout and Examples
- Location: `~/recordings/{session_id}/session.log`
- Example entries:
  - `2025-09-22T10:15:03Z INFO echolog.session: session start id=abc123 device=pulse:alsa_output.pci-0000_00_1f.3.analog-stereo`
  - `2025-09-22T10:15:04Z DEBUG echolog.ffmpeg: cmd=ffmpeg -f pulse -i default -c:a flac -f segment -segment_time 900 ...`
  - `2025-09-22T10:30:03Z INFO echolog.segment: chunk created file=abc123_20250922T101503_chunk_1.flac size=15734289B duration=900.0s`
  - `2025-09-22T12:45:11Z WARN echolog.session: underrun detected; attempting recovery`
  - `2025-09-22T12:50:55Z INFO echolog.session: session stop reason=user_request chunks=10 duration=2h35m52s`

### 10.9 Acceptance Criteria
- [ ] Log file created in recording directory at session start
- [ ] Start/stop, device/settings, and ffmpeg command are logged
- [ ] Chunk creation events are logged with filename and timing
- [ ] Error/warning messages captured, including ffmpeg stderr
- [ ] Configurable log level via config and CLI
- [ ] Log rotation works for long sessions (defaults as specified)

### 10.10 Risks and Mitigations
- Risk: Excessive I/O from verbose logs could interfere with recording
  - Mitigation: Default to `info`, allow `off` for rotation, use buffered writes
- Risk: Parsing ffmpeg output can be noisy
  - Mitigation: Log raw lines at `DEBUG`; summarize important lines at `INFO`
- Risk: Timezone inconsistencies
  - Mitigation: Enforce UTC timestamps in logs
