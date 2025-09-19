#!/usr/bin/env python3
"""
Test script to debug ffmpeg segmentation issues
"""

import subprocess
import time
import os
from pathlib import Path

def test_ffmpeg_segmentation():
    """Test ffmpeg segmentation with a short duration"""
    
    # Create test directory
    test_dir = Path("test_recordings")
    test_dir.mkdir(exist_ok=True)
    
    # Test parameters
    segment_duration = 10  # 10 seconds for testing
    total_duration = 30    # 30 seconds total
    
    print("Testing ffmpeg segmentation...")
    print(f"Segment duration: {segment_duration} seconds")
    print(f"Total duration: {total_duration} seconds")
    print(f"Expected chunks: {total_duration // segment_duration}")
    
    # Get audio device
    try:
        result = subprocess.run(['pactl', 'list', 'short', 'sources'], 
                              capture_output=True, text=True, check=True)
        devices = [line for line in result.stdout.strip().split('\n') if 'monitor' in line]
        if not devices:
            print("No audio devices found!")
            return
        device = devices[0].split('\t')[1]
        print(f"Using device: {device}")
    except Exception as e:
        print(f"Error getting audio device: {e}")
        return
    
    # Build ffmpeg command
    output_pattern = str(test_dir / "test_chunk_%03d.flac")
    
    cmd = [
        'ffmpeg',
        '-f', 'pulse',
        '-i', device,
        '-ac', '2',
        '-ar', '44100',
        '-c:a', 'flac',
        '-f', 'segment',
        '-segment_time', str(segment_duration),
        '-reset_timestamps', '1',
        '-y',
        output_pattern
    ]
    
    print(f"Command: {' '.join(cmd)}")
    print("Starting test recording...")
    
    try:
        # Start ffmpeg process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )
        
        print(f"Process started with PID: {process.pid}")
        
        # Let it run for the total duration
        time.sleep(total_duration)
        
        # Stop the process
        print("Stopping recording...")
        os.killpg(os.getpgid(process.pid), subprocess.signal.SIGTERM)
        process.wait(timeout=5)
        
        # Check output
        stderr_output = process.stderr.read().decode('utf-8')
        if stderr_output:
            print(f"ffmpeg stderr: {stderr_output}")
        
        # Check created files
        flac_files = list(test_dir.glob("test_chunk_*.flac"))
        print(f"\nCreated {len(flac_files)} files:")
        for file in sorted(flac_files):
            size_mb = file.stat().st_size / (1024 * 1024)
            print(f"  - {file.name} ({size_mb:.1f} MB)")
        
        if len(flac_files) < (total_duration // segment_duration):
            print(f"\n⚠️  WARNING: Expected {total_duration // segment_duration} chunks, got {len(flac_files)}")
            print("This indicates a segmentation problem!")
        else:
            print("\n✅ Segmentation working correctly!")
            
    except Exception as e:
        print(f"Error during test: {e}")
    finally:
        # Cleanup
        print(f"\nCleaning up test files in {test_dir}...")
        for file in test_dir.glob("test_chunk_*.flac"):
            file.unlink()
        test_dir.rmdir()

if __name__ == "__main__":
    test_ffmpeg_segmentation()
