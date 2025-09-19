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
