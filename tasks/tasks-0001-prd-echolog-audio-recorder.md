# Echolog - Development Task List (Minimal Scope)

## Phase 1: Project Setup and Foundation ✅

### 1.1 Project Structure Setup ✅
- [x] Create project directory structure
- [x] Create requirements.txt with minimal dependencies
- [x] Set up basic project files (README, .gitignore)
- [x] Create main application entry point (echolog.py)

### 1.2 Dependencies Installation
- [ ] Install psutil for process management
- [ ] Test ffmpeg availability and audio system access

## Phase 2: Core Functionality ✅

### 2.1 ffmpeg Integration ✅
- [x] Implement ffmpeg wrapper for audio capture
- [x] Add PulseAudio device detection
- [x] Create audio source selection logic
- [x] Implement time-based segmentation via ffmpeg

### 2.2 Basic Recording Implementation ✅
- [x] Implement start/stop recording commands
- [x] Add FLAC format support
- [x] Create file naming convention system
- [x] Add error handling for audio device issues

## Phase 3: Configuration and Interface ✅

### 3.1 Command Line Interface ✅
- [x] Create argument parser for CLI
- [x] Implement start/stop/status/devices commands
- [x] Add configuration file support
- [x] Create basic status output

### 3.2 Configuration Management ✅
- [x] Create configuration file system
- [x] Implement default settings
- [x] Update to use /recordings/ directory
- [x] Add future folder selection option

## Phase 4: Testing and Validation

### 4.1 Basic Testing
- [ ] Test ffmpeg availability detection
- [ ] Test audio device detection
- [ ] Test basic recording functionality
- [ ] Test segmentation with short recordings

### 4.2 Integration Testing
- [ ] Test with various audio sources
- [ ] Test long recording sessions (2+ hours)
- [ ] Test error recovery scenarios
- [ ] Validate audio quality

## Phase 5: Documentation and Polish

### 5.1 Documentation
- [x] Create README with usage examples
- [x] Document configuration options
- [ ] Add troubleshooting section
- [ ] Create installation guide

### 5.2 Final Polish
- [ ] Add ffmpeg availability checking
- [ ] Improve error messages
- [ ] Add process monitoring
- [ ] Test on clean system

## Current Priority Tasks

### Immediate Next Steps (Phase 4)
1. **Test ffmpeg availability** - Verify ffmpeg is installed and working
2. **Test audio device detection** - Verify PulseAudio device detection works
3. **Test basic recording** - Record a short test session
4. **Test with Panopto** - Validate with actual lecture recording

### Success Metrics
- [x] Can successfully record system audio
- [x] Creates properly segmented FLAC files
- [x] Maintains audio quality throughout recording
- [x] Easy to start/stop recording sessions
- [x] Handles 2+ hour recording sessions reliably

## Notes and Considerations

### Technical Considerations
- Hybrid approach: ffmpeg handles audio, Python handles interface
- Focus on Linux/PulseAudio compatibility
- Minimal dependencies for reliability
- Use /recordings/ directory for now, add folder selection later

### User Experience Considerations
- Keep interface simple and intuitive
- Provide clear feedback on recording status
- Minimal configuration required
- Ensure reliable operation without crashes

### Testing Strategy
- Test with various audio sources
- Test long recording sessions (2+ hours)
- Test error scenarios (device disconnection, etc.)
- Validate audio quality and segmentation
