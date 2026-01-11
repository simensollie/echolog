# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Echolog is a Python wrapper around ffmpeg for recording and segmenting system audio on Linux. It captures audio from PulseAudio monitor sources (system audio output) and saves it as segmented Ogg Opus files.

## Common Commands

```bash
# Install dependencies (creates .venv)
make install

# Start recording a session
make start my_session_name

# Start with time limit (supports 30m, 2h, etc.)
make start my_session_name TIME_LIMIT=30m

# Test mode (1-minute segments)
make start test_session TEST=true

# Stop recording
make stop

# Check status and list files
make status
make files

# List available audio devices
make devices

# Run tests
pytest
# or single test file
pytest test_time_limit.py
```

## Architecture

The application is a single-file Python CLI (`echolog.py`) with one main class:

- **EchologRecorder**: Manages the entire recording lifecycle
  - Spawns ffmpeg as a subprocess with segment muxer for automatic chunking
  - Uses PulseAudio's monitor sources to capture system audio output
  - Background threads handle: stderr logging, chunk file monitoring, and time limit enforcement
  - Session logging writes to `<output_dir>/<session>/session.log` with rotation

**Recording Flow:**
1. `start_recording()` detects audio device, initializes session logger, spawns ffmpeg process
2. ffmpeg runs with `-f segment` to produce `<session>_chunk_NNN.ogg` files
3. Background threads monitor for new chunks and time limits
4. `stop_recording()` sends SIGTERM to the process group, finalizes logging

**Configuration:** `echolog.conf` (INI format) controls segment duration, sample rate, output format, time limits, and logging. CLI args override config values.

## Key Implementation Details

- ffmpeg is spawned with `preexec_fn=os.setsid` to create a process group for clean termination
- Duration strings (30m, 2h) are parsed by `_parse_duration_to_seconds()` static method
- Time limit can stop immediately or wait for segment boundary (`limit_boundary` config)
- Session logs use UTC timestamps and size-based rotation
