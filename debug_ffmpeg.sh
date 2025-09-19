#!/bin/bash
# Debug script to test ffmpeg segmentation

echo "Testing ffmpeg segmentation..."

# Get audio device
DEVICE=$(pactl list short sources | grep monitor | head -1 | cut -f2)
echo "Using device: $DEVICE"

# Create test directory
mkdir -p test_recordings

# Test with 10-second segments for 30 seconds total
echo "Starting 30-second test with 10-second segments..."

ffmpeg -f pulse -i "$DEVICE" \
    -ac 2 -ar 44100 -c:a flac \
    -f segment -segment_time 10 -reset_timestamps 1 \
    -y test_recordings/test_chunk_%03d.flac &

FFMPEG_PID=$!
echo "ffmpeg PID: $FFMPEG_PID"

# Let it run for 30 seconds
sleep 30

# Stop ffmpeg
echo "Stopping ffmpeg..."
kill $FFMPEG_PID
wait $FFMPEG_PID 2>/dev/null

# Check results
echo ""
echo "Created files:"
ls -la test_recordings/

echo ""
echo "File sizes:"
for file in test_recordings/test_chunk_*.flac; do
    if [ -f "$file" ]; then
        size=$(stat -c%s "$file")
        size_mb=$(echo "scale=1; $size / 1024 / 1024" | bc)
        echo "  $file: ${size_mb} MB"
    fi
done

# Cleanup
echo ""
echo "Cleaning up..."
rm -rf test_recordings
