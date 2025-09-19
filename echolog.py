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
import psutil
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict


class EchologRecorder:
    """Main recorder class that wraps ffmpeg for audio capture and segmentation."""
    
    def __init__(self, config_file: str = "echolog.conf"):
        self.config_file = config_file
        self.config = self._load_config()
        self.ffmpeg_process = None
        self.recording = False
        self.session_id = None
        
    def _load_config(self) -> configparser.ConfigParser:
        """Load configuration from file or create default."""
        config = configparser.ConfigParser()
        
        # Default configuration
        default_config = {
            'recording': {
                'segment_duration': '900',  # 15 minutes in seconds
                'sample_rate': '44100',
                'channels': '2',  # stereo
                'format': 'flac',
                'output_dir': '~/recordings'
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
    
    def _save_config(self, config: configparser.ConfigParser):
        """Save configuration to file."""
        with open(self.config_file, 'w') as f:
            config.write(f)
    
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
                    if len(parts) >= 2:
                        devices.append({
                            'name': parts[1],
                            'id': parts[0]
                        })
            
            return devices
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Error: Could not detect audio devices. Make sure PulseAudio is running.")
            return []
    
    def get_default_monitor_device(self) -> Optional[str]:
        """Get the default monitor device for recording."""
        devices = self.detect_audio_devices()
        if not devices:
            return None
            
        # Look for common monitor device patterns
        for device in devices:
            if 'monitor' in device['name'].lower():
                return device['name']
        
        # Return first available device
        return devices[0]['name'] if devices else None
    
    def start_recording(self, session_id: str, output_dir: Optional[str] = None) -> bool:
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
        
        # Get audio device
        device = self.get_default_monitor_device()
        if not device:
            print("Error: No audio device found!")
            return False
        
        print(f"Using audio device: {device}")
        print(f"Output directory: {output_path}")
        
        # Build ffmpeg command
        segment_duration = self.config.getint('recording', 'segment_duration')
        sample_rate = self.config.get('recording', 'sample_rate')
        channels = self.config.get('recording', 'channels')
        format_type = self.config.get('recording', 'format')
        
        output_pattern = str(output_path / f"{self.session_id}_chunk_%03d.{format_type}")
        
        cmd = [
            'ffmpeg',
            '-f', 'pulse',
            '-i', device,
            '-ac', channels,
            '-ar', sample_rate,
            '-c:a', 'flac' if format_type == 'flac' else 'libmp3lame',
            '-f', 'segment',
            '-segment_time', str(segment_duration),
            '-reset_timestamps', '1',
            '-y',  # Overwrite output files
            output_pattern
        ]
        
        print(f"Starting recording: {self.session_id}")
        print(f"Command: {' '.join(cmd)}")
        
        try:
            # Start ffmpeg process
            self.ffmpeg_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # Create new process group
            )
            
            self.recording = True
            print("Recording started successfully!")
            print(f"Process ID: {self.ffmpeg_process.pid}")
            print("Note: Check the output directory for new chunk files every 15 minutes")
            return True
            
        except FileNotFoundError:
            print("Error: ffmpeg not found! Please install ffmpeg.")
            return False
        except Exception as e:
            print(f"Error starting recording: {e}")
            return False
    
    def stop_recording(self) -> bool:
        """Stop the current recording."""
        if not self.recording or not self.ffmpeg_process:
            print("No active recording to stop.")
            return False
        
        try:
            # Send SIGTERM to the process group
            os.killpg(os.getpgid(self.ffmpeg_process.pid), signal.SIGTERM)
            
            # Wait for process to terminate
            self.ffmpeg_process.wait(timeout=5)
            
            # Check for any errors
            stderr_output = self.ffmpeg_process.stderr.read().decode('utf-8')
            if stderr_output and "error" in stderr_output.lower():
                print(f"ffmpeg stderr: {stderr_output}")
            
            self.recording = False
            self.ffmpeg_process = None
            print("Recording stopped successfully!")
            return True
            
        except subprocess.TimeoutExpired:
            # Force kill if it doesn't stop gracefully
            os.killpg(os.getpgid(self.ffmpeg_process.pid), signal.SIGKILL)
            self.ffmpeg_process = None
            self.recording = False
            print("Recording force-stopped.")
            return True
        except Exception as e:
            print(f"Error stopping recording: {e}")
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
        return {
            'recording': self.is_recording(),
            'session_id': self.session_id,
            'process_id': self.ffmpeg_process.pid if self.ffmpeg_process else None
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
        pattern = f"{self.session_id.split('_')[0]}_*_chunk_*.flac"
        files = list(session_dir.glob(pattern))
        return sorted([f.name for f in files])


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description='Echolog - Audio Recording Application')
    parser.add_argument('action', choices=['start', 'stop', 'status', 'devices', 'files'], 
                       help='Action to perform')
    parser.add_argument('--session-id', '-s', help='Session identifier for recording')
    parser.add_argument('--output-dir', '-o', help='Output directory for recordings')
    parser.add_argument('--config', '-c', default='echolog.conf', 
                       help='Configuration file path')
    
    args = parser.parse_args()
    
    # Create recorder instance
    recorder = EchologRecorder(args.config)
    
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
        
        success = recorder.start_recording(args.session_id, args.output_dir)
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
                flac_files = list(session_dir.glob("*.flac"))
                if flac_files:
                    for file in sorted(flac_files):
                        size_mb = file.stat().st_size / (1024 * 1024)
                        print(f"  - {file.name} ({size_mb:.1f} MB)")
                else:
                    print("  No FLAC files found")


if __name__ == '__main__':
    main()
