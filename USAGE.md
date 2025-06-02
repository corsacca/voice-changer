# Voice Changer Usage Guide

## Overview

This tool changes the voice in recorded videos using AI while maintaining perfect video timing synchronization. It works with all major video players including QuickTime, VLC, and others.

## Quick Start

```bash
# Basic usage
python3 voice_changer.py your_video.mp4

# Specify output file and voice
python3 voice_changer.py input.mp4 -o output.mp4 -v "voice_id_here"

# List available voices
python3 voice_changer.py --list-voices
```

## Setup

1. **Install dependencies:**
   ```bash
   pip install elevenlabs python-dotenv
   pip install openai-whisper  # or faster-whisper
   ```

2. **Set up ElevenLabs API key:**
   - Get your API key from [ElevenLabs](https://elevenlabs.io/)
   - Create a `.env` file: `ELEVEN_LABS_KEY=your_api_key_here`
   - Or set environment variable: `export ELEVENLABS_API_KEY=your_key`

## How It Works

### Processing Steps
1. **Audio Extraction** - Extracts original audio from video
2. **Transcription** - Converts speech to text using Whisper
3. **AI Voice Generation** - Creates new voice using ElevenLabs
4. **Video Speed Adjustment** - Matches video timing to AI voice

### Technical Strategy

The tool uses a **filter-free approach** for maximum compatibility:

- **itsscale method**: Uses ffmpeg's `-itsscale` parameter instead of video filters
- **No timing filters**: Avoids `setpts` and other filters that can cause playback issues
- **Universal compatibility**: Works with all video players without variable speed controls

#### Why This Approach Works

Previous attempts using video filters (`setpts=PTS/ratio`) caused issues:
- Created irregular frame timing
- Triggered variable speed controls in some players
- Inconsistent playback experience

Our solution:
- Uses `-itsscale` to scale input timing naturally
- Maintains consistent frame intervals
- Provides smooth playback across all platforms

## Command Line Options

```bash
python3 voice_changer.py [options] <video_file>

Options:
  -o, --output PATH          Output video path
  -v, --voice ID            ElevenLabs voice ID
  --max-speed-ratio FLOAT   Maximum video speedup (default: 2.5x)
  --no-adjust-video         Keep original video timing
  --list-voices             Show available voices
  --api-key KEY             ElevenLabs API key
```

## Examples

```bash
# Process with default settings
python3 voice_changer.py recording.mp4

# Custom output and voice
python3 voice_changer.py input.mp4 -o my_output.mp4 -v "UgBBYS2sOqTuMpoF3BR0"

# Limit maximum speedup to 2x
python3 voice_changer.py video.mp4 --max-speed-ratio 2.0

# Keep original video timing (no speed adjustment)
python3 voice_changer.py video.mp4 --no-adjust-video
```

## Troubleshooting

### Common Issues

1. **"Could not get transcript"**
   - Install whisper: `pip install openai-whisper`
   - Or manually enter transcript when prompted

2. **"ElevenLabs package not available"**
   - Install: `pip install elevenlabs`
   - Set API key in `.env` file

3. **"ffmpeg not found"**
   - Install ffmpeg: `brew install ffmpeg` (macOS)

### Quality Tips

- **Clear audio**: Ensure original video has clear speech
- **Appropriate speed limits**: Use `--max-speed-ratio` to prevent excessive speedup
- **Voice selection**: Use `--list-voices` to find the best voice for your content

## Technical Details

### Video Processing Pipeline

```
Input Video → Audio Extraction → Transcription → AI Voice → Video Speed Adjustment → Output
```

### ffmpeg Command Structure

The tool generates commands like:
```bash
ffmpeg -itsscale 0.67 -i video.mp4 -i ai_voice.mp3 \
  -c:v libx264 -c:a aac \
  -profile:v baseline -pix_fmt yuv420p \
  -movflags +faststart \
  output.mp4
```

Key parameters:
- `-itsscale`: Scales input timing (filter-free)
- `-profile:v baseline`: Maximum compatibility
- `-movflags +faststart`: Optimized for streaming

### Compatibility Notes

- **All major players**: QuickTime, VLC, Chrome, Safari, etc.
- **No variable speed controls**: Clean playback experience
- **Consistent timing**: Maintains smooth frame intervals
- **Universal format**: MP4 with H.264/AAC encoding

## Performance

- **Processing time**: ~2-3x video duration
- **Quality**: Maintains original video quality
- **File size**: Similar to original (efficient encoding)
- **Memory usage**: Minimal (streaming processing)

## Advanced Usage

### Custom Voice Training
- Use ElevenLabs voice cloning for personalized voices
- Train on your own voice samples for best results

### Batch Processing
```bash
# Process multiple files
for file in *.mp4; do
  python3 voice_changer.py "$file" -o "voiced_$file"
done
```

### Integration
The `VideoVoiceChanger` class can be imported and used in other Python scripts:

```python
from voice_changer import VideoVoiceChanger

changer = VideoVoiceChanger(api_key="your_key")
changer.process_video("input.mp4", "output.mp4")
``` 