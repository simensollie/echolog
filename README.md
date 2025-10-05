# Echolog - Audio Recording Application

A Python wrapper around ffmpeg for recording and segmenting audio from system audio output.

## Features

- **Hybrid Approach**: Uses ffmpeg for robust audio capture and Python for user interface
- **Automatic Segmentation**: Records audio in configurable time segments (default: 15 minutes)
- **Recording Time Limit**: Optional total duration cap with human-friendly input (e.g., 30m, 2h)
- **PulseAudio Integration**: Works seamlessly with Linux audio systems
- **Ogg Opus Format**: Speech-optimized, compact files by default
- **Easy Configuration**: Simple configuration file for customization
- **Device Detection**: Automatically finds the best audio source
 - **Session Logs**: Per-session rotating logs with metadata, ffmpeg output, and events

## Requirements

- Python 3.8+
- ffmpeg
- PulseAudio (Linux)
- Audio output device (speakers/headphones)

## Installation

1. Clone or download this repository
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install ffmpeg (if not already installed):
   ```bash
   # On Arch Linux
   sudo pacman -S ffmpeg
   
   # On Ubuntu/Debian
   sudo apt install ffmpeg
   ```

## Quick Start

### Using Makefile (Recommended)

1. **Install and set up:**
   ```bash
   make install
   ```

2. **Check available audio devices:**
   ```bash
   make devices
   ```

3. **Start recording:**
   ```bash
   make start meeting_2025-01-19
   ```

4. **Test mode (1-minute segments):**
   ```bash
   make test
   # or
   make start test_session TEST=true
   ```

5. **Stop recording:**
   ```bash
   make stop
   ```

6. **Check status and files:**
   ```bash
   make status
   make files
   ```

### Using Python directly

1. **Check available audio devices:**
   ```bash
   python echolog.py devices
   ```

2. **Start recording a session:**
   ```bash
   python echolog.py start --session-id "meeting_2025-01-19"
   ```

3. **Start recording with a specific device (override):**
   ```bash
   python echolog.py start -s "my_session" --device "alsa_output.usb-...analog-stereo.monitor"
   ```
   Tip: find devices with `python echolog.py devices`.

4. **Start recording in test mode (1-minute segments):**
   ```bash
   python echolog.py start --session-id "test_session" --test
   ```

5. **Stop recording:**
   ```bash
   python echolog.py stop
   ```

6. **Check recording status:**
   ```bash
   python echolog.py status
   ```

7. **List all recording files:**
   ```bash
   python echolog.py files
   ```

## Configuration

Edit `echolog.conf` to customize settings:

```ini
[recording]
segment_duration = 900    # 15 minutes
sample_rate = 16000      # 16 kHz (speech)
channels = 1             # Mono (speech)
format = ogg             # Ogg container with Opus codec
output_dir = ~/recordings
time_limit = 0           # 0 disables; supports 90s, 30m, 2h
limit_boundary = immediate  # or end_segment

[audio]
auto_detect_device = true

[logging]
# Log level: debug, info, warning, error
level = info
# Rotation strategy: size | time | off (size default)
rotation = size
# Max size (bytes) before rotating
max_bytes = 5242880
# How many rotated files to keep
backup_count = 3
# Use UTC timestamps
utc = true
```

## Usage Examples

### Basic Recording
```bash
# Start recording with a session ID
python echolog.py start -s "session_01"

# Stop recording
python echolog.py stop
```

### Custom Output Directory
```bash
python echolog.py start -s "session_01" -o "/path/to/recordings"
```

### Test Mode (1-minute segments)
```bash
python echolog.py start -s "test_session" -t
```

### Check Status
```bash
python echolog.py status
```

### Time Limit Examples

Limit total recording time via CLI (overrides config):
```bash
python echolog.py start --session-id "lecture_2025-10-05" --time-limit 30m
# or stop after current segment at the limit
python echolog.py start -s "podcast_ep1" --time-limit 2h --limit-boundary end-segment
```

### Logging Controls
```bash
# Increase verbosity to debug
python echolog.py start -s "session_01" --log-level debug

# Adjust rotation size and backups
python echolog.py start -s "session_01" --log-max-bytes 1048576 --log-backup-count 5
```
On start, the application logs: `Logging to <path>/session.log (level=INFO)`. The status command shows the log path.

## File Organization

Recordings are organized as follows:
```
~/recordings/
└── session_01/
    ├── session_01_20250119_143022_chunk_001.ogg
    ├── session_01_20250119_143022_chunk_002.ogg
    └── session_01_20250119_143022_chunk_003.ogg
    └── session.log
```

## Troubleshooting

### No Audio Devices Found
- Make sure PulseAudio is running: `pulseaudio --check`
- Check available sources: `pactl list short sources`
- Restart PulseAudio if needed: `pulseaudio --kill && pulseaudio --start`

### ffmpeg Not Found
- Install ffmpeg using your package manager
- Make sure ffmpeg is in your PATH

### Permission Issues
- Make sure your user is in the `audio` group
- Check PulseAudio permissions

### Last Segment Duration Issue
- When stopping recording mid-segment, the last chunk may show incorrect duration metadata
- This is normal behavior - the file contains all recorded audio
- The duration shown in media players may be longer than actual content
- Use `python echolog.py files` to check actual file sizes

### Logging Volume
- If logs are too noisy, use `--log-level warning` or set `level = warning` in `echolog.conf`.
- ffmpeg lines are logged at DEBUG unless they indicate warnings/errors.

## Makefile Commands

The Makefile provides convenient shortcuts for common tasks:

```bash
# Show all available commands
make help

# Install dependencies
make install

# Run test recording (1-minute segments)
make test

# Start recording with session name
make start my_meeting

# Start test mode recording
make start test_session TEST=true

# Stop current recording
make stop

# Show status and files
make status
make files

# List audio devices
make devices

# Clean up temporary files
make clean

# Show system info
make info
```

## Development

### Running Tests
```bash
make test
# or
pytest
```

### Code Structure
- `echolog.py` - Main application and EchologRecorder class
- `echolog.conf` - Configuration file
- `requirements.txt` - Python dependencies
- `Makefile` - Convenient build and run commands

## License

MIT License - see LICENSE file for details.
