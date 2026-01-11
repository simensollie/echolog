#!/usr/bin/env python3
"""
Echolog - Audio Recording Application
A Python wrapper around ffmpeg for recording and segmenting audio from browser sessions.
"""

import os
import sys
import subprocess
import argparse
import configparser
import time
import signal
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import threading
import re


class EchologRecorder:
    """Main recorder class that wraps ffmpeg for audio capture and segmentation."""
    
    def __init__(self, config_file: str = "echolog.conf"):
        self.config_file = config_file
        self.config = self._load_config()
        self.ffmpeg_process = None
        self.recording = False
        self.session_id = None
        self.session_logger: Optional[logging.Logger] = None
        self._stderr_thread: Optional[threading.Thread] = None
        self._chunk_thread: Optional[threading.Thread] = None
        self._known_chunks: set[str] = set()
        self._finalized_chunks: set[str] = set()
        self._recording_start_monotonic: Optional[float] = None
        self._session_dir: Optional[Path] = None
        self._time_limit_seconds: int = 0
        self._limit_boundary: str = "immediate"
        self._limit_thread: Optional[threading.Thread] = None
        self._segment_duration_seconds: int = 0
        
    def _load_config(self) -> configparser.ConfigParser:
        """Load configuration from file or create default."""
        config = configparser.ConfigParser()
        
        # Default configuration
        default_config = {
            'recording': {
                'segment_duration': '300',  # 5 minutes in seconds
                'sample_rate': '16000',
                'channels': '1',  # mono for speech
                'format': 'ogg',  # ogg container with Opus codec
                'output_dir': '~/recordings',
                'time_limit': '0',  # 0 disables
                'limit_boundary': 'immediate'  # immediate | end_segment
            },
            'audio': {
                'auto_detect_device': 'true',
                'device_name': '',
                'buffer_size': '1024'
            }
        }
        
        # Load existing config or create with defaults
        if os.path.exists(self.config_file):
            config.read(self.config_file)
        else:
            config.read_dict(default_config)
            self._save_config(config)
            
        return config
    @staticmethod
    def _parse_duration_to_seconds(value: Any) -> int:
        """Parse a human-friendly duration into seconds.

        Supports integers (seconds) or strings with suffixes: s, m, h (case-insensitive).
        Returns 0 for empty/"0". Raises ValueError for negative or invalid values.
        """
        if value is None:
            return 0
        if isinstance(value, int):
            if value < 0:
                raise ValueError("time limit cannot be negative")
            return value
        s = str(value).strip()
        if s == "":
            return 0
        if s.isdigit() or (s.startswith("-") and s[1:].isdigit()):
            iv = int(s)
            if iv < 0:
                raise ValueError("time limit cannot be negative")
            return iv
        s_lower = s.lower()
        try:
            if s_lower.endswith('s'):
                base = int(s_lower[:-1])
                if base < 0:
                    raise ValueError
                return base
            if s_lower.endswith('m'):
                base = int(s_lower[:-1])
                if base < 0:
                    raise ValueError
                return base * 60
            if s_lower.endswith('h'):
                base = int(s_lower[:-1])
                if base < 0:
                    raise ValueError
                return base * 3600
        except ValueError:
            raise ValueError(f"invalid time limit value: {value}")
        raise ValueError(f"invalid time limit value: {value}")

    def _start_limit_timer_if_needed(self) -> None:
        """Start background timer for warnings and auto-stop if a time limit is set."""
        if self._time_limit_seconds <= 0 or not self._recording_start_monotonic:
            return

        def _runner() -> None:
            assert self._recording_start_monotonic is not None
            start = self._recording_start_monotonic
            limit_at = start + self._time_limit_seconds
            # Compute warnings
            warnings: List[int] = []
            if self._time_limit_seconds >= 120:
                warnings = [60, 10]
            elif self._time_limit_seconds >= 20:
                warnings = [10]
            else:
                warnings = [5]

            warned: set[int] = set()
            pending_announced: bool = False
            while self.recording:
                now = time.monotonic()
                remaining = int(max(0, limit_at - now))
                # issue warnings if remaining matches schedule and not warned yet
                for w in warnings:
                    if remaining == w and w not in warned:
                        msg = f"WARNING: Recording will stop in {w} seconds (time limit)."
                        print(msg)
                        if self.session_logger:
                            self.session_logger.warning(f"limit_warning session_id={self.session_id} configured_limit_s={self._time_limit_seconds} remaining_s={w}")
                        warned.add(w)
                if now >= limit_at:
                    # If end_segment boundary requested, wait until the next segment boundary
                    if self._limit_boundary == 'end-segment' and self._segment_duration_seconds > 0:
                        elapsed = now - start
                        rem_to_boundary = self._segment_duration_seconds - (elapsed % self._segment_duration_seconds)
                        if not pending_announced:
                            print(f"Time limit reached; waiting ~{int(rem_to_boundary)}s to finish current segment...")
                            if self.session_logger:
                                self.session_logger.info(f"limit_hit session_id={self.session_id} configured_limit_s={self._time_limit_seconds} pending=end_segment remaining_to_boundary_s={int(rem_to_boundary)}")
                            pending_announced = True
                        # Stop when within a small window of the boundary
                        if rem_to_boundary <= 0.3 or (self._segment_duration_seconds - rem_to_boundary) <= 0.3:
                            print("Segment boundary reached. Stopping...")
                            if self.session_logger:
                                self.session_logger.info(f"limit_hit session_id={self.session_id} configured_limit_s={self._time_limit_seconds} reason=time_limit boundary=end_segment")
                            try:
                                self.stop_recording(reason="time_limit")
                            finally:
                                return
                    else:
                        print("Recording time limit reached. Stopping...")
                        if self.session_logger:
                            self.session_logger.info(f"limit_hit session_id={self.session_id} configured_limit_s={self._time_limit_seconds} reason=time_limit boundary=immediate")
                        try:
                            self.stop_recording(reason="time_limit")
                        finally:
                            return
                time.sleep(0.2)

        try:
            self._limit_thread = threading.Thread(target=_runner, daemon=True)
            self._limit_thread.start()
        except Exception as e:
            if self.session_logger:
                self.session_logger.warning(f"limit timer start failed err={e}")
    
    def _save_config(self, config: configparser.ConfigParser):
        """Save configuration to file."""
        with open(self.config_file, 'w') as f:
            config.write(f)
    
    def _init_session_logger(self, session_dir: Path, level: int = logging.INFO,
                              max_bytes: int = 5 * 1024 * 1024, backup_count: int = 3) -> None:
        """Initialize a rotating file logger for the current recording session.

        Creates `session.log` under the provided `session_dir` with size-based rotation.
        Uses UTC timestamps and a human-readable line format.
        """
        # Ensure directory exists
        session_dir.mkdir(parents=True, exist_ok=True)

        log_path = session_dir / "session.log"

        logger_name = f"echolog.session.{self.session_id or 'unknown'}"
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        logger.propagate = False

        # Avoid duplicate handlers on repeated init
        if logger.handlers:
            self.session_logger = logger
            return

        handler = RotatingFileHandler(str(log_path), maxBytes=max_bytes, backupCount=backup_count)

        class UtcFormatter(logging.Formatter):
            converter = time.gmtime

        formatter = UtcFormatter("%(asctime)s %(levelname)s %(name)s: %(message)s", "%Y-%m-%dT%H:%M:%SZ")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        self.session_logger = logger

    def _get_logging_config(self):
        """Resolve logging configuration from config with defaults."""
        level_str = (self.config.get('logging', 'level', fallback='info') or 'info').lower()
        level_map = {
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'warning': logging.WARNING,
            'error': logging.ERROR,
        }
        level = level_map.get(level_str, logging.INFO)
        rotation = (self.config.get('logging', 'rotation', fallback='size') or 'size').lower()
        max_bytes = self.config.getint('logging', 'max_bytes', fallback=5 * 1024 * 1024)
        backup_count = self.config.getint('logging', 'backup_count', fallback=3)
        utc = self.config.getboolean('logging', 'utc', fallback=True)
        return {
            'level': level,
            'rotation': rotation,
            'max_bytes': max_bytes,
            'backup_count': backup_count,
            'utc': utc,
        }

    def _flush_session_logger(self):
        """Flush and close session logger handlers safely."""
        if not self.session_logger:
            return
        for handler in list(self.session_logger.handlers):
            try:
                handler.flush()
                handler.close()
            except Exception:
                pass

    def detect_audio_devices(self) -> List[Dict[str, str]]:
        """Detect available PulseAudio monitor sources."""
        try:
            # Get list of PulseAudio sources
            result = subprocess.run(
                ['pactl', 'list', 'short', 'sources'],
                capture_output=True, text=True, check=True
            )
            
            devices = []
            for line in result.stdout.strip().split('\n'):
                if 'monitor' in line:
                    parts = line.split('\t')
                    if len(parts) >= 5:  # Ensure we have status information
                        devices.append({
                            'name': parts[1],
                            'id': parts[0],
                            'status': parts[4]  # RUNNING, SUSPENDED, etc.
                        })
            
            return devices
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Error: Could not detect audio devices. Make sure PulseAudio is running.")
            return []
    
    def _get_default_sink_monitor(self) -> Optional[str]:
        """Return the default sink's monitor source name if available.

        Strategy: parse `pactl info` for Default Sink, then look for a source
        named `<default_sink>.monitor` in the list of sources.
        """
        try:
            info = subprocess.run(['pactl', 'info'], capture_output=True, text=True, check=True)
            default_sink = None
            for line in info.stdout.splitlines():
                if line.strip().lower().startswith('default sink:'):
                    default_sink = line.split(':', 1)[1].strip()
                    break
            if not default_sink:
                return None

            monitor_candidate = f"{default_sink}.monitor"
            for dev in self.detect_audio_devices():
                if dev.get('name') == monitor_candidate:
                    return monitor_candidate
            return None
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    def get_default_monitor_device(self) -> Optional[str]:
        """Get the default monitor device for recording."""
        # If user specified a device in config, honor it
        configured = (self.config.get('audio', 'device_name', fallback='') or '').strip()
        if configured:
            print(f"Using configured device: {configured}")
            return configured

        # Prefer the default sink's monitor
        sink_monitor = self._get_default_sink_monitor()
        if sink_monitor:
            print(f"Selected default sink monitor: {sink_monitor}")
            return sink_monitor

        devices = self.detect_audio_devices()
        if not devices:
            return None
        
        monitors = [d for d in devices if 'monitor' in d['name'].lower()]
        # Prefer RUNNING monitors, then IDLE, then any monitor
        for state in ('RUNNING', 'IDLE'):
            for device in monitors:
                if device.get('status') == state:
                    print(f"Selected {state} monitor: {device['name']}")
                    return device['name']
        
        # If no running device found, look for any monitor device
        for device in monitors:
            print(f"Selected SUSPENDED monitor: {device['name']} (status: {device.get('status', 'UNKNOWN')})")
            return device['name']
        
        # Return first available device as fallback
        if devices:
            print(f"Fallback to first device: {devices[0]['name']}")
            return devices[0]['name']
        
        return None
    
    def start_recording(self, session_id: str, output_dir: Optional[str] = None, test_mode: bool = False, custom_duration: Optional[int] = None) -> bool:
        """Start recording audio with ffmpeg."""
        if self.recording:
            print("Error: Already recording!")
            return False
        
        # Generate session ID
        self.session_id = f"{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Set up output directory
        if output_dir is None:
            output_dir = os.path.expanduser(self.config.get('recording', 'output_dir'))
        
        output_path = Path(output_dir) / session_id
        output_path.mkdir(parents=True, exist_ok=True)
        self._session_dir = output_path

        # Initialize session logger with configured settings
        log_cfg = self._get_logging_config()
        self._init_session_logger(
            output_path,
            level=log_cfg['level'],
            max_bytes=log_cfg['max_bytes'],
            backup_count=log_cfg['backup_count']
        )
        if self.session_logger:
            human_level = logging.getLevelName(log_cfg['level'])
            self.session_logger.info(f"Logging to {output_path / 'session.log'} (level={human_level})")
        
        # Get audio device
        device = self.get_default_monitor_device()
        if not device:
            print("Error: No audio device found!")
            return False
        
        print(f"Using audio device: {device}")
        print(f"Output directory: {output_path}")
        
        # Resolve time limit configuration
        try:
            time_limit_raw = self.config.get('recording', 'time_limit', fallback='0')
            self._time_limit_seconds = self._parse_duration_to_seconds(time_limit_raw)
            self._limit_boundary = (self.config.get('recording', 'limit_boundary', fallback='immediate') or 'immediate').lower()
            if self._time_limit_seconds < 0:
                print("Error: time limit cannot be negative")
                return False
        except ValueError as e:
            print(f"Error: {e}")
            return False

        # Build ffmpeg command
        if custom_duration:
            segment_duration = custom_duration
            print(f"📏 Using custom segment duration: {segment_duration} seconds")
        elif test_mode:
            segment_duration = 60  # 1 minute for test mode
            print("🧪 TEST MODE: Using 1-minute segments")
        else:
            segment_duration = self.config.getint('recording', 'segment_duration')
        # Persist for end-segment handling
        try:
            self._segment_duration_seconds = int(segment_duration)
        except Exception:
            self._segment_duration_seconds = 0
        
        sample_rate = self.config.get('recording', 'sample_rate')
        channels = self.config.get('recording', 'channels')
        format_type = self.config.get('recording', 'format')
        
        output_pattern = str(output_path / f"{self.session_id}_chunk_%03d.{format_type}")
        
        # Map requested format to codec/container specifics
        codec = 'libopus' if format_type == 'ogg' else ('flac' if format_type == 'flac' else 'libmp3lame')
        # Choose a speech-friendly bitrate for Opus if applicable
        bitrate = None
        if codec == 'libopus':
            # 24 kbps is a good default for speech; users can still change sample_rate/channels in config
            bitrate = '24k'

        cmd = [
            'ffmpeg',
            '-f', 'pulse',
            '-i', device,
            '-ac', channels,
            '-ar', sample_rate,
            '-c:a', codec,
            '-f', 'segment',
            '-segment_time', str(segment_duration),
            '-segment_format', format_type,  # Explicitly specify segment format
            '-reset_timestamps', '1',
            '-y',  # Overwrite output files
        ]
        if bitrate:
            cmd.extend(['-b:a', bitrate])
        cmd.append(output_pattern)
        
        # Log session metadata before starting process
        if self.session_logger:
            meta = {
                'session_id': self.session_id,
                'device': device,
                'sample_rate': sample_rate,
                'channels': channels,
                'format': format_type,
                'segment_duration_s': segment_duration,
                'time_limit_s': self._time_limit_seconds,
                'output_dir': str(output_path),
            }
            meta_str = ' '.join([f"{k}={v}" for k, v in meta.items()])
            self.session_logger.info(f"session metadata {meta_str}")

        print(f"Starting recording: {self.session_id}")
        print(f"Command: {' '.join(cmd)}")
        if self.session_logger:
            self.session_logger.info(f"session start id={self.session_id} device={device}")
            self.session_logger.info(f"ffmpeg cmd={' '.join(cmd)}")
        
        try:
            # Start ffmpeg process
            self.ffmpeg_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # Create new process group
            )
            
            self.recording = True
            self._recording_start_monotonic = time.monotonic()
            print("Recording started successfully!")
            print(f"Process ID: {self.ffmpeg_process.pid}")
            if self.session_logger:
                self.session_logger.info(f"process pid={self.ffmpeg_process.pid}")

            # Start background stderr reader to capture ffmpeg output
            try:
                self._stderr_thread = threading.Thread(target=self._stream_ffmpeg_stderr, daemon=True)
                self._stderr_thread.start()
            except Exception as _thr_err:
                if self.session_logger:
                    self.session_logger.warning(f"stderr thread failed err={_thr_err}")

            # Start background chunk watcher to log new chunk files
            try:
                self._chunk_thread = threading.Thread(
                    target=self._watch_chunks,
                    args=(output_path, f"{self.session_id}_chunk_*.{format_type}", segment_duration),
                    daemon=True
                )
                self._chunk_thread.start()
            except Exception as _ct_err:
                if self.session_logger:
                    self.session_logger.warning(f"chunk watcher failed err={_ct_err}")
            if segment_duration < 60:
                print(f"Note: Check the output directory for new chunk files every {segment_duration} seconds")
            else:
                minutes = segment_duration // 60
                print(f"Note: Check the output directory for new chunk files every {minutes} minute{'s' if minutes != 1 else ''}")
            # Start limit timer if configured
            try:
                self._start_limit_timer_if_needed()
            except Exception as _lt_err:
                if self.session_logger:
                    self.session_logger.warning(f"limit timer error err={_lt_err}")
            return True
            
        except FileNotFoundError:
            print("Error: ffmpeg not found! Please install ffmpeg.")
            return False
        except Exception as e:
            print(f"Error starting recording: {e}")
            return False

    def _stream_ffmpeg_stderr(self):
        """Continuously read ffmpeg stderr and write to session logger.

        Maps lines containing 'error' to ERROR, 'warn'/'warning' to WARNING.
        All other lines are logged at DEBUG to reduce noise at higher levels.
        """
        if not self.ffmpeg_process or not self.session_logger:
            return
        try:
            assert self.ffmpeg_process.stderr is not None
            for raw in iter(self.ffmpeg_process.stderr.readline, b''):
                if not raw:
                    break
                line = raw.decode('utf-8', errors='replace').strip()
                if not line:
                    continue
                low = line.lower()
                if 'error' in low:
                    self.session_logger.error(f"ffmpeg {line}")
                elif 'warn' in low:
                    self.session_logger.warning(f"ffmpeg {line}")
                else:
                    # Only visible if logger level allows DEBUG
                    self.session_logger.debug(f"ffmpeg {line}")
        except Exception as e:
            try:
                self.session_logger.warning(f"stderr reader exception err={e}")
            except Exception:
                pass

    def _watch_chunks(self, session_dir: Path, pattern: str, segment_duration: int):
        """Poll the session directory for new chunk files, logging creation and final sizes.

        Strategy: when chunk N appears, log its creation; also finalize chunk N-1 with
        its final size if present and not already finalized. On stop, the last chunk
        is finalized in stop flow.
        """
        chunk_index_re = re.compile(r"_chunk_(\d{3})\.")
        try:
            while self.recording:
                files = sorted(session_dir.glob(pattern))
                for f in files:
                    name = f.name
                    if name not in self._known_chunks:
                        # First time seeing this chunk: creation
                        try:
                            size = f.stat().st_size
                        except FileNotFoundError:
                            size = 0
                        self._known_chunks.add(name)
                        if self.session_logger:
                            self.session_logger.info(f"chunk created file={name} size={size}B")

                        # Attempt to finalize previous chunk if applicable
                        m = chunk_index_re.search(name)
                        if m:
                            try:
                                cur_idx = int(m.group(1))
                            except ValueError:
                                cur_idx = None
                            if cur_idx is not None and cur_idx > 0:
                                prev_name = name.replace(f"_chunk_{cur_idx:03d}.", f"_chunk_{cur_idx-1:03d}.")
                                if prev_name not in self._finalized_chunks:
                                    prev_path = session_dir / prev_name
                                    if prev_path.exists():
                                        try:
                                            final_size = prev_path.stat().st_size
                                        except FileNotFoundError:
                                            final_size = 0
                                        if self.session_logger:
                                            self.session_logger.info(f"chunk finalized file={prev_name} size={final_size}B")
                                        self._finalized_chunks.add(prev_name)
                time.sleep(min(2, max(1, segment_duration // 10)))
        except Exception as e:
            if self.session_logger:
                self.session_logger.warning(f"chunk watcher exception err={e}")
    
    def stop_recording(self, reason: str = "user_request") -> bool:
        """Stop the current recording.

        Args:
            reason: Reason for stopping, used for logging (e.g., 'user_request', 'time_limit', 'force_kill').
        """
        if not self.recording or not self.ffmpeg_process:
            print("No active recording to stop.")
            return False
        
        try:
            print("Stopping recording gracefully...")
            
            # Send SIGTERM to the process group
            os.killpg(os.getpgid(self.ffmpeg_process.pid), signal.SIGTERM)
            
            # Wait for process to terminate with longer timeout for proper finalization
            self.ffmpeg_process.wait(timeout=10)
            
            # Check for any errors
            stderr_output = self.ffmpeg_process.stderr.read().decode('utf-8')
            if stderr_output and "error" in stderr_output.lower():
                print(f"ffmpeg stderr: {stderr_output}")
            
            self.recording = False
            self.ffmpeg_process = None
            print("Recording stopped successfully!")
            
            # Check if we need to fix the last segment
            self._fix_last_segment_metadata()
            # Log stop summary
            try:
                if self.session_logger:
                    # Finalize the last chunk size if not already
                    try:
                        output_dir = os.path.expanduser(self.config.get('recording', 'output_dir'))
                        session_dir = Path(output_dir) / self.session_id.split('_')[0]
                        all_chunks = sorted(session_dir.glob(f"{self.session_id.split('_')[0]}_*_chunk_*.{self.config.get('recording', 'format', fallback='ogg')}"))
                        if all_chunks:
                            last = all_chunks[-1].name
                            if last not in self._finalized_chunks:
                                final_size = all_chunks[-1].stat().st_size
                                self.session_logger.info(f"chunk finalized file={last} size={final_size}B")
                                self._finalized_chunks.add(last)
                    except Exception:
                        pass
                    # Count chunks for this session
                    output_dir = os.path.expanduser(self.config.get('recording', 'output_dir'))
                    session_dir = Path(output_dir) / self.session_id.split('_')[0]
                    files = list(session_dir.glob(f"{self.session_id.split('_')[0]}_*_chunk_*.{self.config.get('recording', 'format', fallback='ogg')}"))
                    count = len(files)
                    duration_s = 0.0
                    if self._recording_start_monotonic is not None:
                        duration_s = max(0.0, time.monotonic() - self._recording_start_monotonic)
                    self.session_logger.info(f"session stop reason={reason} chunks={count} duration={duration_s:.1f}s")
            finally:
                self._flush_session_logger()
            return True
            
        except subprocess.TimeoutExpired:
            print("Process didn't stop gracefully, force stopping...")
            # Force kill if it doesn't stop gracefully
            os.killpg(os.getpgid(self.ffmpeg_process.pid), signal.SIGKILL)
            self.ffmpeg_process = None
            self.recording = False
            print("Recording force-stopped.")
            try:
                if self.session_logger:
                    output_dir = os.path.expanduser(self.config.get('recording', 'output_dir'))
                    session_dir = Path(output_dir) / self.session_id.split('_')[0]
                    files = list(session_dir.glob(f"{self.session_id.split('_')[0]}_*_chunk_*.flac"))
                    count = len(files)
                    duration_s = 0.0
                    if self._recording_start_monotonic is not None:
                        duration_s = max(0.0, time.monotonic() - self._recording_start_monotonic)
                    self.session_logger.info(f"session stop reason=force_kill chunks={count} duration={duration_s:.1f}s")
            finally:
                self._flush_session_logger()
            return True
        except Exception as e:
            print(f"Error stopping recording: {e}")
            try:
                if self.session_logger:
                    self.session_logger.error(f"stop exception err={e}")
            finally:
                self._flush_session_logger()
            return False
    
    def is_recording(self) -> bool:
        """Check if currently recording."""
        if not self.recording or not self.ffmpeg_process:
            return False
        
        # Check if process is still running
        try:
            return self.ffmpeg_process.poll() is None
        except:
            return False
    
    def get_status(self) -> Dict[str, any]:
        """Get current recording status."""
        log_path = None
        if self._session_dir is not None:
            candidate = self._session_dir / 'session.log'
            log_path = str(candidate)
        
        # Calculate elapsed time if recording
        elapsed_seconds = 0
        if self.is_recording() and self._recording_start_monotonic is not None:
            elapsed_seconds = int(time.monotonic() - self._recording_start_monotonic)
        
        # Calculate segment progress
        segment_duration = self._segment_duration_seconds if self._segment_duration_seconds > 0 else 300
        segment_elapsed = 0
        segment_remaining = segment_duration
        current_chunk = 0
        
        if self.is_recording() and elapsed_seconds > 0:
            current_chunk = (elapsed_seconds // segment_duration) + 1
            segment_elapsed = elapsed_seconds % segment_duration
            segment_remaining = segment_duration - segment_elapsed
        
        # Get device name from config
        device_name = self.config.get('audio', 'device_name', fallback='')
        if not device_name or self.config.getboolean('audio', 'auto_detect_device', fallback=True):
            device_name = 'Auto-detect'
        
        # Get format display name
        fmt = self.config.get('recording', 'format', fallback='ogg')
        format_display = {
            'ogg': 'OGG/Opus',
            'mp3': 'MP3',
            'flac': 'FLAC',
            'wav': 'WAV'
        }.get(fmt, fmt.upper())
        
        # Build chunk list with filenames, sizes, and completion status
        chunks: List[Dict[str, Any]] = []
        if self._session_dir is not None and self.session_id:
            try:
                fmt = self.config.get('recording', 'format', fallback='ogg')
                session_name = self.session_id.split('_')[0]
                pattern = f"{session_name}_*_chunk_*.{fmt}"
                chunk_files = sorted(self._session_dir.glob(pattern))
                for chunk_file in chunk_files:
                    name = chunk_file.name
                    try:
                        size_bytes = chunk_file.stat().st_size
                    except (FileNotFoundError, OSError):
                        size_bytes = 0
                    is_finalized = name in self._finalized_chunks
                    chunks.append({
                        'filename': name,
                        'size_bytes': size_bytes,
                        'finalized': is_finalized,
                    })
            except Exception:
                pass
        
        # Calculate disk space in output directory
        disk_free_bytes = 0
        try:
            output_dir = os.path.expanduser(self.config.get('recording', 'output_dir'))
            stat = os.statvfs(output_dir)
            disk_free_bytes = stat.f_bavail * stat.f_frsize
        except Exception:
            pass
        
        return {
            'recording': self.is_recording(),
            'session_id': self.session_id,
            'process_id': self.ffmpeg_process.pid if self.ffmpeg_process else None,
            'log_path': log_path,
            'elapsed_seconds': elapsed_seconds,
            'segment_duration_seconds': segment_duration,
            'segment_elapsed_seconds': segment_elapsed,
            'segment_remaining_seconds': segment_remaining,
            'current_chunk_number': current_chunk,
            'device_name': device_name,
            'format': format_display,
            'sample_rate': self.config.get('recording', 'sample_rate', fallback='16000'),
            'chunks': chunks,
            'disk_free_bytes': disk_free_bytes,
        }
    
    def check_recording_files(self) -> List[str]:
        """Check what recording files have been created."""
        if not self.session_id:
            return []
        
        # Get the output directory from config
        output_dir = os.path.expanduser(self.config.get('recording', 'output_dir'))
        session_dir = Path(output_dir) / self.session_id.split('_')[0]  # Get session name without timestamp
        
        if not session_dir.exists():
            return []
        
        # Find all files matching the session pattern
        pattern = f"{self.session_id.split('_')[0]}_*_chunk_*.{self.config.get('recording', 'format', fallback='ogg')}"
        files = list(session_dir.glob(pattern))
        return sorted([f.name for f in files])
    
    def _fix_last_segment_metadata(self):
        """Fix metadata for the last segment if it was stopped mid-segment."""
        if not self.session_id:
            return
        
        try:
            # Get the output directory
            output_dir = os.path.expanduser(self.config.get('recording', 'output_dir'))
            session_dir = Path(output_dir) / self.session_id.split('_')[0]
            
            if not session_dir.exists():
                return
            
            # Find all chunk files
            pattern = f"{self.session_id.split('_')[0]}_*_chunk_*.flac"
            files = sorted(session_dir.glob(pattern))
            
            if len(files) < 2:
                return  # Need at least 2 files to compare
            
            # Check if the last file is unusually large (indicating mid-segment stop)
            last_file = files[-1]
            second_last_file = files[-2]
            
            last_size = last_file.stat().st_size
            second_last_size = second_last_file.stat().st_size
            
            # If last file is significantly larger than the second last, it might be mid-segment
            if last_size > second_last_size * 1.5:  # 50% larger
                print(f"⚠️  Last segment appears to be incomplete: {last_file.name}")
                print(f"   Size: {last_size / (1024*1024):.1f} MB (expected ~{second_last_size / (1024*1024):.1f} MB)")
                print("   This is normal when stopping mid-segment.")
                print("   The file contains all recorded audio but metadata may be incorrect.")
                
        except Exception as e:
            print(f"Warning: Could not check last segment metadata: {e}")


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description='Echolog - Audio Recording Application')
    parser.add_argument('action', choices=['start', 'stop', 'status', 'devices', 'files', 'tui'], 
                       help='Action to perform')
    parser.add_argument('--session-id', '-s', help='Session identifier for recording')
    parser.add_argument('--output-dir', '-o', help='Output directory for recordings')
    parser.add_argument('--config', '-c', default='echolog.conf', 
                       help='Configuration file path')
    parser.add_argument('--device', '-D', help='Override PulseAudio source (e.g., <sink_name>.monitor)')
    parser.add_argument('--test', '-t', action='store_true',
                       help='Test mode: use 1-minute segments instead of configured duration')
    parser.add_argument('--segment-duration', '-d', type=int,
                       help='Custom segment duration in seconds (overrides config)')
    parser.add_argument('--time-limit', '-T', type=str,
                        help='Total recording time limit (e.g., 90s, 30m, 2h, or seconds)')
    parser.add_argument('--limit-boundary', type=str, choices=['immediate', 'end-segment'],
                        help='Whether to stop immediately at limit or after current segment')
    # Logging CLI overrides
    parser.add_argument('--log-level', choices=['debug', 'info', 'warning', 'error'],
                        help='Logging level for session logs')
    parser.add_argument('--log-rotation', choices=['size', 'time', 'off'],
                        help='Logging rotation strategy (size|time|off)')
    parser.add_argument('--log-max-bytes', type=int,
                        help='Max size in bytes before rotating session.log')
    parser.add_argument('--log-backup-count', type=int,
                        help='Number of rotated session.log files to keep')
    
    args = parser.parse_args()
    
    # Create recorder instance
    recorder = EchologRecorder(args.config)

    # Apply CLI logging overrides with precedence over config
    if any([args.log_level, args.log_rotation, args.log_max_bytes, args.log_backup_count]):
        if not recorder.config.has_section('logging'):
            recorder.config.add_section('logging')
        if args.log_level:
            recorder.config.set('logging', 'level', args.log_level)
        if args.log_rotation:
            recorder.config.set('logging', 'rotation', args.log_rotation)
        if args.log_max_bytes is not None:
            recorder.config.set('logging', 'max_bytes', str(args.log_max_bytes))
        if args.log_backup_count is not None:
            recorder.config.set('logging', 'backup_count', str(args.log_backup_count))
    
    # Apply CLI time limit overrides with precedence over config
    if args.time_limit is not None:
        if not recorder.config.has_section('recording'):
            recorder.config.add_section('recording')
        recorder.config.set('recording', 'time_limit', args.time_limit)
    if args.limit_boundary is not None:
        if not recorder.config.has_section('recording'):
            recorder.config.add_section('recording')
        recorder.config.set('recording', 'limit_boundary', args.limit_boundary)

    if args.action == 'devices':
        print("Available audio devices:")
        devices = recorder.detect_audio_devices()
        for i, device in enumerate(devices):
            print(f"  {i+1}. {device['name']}")
        return
    
    elif args.action == 'start':
        if not args.session_id:
            print("Error: --session-id is required for start action")
            sys.exit(1)
        
        # Device CLI override takes precedence
        if args.device:
            if not recorder.config.has_section('audio'):
                recorder.config.add_section('audio')
            recorder.config.set('audio', 'device_name', args.device)

        success = recorder.start_recording(args.session_id, args.output_dir, args.test, args.segment_duration)
        if not success:
            sys.exit(1)
        
        # Keep running until interrupted
        try:
            while recorder.is_recording():
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping recording...")
            recorder.stop_recording()
    
    elif args.action == 'stop':
        recorder.stop_recording()
    
    elif args.action == 'status':
        status = recorder.get_status()
        print(f"Recording: {status['recording']}")
        if status['session_id']:
            print(f"Session ID: {status['session_id']}")
        if status['process_id']:
            print(f"Process ID: {status['process_id']}")
        if status.get('log_path'):
            print(f"Log: {status['log_path']}")
        
        # Show created files
        files = recorder.check_recording_files()
        if files:
            print(f"Created files ({len(files)}):")
            for file in files:
                print(f"  - {file}")
        else:
            print("No recording files found yet.")
    
    elif args.action == 'files':
        # Show all recording files
        output_dir = os.path.expanduser(recorder.config.get('recording', 'output_dir'))
        recordings_dir = Path(output_dir)
        
        if not recordings_dir.exists():
            print(f"No recordings directory found at {output_dir}")
            return
        
        print(f"Recording files in {output_dir}:")
        for session_dir in recordings_dir.iterdir():
            if session_dir.is_dir():
                print(f"\nSession: {session_dir.name}")
                ext = recorder.config.get('recording', 'format', fallback='ogg')
                fmt_files = list(session_dir.glob(f"*.{ext}"))
                if fmt_files:
                    for file in sorted(fmt_files):
                        size_mb = file.stat().st_size / (1024 * 1024)
                        print(f"  - {file.name} ({size_mb:.1f} MB)")
                else:
                    print(f"  No {ext.upper()} files found")
    
    elif args.action == 'tui':
        from echolog_tui import run_tui
        run_tui(recorder=recorder)


if __name__ == '__main__':
    main()
