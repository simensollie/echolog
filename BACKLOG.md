# Echolog - Development Backlog

## Overview
This backlog contains future enhancements and features for the Echolog audio recording tool. Items are prioritized based on user value and implementation complexity.

## Backlog Items

### 🔥 High Priority

#### 1. Recording Time Limit
- **Description**: Add option to set a maximum duration for recording sessions
- **Use Cases**: 
  - Prevent accidentally recording for hours
  - Set automatic stop for time-limited sessions
  - Battery/disk space management
- **Implementation**:
  - Add `--time-limit` CLI argument (e.g., `--time-limit 30m`, `--time-limit 2h`)
  - Add `time_limit` configuration option
  - Implement timer-based automatic stop
  - Show countdown in status output
- **Acceptance Criteria**:
  - [ ] CLI accepts time limit in human-readable format (30m, 2h, 90s)
  - [ ] Recording automatically stops when time limit reached
  - [ ] Status shows remaining time
  - [ ] Graceful shutdown with proper file closure
- **Estimated Effort**: 2-3 hours

### 🟡 Medium Priority

#### 2. Custom Output Directory Selection
- **Description**: Allow users to specify custom output directories per session
- **Use Cases**:
  - Organize recordings by project/client
  - Use different storage locations
  - Temporary recording locations
- **Implementation**:
  - Add `--output-dir` CLI argument
  - Override default `~/recordings/` location
  - Validate directory permissions and space
- **Acceptance Criteria**:
  - [ ] CLI accepts custom output directory
  - [ ] Directory is created if it doesn't exist
  - [ ] Proper error handling for invalid paths
  - [ ] Maintains existing folder structure within custom dir
- **Estimated Effort**: 1-2 hours

#### 3. Audio Level Monitoring
- **Description**: Add real-time audio level monitoring and display
- **Use Cases**:
  - Verify audio is being captured
  - Monitor audio quality
  - Detect silent periods
- **Implementation**:
  - Parse ffmpeg output for audio levels
  - Display visual level indicators
  - Add `--monitor-levels` flag
- **Acceptance Criteria**:
  - [ ] Real-time audio level display
  - [ ] Visual indicators (bars, colors)
  - [ ] Silent period detection
  - [ ] Optional feature (not enabled by default)
- **Estimated Effort**: 3-4 hours

#### 4. Multiple Audio Format Support
- **Description**: Support additional audio formats beyond FLAC
- **Use Cases**:
  - Smaller file sizes (MP3)
  - Uncompressed quality (WAV)
  - Different compression levels
- **Implementation**:
  - Add format selection in config
  - Update ffmpeg command generation
  - Add format validation
- **Acceptance Criteria**:
  - [ ] Support WAV, MP3, FLAC formats
  - [ ] Configurable via config file
  - [ ] Proper codec selection for each format
  - [ ] Maintain quality settings per format
- **Estimated Effort**: 2-3 hours

### 🟢 Low Priority

#### 5. GUI Interface
- **Description**: Create a simple graphical user interface
- **Use Cases**:
  - Users who prefer GUI over CLI
  - Easier session management
  - Visual status display
- **Implementation**:
  - Use tkinter for basic GUI
  - Start/stop buttons
  - Configuration panel
  - Real-time status display
- **Acceptance Criteria**:
  - [ ] Simple, intuitive interface
  - [ ] All CLI functionality available
  - [ ] Real-time status updates
  - [ ] Configuration management
- **Estimated Effort**: 1-2 days

#### 6. Audio Device Selection
- **Description**: Allow manual selection of audio input device
- **Use Cases**:
  - Multiple audio devices available
  - Specific device requirements
  - Troubleshooting audio issues
- **Implementation**:
  - Add `--device` CLI argument
  - Device list display
  - Device validation
- **Acceptance Criteria**:
  - [ ] List available devices
  - [ ] Manual device selection
  - [ ] Device validation
  - [ ] Fallback to auto-detection
- **Estimated Effort**: 1-2 hours

#### 7. Recording Metadata
- **Description**: Add metadata to recorded files
- **Use Cases**:
  - File organization
  - Session information
  - Audio quality details
- **Implementation**:
  - Use mutagen for metadata
  - Add session info, timestamps
  - Audio quality metadata
- **Acceptance Criteria**:
  - [ ] Session metadata in files
  - [ ] Timestamp information
  - [ ] Audio quality details
  - [ ] Configurable metadata fields
- **Estimated Effort**: 2-3 hours

#### 8. Batch Processing
- **Description**: Process multiple recorded segments
- **Use Cases**:
  - Combine segments into single file
  - Convert between formats
  - Apply audio processing
- **Implementation**:
  - Add `batch` command
  - Segment combination
  - Format conversion
- **Acceptance Criteria**:
  - [ ] Combine segments command
  - [ ] Format conversion
  - [ ] Batch processing options
  - [ ] Progress indication
- **Estimated Effort**: 1-2 days

### 🔮 Future Considerations

#### 9. Cloud Storage Integration
- **Description**: Automatic upload to cloud storage
- **Use Cases**:
  - Backup recordings
  - Access from multiple devices
  - Long-term storage
- **Implementation**:
  - Support for major cloud providers
  - Automatic upload after recording
  - Configuration for cloud settings
- **Estimated Effort**: 3-5 days

#### 10. Audio Transcription
- **Description**: Automatic transcription of recorded audio
- **Use Cases**:
  - Meeting notes
  - Lecture transcripts
  - Searchable content
- **Implementation**:
  - Integration with speech-to-text APIs
  - Text file generation
  - Search functionality
- **Estimated Effort**: 5-7 days

#### 11. Cross-Platform Support
- **Description**: Support for Windows and macOS
- **Use Cases**:
  - Broader user base
  - Multi-platform workflows
- **Implementation**:
  - Windows: WASAPI audio
  - macOS: Core Audio
  - Platform-specific audio handling
- **Estimated Effort**: 1-2 weeks

## Backlog Management

### Prioritization Criteria
1. **User Value**: How much does this feature improve user experience?
2. **Implementation Complexity**: How difficult is it to implement?
3. **Dependencies**: Does this feature depend on other features?
4. **Maintenance**: How much ongoing maintenance does this require?

### Status Legend
- 🔥 **High Priority**: Core functionality, high user value
- 🟡 **Medium Priority**: Nice-to-have features, moderate complexity
- 🟢 **Low Priority**: Future enhancements, lower urgency
- 🔮 **Future Considerations**: Long-term vision, significant effort

### Effort Estimation
- **Hours**: 1-4 hours (small features)
- **Days**: 1-2 days (medium features)
- **Weeks**: 1+ weeks (major features)

## Notes
- This backlog is living document and will be updated as features are completed
- Effort estimates are rough guidelines and may vary
- Features may be reprioritized based on user feedback
- Some features may be combined or split based on implementation details
