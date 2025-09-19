# Echolog - Audio Recording Application

A Python wrapper around ffmpeg for recording and segmenting audio from system audio output.

## Features

- **Hybrid Approach**: Uses ffmpeg for robust audio capture and Python for user interface
- **Automatic Segmentation**: Records audio in configurable time segments (default: 15 minutes)
- **PulseAudio Integration**: Works seamlessly with Linux audio systems
- **FLAC Format**: High-quality lossless compression
- **Easy Configuration**: Simple configuration file for customization
- **Device Detection**: Automatically finds the best audio source

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

1. **Check available audio devices:**
   ```bash
   python echolog.py devices
   ```

2. **Start recording a session:**
   ```bash
   python echolog.py start --session-id "meeting_2025-01-19"
   ```

3. **Start recording in test mode (1-minute segments):**
   ```bash
   python echolog.py start --session-id "test_session" --test
   ```

4. **Stop recording:**
   ```bash
   python echolog.py stop
   ```

5. **Check recording status:**
   ```bash
   python echolog.py status
   ```

6. **List all recording files:**
   ```bash
   python echolog.py files
   ```

## Configuration

Edit `echolog.conf` to customize settings:

```ini
[recording]
segment_duration = 900    # 15 minutes
sample_rate = 44100      # 44.1 kHz
channels = 2             # Stereo
format = flac            # Output format
output_dir = ~/recordings

[audio]
auto_detect_device = true
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

## File Organization

Recordings are organized as follows:
```
~/recordings/
└── session_01/
    ├── session_01_20250119_143022_chunk_001.flac
    ├── session_01_20250119_143022_chunk_002.flac
    └── session_01_20250119_143022_chunk_003.flac
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

## Development

### Running Tests
```bash
pytest
```

### Code Structure
- `echolog.py` - Main application and EchologRecorder class
- `echolog.conf` - Configuration file
- `requirements.txt` - Python dependencies

## License

MIT License - see LICENSE file for details.
